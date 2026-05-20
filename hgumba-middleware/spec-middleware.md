# Middleware H Gu Marabá — Spec-first

## Visão Geral

API Gateway que orquestra a integração entre o SENAITE LIS (Laboratório) e os sistemas do Exército Brasileiro (SANDRA, SIRE, CADBEN).

**Stack:** Python 3.12+ / FastAPI / Pydantic / httpx / uvicorn

**Função:** Blindar o SENAITE de mudanças externas, validar dados na entrada, e traduzir contratos entre os sistemas.

---

## Rotas

### 1. SANDRA → Middleware (Ingestão de Pedidos)

```http
POST /api/v1/sandra/ingestao
Content-Type: application/json
Accept: application/json

{
  "id_pedido": "PED-2026-0001",
  "cpf_paciente": "12345678901",
  "nome_paciente": "JOÃO SILVA",
  "medico_solicitante": "Dr. Carlos Almeida",
  "crm_solicitante": "12345-AM",
  "data_solicitacao": "2026-05-18T10:30:00Z",
  "exames": [
    {"codigo_catserv": "HEM001", "descricao": "Hemograma Completo", "urgente": false},
    {"codigo_catserv": "GLI001", "descricao": "Glicemia em Jejum", "urgente": true}
  ]
}
```

**Resposta (202 Accepted):**
```json
{
  "status": "aceito",
  "id_pedido": "PED-2026-0001",
  "mensagem": "Pedido em processamento"
}
```

**Fluxo interno (BackgroundTasks):**
1. Validar elegibilidade no CADBEN
2. Validar autorização no SIRE
3. Mapear `codigo_catserv` → UID AnalysisService (via tabela CATSERV no PostgreSQL)
4. Criar AnalysisRequest no SENAITE via `@@hgumba-create-ar` (bypass do `@@API/create` que bloqueia AR)

### 2. SENAITE → Middleware (Webhook Laudo Publicado)

```http
POST /api/v1/senaite/webhook/laudo_publicado
Content-Type: application/json

{
  "analysis_request_id": "HGU-AR-001",
  "client_id": "hgu",
  "patient_name": "JOÃO SILVA",
  "pdf_url": "http://senaite:8080/clients/hgu/HGU-AR-001/@@cdm-pdf",
  "review_state": "published",
  "results": [
    {"analysis": "Hemograma", "result": "5.2", "unit": "milhões/mm³", "status": "published"}
  ]
}
```

**Resposta:**
```json
{
  "status": "processado",
  "analysis_request_id": "HGU-AR-001",
  "sandra_notificado": true
}
```

**Fluxo:**
1. Validar que `review_state == "published"`
2. Buscar PDF do laudo via `@@cdm-pdf` ou `@@hgumba-report-pdf`
3. Codificar em base64
4. Enviar ao SANDRA via `POST /api/v1/resultados`

### 3. Health Check

```http
GET /health
```

```json
{
  "status": "healthy",
  "service": "hgumba-middleware",
  "version": "1.0.0"
}
```

---

## Contratos de Dados (Pydantic)

### `sandra.py`

| Modelo | Campo | Tipo | Validação |
|--------|-------|------|-----------|
| `ExameSolicitado` | `codigo_catserv` | `str` | Obrigatório |
| | `descricao` | `str` | — |
| | `urgente` | `bool` | Default `false` |
| `OrdemServicoSANDRA` | `id_pedido` | `str` | Obrigatório |
| | `cpf_paciente` | `str` | `pattern=r"^\d{11}$"` |
| | `nome_paciente` | `str` | — |
| | `medico_solicitante` | `str` | — |
| | `crm_solicitante` | `str` | — |
| | `data_solicitacao` | `datetime` | ISO 8601 |
| | `exames` | `List[ExameSolicitado]` | Mínimo 1 |
| `ResultadoExameSANDRA` | `id_pedido` | `str` | — |
| | `cpf_paciente` | `str` | — |
| | `analysis_request_id` | `str` | — |
| | `pdf_laudo_base64` | `str` | Base64 |
| | `data_publicacao` | `datetime` | — |
| | `observacoes` | `Optional[str]` | — |

### `cadben.py`

