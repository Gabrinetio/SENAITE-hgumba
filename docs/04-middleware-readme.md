> **Origem:** `SENAITE/hgumba-middleware/README.md`

# HGUMBA Middleware

API Gateway que orquestra a integraÃ§Ã£o entre o **SENAITE LIS**, os **5 analisadores clÃ­nicos** e os sistemas do **ExÃ©rcito Brasileiro** (SANDRA, SIRE, CADBEN).

Stack: **Python 3.12+ / FastAPI / httpx / Pydantic / uv**

---

## Arquitetura

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     ASTM E1381/E1394 (TCP)     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Mindray  â”‚â”€â”€â”€â”€â”€ porta 5001 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                   â”‚
â”‚ BS-200   â”‚                                â”‚  INSTRUMENTS      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤                                â”‚  Daemon TCP       â”‚
â”‚ Sysmex   â”‚â”€â”€â”€â”€â”€ porta 5002 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  (async)          â”‚
â”‚ XN-550   â”‚                                â”‚                   â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤                                â”‚  â”Œâ”€ listener.py   â”‚
â”‚ Roche    â”‚â”€â”€â”€â”€â”€ porta 5003 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  â”œâ”€ astm.py       â”‚
â”‚ Cobas411 â”‚                                â”‚  â””â”€ runner.py     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤                                â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”‚ Roche    â”‚â”€â”€â”€â”€â”€ porta 5004 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º         â”‚
â”‚ Cobas311 â”‚                                         â”‚ JSON API v1
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤                                         â–¼
â”‚ Bio-Rad  â”‚â”€â”€â”€â”€â”€ porta 5005 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ D-10     â”‚                                â”‚  GATEWAY FastAPI   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                â”‚  (porta 8000)     â”‚
                                             â”‚                    â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  POST /api/v1/sandra/ingestao  â”‚  â”Œâ”€ ingestao.py   â”‚
â”‚  SANDRA  â”‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  â”œâ”€ webhooks.py   â”‚
â”‚ (Pront.) â”‚                                â”‚  â”œâ”€ senaite_api   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                â”‚  â””â”€ exercito_api  â”‚
                                             â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  Webhook laudo_publicado               â”‚
â”‚ SENAITE  â”‚ â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”‚ (LIS)    â”‚      JSON API v1 (search, update)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  CADBEN  â”‚     â”‚   SIRE   â”‚     â”‚PostgreSQLâ”‚
â”‚(Elegib.) â”‚     â”‚ (Verba)  â”‚     â”‚(CATSERV) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Duas AplicaÃ§Ãµes

| Processo | Entry Point | Responsabilidade | Portas |
|----------|-------------|------------------|--------|
| **Gateway** | `uv run gateway` | API REST (SANDRA â†’ SENAITE, webhooks) | 8000 |
| **Instrumentos** | `uv run instrumentos` | Daemon TCP (5 analisadores â†’ SENAITE) | 5001-5005 |

### Camadas Internas

| Camada | MÃ³dulo | FunÃ§Ã£o |
|--------|--------|--------|
| Router | `routers/ingestao.py` | Endpoints SANDRA â†’ SENAITE |
| Router | `routers/webhooks.py` | Webhooks SENAITE â†’ SANDRA |
| Client | `clients/senaite_api.py` | HTTP async para API do SENAITE |
| Client | `clients/exercito_api.py` | HTTP async para SANDRA/CADBEN/SIRE (mocks) |
| Model | `models/sandra.py`, `models/cadben.py`, `models/senaite.py` | Schemas Pydantic |
| Instrument | `instruments/listener.py` | Servidor TCP assÃ­ncrono ASTM E1381/E1394 |
| Instrument | `instruments/protocols/astm.py` | Parser ASTM com checksum, H/P/O/R/C/L |

---

## PrÃ©-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gerenciador de dependÃªncias)

### InstalaÃ§Ã£o

```bash
cd hgumba-middleware
uv sync                     # instala dependÃªncias (runtime + dev)
cp .env.example .env        # ajustar variÃ¡veis se necessÃ¡rio
```

---

## ðŸƒ Como Rodar

### API Gateway

