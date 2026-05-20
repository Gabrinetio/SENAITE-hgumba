# H Gu Marabá Middleware

API Gateway que orquestra a integração entre o **SENAITE LIS**, os **5 analisadores clínicos** e os sistemas do **Exército Brasileiro** (SANDRA, SIRE, CADBEN).

Stack: **Python 3.12+ / FastAPI / httpx / Pydantic / uv**

---

## Arquitetura

```
┌──────────┐     ASTM E1381/E1394 (TCP)     ┌───────────────────┐
│ Mindray  │───── porta 5001 ──────────────►│                   │
│ BS-200   │                                │  INSTRUMENTS      │
├──────────┤                                │  Daemon TCP       │
│ Sysmex   │───── porta 5002 ──────────────►│  (async)          │
│ XN-550   │                                │                   │
├──────────┤                                │  ┌─ listener.py   │
│ Roche    │───── porta 5003 ──────────────►│  ├─ astm.py       │
│ Cobas411 │                                │  └─ runner.py     │
├──────────┤                                └────────┬──────────┘
│ Roche    │───── porta 5004 ──────────────►         │
│ Cobas311 │                                         │ JSON API v1
├──────────┤                                         ▼
│ Bio-Rad  │───── porta 5005 ──────────────►  ┌───────────────────┐
│ D-10     │                                │  GATEWAY FastAPI   │
└──────────┘                                │  (porta 8000)     │
                                            │                    │
┌──────────┐  POST /api/v1/sandra/ingestao  │  ┌─ ingestao.py   │
│  SANDRA  │ ──────────────────────────────►│  ├─ webhooks.py   │
│ (Pront.) │                                │  ├─ senaite_api   │
└──────────┘                                │  └─ exercito_api  │
                                            └────────┬───────────┘
┌──────────┐  Webhook laudo_publicado               │
│ SENAITE  │ ◄───────────────────────────────────────┘
│ (LIS)    │      JSON API v1 (search, update)
└──────────┘
       │
       ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│  CADBEN  │     │   SIRE   │     │PostgreSQL│
│(Elegib.) │     │ (Verba)  │     │(CATSERV) │
└──────────┘     └──────────┘     └──────────┘
```

### Duas Aplicações

| Processo | Entry Point | Responsabilidade | Portas |
|----------|-------------|------------------|--------|
| **Gateway** | `uv run gateway` | API REST (SANDRA → SENAITE, webhooks) | 8000 |
| **Instrumentos** | `uv run instrumentos` | Daemon TCP (5 analisadores → SENAITE) | 5001-5005 |

### Camadas Internas

| Camada | Módulo | Função |
|--------|--------|--------|
| Router | `routers/ingestao.py` | Endpoints SANDRA → SENAITE |
| Router | `routers/webhooks.py` | Webhooks SENAITE → SANDRA |
| Client | `clients/senaite_api.py` | HTTP async para API do SENAITE |
| Client | `clients/exercito_api.py` | HTTP async para SANDRA/CADBEN/SIRE (mocks) |
| Model | `models/sandra.py`, `models/cadben.py`, `models/senaite.py` | Schemas Pydantic |
| Instrument | `instruments/listener.py` | Servidor TCP assíncrono ASTM E1381/E1394 |
| Instrument | `instruments/protocols/astm.py` | Parser ASTM com checksum, H/P/O/R/C/L |

---

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gerenciador de dependências)

### Instalação

```bash
cd hgumba-middleware
uv sync                     # instala dependências (runtime + dev)
cp .env.example .env        # ajustar variáveis se necessário
```

---

## 🏃 Como Rodar

### API Gateway

```bash
# Desenvolvimento (hot-reload)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Daemon de Instrumentos (Múltiplas Portas)

```bash
# Escuta todas as 5 portas (5001-5005)
uv run instrumentos --portas=5001,5002,5003,5004,5005

# Porta específica
uv run instrumentos --portas=5001
```

### Docker Compose (Stack Completa)

O middleware roda ao lado do SENAITE e do PostgreSQL:

```yaml
# compose.local.yaml (diretório pai)
services:
  app                    # SENAITE LIS (porta 8083)
  db                     # PostgreSQL CATSERV (porta 5433)
  middleware_gateway     # Gateway FastAPI (porta 8000)
  middleware_instruments # Daemon TCP (portas 5001-5005)
```

```bash
# Subir tudo
docker compose -f ../compose.local.yaml up -d

# Verificar health do gateway
curl http://localhost:8000/health

# Logs
docker compose -f ../compose.local.yaml logs -f middleware_gateway
docker compose -f ../compose.local.yaml logs -f middleware_instruments
```

---

## 🧪 Testes

### Suite completa

```bash
uv run pytest -v
```

### Por módulo

```bash
uv run pytest -v tests/test_astm_parser.py   # 25 testes — parser ASTM
uv run pytest -v tests/test_api.py           # 9 testes — endpoints da API
uv run pytest -v tests/test_pipeline.py      # 5 testes — integração ponta a ponta
```

### Por filtro

```bash
uv run pytest -k "astm"       # apenas parser
uv run pytest -k "pipeline"   # apenas integração
uv run pytest -k "api"        # apenas API
```

### Emulador de Instrumento ASTM

Para testar a comunicação com uma máquina física localmente, utilize o emulador:

```bash
# Terminal 1 — Iniciar o daemon em uma porta
uv run instrumentos --portas=5001