| Modelo | Campo | Tipo | Validação |
|--------|-------|------|-----------|
| `BeneficiarioCADBEN` | `cpf` | `str` | `pattern=r"^\d{11}$"` |
| | `nome` | `str` | — |
| | `posto_graduacao` | `Optional[str]` | — |
| | `organizacao_militar` | `Optional[str]` | — |
| | `ativo` | `bool` | Default `true` |
| | `data_nascimento` | `Optional[date]` | — |
| `ElegibilidadeResponse` | `cpf` | `str` | — |
| | `elegivel` | `bool` | — |
| | `motivo` | `Optional[str]` | — |
| | `beneficiario` | `Optional[BeneficiarioCADBEN]` | — |

### `senaite.py`

| Modelo | Campo | Tipo | Descrição |
|--------|-------|------|-----------|
| `AnalysisRequestPayload` | `client_id` | `str` | Default `"hgu"` |
| | `contact_uid` | `Optional[str]` | UID do médico solicitante |
| | `patient_uid` | `Optional[str]` | UID do paciente |
| | `services` | `List[str]` | Lista de UIDs/códigos CATSERV |
| | `title` | `Optional[str]` | — |
| `WebhookLaudoPayload` | `analysis_request_id` | `str` | ID da AR publicada |
| | `client_id` | `str` | — |
| | `patient_name` | `Optional[str]` | — |
| | `pdf_url` | `Optional[str]` | — |
| | `review_state` | `str` | Estado do workflow |
| | `results` | `Optional[List[dict]]` | Resultados dos exames |

---

## Arquitetura

```
┌──────────┐     POST /api/v1/sandra/ingestao     ┌──────────────────┐
│  SANDRA  │ ──────────────────────────────────►   │                  │
│ (Pront.) │                                       │   MIDDLEWARE     │
└──────────┘                                       │   FastAPI        │
                                                   │   8000           │
┌──────────┐     POST /api/v1/senaite/...          │                  │
│ SENAITE  │ ◄──────────────────────────────────   │  ┌─ ingestao.py  │
│ (LIS)    │                                       │  ├─ webhooks.py  │
└──────────┘                                       │  ├─ senaite_api  │
                                                   │  └─ exercito_api │
┌──────────┐                                       └────────┬─────────┘
│ CADBEN   │ ◄─────── GET /api/v1/beneficiarios            │
│ (Elegib.)│                                                │
└──────────┘                                     ┌──────────▼─────────┐
                                                  │  PostgreSQL        │
┌──────────┐                                      │  (CATSERV billing) │
│  SIRE    │ ◄─────── GET /api/v1/guias           └────────────────────┘
│ (Verba)  │
└──────────┘
```

### Camadas

| Camada | Módulo | Responsabilidade |
|--------|--------|------------------|
| **Router** | `routers/ingestao.py` | Endpoints de entrada (SANDRA) |
| | `routers/webhooks.py` | Webhooks de saída (SENAITE) |
| **Client** | `clients/senaite_api.py` | httpx AsyncClient para JSON API do SENAITE |
| | `clients/exercito_api.py` | httpx AsyncClient para CADBEN/SIRE/SANDRA |
| **Model** | `models/sandra.py` | Schemas Pydantic — contratos SANDRA |
| | `models/cadben.py` | Schemas Pydantic — contratos CADBEN |
| | `models/senaite.py` | Schemas Pydantic — contratos SENAITE |
| **Config** | `config.py` | `BaseSettings` via variáveis de ambiente /.env |

---

## Configuração

Variáveis de ambiente (`.env`):

```
SENAITE_URL=http://localhost:8083/senaite
SENAITE_USER=admin
SENAITE_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5433
DB_NAME=financeiro
DB_USER=catserv
DB_PASSWORD=catserv_secret
SANDRA_BASE_URL=
CADBEN_BASE_URL=
SIRE_BASE_URL=
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
```

---

## Execução

```bash
# Desenvolvimento (hot-reload)
uv run uvicorn src.main:app --reload --port 8000

# Produção
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Teste de health
curl http://localhost:8000/health
```

---

## Próximos Passos

1. **Mapeamento CATSERV**: Integrar tabela `tabela_catserv` do PostgreSQL para converter `codigo_catserv` → UID/ID do AnalysisService no SENAITE.
2. **Configurar Webhook no SENAITE**: Registrar o webhook `POST /api/v1/senaite/webhook/laudo_publicado` no Zope Management Interface (via `@@webhooks-controlpanel` ou ZCML).
3. **Dockerizar**: `compose.middleware.yaml` com o middleware ao lado do SENAITE.
4. **Autenticação SANDRA**: Quando API real for fornecida, substituir mocks por autenticação real.

---

*Documento gerado em 2026-05-18 | v1.0.0*
