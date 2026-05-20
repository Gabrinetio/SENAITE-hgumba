> **Origem:** `SENAITE/hgumba-middleware/spec-middleware.md`

# Middleware HGUMBA â€” Spec-first

## VisÃ£o Geral

API Gateway que orquestra a integraÃ§Ã£o entre o SENAITE LIS (LaboratÃ³rio) e os sistemas do ExÃ©rcito Brasileiro (SANDRA, SIRE, CADBEN).

**Stack:** Python 3.12+ / FastAPI / Pydantic / httpx / uvicorn

**FunÃ§Ã£o:** Blindar o SENAITE de mudanÃ§as externas, validar dados na entrada, e traduzir contratos entre os sistemas.

---

## Rotas

### 1. SANDRA â†’ Middleware (IngestÃ£o de Pedidos)

```http
POST /api/v1/sandra/ingestao
Content-Type: application/json
Accept: application/json

{
  "id_pedido": "PED-2026-0001",
  "cpf_paciente": "12345678901",
  "nome_paciente": "JOÃƒO SILVA",
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
2. Validar autorizaÃ§Ã£o no SIRE
3. Mapear `codigo_catserv` â†’ UID AnalysisService (via tabela CATSERV no PostgreSQL)
4. Criar AnalysisRequest no SENAITE via `@@hgumba-create-ar` (bypass do `@@API/create` que bloqueia AR)

### 2. SENAITE â†’ Middleware (Webhook Laudo Publicado)

```http
POST /api/v1/senaite/webhook/laudo_publicado
Content-Type: application/json