```bash
# Desenvolvimento (hot-reload)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Daemon de Instrumentos (MÃºltiplas Portas)

```bash
# Escuta todas as 5 portas (5001-5005)
uv run instrumentos --portas=5001,5002,5003,5004,5005

# Porta especÃ­fica
uv run instrumentos --portas=5001
```

### Docker Compose (Stack Completa)

O middleware roda ao lado do SENAITE e do PostgreSQL:

```yaml
# compose.local.yaml (diretÃ³rio pai)
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

## ðŸ§ª Testes

### Suite completa

```bash
uv run pytest -v
```

### Por mÃ³dulo

```bash
uv run pytest -v tests/test_astm_parser.py   # 25 testes â€” parser ASTM
uv run pytest -v tests/test_api.py           # 9 testes â€” endpoints da API
uv run pytest -v tests/test_pipeline.py      # 5 testes â€” integraÃ§Ã£o ponta a ponta
```

### Por filtro

```bash
uv run pytest -k "astm"       # apenas parser
uv run pytest -k "pipeline"   # apenas integraÃ§Ã£o
uv run pytest -k "api"        # apenas API
```

### Emulador de Instrumento ASTM

Para testar a comunicaÃ§Ã£o com uma mÃ¡quina fÃ­sica localmente, utilize o emulador:

```bash
# Terminal 1 â€” Iniciar o daemon em uma porta
uv run instrumentos --portas=5001

# Terminal 2 â€” Simular analisador enviando 3 amostras
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200
```

O emulador envia 3 frames ASTM completos (com handshake ENQ/ACK/EOT) e o daemon responde com ACK a cada frame vÃ¡lido, parseia os registros e tenta enviar os resultados para o SENAITE via API v1.

```bash
# Personalizar amostras
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200 \
  --sample-id HGU-AR-001 --keyword GLI001 --valor 105.5 --unidade "mg/dL"
```

### Health check do Gateway

```bash
curl http://localhost:8000/health
# â†’ {"status":"healthy","service":"hgumba-middleware","version":"1.0.0"}
```

---

## Endpoints

### Gateway (porta 8000)

| MÃ©todo | Rota | DescriÃ§Ã£o |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/sandra/ingestao` | Recebe pedido de exames do SANDRA |
| `POST` | `/api/v1/senaite/webhook/laudo_publicado` | Webhook disparado pelo SENAITE |

Docs interativos: `http://localhost:8000/docs`

### SENAITE Add-on (porta 8083)

| MÃ©todo | Rota | DescriÃ§Ã£o |
|--------|------|-----------|
| `GET` | `@@hgumba-seed` | Cria dados de teste (Client + Services + ARs) |
| `GET` | `@@cdm-pdf` | PDF do CDM (billing) |
| `GET` | `@@hgumba-report-pdf` | Laudo com grÃ¡fico de histÃ³rico |
| `POST` | `@@hgumba-create-ar` | **Cria AR (bypass do @@API/create bloqueado)** |
| `POST` | `@@hgumba-set-remark` | **Define Remarks em AR existente (bypass validaÃ§Ã£o @@API/update)** |
| `GET` | `@@hgumba-debug` | Debug/introspecÃ§Ã£o |

---

## Instrumentos

| # | Equipamento | Porta | Exames |
|---|-------------|-------|--------|
| 1 | Mindray BS-200 | 5001 | BioquÃ­mica (glicose, colesterol, etc.) |
| 2 | Sysmex XN-550 | 5002 | Hematologia (hemograma) |
| 3 | Roche Cobas e411 | 5003 | ImunoquÃ­mica (hormÃ´nios, marcadores) |
| 4 | Roche Cobas c311 | 5004 | QuÃ­mica ClÃ­nica |
| 5 | Bio-Rad D-10 | 5005 | HbA1c |

Protocolo: ASTM E1381 (enquadramento) + E1394 (registros H/P/O/R/C/L) sobre TCP/IP.

---

## Estrutura do Projeto

