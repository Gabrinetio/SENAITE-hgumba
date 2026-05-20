# SENAITE LIS — HGUMBA

Middleware de integração entre o **SENAITE LIMS** (Zope/Plone), **5 analisadores clínicos** (ASTM E1381/E1394, HL7 v2.x, RS-232) e os sistemas do **Exército Brasileiro** (SANDRA, SIRE, CADBEN).

```
Analisadores (TCP:5001–5005)          SANDRA / SIRE / CADBEN (REST)
       │                                       │
       ▼ ASTM / HL7 / RS-232                   ▼ JSON API
┌──────────────────┐                  ┌────────────────────┐
│  instruments     │                  │  gateway           │
│  daemon (async)  │                  │  FastAPI (porta    │
│  listener.py     │─────────────────►│  8000)             │
│  astm/hl7/rs232  │   JSON API v1    │  ingestão +        │
│  parsers         │                  │  webhooks          │
└──────────────────┘                  └────────┬───────────┘
                                               │
                                               ▼
                                        ┌──────────────────┐
                                        │  SENAITE LIS     │
                                        │  Zope/Plone      │
                                        │  porta 8083      │
                                        │  custom add-on   │
                                        │  (cdm, report,   │
                                        │   create-ar)     │
                                        └──────────────────┘
```

## Status do Projeto

| Indicador | Valor |
|-----------|-------|
| **Testes** | ![108](https://img.shields.io/badge/tests-108%20passing-brightgreen) |
| **Python** | 3.12+ (middleware) / 2.7 (add-on Zope) |
| **Dependências** | Gerenciadas via `uv` — sem `pip install` manual |
| **Orquestração** | Docker Compose (dev) / Docker Swarm (prod) |
| **Parser** | ASTM E1381/E1394, HL7 v2.x (ORU^R01), RS-232 raw |
| **Protocolos suportados** | 3 (`ASTM`, `HL7`, `RS232`) — selecionáveis por `InstrumentoConfig.protocolo` |
| **Auditoria** | Logs JSON estruturados (RDC 978/2025) |
| **Segurança** | SAST sanitizado — sem credenciais hardcoded, sem IPs internos, sem dados reais |
| **SLA** | 98% (máx. 14h24min downtime/mês) |

## Índice de Documentação

A documentação completa está em [`docs/`](./docs/). Consulte conforme sua necessidade:

### Infraestrutura & Deploy

| Documento | Conteúdo |
|-----------|----------|
| [`docs/00-specification.md`](./docs/00-specification.md) | Stack, acesso, credenciais, arquitetura ZODB |
| [`docs/06-deploy.md`](./docs/06-deploy.md) | Deploy Swarm: volumes NFS, redes overlay, constraints, rollback |
| [`docs/09-drp.md`](./docs/09-drp.md) | Disaster Recovery expandido: restore ZODB, pg_dump, migração NFS, SLA 98% |
| [`docs/drp.md`](./docs/drp.md) | DRP oficial do edital — conciso (repozo, pg_dump, contingência Swarm) |

### Integração & Protocolos

| Documento | Conteúdo |
|-----------|----------|
| [`docs/05-integracao.md`](./docs/05-integracao.md) | Manual de integração: CATSERV → SENAITE, ASTM E1394 campo-a-campo, portas TCP, troubleshooting com audit logger |
| [`docs/03-middleware.md`](./docs/03-middleware.md) | Spec-first do middleware: rotas, contratos Pydantic, camadas internas |
| [`docs/04-middleware-readme.md`](./docs/04-middleware-readme.md) | README do middleware: instalação, execução, testes, endpoints |
| [`docs/requisitos_ti.md`](./docs/requisitos_ti.md) | Requisitos de integração pós-sigilo: endpoints CADBEN/SIRE/SANDRA, segurança, homologação |

### Customizações & Add-on Zope

| Documento | Conteúdo |
|-----------|----------|
| [`docs/02-customizations.md`](./docs/02-customizations.md) | Add-on senaite.hgumba: CDM, CoPhysicians, report PDF, create-ar, set-remark |

### Operação & Auditoria

| Documento | Conteúdo |
|-----------|----------|
| [`docs/08-manual-operador.md`](./docs/08-manual-operador.md) | POP diário do LAC: cadastro, CDM, flags, publish, troubleshooting |
| [`docs/07-auditoria.md`](./docs/07-auditoria.md) | POP RDC 978: rastreabilidade, logs JSON, mapa de auditoria |

### Progresso & Plano de Correção

| Documento | Conteúdo |
|-----------|----------|
| [`docs/01-summary.md`](./docs/01-summary.md) | Progresso, lições aprendidas, critical context |
| [`docs/10-sast-plano-correcao.md`](./docs/10-sast-plano-correcao.md) | Plano de correção SAST (Fases 1–4) |

## Quick Start

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gerenciador de dependências)
- Docker + Docker Compose

