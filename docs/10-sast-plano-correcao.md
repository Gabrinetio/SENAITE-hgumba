# SAST — Plano de Correção

**Data:** 2026-05-19  
**Baseado em:** `docs/01-summary.md` (relatório SAST completo)  
**Total de vulnerabilidades:** 15 (3 críticas, 5 altas, 7 médias, 3 baixas)

---

## Fase 1 — 🔴 CRÍTICO

### 1.1 — Autenticação no Middleware (C1/C2)

**Arquivos:** `hgumba-middleware/src/auth.py` (novo), `src/routers/ingestao.py`, `src/routers/webhooks.py`, `src/config.py`

Criar `src/auth.py` com `APIKeyHeader` do FastAPI:

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)) -> str:
    if not settings.api_key:
        return "dev_mode"
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado",
        )
    return key
```

- `config.py`: adicionar `api_key: str = ""` (lido de env var `API_KEY`)
- `ingestao.py`: adicionar `dependencies=[Depends(verify_api_key)]` no router
- `webhooks.py`: idem
- Manter `/health` público

### 1.2 — Permissão Zope (C3)

**Arquivos:** `customizations/src/senaite.hgumba/src/senaite/hgumba/profiles/default/rolemap.xml` (novo), `browser/configure.zcml`

Criar `rolemap.xml`:

```xml
<?xml version="1.0"?>
<rolemap>
  <permissions>
    <permission name="senaite.hgumba: Manage Analysis Requests" acquire="True">
      <role name="Manager"/>
      <role name="LabManager"/>
      <role name="LabClerk"/>
    </permission>
  </permissions>
</rolemap>
```

Alterar `browser/configure.zcml`:

| View | Permissão atual | Nova permissão |
|------|----------------|----------------|
| `hgumba-create-ar` | `zope2.View` | `senaite.hgumba: Manage Analysis Requests` |
| `hgumba-set-remark` | `zope2.View` | `senaite.hgumba: Manage Analysis Requests` |
| `hgumba-seed` | `zope2.View` | `senaite.hgumba: Manage Analysis Requests` |
| `hgumba-debug` | `zope2.View` | `cmf.ManagePortal` |
| `cdm-pdf` | `zope2.View` | manter (leitura pública) |
| `hgumba-report-pdf` | `zope2.View` | manter (leitura pública) |

---

## Fase 2 — 🟠 ALTO

### 2.1 — CORS (H1)

**Arquivo:** `src/main.py`

```python
allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["http://localhost:3000"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```

- `config.py`: adicionar `cors_origins: str = "http://localhost:3000"`
- Remover `allow_origins=["*"]` com `allow_credentials=True`

### 2.2 — Credenciais hardcoded (H2)

**Arquivo:** `src/config.py`, `.env.example`

- `config.py`: `senaite_password: str = ""`, `db_password: str = ""`
- `.env.example`: `SENAITE_PASSWORD=`, `DB_PASSWORD=`
- Adicionar validação no startup se senhas vazias

### 2.3 — Webhook Zope com retry (H3)

**Arquivo:** `events.py`

Refatorar `_post_webhook`:

```python
def _post_webhook(url, payload, retries=3):
    data = json.dumps(payload)
    for attempt in range(retries):
        try:
            req = urllib2.Request(url, data, {"Content-Type": "application/json"})
            urllib2.urlopen(req, timeout=5)
            logger.info("Webhook enviado para %s", payload.get("analysis_request_id"))
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error("Webhook falhou apos %d tentativas: %s", retries, e)
```

- Adicionar `import time`

### 2.4 — Information disclosure (H4)

**Arquivo:** `create_ar.py`

- `CreateAnalysisRequestView.__call__`: trocar `"JSON invalido: %s" % str(e)` por `"JSON invalido"`
- Bloco except final: `logger.exception("Erro ao criar AR")` + retornar `{"success": False, "message": "Erro interno"}`
- `SetRemarkView.__call__`: idem

### 2.5 — CDM PostgreSQL SSL (H5)

**Arquivo:** `cdm_view.py`

Adicionar na conexão `psycopg2.connect`:

```python
sslmode=os.environ.get("DB_SSLMODE", "prefer"),
```

---

## Fase 3 — 🟡 MÉDIO ✅ (2026-05-20)

### M1 — Rate limiting ✅

**Arquivo:** `src/main.py`, `pyproject.toml`

- Adicionado `slowapi>=0.1.9` ao `pyproject.toml`
- `Limiter` com `key_func=get_remote_address`, `default_limits=["200/minute"]`
- `@limiter.limit("100/minute")` no endpoint `POST /ingestao`
- `SlowAPIMiddleware` adicionado ao app
- `_rate_limit_exceeded_handler` registrado para status 429

### M2 — Body size limit ✅

**Arquivo:** `src/main.py`

- `RequestBodySizeMiddleware` (BaseHTTPMiddleware) verifica `content-length` header
- Rejeita payloads > 10MB com status 413

### M3 — Input validation Zope ✅

**Arquivo:** `create_ar.py`

- `import re` adicionado
- `client_id`: validado com `re.match(r'^[a-zA-Z0-9_-]+$', client_id)`
- `services`: verifica `isinstance(list)` + não-vazia + todas strings não-vazias
- `ar_id`: limite de 64 caracteres

### M4 — Audit trail persistente ✅

**Arquivo:** `src/logger.py`

- `RotatingFileHandler("audit.log", maxBytes=10MB, backupCount=10, encoding="utf-8")` adicionado
- `StreamHandler` mantido para docker logs

### M5 — BackgroundTasks error notification ✅

**Arquivo:** `ingestao.py`

- `audit_logger.error` com evento `pedido_falha` em falhas CADBEN (inelegível) e SIRE (não autorizada)
- Inclui `id_pedido`, `motivo`, `cpf` no payload de auditoria

### M6 — ASTM buffer limit ✅

**Arquivo:** `listener.py`

- Guard `if len(buf) > 65536:` resetando buffer e parser
- Log `logger.warning("[...] Buffer excedeu 64KB, resetando")`

### M7 — Webhook retry no middleware

**Arquivo:** eventos do middleware já têm tratamento (implementado na Fase 2). ✅

---

## Fase 4 — 🟢 BAIXO ✅ (2026-05-20)

### L1 — Bind host ✅

**Arquivo:** `src/config.py`

- `host: str = "127.0.0.1"` (default para dev local)
- Docker/Compose sobrepõe com `--host 0.0.0.0` (obrigatório dentro do container)

### L2 — .env.example sanitizado ✅

**Arquivo:** `.env.example`

- `HOST=127.0.0.1` (consistente com config.py)
- `SENAITE_PASSWORD=` vazio
- `DB_PASSWORD=` vazio

### L3 — CATSERV fallback warning ✅

**Arquivo:** `cdm_view.py`

- `logger.warn` → `logger.warning` (não-deprecado)
- Mensagem: `"CATSERV usando fallback hardcoded — dados financeiros podem estar desatualizados (erro: %s)"`

---

## Resultado Final

```
Fase 1 ──► Fase 2 ──► Fase 3 ──► Fase 4
 ✅          ✅          ✅          ✅

Testes: 91/91 passando
slowapi: instalado (0.1.9)
```

**Total:** ~15 arquivos modificados, ~200 linhas de alteração (conforme estimado).