```
hgumba-middleware/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ main.py                  # FastAPI app, entrada do gateway
â”‚   â”œâ”€â”€ config.py                # Settings via .env / variÃ¡veis de ambiente
â”‚   â”œâ”€â”€ clients/
â”‚   â”‚   â”œâ”€â”€ senaite_api.py       # httpx AsyncClient para API SENAITE
â”‚   â”‚   â””â”€â”€ exercito_api.py      # httpx AsyncClient para SANDRA/CADBEN/SIRE
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ sandra.py            # OrdemServicoSANDRA, ExameSolicitado
â”‚   â”‚   â”œâ”€â”€ cadben.py            # BeneficiarioCADBEN, ElegibilidadeResponse
â”‚   â”‚   â””â”€â”€ senaite.py           # WebhookLaudoPayload, AnalysisRequestPayload
â”‚   â”œâ”€â”€ routers/
â”‚   â”‚   â”œâ”€â”€ ingestao.py          # POST /api/v1/sandra/ingestao
â”‚   â”‚   â””â”€â”€ webhooks.py          # POST /api/v1/senaite/webhook/laudo_publicado
â”‚   â””â”€â”€ instruments/
â”‚       â”œâ”€â”€ config.py            # 5 instrumentos configurados
â”‚       â”œâ”€â”€ models.py            # AmostraProcessada, ResultadoExameInstrumento
â”‚       â”œâ”€â”€ listener.py          # TCP async server com handshake ACK/NAK/ENQ/EOT
â”‚       â”œâ”€â”€ runner.py            # CLI daemon (entry point "instrumentos")
â”‚       â””â”€â”€ protocols/
â”‚           â””â”€â”€ astm.py          # Parser ASTM E1381/E1394
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_astm_parser.py      # 25 testes do parser ASTM
â”‚   â”œâ”€â”€ test_api.py              # 9 testes da API (health, webhook, sandra)
â”‚   â”œâ”€â”€ test_pipeline.py         # 5 testes de integraÃ§Ã£o (emulador â†’ parse â†’ dados)
â”‚   â””â”€â”€ mock_instrument.py       # Emulador ASTM CLI
â”œâ”€â”€ Dockerfile                   # python:3.12-slim + uv sync
â”œâ”€â”€ pyproject.toml               # uv: 5 deps runtime, 2 deps dev
â”œâ”€â”€ .env.example                 # Template de variÃ¡veis de ambiente
â””â”€â”€ spec-middleware.md           # Spec-first do projeto
```

---

## VariÃ¡veis de Ambiente

| VariÃ¡vel | Default | DescriÃ§Ã£o |
|----------|---------|-----------|
| `SENAITE_URL` | `http://localhost:8083/senaite` | URL base do SENAITE |
| `SENAITE_USER` | `admin` | UsuÃ¡rio da API |
| `SENAITE_PASSWORD` | `admin` | Senha da API |
| `DB_HOST` | `localhost` | PostgreSQL CATSERV |
| `DB_PORT` | `5433` | Porta do PostgreSQL |
| `DB_NAME` | `financeiro` | Database CATSERV |
| `DB_USER` | `catserv` | UsuÃ¡rio CATSERV |
| `DB_PASSWORD` | `catserv_secret` | Senha CATSERV |
| `HOST` | `0.0.0.0` | Bind do gateway |
| `PORT` | `8000` | Porta do gateway |
| `LOG_LEVEL` | `info` | NÃ­vel de log |

---

## DependÃªncias

**Runtime** (5): `fastapi`, `httpx`, `pydantic`, `pydantic-settings`, `uvicorn`
**Dev** (2): `pytest`, `pytest-asyncio`

Gerenciadas exclusivamente via `uv add` / `uv sync` â€” sem `pip install` manual.

---

## Notas Operacionais

- **APIs ExÃ©rcito**: SANDRA, CADBEN e SIRE estÃ£o em modo mock atÃ© assinatura de termo de sigilo.
- **CATSERV**: PostgreSQL com tabela `tabela_catserv` mapeia cÃ³digos de exame â†’ UIDs do SENAITE.
- **Volume ZODB**: O banco do SENAITE (`Data.fs`) persiste em volume nomeado `senaite_data:/data`.
- **Buildout**: NÃ£o use `SITE=senaite` em restarts â€” destrÃ³i `package-includes/` do add-on custom.
- **Webhook SENAITE**: Implementado via Event Subscriber ZCML (nÃ£o painel webhooks). Dispara POST para o gateway ao publicar laudo.
