# SENAITE LIS — HGUMBA

Middleware de integraÃ§Ã£o entre o **SENAITE LIMS** (Zope/Plone), **5 analisadores clÃ­nicos** (ASTM E1381/E1394, HL7 v2.x, RS-232) e os sistemas do **ExÃ©rcito Brasileiro** (SANDRA, SIRE, CADBEN).

```
Analisadores (TCP:5001â€“5005)          SANDRA / SIRE / CADBEN (REST)
       â”‚                                       â”‚
       â–¼ ASTM / HL7 / RS-232                   â–¼ JSON API
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  instruments     â”‚                  â”‚  gateway           â”‚
â”‚  daemon (async)  â”‚                  â”‚  FastAPI (porta    â”‚
â”‚  listener.py     â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  8000)             â”‚
â”‚  astm/hl7/rs232  â”‚   JSON API v1    â”‚  ingestÃ£o +        â”‚
â”‚  parsers         â”‚                  â”‚  webhooks          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                               â”‚
                                               â–¼
                                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                        â”‚  SENAITE LIS     â”‚
                                        â”‚  Zope/Plone      â”‚
                                        â”‚  porta 8083      â”‚
                                        â”‚  custom add-on   â”‚
                                        â”‚  (cdm, report,   â”‚
                                        â”‚   create-ar)     â”‚
                                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Status do Projeto

| Indicador | Valor |
|-----------|-------|
| **Testes** | ![108](https://img.shields.io/badge/tests-108%20passing-brightgreen) |
| **Python** | 3.12+ (middleware) / 2.7 (add-on Zope) |
| **DependÃªncias** | Gerenciadas via `uv` â€” sem `pip install` manual |
| **OrquestraÃ§Ã£o** | Docker Compose (dev) / Docker Swarm (prod) |
| **Parser** | ASTM E1381/E1394, HL7 v2.x (ORU^R01), RS-232 raw |
| **Protocolos suportados** | 3 (`ASTM`, `HL7`, `RS232`) â€” selecionÃ¡veis por `InstrumentoConfig.protocolo` |
| **Auditoria** | Logs JSON estruturados (RDC 978/2025) |
| **SeguranÃ§a** | SAST sanitizado â€” sem credenciais hardcoded, sem IPs internos, sem dados reais |
| **SLA** | 98% (mÃ¡x. 14h24min downtime/mÃªs) |

## Ãndice de DocumentaÃ§Ã£o

A documentaÃ§Ã£o completa estÃ¡ em [`docs/`](./docs/). Consulte conforme sua necessidade:

### Infraestrutura & Deploy

| Documento | ConteÃºdo |
|-----------|----------|
| [`docs/00-specification.md`](./docs/00-specification.md) | Stack, acesso, credenciais, arquitetura ZODB |
| [`docs/06-deploy.md`](./docs/06-deploy.md) | Deploy Swarm: volumes NFS, redes overlay, constraints, rollback |
| [`docs/09-drp.md`](./docs/09-drp.md) | Disaster Recovery expandido: restore ZODB, pg_dump, migraÃ§Ã£o NFS, SLA 98% |
| [`docs/drp.md`](./docs/drp.md) | DRP oficial do edital â€” conciso (repozo, pg_dump, contingÃªncia Swarm) |

### IntegraÃ§Ã£o & Protocolos

| Documento | ConteÃºdo |
|-----------|----------|
| [`docs/05-integracao.md`](./docs/05-integracao.md) | Manual de integraÃ§Ã£o: CATSERV â†’ SENAITE, ASTM E1394 campo-a-campo, portas TCP, troubleshooting com audit logger |
| [`docs/03-middleware.md`](./docs/03-middleware.md) | Spec-first do middleware: rotas, contratos Pydantic, camadas internas |
| [`docs/04-middleware-readme.md`](./docs/04-middleware-readme.md) | README do middleware: instalaÃ§Ã£o, execuÃ§Ã£o, testes, endpoints |
| [`docs/requisitos_ti.md`](./docs/requisitos_ti.md) | Requisitos de integraÃ§Ã£o pÃ³s-sigilo: endpoints CADBEN/SIRE/SANDRA, seguranÃ§a, homologaÃ§Ã£o |

### CustomizaÃ§Ãµes & Add-on Zope

| Documento | ConteÃºdo |
|-----------|----------|
| [`docs/02-customizations.md`](./docs/02-customizations.md) | Add-on senaite.hgumba: CDM, CoPhysicians, report PDF, create-ar, set-remark |

### OperaÃ§Ã£o & Auditoria

| Documento | ConteÃºdo |
|-----------|----------|
| [`docs/08-manual-operador.md`](./docs/08-manual-operador.md) | POP diÃ¡rio do LAC: cadastro, CDM, flags, publish, troubleshooting |
| [`docs/07-auditoria.md`](./docs/07-auditoria.md) | POP RDC 978: rastreabilidade, logs JSON, mapa de auditoria |

### Progresso & Plano de CorreÃ§Ã£o

| Documento | ConteÃºdo |
|-----------|----------|
| [`docs/01-summary.md`](./docs/01-summary.md) | Progresso, liÃ§Ãµes aprendidas, critical context |
| [`docs/10-sast-plano-correcao.md`](./docs/10-sast-plano-correcao.md) | Plano de correÃ§Ã£o SAST (Fases 1â€“4) |

## Quick Start

### PrÃ©-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gerenciador de dependÃªncias)
- Docker + Docker Compose

### 1. Subir a Stack Local

```bash
# Do diretÃ³rio raiz do projeto
docker compose -f compose.local.yaml up -d