# Terminal 2 — Simular analisador enviando 3 amostras
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200
```

O emulador envia 3 frames ASTM completos (com handshake ENQ/ACK/EOT) e o daemon responde com ACK a cada frame válido, parseia os registros e tenta enviar os resultados para o SENAITE via API v1.

```bash
# Personalizar amostras
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200 \
  --sample-id HGU-AR-001 --keyword GLI001 --valor 105.5 --unidade "mg/dL"
```

### Health check do Gateway

```bash
curl http://localhost:8000/health
# → {"status":"healthy","service":"hgumba-middleware","version":"1.0.0"}
```

---

## Endpoints

### Gateway (porta 8000)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/sandra/ingestao` | Recebe pedido de exames do SANDRA |
| `POST` | `/api/v1/senaite/webhook/laudo_publicado` | Webhook disparado pelo SENAITE |

Docs interativos: `http://localhost:8000/docs`

### SENAITE Add-on (porta 8083)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `@@hgumba-seed` | Cria dados de teste (Client + Services + ARs) |
| `GET` | `@@cdm-pdf` | PDF do CDM (billing) |
| `GET` | `@@hgumba-report-pdf` | Laudo com gráfico de histórico |
| `POST` | `@@hgumba-create-ar` | **Cria AR (bypass do @@API/create bloqueado)** |
| `POST` | `@@hgumba-set-remark` | **Define Remarks em AR existente (bypass validação @@API/update)** |
| `GET` | `@@hgumba-debug` | Debug/introspecção |

---

## Instrumentos

| # | Equipamento | Porta | Exames |
|---|-------------|-------|--------|
| 1 | Mindray BS-200 | 5001 | Bioquímica (glicose, colesterol, etc.) |
| 2 | Sysmex XN-550 | 5002 | Hematologia (hemograma) |
| 3 | Roche Cobas e411 | 5003 | Imunoquímica (hormônios, marcadores) |
| 4 | Roche Cobas c311 | 5004 | Química Clínica |
| 5 | Bio-Rad D-10 | 5005 | HbA1c |

Protocolo: ASTM E1381 (enquadramento) + E1394 (registros H/P/O/R/C/L) sobre TCP/IP.

---

## Estrutura do Projeto

```
hgumba-middleware/
├── src/
│   ├── main.py                  # FastAPI app, entrada do gateway
│   ├── config.py                # Settings via .env / variáveis de ambiente
│   ├── clients/
│   │   ├── senaite_api.py       # httpx AsyncClient para API SENAITE
│   │   └── exercito_api.py      # httpx AsyncClient para SANDRA/CADBEN/SIRE
│   ├── models/
│   │   ├── sandra.py            # OrdemServicoSANDRA, ExameSolicitado
│   │   ├── cadben.py            # BeneficiarioCADBEN, ElegibilidadeResponse
│   │   └── senaite.py           # WebhookLaudoPayload, AnalysisRequestPayload
│   ├── routers/
│   │   ├── ingestao.py          # POST /api/v1/sandra/ingestao
│   │   └── webhooks.py          # POST /api/v1/senaite/webhook/laudo_publicado
│   └── instruments/
│       ├── config.py            # 5 instrumentos configurados
│       ├── models.py            # AmostraProcessada, ResultadoExameInstrumento
│       ├── listener.py          # TCP async server com handshake ACK/NAK/ENQ/EOT
│       ├── runner.py            # CLI daemon (entry point "instrumentos")
│       └── protocols/
│           └── astm.py          # Parser ASTM E1381/E1394
├── tests/
│   ├── test_astm_parser.py      # 25 testes do parser ASTM
│   ├── test_api.py              # 9 testes da API (health, webhook, sandra)
│   ├── test_pipeline.py         # 5 testes de integração (emulador → parse → dados)
│   └── mock_instrument.py       # Emulador ASTM CLI
├── Dockerfile                   # python:3.12-slim + uv sync
├── pyproject.toml               # uv: 5 deps runtime, 2 deps dev
├── .env.example                 # Template de variáveis de ambiente
└── spec-middleware.md           # Spec-first do projeto
```

---

## Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `SENAITE_URL` | `http://localhost:8083/senaite` | URL base do SENAITE |
| `SENAITE_USER` | `admin` | Usuário da API |
| `SENAITE_PASSWORD` | `admin` | Senha da API |
| `DB_HOST` | `localhost` | PostgreSQL CATSERV |
| `DB_PORT` | `5433` | Porta do PostgreSQL |
| `DB_NAME` | `financeiro` | Database CATSERV |
| `DB_USER` | `catserv` | Usuário CATSERV |
| `DB_PASSWORD` | `catserv_secret` | Senha CATSERV |
| `HOST` | `0.0.0.0` | Bind do gateway |
| `PORT` | `8000` | Porta do gateway |
| `LOG_LEVEL` | `info` | Nível de log |

---

## Dependências

**Runtime** (5): `fastapi`, `httpx`, `pydantic`, `pydantic-settings`, `uvicorn`
**Dev** (2): `pytest`, `pytest-asyncio`

Gerenciadas exclusivamente via `uv add` / `uv sync` — sem `pip install` manual.

---

## Notas Operacionais

- **APIs Exército**: SANDRA, CADBEN e SIRE estão em modo mock até assinatura de termo de sigilo.
- **CATSERV**: PostgreSQL com tabela `tabela_catserv` mapeia códigos de exame → UIDs do SENAITE.
- **Volume ZODB**: O banco do SENAITE (`Data.fs`) persiste em volume nomeado `senaite_data:/data`.
- **Buildout**: Não use `SITE=senaite` em restarts — destrói `package-includes/` do add-on custom.
- **Webhook SENAITE**: Implementado via Event Subscriber ZCML (não painel webhooks). Dispara POST para o gateway ao publicar laudo.
