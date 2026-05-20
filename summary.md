## Goal
- Provisionar SENAITE LIMS localmente (Docker Desktop) e implementar três módulos custom add-on (multi-profissional solicitante, CDM billing, relatório com histórico gráfico) para Hospital Geral de Umba.

## Constraints & Preferences
- SENAITE roda Zope/Plone 5.2.15 sobre Python 2.7; ZODB exige 1 réplica.
- Desenvolvimento agora em Docker Desktop (Windows), não mais no cluster Swarm.
- Imagem base: `192.168.4.23:5000/senaite:2.x`.
- Dependências pip pré-instaladas via Dockerfile (evita `pip install` a cada restart).
- Add-on montado como bind volume para hot-reload durante desenvolvimento.
- Bind mounts do Windows não podem ser `chown` pelo container — entrypoint patcheado para ignorar erros (`|| true`).
- Credenciais Zope: `admin:admin` (configurável via env `PASSWORD`).
- Container tem volume anônimo (`0e910d04...`) montado em `/data` — lá está o Data.fs real, fora do layer da imagem.
- Compose `.local.yaml` mapeia `senaite_data:/opt/senaite/var` (named volume), mas o zope.conf aponta para `/data/filestorage/Data.fs` (anonymous volume). `instance run` via compose **não monta** anonymous volumes.

## Progress

### Done
- Cluster Swarm removido; Docker Desktop limpo.
- Imagem base baixada, Dockerfile custom criado com pip deps, .pth, package-includes, entrypoint patcheado.
- `compose.local.yaml` criado (build local, porta 8083, volume persistente, bind do add-on).
- Fix `cdm_view.py`: `from senaite.core.logger import get_logger` → `import logging` / `logging.getLogger(...)`.
- Fix `extensions/schema.py`: `BaseSchemaExtender` → `@implementer(ISchemaExtender) @adapter(IExtensible)`.
- Zope iniciou sem erros, HTTP 200 em `http://127.0.0.1:8083/`.
- Site SENAITE criado via `@@senaite-addsite` (POST auth basic `admin:admin`).
- Add-on `senaite.hgumba` instalado via Plone Control Panel (Add-ons) — ativado.
- Views registradas: `@@cdm-pdf`, `@@hgumba-report-pdf`, `@@hgumba-seed`, `@@hgumba-debug`, `@@hgumba-create-ar`.
- HTTP API (`@@API/create`) criou 5 AnalysisServices + 1 Client com sucesso.
- **senaite.patient** instalado e ativado (Patient FTI existe após install via formulário).
- Contacts criados como doutores solicitantes via `@@API/create` (Contact type, não Patient).
- Seed view `@@hgumba-seed` cria AnalysisRequests com dados de paciente (MRN, nome, sexo) e Contact.
- **CDM PDF** (`@@cdm-pdf`) — Funcionando: gera PDF com ID requisição, nome paciente e tabela de exames com código CATSERV e valor.
- **Report PDF** (`@@hgumba-report-pdf`) — Funcionando: gera PDF com resultados, flags fora-do-intervalo, nome do paciente e gráfico de histórico.
- Tabela CATSERV hardcoded no `cdm_view.py` (`CATSERV_TABLE` dict) com 3 exames (Hemograma, Urocultura, Glicemia).
- Helper `_val(obj, attr, default)` criado para lidar com atributos que podem ser string ou método (API do SENAITE inconsistente).
- **`@@API/create` bypass**: endpoint custom `@@hgumba-create-ar` criado para contornar a restrição explícita do SENAITE core (`bika/lims/jsonapi/create.py:168` — `raise BadRequest("not supported")`). Usa `invokeFactory` diretamente. Testado com `POST` JSON: `client_id`, `services[]`, `contact_id`, `mrn`, `patient_name`. Retorna `{success, id, uid, url}`.
- Middleware `senaite_api.py:create_analysis_request()` atualizado para chamar `@@hgumba-create-ar` em vez de `@@API/create`.
- Rota `ingestao.py` atualizada para passar `patient_fullname` e `mrn` (CPF) ao criar AR.
- **Parser ASTM corrigido**: `_parse_patient()` lê `patient_name` de `c[3]` (não `c[4]`). Testes: 40/40.
- **@@hgumba-set-remark**: BrowserView custom `SetRemarkView` para bypass da validação de campos obrigatórios do `@@API/senaite/v1/update`. Faz append de remark em AR existente via `ar.getField('Remarks').set()`.
- **Audit Trail RDC 978**: `JSONAuditFormatter` + `audit_logger` em `src/logger.py`. Eventos: `resultado_recebido`, `resultado_enviado`, `webhook_recebido`, `sandra_notificado`, `erro_integracao`. Gravados em estrutura JSON com timestamp, user, ar_id, machine, metadata.
- **compose.local.yaml**: Volume `:ro` removido (read-write para desenvolvimento).
- **create_ar.py refatorado**: `_find_service_by_keyword` e `_set_ar_fields` como funções de módulo (não mais aninhadas em classe), `_ensure_ar` como método de `CreateAnalysisRequestView`.
 
