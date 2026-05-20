# Manual de Integração API & ASTM

> De/Para entre sistemas: SANDRA, CADBEN, SIRE, SENAITE e analisadores clínicos.

---

## Sumário

1. [CATSERV → SENAITE (Tabela de Exames)](#1-catserv--senaite-tabela-de-exames)
2. [ASTM E1394 → AmostraProcessada (Parser)](#2-astm-e1394--amostraprocessada-parser)
3. [Portas TCP → Equipamentos](#3-portas-tcp--equipamentos)
4. [Gateway API — De/Para Completo](#4-gateway-api--depara-completo)
5. [Pipeline de Dados (Campo a Campo)](#5-pipeline-de-dados-campo-a-campo)
6. [Mocks e Dados de Teste](#6-mocks-e-dados-de-teste)

---

## 1. CATSERV → SENAITE (Dicionário de Conversão de Exames)

### Origem: Tabela CATSERV (Exército — Tabela de Custos)

Cada exame no SANDRA é identificado por um **código CATSERV** (ex: `03.02.005`). Este código precisa ser convertido para a **Keyword** do AnalysisService no SENAITE antes de criar a AR ou receber resultados.

### Dicionário de Conversão (CATSERV → SENAITE)

| CATSERV (SANDRA) | Exame | SENAITE Keyword | Object ID | Unidade | Observação |
|------------------|-------|-----------------|-----------|---------|------------|
| `03.02.005` | Glicemia | `GLI001` | `glicose` | mg/dL | Seed + ASTM testado |
| `01.01.001` | Hemograma | `HEM001` | `hemograma` | milhoes/mm³ | Seed + ASTM testado |
| `02.03.010` | Urocultura | *(pendente)* | — | — | Não implementado |
| `04.01.001` | Colesterol Total | *(pendente)* | — | — | Não implementado |
| `04.01.002` | Colesterol HDL | *(pendente)* | — | — | Não implementado |
| `04.02.001` | Triglicerídeos | *(pendente)* | — | — | Não implementado |
| `05.01.001` | Creatinina | *(pendente)* | — | — | Não implementado |
| `05.02.001` | Ureia | *(pendente)* | — | — | Não implementado |
| `06.01.001` | TGO/AST | *(pendente)* | — | — | Não implementado |
| `06.01.002` | TGP/ALT | *(pendente)* | — | — | Não implementado |
| — | Lipidograma | `LIP001` | `lipidograma` | mg/dL | Apenas ASTM (sem CATSERV) |

### Como Funciona a Conversão

O fluxo esperado em produção:

```
SANDRA envia: {"exames": [{"codigo_catserv": "03.02.005", ...}]}
     │
     ▼
Middleware consulta PostgreSQL (tabela_catserv):
     SELECT senaite_keyword FROM tabela_catserv WHERE codigo = '03.02.005'
     → retorna 'GLI001'
     │
     ▼
Middleware busca AnalysisService no SENAITE:
     GET /@@API/senaite/v1/search?portal_type=AnalysisService&getKeyword=GLI001
     → retorna UID do AnalysisService
     │
     ▼
Cria AR com UID do serviço:
     POST @@hgumba-create-ar {"services": ["GLI001"], ...}
```

### Para Popular a Tabela CATSERV

```sql
-- Criar coluna de mapeamento
ALTER TABLE tabela_catserv ADD COLUMN senaite_keyword VARCHAR(20);

-- Alimentar com os seed values
UPDATE tabela_catserv SET senaite_keyword = 'GLI001' WHERE codigo = '03.02.005';
UPDATE tabela_catserv SET senaite_keyword = 'HEM001' WHERE codigo = '01.01.001';

-- Demais exames requerem cadastro no SENAITE + mapeamento
```

> **⚠️ Status atual:** A conversão CATSERV → Keyword **ainda não está implementada** no middleware. O seed data usa Keywords diretamente (`GLI001`, `HEM001`) como se fossem códigos CATSERV. Para produção, implementar o lookup no PostgreSQL em `routers/ingestao.py` ou `clients/senaite_api.py`. 
> 
> **Contorno temporário:** Configurar o SANDRA para enviar as Keywords do SENAITE (`GLI001`, `HEM001`) diretamente no campo `codigo_catserv` até o mapeamento via PostgreSQL ser implementado.

---

## 2. ASTM E1394 → AmostraProcessada (Parser)

### Visão Geral do Frame

```
[STX] payload [ETX] checksum

Payload = registros separados por CR ou CRLF:
    H - Header (1 por grupo)
    P - Patient (1 por grupo)
    O - Order (1 por amostra)
    R - Result (1+ por amostra)
    C - Comment (opcional)
    L - Terminator (1 por grupo)
```

### Record H — Header

```
{seq}H|\^&||||sender_id||||||||
```

| Campo Frame | Parser Index | Modelo | Exemplo | Observação |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `tipo_mensagem` | _(descartado)_ | | |
| `c[2]` | `delimitadores` | _(descartado)_ | `\^&` | |
| `c[4]` | `sender_id` | `machine_name` | `Mindray_BS200` | Nome do equipamento que enviou |
| demais | _(descartados)_ | | | |

### Record P — Patient

```
{seq}P|seq|patient_id|patient_name|mother_maiden|birth_date|sex|...
```

| Campo Frame | Parser Index | Modelo | Exemplo | Observação |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `sequence` | _(descartado)_ | `1` | |
| `c[2]` | `patient_id` | `AmostraProcessada.patient_id` | `MRN000001` | Field 3 ASTM |
| `c[3]` | `patient_name` | `AmostraProcessada.patient_name` | `SGT MENDES^JOAO` | Field 4 ASTM, formato `SOBRENOME^NOME` |
| `c[4]` | `mother_maiden` | _(descartado)_ | | Nome de solteira da mãe |
| `c[5]` | `birth_date` | _(descartado)_ | `19800101` | Formato YYYYMMDD |
| `c[6]` | `sex` | _(descartado)_ | `M` | M/F |

### Record O — Order

```
{seq}O|seq|sample_id||universal_test_id|...
```

| Campo Frame | Parser Index | Modelo | Exemplo | Observação |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `sequence` | _(descartado)_ | `1` | |
| `c[2]` | `sample_id` | `AmostraProcessada.sample_id` | `HGU-AR-001` | Código de barras da AR — **chave para o SENAITE** |
| `c[4]` | `universal_test_id` | _(descartado)_ | `^^^GLI001` | Formato `^^^codigo` |
| `c[4].parts[0]` | — | _(descartado)_ | | |
| `c[4].parts[1]` | — | _(descartado)_ | | |

### Record R — Result

```
{seq}R|seq|universal_test_id|valor|type|unidade|ref_range|flag|...
```

| Campo Frame | Parser Index | Modelo | Exemplo | Observação |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `sequence` | _(descartado)_ | `1` | |
| `c[2].parts[-1]` | `keyword` | `ResultadoExameInstrumento.keyword` | `GLI001` | Última parte após `^^^` |
| `c[3]` | `valor` | `ResultadoExameInstrumento.valor` | `105.5` | String, sem formatação |
| `c[4]` | `type` | _(descartado)_ | `N` | N=Normal, C=Control, etc. |
| `c[5]` | `unidade` | `ResultadoExameInstrumento.unidade` | `mg/dL` | |
| `c[6]` | `ref_range` | _(descartado)_ | | Intervalo de referência |
| `c[7]` | `flag` | `ResultadoExameInstrumento.flag_anormalidade` | `H` | H=High, L=Low, HH=Critical, LL=Critical Low |
| demais | — | _(descartados)_ | | |

### Record C — Comment

```
{seq}C|texto|...
```

| Campo Frame | Parser Index | Modelo | Exemplo |
|-------------|-------------|--------|---------|
| `c[1]` | `texto` | _(descartado)_ | `Amostra hemolisada` |

### Record L — Terminator

```
{seq}L|seq|termination_code
```

**Apenas o registro `L` dispara a extração da amostra.** Ao encontrar `L`, o parser consolida os dados em `AmostraProcessada`.

### Modelos Finais

```python
class ResultadoExameInstrumento(BaseModel):
    keyword: str           # ex: "GLI001"
    valor: str             # ex: "105.5"
    unidade: Optional[str] # ex: "mg/dL"
    flag_anormalidade: Optional[str]  # "H" | "L" | "HH" | None

class AmostraProcessada(BaseModel):
    sample_id: str         # código de barras, ex: "HGU-AR-001"
    machine_name: str      # nome do equipamento
    patient_id: Optional[str]
    patient_name: Optional[str]
    resultados: List[ResultadoExameInstrumento]
```

### Exemplo Completo de Parse

**Frame ASTM:**
```
\x02
1H|^&|||Mindray_BS200|||||||||
2P|1|MRN000001|SGT MENDES^JOAO||19800101|M
3O|1|HGU-AR-001||^^^GLI001
4R|1|^^^GLI001|105.5|N|mg/dL||H
5L|1|N
\x0261
```

**Resultado do Parse:**
```python
AmostraProcessada(
    sample_id="HGU-AR-001",
    machine_name="Mindray_BS200",
    patient_id="MRN000001",
    patient_name="SGT MENDES^JOAO",
    resultados=[
        ResultadoExameInstrumento(
            keyword="GLI001",
            valor="105.5",
            unidade="mg/dL",
            flag_anormalidade="H"
        )
    ]
)
```

---

## 3. Portas TCP → Equipamentos

### Mapeamento (configurado em `instruments/config.py`)

Cada analisador deve ser configurado para enviar resultados ASTM para o IP do middleware na porta designada:

| Porta | Nome Interno | Equipamento Real | Especialidade | Protocolo |
|-------|-------------|-------------------|---------------|-----------|
| **5001** | `Mindray_BS200` | Mindray BS-200 | Bioquímica | ASTM E1381/E1394 |
| **5002** | `Sysmex_XN550` | Sysmex XN-550 | Hematologia | ASTM E1381/E1394 |
| **5003** | `Roche_Cobas_e411` | Roche Cobas e411 | Imunoquímica | ASTM E1381/E1394 |
| **5004** | `Roche_Cobas_c311` | Roche Cobas c311 | Química Clínica | ASTM E1381/E1394 |
| **5005** | `BioRad_D10` | Bio-Rad D-10 | HbA1c | ASTM E1381/E1394 |

### Topologia de Rede (Middleware Gateway)

```
┌─ Rede Laboratório ───────────────────────────────────────────────┐
│                                                                  │
│   Analisadores                             Middleware (porta 8000)│
│   ┌──────────────┐     TCP/IP:5001          ┌─────────────────┐  │
│   │ Mindray BS200 │──── ENQ/ACK/STX/EOT ───►│                 │  │
│   └──────────────┘                          │  listener.py    │  │
│   ┌──────────────┐     TCP/IP:5002          │  (daemon TCP    │  │
│   │ Sysmex XN550 │─────────────────────────►│   assíncrono)   │  │
│   └──────────────┘                          │                 │  │
│   ┌──────────────┐     TCP/IP:5003          │  ── parseia     │  │
│   │ Cobas e411   │─────────────────────────►│  ── audita      │  │
│   └──────────────┘                          │  ── envia       │  │
│   ┌──────────────┐     TCP/IP:5004          │       para      │  │
│   │ Cobas c311   │─────────────────────────►│    SENAITE      │  │
│   └──────────────┘                          └────────┬────────┘  │
│   ┌──────────────┐     TCP/IP:5005                   │           │
│   │ BioRad D10   │─────────────────────────►         │           │
│   └──────────────┘                                   │           │
│                                                       ▼           │
│                                            ┌─────────────────┐  │
│                                            │  SENAITE LIMS   │  │
│                                            │   port 8083     │  │
│                                            └─────────────────┘  │
│                                                                  │
│   Gateway (porta 8000)                                           │
│   ┌────────────────────────────────────────────────────────────┐ │
│   │ POST /api/v1/sandra/ingestao  ← SANDRA (prontuário)       │ │
│   │ POST /api/v1/senaite/webhook/... ← SENAITE (laudo pub.)   │ │
│   └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

#### Configuração no Analisador

Cada equipamento deve ser configurado (via software do fabricante) com:

| Parâmetro | Valor |
|-----------|-------|
| **IP destino** | IP do servidor middleware (`192.168.x.x` — conforme rede do laboratório) |
| **Porta** | Conforme tabela acima (5001–5005) |
| **Protocolo** | ASTM E1381 (enquadramento) / E1394 (registros) |
| **Handshake** | Hardware (ENQ/ACK) |
| **Encoding** | ASCII |
| **Checksum** | XOR (2 hex chars ao final do frame) |
| **Terminador** | CR ou CRLF |

> **Instrução para engenharia clínica:** Ao conectar um novo analisador, cadastre a porta em `instruments/config.py` (dicionário `INSTRUMENTOS`), adicione a porta ao parâmetro `--portas=` no `compose.local.yaml`, e configure o equipamento com o IP do middleware e a porta designada.

### Handshake (E1381)

### Handshake (E1381)

| Byte | Símbolo | Quem Envia | Significado |
|------|---------|-----------|-------------|
| `0x05` | ENQ | Analisador | "Quer enviar dados" |
| `0x06` | ACK | Middleware | "Pronto para receber" |
| `0x02...0x03 + cks` | STX+ETX+chk | Analisador | Payload com checksum |
| `0x06` / `0x15` | ACK/NAK | Middleware | "Frame OK / Corrompido" |
| `0x04` | EOT | Analisador | "Fim da transmissão" |
| `0x06` | ACK | Middleware | "Transmissão recebida" |

---

## 4. Gateway API — De/Para Completo

### 4.1 `POST /api/v1/sandra/ingestao`

> Entrada: SANDRA → Middleware. Saída: CADBEN + SIRE + SENAITE.

#### De/Para Campos

| Campo Input (SANDRA) | Tipo | Validação | Para Onde Vai | Campo Destino |
|---------------------|------|-----------|---------------|---------------|
| `id_pedido` | `str` | obrigatório | SIRE (GET `/api/v1/guias/{id_pedido}`) | path param |
| `cpf_paciente` | `str` | regex `^\d{11}$` | CADBEN (GET `/api/v1/beneficiarios/{cpf}/elegibilidade`) | path param |
| `nome_paciente` | `str` | obrigatório | _(log apenas)_ | — |
| `medico_solicitante` | `str` | obrigatório | SENAITE (`create_analysis_request`) | `doctor_name` |
| `crm_solicitante` | `str` | obrigatório | SENAITE (`create_analysis_request`) | `doctor_crm` |
| `data_solicitacao` | `datetime` | ISO 8601 | _(log apenas)_ | — |
| `exames[].codigo_catserv` | `str` | obrigatório | SENAITE (`create_analysis_request`) | `services[]` |
| `exames[].descricao` | `str` | — | _(log apenas)_ | — |
| `exames[].urgente` | `bool` | default `false` | _(log apenas)_ | — |

#### Fluxo de Validação Interna

```
OrdemServicoSANDRA
  ├── CADBEN.validar_elegibilidade(cpf)       →  elegivel? (mock: sempre True)
  ├── SIRE.validar_guia(id_pedido)            →  autorizada? (mock: sempre True)
  └── SENAITE.create_analysis_request(
        client_id="hgu",
        services=[codigos catserv...],
        doctor_name=medico_solicitante,
        doctor_crm=crm_solicitante
      )
```

#### Resposta

```json
{"status": "aceito", "id_pedido": "...", "mensagem": "Pedido em processamento"}
```

---

### 4.2 `POST /api/v1/senaite/webhook/laudo_publicado`

> Entrada: SENAITE → Middleware (via Event Subscriber ZCML). Saída: SANDRA.

#### Payload de Entrada (enviado pelo SENAITE)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `analysis_request_id` | `str` | sim | ID da AR publicada (ex: `HGU-AR-001`) |
| `client_id` | `str` | sim | Identificador do cliente (ex: `hgu`) |
| `patient_name` | `str?` | não | Nome do paciente |
| `pdf_url` | `str?` | não | URL do PDF (não usado — middleware baixa direto) |
| `review_state` | `str` | sim | **Deve ser `"published"`** |
| `results` | `list[dict]?` | não | Resultados dos exames |

#### Critério de Filtro

```python
if payload.review_state != "published":
    → {"status": "ignorado", "motivo": "Apenas laudos publicados são processados"}
```

#### Ações Disparadas

```
WebhookLaudoPayload
  │
  ├── SENAITE.get_ar_pdf(ar_id)
  │     GET /clients/hgu/{analysis_request_id}/@@cdm-pdf
  │     → bytes do PDF
  │
  └── SANDRA.notificar_sandra(ar_id, pdf_base64)
        POST /api/v1/resultados
        {
          "id_pedido": analysis_request_id,
          "analysis_request_id": analysis_request_id,
          "pdf_laudo_base64": <base64 do PDF>,
          "observacoes": None
        }
```

#### Resposta

```json
{"status": "processado", "analysis_request_id": "HGU-AR-001", "sandra_notificado": true}
```

---

### 4.3 `POST @@hgumba-create-ar` (Bypass)

> Endpoint custom do add-on Zope. Bypassa a restrição do `@@API/create` que bloqueia AnalysisRequest.

| Aspecto | Detalhe |
|---------|---------|
| URL | `http://app:8080/senaite/@@hgumba-create-ar` |
| Método | `POST` |
| Content-Type | `application/json` |
| Autenticação | Basic Auth (mesmo admin:admin) |

#### Payload de Entrada

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `client_id` | `str` | não (default `"hgu"`) | Client onde criar a AR |
| `services` | `list[str]` | **sim** | Keywords dos AnalysisServices (ex: `["GLI001"]`) |
| `contact_id` | `str?` | não | ID do Contact (médico solicitante) |
| `patient_name` | `str?` | não | Nome completo do paciente |
| `mrn` | `str?` | não | Medical Record Number (ou CPF) |
| `ar_id` | `str?` | não | ID desejado para a AR (ex: `HGU-AR-001`) |
| `title` | `str?` | não | Título da AR (fallback: `ar_id` ou services[0]) |

#### Exemplo

```json
{
  "client_id": "hgu",
  "services": ["GLI001"],
  "contact_id": "contact-1",
  "mrn": "MRN-001",
  "patient_name": "Maria Silva",
  "ar_id": "HGU-AR-001"
}
```

#### Resposta (201)

```json
{
  "success": true,
  "id": "HGU-AR-001",
  "uid": "463022b33a9347c497f8fb79cd5eec64",
  "url": "http://.../clients/hgu/HGU-AR-001"
}
```

#### Motor Interno

Diferente do `@@API/create` (que usa `bika/lims/jsonapi/create.py` e explicitamente bloqueia ARs em `create.py:168`), este endpoint:

1. Lê o JSON body
2. Busca o Client por `client_id`
3. Percorre `bika_setup.bika_analysisservices` procurando cada `Keyword` correspondente → extrai UID
4. Chama `client.invokeFactory('AnalysisRequest', ar_id, Analyses=[...], Contact=...)`
5. Seta `MedicalRecordNumber` e `PatientFullName` via `ar.getField()`
6. `transaction.commit()`
7. Retorna `{success, id, uid, url}`

### 4.4 `GET /health`

| Campo | Valor Fixo |
|-------|-----------|
| `status` | `"healthy"` |
| `service` | `"hgumba-middleware"` |
| `version` | `"1.0.0"` |

---

## 5. Pipeline de Dados (Campo a Campo)

### Sentido: Analisador → SENAITE

```
Analisador (TCP:5001)
  │ ASTM Frame (STX/ETX/checksum)
  ▼
listener.py :: AnalisadorTCP.alimentar()
  │ handshake ACK/NAK, valida checksum
  ▼
astm.py :: ASTM1394Parser.alimentar()
  │ decodifica registros H,P,O,R,L
  ▼
AmostraProcessada (modelo)
  ├── sample_id    ← O[2]
  ├── machine_name ← do config (porta → nome)
  ├── patient_id   ← P[2]   ──────→ DESCARTADO no envio
  ├── patient_name ← P[3]   ──────→ DESCARTADO
  └── resultados[]
       ├── keyword  ← R[2] último elemento após ^^^
       ├── valor    ← R[3]        ──→ SENAITE Result
       ├── unidade  ← R[5]        ──→ DESCARTADO
       └── flag     ← R[7]        ──→ DESCARTADO
  ▼
listener.py :: _enviar_para_senaite()
  │ Envia para SENAITE apenas: (sample_id, keyword, valor)
  ▼
senaite_api.py :: set_analysis_result()
  │ GET /@@API/senaite/v1/search?portal_type=Analysis&getKeyword={keyword}&parent_path=/senaite/clients/hgu/{sample_id}
  │ → extrai uid do primeiro resultado
  │ POST /@@API/senaite/v1/update?uid={uid}&Result={valor}
  ▼
SENAITE — Analysis.Result atualizado
```

### Sentido: SANDRA → SENAITE (via Gateway)

```
SANDRA (POST /api/v1/sandra/ingestao)
  │ JSON body: OrdemServicoSANDRA
  ▼
validar_elegibilidade(CADBEN) → True/False
validar_guia(SIRE)             → True/False
  ▼
SENAITE.create_analysis_request()
  │ POST /@@hgumba-create-ar
  │   client_id     = "hgu"
  │   services      = [codigos catserv...]
  │   patient_name  = ordem.nome_paciente
  │   mrn           = ordem.cpf_paciente
  │   contact_id    = "contact-1"
  │   ar_id         = ordem.id_pedido
  │
  │ (BrowserView custom — bypass do @@API/create)
  │   → invokeFactory + setField + commit
  ▼
SENAITE — AnalysisRequest criada em estado "sample_registered"
```

### Sentido: SENAITE → SANDRA (via Webhook)

```
SENAITE (Event Subscriber — IAfterTransitionEvent, state="published")
  │ POST async via urllib2 para:
  ▼
POST /api/v1/senaite/webhook/laudo_publicado
  │ JSON body: WebhookLaudoPayload
  │ review_state == "published" ?
  ▼
get_ar_pdf(ar_id)
  │ GET /clients/hgu/{ar_id}/@@cdm-pdf
  │ → PDF bytes → base64
  ▼
notificar_sandra(ar_id, pdf_base64)
  │ POST /api/v1/resultados (SANDRA)
  ▼
SANDRA — laudo registrado no prontuário
```

---

## 6. Mocks e Dados de Teste

### APIs Exército (modo DEV)

Quando as variáveis de ambiente `SANDRA_BASE_URL`, `CADBEN_BASE_URL` e `SIRE_BASE_URL` **estão vazias**, o client retorna respostas mock:

| API | Resposta Mock |
|-----|--------------|
| CADBEN | `{"cpf": "...", "elegivel": true, "beneficiario": {"nome": "Paciente DEV", "posto_graduacao": "Sd DEV", "organizacao_militar": "H Gu Marabá", "ativo": true}}` |
| SIRE | `True` (sempre autorizada) |
| SANDRA | `True` (sempre notificado com sucesso) |

### Emulador ASTM (`tests/mock_instrument.py`)

```bash
# Simular Mindray BS-200 na porta 5001
uv run python tests/mock_instrument.py --port 5001 --machine Mindray_BS200
```

Envia 3 amostras fixas:

| sample_id | keyword | valor | unidade | flag | paciente |
|-----------|---------|-------|---------|------|----------|
| `HGU-AR-001` | `GLI001` | `105.5` | `mg/dL` | `H` | `SGT MENDES^JOAO` |
| `HGU-AR-002` | `HEM001` | `5.2` | `milhoes/mm3` | — | `CB MOURA^MARIA` |
| `HGU-AR-003` | `LIP001` | `320` | `mg/dL` | `HH` | `CAP OLIVEIRA^CARLOS` |

### Seed Data (SENAITE)

Para criar os dados de teste no SENAITE, acessar via browser:

```
http://admin:admin@localhost:8083/senaite/@@hgumba-seed
```

Cria:

| Objeto | ID | Detalhes |
|--------|----|----------|
| Client | `hgu` | Title: "HGU - Hospital Gumarba" |
| AnalysisService | `glicose` | Keyword: `GLI001`, Unit: `mg/dL` |
| AnalysisService | `hemograma` | Keyword: `HEM001`, Unit: `milhoes/mm3` |
| AnalysisService | `lipidograma` | Keyword: `LIP001`, Unit: `mg/dL` |
| Contact | `contact-1` | Dr. Admin |
| AnalysisRequest | `HGU-AR-001` | MRN-001, Maria Silva, GLI001 |
| AnalysisRequest | `HGU-AR-002` | MRN-002, Jose Santos, HEM001 |
| AnalysisRequest | `HGU-AR-003` | MRN-003, Carlos Oliveira, LIP001 |

---

## 7. Troubleshooting com Audit Logger

O middleware registra todos os eventos críticos do pipeline em formato JSON estruturado via `audit_logger`. Este log é a principal ferramenta de troubleshooting para rastrear resultados rejeitados ou fluxos interrompidos.

### 7.1 Como Visualizar os Logs de Auditoria

```bash
# Gateway (FastAPI)
docker logs -f middleware_gateway 2>&1 | findstr "HGUMBA-Audit"

# Daemon de Instrumentos (TCP)
docker logs -f middleware_instruments 2>&1 | findstr "HGUMBA-Audit"

# Ambos — cores para leitura facilitada
docker logs middleware_gateway 2>&1 | findstr "HGUMBA-Audit" | python -m json.tool
```

Para seguir em tempo real:
```bash
docker logs -f middleware_gateway 2>&1 | findstr "HGUMBA-Audit"
```

### 7.2 Estrutura do JSON de Auditoria

Cada linha de auditoria segue este formato:

```json
{
  "timestamp": "2026-05-19T14:30:00Z",
  "level": "INFO",
  "component": "HGUMBA-Audit",
  "message": "Resultado injetado no SENAITE",
  "audit_data": {
    "evento": "resultado_importado",
    "sample_id": "HGU-AR-001",
    "keyword": "GLI001",
    "valor": "105.5",
    "unidade": "mg/dL",
    "flag": "H",
    "maquina": "Mindray_BS200",
    "via": "ASTM E1394"
  }
}
```

### 7.3 Catálogo de Eventos

| Evento | Message | Onde é Gerado | Causa Comum |
|--------|---------|---------------|-------------|
| `gateway_iniciado` | "Gateway iniciado" | `main.py` startup | Serviço subiu |
| `gateway_finalizado` | "Gateway finalizado" | `main.py` shutdown | Serviço parou |
| `daemon_iniciado` | "Daemon de instrumentos iniciado" | `runner.py` | Daemon TCP subiu |
| `daemon_finalizado` | "Daemon de instrumentos finalizado" | `runner.py` | Daemon TCP parou |
| `resultado_importado` | "Resultado injetado no SENAITE" | `listener.py` | ✅ Sucesso — resultado enviado ao SENAITE |
| `resultado_falha` | "Falha ao injetar resultado" | `listener.py` | ❌ AR não encontrada, keyword inválida, SENAITE offline |
| `pedido_injetado` | "Pedido SANDRA injetado no SENAITE" | `ingestao.py` | ✅ Sucesso — AR criada via ingestão |
| `webhook_pdf_falha` | "Falha ao obter PDF do laudo" | `webhooks.py` | ❌ AR não encontrada, SENAITE offline, PDF não gerado |
| `laudo_publicado` | "Laudo publicado processado" | `webhooks.py` | Webhook recebido e encaminhado ao SANDRA |

### 7.4 Fluxo de Troubleshooting para Resultado Rejeitado

Quando um resultado não aparece no SENAITE, siga estes passos:

```
Passo 1: Verificar se o frame chegou ao daemon
└─ docker logs middleware_instruments 2>&1 | findstr "HGUMBA-Audit" | findstr "HGU-AR-001"
   ├─ Se encontrar "resultado_importado" → o parse funcionou, o SENAITE recebeu
   ├─ Se encontrar "resultado_falha" → o parse funcionou mas o envio falhou
   │    └─ Ver o campo "erro" no audit_data:
   │       ├─ "Analysis not found" → Keyword não existe no SENAITE
   │       ├─ "404" → AR não encontrada (sample_id errado?)
   │       └─ "Connection refused" → SENAITE offline
   └─ Se NÃO encontrar → o frame não chegou ou foi rejeitado no handshake
        └─ Verificar logs do analisador + conectividade TCP

Passo 2: Se há "resultado_falha", checar o campo audit_data.erro

Passo 3: Verificar se a AR existe no SENAITE
└─ curl -u admin:admin "http://localhost:8083/senaite/@@API/senaite/v1/search?portal_type=AnalysisRequest&getId=HGU-AR-001"

Passo 4: Verificar se o AnalysisService existe
└─ curl -u admin:admin "http://localhost:8083/senaite/@@API/senaite/v1/search?portal_type=AnalysisService&getKeyword=GLI001"
```

### 7.5 Exemplos de JSON Reais e sua Interpretação

#### Caso 1: Sucesso — resultado importado
```json
{"timestamp":"2026-05-19T14:30:00Z","level":"INFO","message":"Resultado injetado no SENAITE","audit_data":{"evento":"resultado_importado","sample_id":"HGU-AR-001","keyword":"GLI001","valor":"105.5","maquina":"Mindray_BS200"}}
```
> **Interpretação:** A máquina Mindray BS200 enviou glicemia 105.5 mg/dL para AR HGU-AR-001. O SENAITE aceitou e o remark de auditoria foi registrado.

#### Caso 2: Falha — AR não encontrada
```json
{"timestamp":"2026-05-19T14:31:00Z","level":"ERROR","message":"Falha ao injetar resultado","audit_data":{"evento":"resultado_falha","sample_id":"HGU-AR-999","keyword":"GLI001","erro":"Analysis not found","maquina":"Mindray_BS200"}}
```
> **Interpretação:** A AR `HGU-AR-999` não existe no SENAITE. Verificar se o código de barras lido pelo analisador corresponde ao ID da AR.

#### Caso 3: Falha — SENAITE offline
```json
{"timestamp":"2026-05-19T14:32:00Z","level":"ERROR","message":"Falha ao injetar resultado","audit_data":{"evento":"resultado_falha","sample_id":"HGU-AR-001","keyword":"GLI001","erro":"ConnectError: Connection refused","maquina":"Sysmex_XN550"}}
```
> **Interpretação:** O SENAITE não está respondendo. Verificar `docker ps` e logs do container SENAITE.

#### Caso 4: Ingestão de pedido SANDRA
```json
{"timestamp":"2026-05-19T14:33:00Z","level":"INFO","message":"Pedido SANDRA injetado no SENAITE","audit_data":{"evento":"pedido_injetado","id_pedido":"PED-001","cpf_paciente":"12345678901","exames":["GLI001"],"via":"sandra_ingestao"}}
```
> **Interpretação:** Pedido PED-001 do SANDRA foi recebido e a AR foi criada no SENAITE com exame GLI001.

#### Caso 5: Webhook de laudo publicado
```json
{"timestamp":"2026-05-19T14:34:00Z","level":"INFO","message":"Laudo publicado processado","audit_data":{"evento":"laudo_publicado","analysis_request_id":"HGU-AR-001","sandra_notificado":true,"via":"webhook"}}
```
> **Interpretação:** A AR HGU-AR-001 foi publicada no SENAITE, o PDF foi obtido e enviado ao SANDRA com sucesso.

### 7.6 Comandos Úteis para Troubleshooting Rápido

```bash
# Últimos 10 eventos de auditoria
docker logs middleware_gateway 2>&1 | findstr "HGUMBA-Audit" | findstr /v "daemon" | python -c "import sys; [print(l) for l in sys.stdin.readlines()[-10:]]"

# Todas as falhas de resultado
docker logs middleware_instruments 2>&1 | findstr "HGUMBA-Audit" | findstr "resultado_falha"

# Filtrar por uma AR específica
docker logs middleware_instruments 2>&1 | findstr "HGU-AR-001"

# Verificar se o remark de auditoria foi registrado na AR
curl -u admin:admin "http://localhost:8083/senaite/clients/hgu/HGU-AR-001/@@hgumba-debug" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('Remarks',''))"

# Acompanhar em tempo real eventos de erro
docker logs -f middleware_gateway 2>&1 | findstr "ERROR.*HGUMBA"
```

---

## Anexo: Derivação dos Keywords

Os códigos de 3 letras + 3 dígitos (`GLI001`, `HEM001`, `LIP001`) são **internos do SENAITE** (definidos como `Keyword` no AnalysisService). Eles são usados como:

| Sistema | Como Usa |
|---------|----------|
| **ASTM** (R[2]) | Código do exame no equipamento (`^^^GLI001`) |
| **SENAITE** | `getKeyword` do AnalysisService, identifica qual análise recebe o resultado |
| **CATSERV** | _(ainda não mapeado)_ — a coluna `codigo` (`01.01.001` etc.) é o código oficial do Exército |

Para produção, cada linha da `tabela_catserv` deve ter seu `codigo` mapeado para a `Keyword` SENAITE correspondente.

---

*Documento gerado em 2026-05-19 | v2.0.0*