{
  "analysis_request_id": "HGU-AR-001",
  "client_id": "hgu",
  "patient_name": "JOÃƒO SILVA",
  "pdf_url": "http://senaite:8080/clients/hgu/HGU-AR-001/@@cdm-pdf",
  "review_state": "published",
  "results": [
    {"analysis": "Hemograma", "result": "5.2", "unit": "milhÃµes/mmÂ³", "status": "published"}
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

| Modelo | Campo | Tipo | ValidaÃ§Ã£o |
|--------|-------|------|-----------|
| `ExameSolicitado` | `codigo_catserv` | `str` | ObrigatÃ³rio |
| | `descricao` | `str` | â€” |
| | `urgente` | `bool` | Default `false` |
| `OrdemServicoSANDRA` | `id_pedido` | `str` | ObrigatÃ³rio |
| | `cpf_paciente` | `str` | `pattern=r"^\d{11}$"` |
| | `nome_paciente` | `str` | â€” |
| | `medico_solicitante` | `str` | â€” |
| | `crm_solicitante` | `str` | â€” |
| | `data_solicitacao` | `datetime` | ISO 8601 |
| | `exames` | `List[ExameSolicitado]` | MÃ­nimo 1 |
| `ResultadoExameSANDRA` | `id_pedido` | `str` | â€” |
| | `cpf_paciente` | `str` | â€” |
| | `analysis_request_id` | `str` | â€” |
| | `pdf_laudo_base64` | `str` | Base64 |
| | `data_publicacao` | `datetime` | â€” |
| | `observacoes` | `Optional[str]` | â€” |

### `cadben.py`

| Modelo | Campo | Tipo | ValidaÃ§Ã£o |
|--------|-------|------|-----------|
| `BeneficiarioCADBEN` | `cpf` | `str` | `pattern=r"^\d{11}$"` |
| | `nome` | `str` | â€” |
| | `posto_graduacao` | `Optional[str]` | â€” |
| | `organizacao_militar` | `Optional[str]` | â€” |
| | `ativo` | `bool` | Default `true` |
| | `data_nascimento` | `Optional[date]` | â€” |
| `ElegibilidadeResponse` | `cpf` | `str` | â€” |
| | `elegivel` | `bool` | â€” |
| | `motivo` | `Optional[str]` | â€” |
| | `beneficiario` | `Optional[BeneficiarioCADBEN]` | â€” |

### `senaite.py`

| Modelo | Campo | Tipo | DescriÃ§Ã£o |
|--------|-------|------|-----------|
| `AnalysisRequestPayload` | `client_id` | `str` | Default `"hgu"` |
| | `contact_uid` | `Optional[str]` | UID do mÃ©dico solicitante |
| | `patient_uid` | `Optional[str]` | UID do paciente |
| | `services` | `List[str]` | Lista de UIDs/cÃ³digos CATSERV |
| | `title` | `Optional[str]` | â€” |
| `WebhookLaudoPayload` | `analysis_request_id` | `str` | ID da AR publicada |
| | `client_id` | `str` | â€” |
| | `patient_name` | `Optional[str]` | â€” |
| | `pdf_url` | `Optional[str]` | â€” |
| | `review_state` | `str` | Estado do workflow |
| | `results` | `Optional[List[dict]]` | Resultados dos exames |

---

## Arquitetura

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     POST /api/v1/sandra/ingestao     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  SANDRA  â”‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º   â”‚                  â”‚
â”‚ (Pront.) â”‚                                       â”‚   MIDDLEWARE     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                       â”‚   FastAPI        â”‚
                                                    â”‚   8000           â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     POST /api/v1/senaite/...          â”‚                  â”‚
â”‚ SENAITE  â”‚ â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚  â”Œâ”€ ingestao.py  â”‚
â”‚ (LIS)    â”‚                                       â”‚  â”œâ”€ webhooks.py  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                       â”‚  â”œâ”€ senaite_api  â”‚
                                                    â”‚  â””â”€ exercito_api â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                                       â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”‚ CADBEN   â”‚ â—„â”€â”€â”€â”€â”€â”€â”€ GET /api/v1/beneficiarios            â”‚
â”‚ (Elegib.)â”‚                                                â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                                   â”‚  PostgreSQL        â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                                      â”‚  (CATSERV billing) â”‚
â”‚  SIRE    â”‚ â—„â”€â”€â”€â”€â”€â”€â”€ GET /api/v1/guias           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”‚ (Verba)  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Camadas

| Camada | MÃ³dulo | Responsabilidade |
|--------|--------|------------------|
| **Router** | `routers/ingestao.py` | Endpoints de entrada (SANDRA) |
| | `routers/webhooks.py` | Webhooks de saÃ­da (SENAITE) |
| **Client** | `clients/senaite_api.py` | httpx AsyncClient para JSON API do SENAITE |
| | `clients/exercito_api.py` | httpx AsyncClient para CADBEN/SIRE/SANDRA |
| **Model** | `models/sandra.py` | Schemas Pydantic â€” contratos SANDRA |
| | `models/cadben.py` | Schemas Pydantic â€” contratos CADBEN |
| | `models/senaite.py` | Schemas Pydantic â€” contratos SENAITE |
| **Config** | `config.py` | `BaseSettings` via variÃ¡veis de ambiente /.env |

---

## ConfiguraÃ§Ã£o

VariÃ¡veis de ambiente (`.env`):

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

## ExecuÃ§Ã£o

```bash
# Desenvolvimento (hot-reload)
uv run uvicorn src.main:app --reload --port 8000

# ProduÃ§Ã£o
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Teste de health
curl http://localhost:8000/health
```

---

## PrÃ³ximos Passos

1. **Mapeamento CATSERV**: Integrar tabela `tabela_catserv` do PostgreSQL para converter `codigo_catserv` â†’ UID/ID do AnalysisService no SENAITE.
2. **Configurar Webhook no SENAITE**: Registrar o webhook `POST /api/v1/senaite/webhook/laudo_publicado` no Zope Management Interface (via `@@webhooks-controlpanel` ou ZCML).
3. **Dockerizar**: `compose.middleware.yaml` com o middleware ao lado do SENAITE.
4. **AutenticaÃ§Ã£o SANDRA**: Quando API real for fornecida, substituir mocks por autenticaÃ§Ã£o real.

---

*Documento gerado em 2026-05-18 | v1.0.0*