### Key Learnings
- `AnalysisRequest.getPatient()` **não existe** — a relação Patient-AR usa `MedicalRecordNumber` field + `getPatientFullName()` monkeypatch do `senaite.patient`.
- `analysis.Title` e `analysis.getResult()` em objetos retornados por `getAnalyses()` são **strings**, não métodos — `Title()` falha com `TypeError: 'str' object is not callable`.
- `for="*"` em BrowserView ZCML funciona corretamente (context é o objeto do traversal, não RequestContainer como parecia inicialmente).
- `@@API/create` bloqueia `AnalysisRequest` explicitamente em `bika/lims/jsonapi/create.py:168` — a v1 API (`@@API/senaite/v1/create`) tem tratamento especial mas não foi validada. Solução prática: BrowserView custom com `invokeFactory`.
- `instance run` NÃO funciona com o Data.fs real porque o ZODB está em anonymous volume não montado pelo `compose run`.

### Em Andamento
- Validar integração completa: pipeline ASTM → middleware → SENAITE (cria AR + seta remark + auditoria).

### Próximos Passos
1. Validar audit trail RDC 978 com dados reais de analisador (simular envio ASTM).
2. Implementar container PostgreSQL (`db_financeiro`) com `tabela_catserv` para substituir `CATSERV_TABLE` hardcoded.
3. Conectar `cdm_view.py` ao PostgreSQL via `psycopg2`.
4. Expandir seed para criar análises com resultados históricos (para testar gráfico no report).
5. Limpar orphans containers do compose (`docker compose run --remove-orphans`).

## Critical Context
- Container local: `senaite-app-1`, imagem `senaite-hgumba:local`.
- Add-on bind-mount: `C:\...\customizations\src\senaite.hgumba\src\` → `/opt/senaite/addons/src` (agora **read-write** — `:ro` removido para desenvolvimento).
- Acesso SENAITE: `http://127.0.0.1:8083/senaite` (admin:admin).
- Volume anônimo `/data` contém o ZODB Data.fs real — persiste entre restarts.
- API `@@API/create` funciona para: AnalysisService, Client, Contact. **Falha/bloqueia: AnalysisRequest** (`bika/lims/jsonapi/create.py:168`).
- **Bypass**: `@@hgumba-create-ar` (POST JSON, `invokeFactory`, retorna `{success, id, uid, url}`).
- **Bypass update**: `@@hgumba-set-remark` (POST JSON, seta campo Remarks via `getField().set()`, sem validação de obrigatórios).
- **Audit Trail**: `src/logger.py` — `audit_logger` com `JSONAuditFormatter`. Eventos registrados em `listener.py`, `webhooks.py`, `ingestao.py`, `runner.py`.
- Erros anteriores resolvidos: namespace ZCML `plone`, `ISenaiteCoreLayer`, `senaite.core.logger`, `BaseSchemaExtender`, `cmf.ManagePortal`, encoding utf-8.
- Permit `cmf.ManagePortal` não disponível — usar `zope2.View` para views de desenvolvimento.
- `hasattr(ar, 'getPatient')` retorna False — `getPatient` não existe; usar `getPatientFullName()` e `getMedicalRecordNumberValue()` do monkeypatch senaite.patient.
- Análises nos ARs acessíveis via `ar.getAnalyses()` — atributos como `Title`, `getResult`, `getUnit`, `getKeyword` são strings, não métodos.

## Relevant Files
- `C:\...\SENAITE\Dockerfile` — imagem local com pip deps, .pth, package-includes, entrypoint patcheado.
- `C:\...\SENAITE\compose.local.yaml` — stack local (build, porta 8083, volumes addon + data named).
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\browser\views\cdm_view.py` — CDM PDF (CATSERV_TABLE hardcoded, ReportLab).
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\browser\views\report_view.py` — Laudo com histórico gráfico (matplotlib + ReportLab).
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\browser\views\seed.py` — Seed view (`@@hgumba-seed`) para criar dados de teste.
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\browser\views\create_ar.py` — Endpoints `@@hgumba-create-ar` + `@@hgumba-set-remark`, funções de módulo `_find_service_by_keyword`, `_set_ar_fields`.
- `C:\...\SENAITE\hgumba-middleware\src\logger.py` — `JSONAuditFormatter` + `audit_logger` (RDC 978).
- `C:\...\SENAITE\hgumba-middleware\src\instruments\listener.py` — `set_analysis_result(machine_name)` registra remark de auditoria na AR.
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\extensions\schema.py` — CoPhysiciansField extender (ISchemaExtender adapter).
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\extensions\configure.zcml` — adapter registration.
- `C:\...\SENAITE\customizations\src\senaite.hgumba\src\senaite\hgumba\browser\configure.zcml` — views registration (cdm-pdf, hgumba-report-pdf, hgumba-seed, hgumba-debug, **hgumba-create-ar**).
- `C:\...\SENAITE\customizations\package-includes\050-senaite-hgumba-configure.zcml` — include ZCML (copiado para imagem).
- `C:\...\SENAITE\customizations\patch-entrypoint.py` — script que adiciona `|| true` aos `chown` do entrypoint.