### 1. Subir a Stack Local

```bash
# Do diretório raiz do projeto
docker compose -f compose.local.yaml up -d

# Verificar se os serviços estão rodando
docker compose -f compose.local.yaml ps
```

A stack sobe 4 serviços:

| Serviço | Função | Porta |
|---------|--------|-------|
| `app` | SENAITE LIS (Zope/Plone) | `8083` |
| `db` | PostgreSQL CATSERV | `5433` |
| `middleware_gateway` | API Gateway FastAPI | `8000` |
| `middleware_instruments` | Daemon TCP ASTM/HL7/RS232 | `5001–5005` |

### 2. Configurar o SENAITE

Acesse `http://localhost:8083/` e clique em **Create a new SENAITE site**.

Após a criação do site, execute o seed de dados:

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
# Terminal 1 — iniciar o daemon de instrumentos
cd hgumba-middleware
uv run instrumentos --portas=5001

# Terminal 2 — emular Mindray BS200 enviando 3 amostras ASTM
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200
```

### 5. Rodar os Testes

```bash
cd hgumba-middleware
uv run pytest -v
```

108 testes, 0 falhas esperado.

```bash
# Ou por módulo
uv run pytest -v tests/test_astm_parser.py   # 25 testes — parser ASTM
uv run pytest -v tests/test_api.py           # 8 testes  — endpoints REST
uv run pytest -v tests/test_pipeline.py      # 4 testes  — pipeline integrado
uv run pytest -v tests/test_protocols.py     # 17 testes — HL7 + RS232 parsers
uv run pytest -v tests/test_security.py      # 54 testes — SAST Fases 1–4
```

### 6. Ambiente para Desenvolvimento

```bash
cd hgumba-middleware
uv sync                              # instala runtime + dev
cp .env.example .env                 # ajustar variáveis se necessário

# Gateway com hot-reload
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Estrutura do Repositório

```
SENAITE/
├── compose.yaml               # Stack Swarm de produção
├── compose.local.yaml         # Stack Docker Compose local (dev)
├── Dockerfile                 # Imagem SENAITE com add-on custom
├── .gitignore                 # ZODB, logs, .env, __pycache__
├── customizations/
│   └── src/senaite/hgumba/    # Add-on Zope (Python 2.7)
│       ├── browser/views/     # cdm_view, report_view, create_ar, seed
│       ├── extensions/        # CoPhysiciansField (ISchemaExtender)
│       └── configure.zcml     # Registro de views e permissions
├── hgumba-middleware/         # Middleware FastAPI (Python 3.12+)
│   ├── src/
│   │   ├── main.py            # App FastAPI + middlewares
│   │   ├── config.py          # Settings Pydantic v2
│   │   ├── auth.py            # API Key header security
│   │   ├── logger.py          # JSON audit trail (RDC 978)
│   │   ├── clients/           # senaite_api, exercito_api
│   │   ├── models/            # sandra, cadben, senaite (Pydantic)
│   │   ├── routers/           # ingestao, webhooks
│   │   └── instruments/       # listener, runner, parser ASTM/HL7/RS232
│   ├── tests/                 # 108 testes (pytest)
│   └── pyproject.toml         # uv: 5 deps runtime, 2 dev
└── docs/                      # Documentação completa
```

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| **LIS** | SENAITE 2.x (Zope/Plone 5.2.15, Python 2.7) |
| **Banco clínico** | ZODB (single replica) |
| **Middleware** | Python 3.12+ / FastAPI / httpx / Pydantic v2 |
| **Parser ASTM** | E1381 (STX/ETX/checksum) + E1394 (H/P/O/R/C/L) |
| **Parser HL7** | ORU^R01 (\r ou \n como terminador) |
| **Parser RS-232** | Raw text (H/P/O/R/L) com terminador CR/LF |
| **Auditoria** | JSON estruturado (RDC 978/2025) |
| **Rate limit** | slowapi — 200/min global, 100/min no `/ingestao` |
| **Orquestração** | Docker Compose (dev) / Docker Swarm (prod) |
| **Dependências** | uv (sem pip install manual) |
| **Persistência** | NFS em `192.168.4.23` (ZODB + PostgreSQL) |

---

**Licença:** Uso interno — HGUMBA / Exército Brasileiro