# Verificar se os serviÃ§os estÃ£o rodando
docker compose -f compose.local.yaml ps
```

A stack sobe 4 serviÃ§os:

| ServiÃ§o | FunÃ§Ã£o | Porta |
|---------|--------|-------|
| `app` | SENAITE LIS (Zope/Plone) | `8083` |
| `db` | PostgreSQL CATSERV | `5433` |
| `middleware_gateway` | API Gateway FastAPI | `8000` |
| `middleware_instruments` | Daemon TCP ASTM/HL7/RS232 | `5001â€“5005` |

### 2. Configurar o SENAITE

Acesse `http://localhost:8083/` e clique em **Create a new SENAITE site**.

ApÃ³s a criaÃ§Ã£o do site, execute o seed de dados:

```
http://admin:admin@localhost:8083/senaite/@@hgumba-seed
```

Isso cria: Client `hgu`, 3 AnalysisServices (`GLI001`, `HEM001`, `LIP001`), 1 Contact e 3 AnalysisRequests de exemplo.

### 3. Verificar o Middleware

```bash
# Health check do gateway
curl http://localhost:8000/health

# Deve retornar:
# {"status":"healthy","service":"hgumba-middleware","version":"1.0.0"}
```

### 4. Simular o Envio de um Analisador

```bash
# Terminal 1 â€” iniciar o daemon de instrumentos
cd hgumba-middleware
uv run instrumentos --portas=5001

# Terminal 2 â€” emular Mindray BS200 enviando 3 amostras ASTM
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200
```

### 5. Rodar os Testes

```bash
cd hgumba-middleware
uv run pytest -v
```

108 testes, 0 falhas esperado.

```bash
# Ou por mÃ³dulo
uv run pytest -v tests/test_astm_parser.py   # 25 testes â€” parser ASTM
uv run pytest -v tests/test_api.py           # 8 testes  â€” endpoints REST
uv run pytest -v tests/test_pipeline.py      # 4 testes  â€” pipeline integrado
uv run pytest -v tests/test_protocols.py     # 17 testes â€” HL7 + RS232 parsers
uv run pytest -v tests/test_security.py      # 54 testes â€” SAST Fases 1â€“4
```

### 6. Ambiente para Desenvolvimento

```bash
cd hgumba-middleware
uv sync                              # instala runtime + dev
cp .env.example .env                 # ajustar variÃ¡veis se necessÃ¡rio

# Gateway com hot-reload
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Estrutura do RepositÃ³rio

```
SENAITE/
â”œâ”€â”€ compose.yaml               # Stack Swarm de produÃ§Ã£o
â”œâ”€â”€ compose.local.yaml         # Stack Docker Compose local (dev)
â”œâ”€â”€ Dockerfile                 # Imagem SENAITE com add-on custom
â”œâ”€â”€ .gitignore                 # ZODB, logs, .env, __pycache__
â”œâ”€â”€ customizations/
â”‚   â””â”€â”€ src/senaite/hgumba/    # Add-on Zope (Python 2.7)
â”‚       â”œâ”€â”€ browser/views/     # cdm_view, report_view, create_ar, seed
â”‚       â”œâ”€â”€ extensions/        # CoPhysiciansField (ISchemaExtender)
â”‚       â””â”€â”€ configure.zcml     # Registro de views e permissions
â”œâ”€â”€ hgumba-middleware/         # Middleware FastAPI (Python 3.12+)
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ main.py            # App FastAPI + middlewares
â”‚   â”‚   â”œâ”€â”€ config.py          # Settings Pydantic v2
â”‚   â”‚   â”œâ”€â”€ auth.py            # API Key header security
â”‚   â”‚   â”œâ”€â”€ logger.py          # JSON audit trail (RDC 978)
â”‚   â”‚   â”œâ”€â”€ clients/           # senaite_api, exercito_api
â”‚   â”‚   â”œâ”€â”€ models/            # sandra, cadben, senaite (Pydantic)
â”‚   â”‚   â”œâ”€â”€ routers/           # ingestao, webhooks
â”‚   â”‚   â””â”€â”€ instruments/       # listener, runner, parser ASTM/HL7/RS232
â”‚   â”œâ”€â”€ tests/                 # 108 testes (pytest)
â”‚   â””â”€â”€ pyproject.toml         # uv: 5 deps runtime, 2 dev
â””â”€â”€ docs/                      # DocumentaÃ§Ã£o completa
```

## Stack TÃ©cnica

| Camada | Tecnologia |
|--------|-----------|
| **LIS** | SENAITE 2.x (Zope/Plone 5.2.15, Python 2.7) |
| **Banco clÃ­nico** | ZODB (single replica) |
| **Middleware** | Python 3.12+ / FastAPI / httpx / Pydantic v2 |
| **Parser ASTM** | E1381 (STX/ETX/checksum) + E1394 (H/P/O/R/C/L) |
| **Parser HL7** | ORU^R01 (\r ou \n como terminador) |
| **Parser RS-232** | Raw text (H/P/O/R/L) com terminador CR/LF |
| **Auditoria** | JSON estruturado (RDC 978/2025) |
| **Rate limit** | slowapi â€” 200/min global, 100/min no `/ingestao` |
| **OrquestraÃ§Ã£o** | Docker Compose (dev) / Docker Swarm (prod) |
| **DependÃªncias** | uv (sem pip install manual) |
| **PersistÃªncia** | NFS em `192.168.4.23` (ZODB + PostgreSQL) |

---

**Licença:** Uso interno — HGUMBA / Exército Brasileiro
