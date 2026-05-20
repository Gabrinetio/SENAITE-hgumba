> **Origem:** `SENAITE/hgumba-middleware/docs/integracao.md`

# Manual de IntegraÃ§Ã£o API & ASTM

> De/Para entre sistemas: SANDRA, CADBEN, SIRE, SENAITE e analisadores clÃ­nicos.

---

## SumÃ¡rio

1. [CATSERV â†’ SENAITE (Tabela de Exames)](#1-catserv--senaite-tabela-de-exames)
2. [ASTM E1394 â†’ AmostraProcessada (Parser)](#2-astm-e1394--amostraprocessada-parser)
3. [Portas TCP â†’ Equipamentos](#3-portas-tcp--equipamentos)
4. [Gateway API â€” De/Para Completo](#4-gateway-api--depara-completo)
5. [Pipeline de Dados (Campo a Campo)](#5-pipeline-de-dados-campo-a-campo)
6. [Mocks e Dados de Teste](#6-mocks-e-dados-de-teste)
7. [Troubleshooting com Audit Logger](#7-troubleshooting-com-audit-logger)

---

## 1. CATSERV â†’ SENAITE (DicionÃ¡rio de ConversÃ£o de Exames)

### Origem: Tabela CATSERV (ExÃ©rcito â€” Tabela de Custos)

Cada exame no SANDRA Ã© identificado por um **cÃ³digo CATSERV** (ex: `03.02.005`). Este cÃ³digo precisa ser convertido para a **Keyword** do AnalysisService no SENAITE antes de criar a AR ou receber resultados.

### DicionÃ¡rio de ConversÃ£o (CATSERV â†’ SENAITE)

| CATSERV (SANDRA) | Exame | SENAITE Keyword | Object ID | Unidade | ObservaÃ§Ã£o |
|------------------|-------|-----------------|-----------|---------|------------|
| `03.02.005` | Glicemia | `GLI001` | `glicose` | mg/dL | Seed + ASTM testado |
| `01.01.001` | Hemograma | `HEM001` | `hemograma` | milhoes/mmÂ³ | Seed + ASTM testado |
| `02.03.010` | Urocultura | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `04.01.001` | Colesterol Total | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `04.01.002` | Colesterol HDL | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `04.02.001` | TriglicerÃ­deos | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `05.01.001` | Creatinina | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `05.02.001` | Ureia | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `06.01.001` | TGO/AST | *(pendente)* | â€” | â€” | NÃ£o implementado |
| `06.01.002` | TGP/ALT | *(pendente)* | â€” | â€” | NÃ£o implementado |
| â€” | Lipidograma | `LIP001` | `lipidograma` | mg/dL | Apenas ASTM (sem CATSERV) |

### Como Funciona a ConversÃ£o

O fluxo esperado em produÃ§Ã£o:

```
SANDRA envia: {"exames": [{"codigo_catserv": "03.02.005", ...}]}
     â”‚
     â–¼
Middleware consulta PostgreSQL (tabela_catserv):
     SELECT senaite_keyword FROM tabela_catserv WHERE codigo = '03.02.005'
     â†’ retorna 'GLI001'
     â”‚
     â–¼
Middleware busca AnalysisService no SENAITE:
     GET /@@API/senaite/v1/search?portal_type=AnalysisService&getKeyword=GLI001
     â†’ retorna UID do AnalysisService
     â”‚
     â–¼
Cria AR com UID do serviÃ§o:
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

> **âš ï¸ Status atual:** A conversÃ£o CATSERV â†’ Keyword **ainda nÃ£o estÃ¡ implementada** no middleware. O seed data usa Keywords diretamente (`GLI001`, `HEM001`) como se fossem cÃ³digos CATSERV. Para produÃ§Ã£o, implementar o lookup no PostgreSQL em `routers/ingestao.py` ou `clients/senaite_api.py`. 
> 
> **Contorno temporÃ¡rio:** Configurar o SANDRA para enviar as Keywords do SENAITE (`GLI001`, `HEM001`) diretamente no campo `codigo_catserv` atÃ© o mapeamento via PostgreSQL ser implementado.

---

## 2. ASTM E1394 â†’ AmostraProcessada (Parser)

### VisÃ£o Geral do Frame

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

### Record H â€” Header

```
{seq}H|\^&||||sender_id||||||||
```

| Campo Frame | Parser Index | Modelo | Exemplo | ObservaÃ§Ã£o |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `tipo_mensagem` | _(descartado)_ | | |
| `c[2]` | `delimitadores` | _(descartado)_ | `\^&` | |
| `c[4]` | `sender_id` | `machine_name` | `Mindray_BS200` | Nome do equipamento que enviou |
| demais | _(descartados)_ | | | |

### Record P â€” Patient

```
{seq}P|seq|patient_id|patient_name|mother_maiden|birth_date|sex|...
```

| Campo Frame | Parser Index | Modelo | Exemplo | ObservaÃ§Ã£o |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `sequence` | _(descartado)_ | `1` | |
| `c[2]` | `patient_id` | `AmostraProcessada.patient_id` | `MRN000001` | Field 3 ASTM |
| `c[3]` | `patient_name` | `AmostraProcessada.patient_name` | `SGT MENDES^JOAO` | Field 4 ASTM, formato `SOBRENOME^NOME` |
| `c[4]` | `mother_maiden` | _(descartado)_ | | Nome de solteira da mÃ£e |
| `c[5]` | `birth_date` | _(descartado)_ | `19800101` | Formato YYYYMMDD |
| `c[6]` | `sex` | _(descartado)_ | `M` | M/F |

### Record O â€” Order

```
{seq}O|seq|sample_id||universal_test_id|...
```

| Campo Frame | Parser Index | Modelo | Exemplo | ObservaÃ§Ã£o |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `sequence` | _(descartado)_ | `1` | |
| `c[2]` | `sample_id` | `AmostraProcessada.sample_id` | `HGU-AR-001` | CÃ³digo de barras da AR â€” **chave para o SENAITE** |
| `c[4]` | `universal_test_id` | _(descartado)_ | `^^^GLI001` | Formato `^^^codigo` |

### Record R â€” Result

```
{seq}R|seq|universal_test_id|valor|type|unidade|ref_range|flag|...
```

| Campo Frame | Parser Index | Modelo | Exemplo | ObservaÃ§Ã£o |
|-------------|-------------|--------|---------|------------|
| `c[1]` | `sequence` | _(descartado)_ | `1` | |
| `c[2].parts[-1]` | `keyword` | `ResultadoExameInstrumento.keyword` | `GLI001` | Ãšltima parte apÃ³s `^^^` |
| `c[3]` | `valor` | `ResultadoExameInstrumento.valor` | `105.5` | String, sem formataÃ§Ã£o |
| `c[4]` | `type` | _(descartado)_ | `N` | N=Normal, C=Control, etc. |
| `c[5]` | `unidade` | `ResultadoExameInstrumento.unidade` | `mg/dL` | |
| `c[6]` | `ref_range` | _(descartado)_ | | Intervalo de referÃªncia |
| `c[7]` | `flag` | `ResultadoExameInstrumento.flag_anormalidade` | `H` | H=High, L=Low, HH=Critical, LL=Critical Low |
| demais | â€” | _(descartados)_ | | |

### Record C â€” Comment

```
{seq}C|texto|...
```

| Campo Frame | Parser Index | Modelo | Exemplo |
|-------------|-------------|--------|---------|
| `c[1]` | `texto` | _(descartado)_ | `Amostra hemolisada` |

### Record L â€” Terminator

```
{seq}L|seq|termination_code
```

**Apenas o registro `L` dispara a extraÃ§Ã£o da amostra.** Ao encontrar `L`, o parser consolida os dados em `AmostraProcessada`.

### Modelos Finais

```python
class ResultadoExameInstrumento(BaseModel):
    keyword: str           # ex: "GLI001"
    valor: str             # ex: "105.5"
    unidade: Optional[str] # ex: "mg/dL"
    flag_anormalidade: Optional[str]  # "H" | "L" | "HH" | None

class AmostraProcessada(BaseModel):
    sample_id: str         # cÃ³digo de barras, ex: "HGU-AR-001"
    machine_name: str      # nome do equipamento
    patient_id: Optional[str]
    patient_name: Optional[str]
    resultados: List[ResultadoExameInstrumento]
```

### Exemplo Completo de Parse

**Frame ASTM:```
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

## 3. Portas TCP â†’ Equipamentos

### Mapeamento (configurado em `instruments/config.py`)

Cada analisador deve ser configurado para enviar resultados ASTM para o IP do middleware na porta designada:

| Porta | Nome Interno | Equipamento Real | Especialidade | Protocolo |
|-------|-------------|-------------------|---------------|-----------|
| **5001** | `Mindray_BS200` | Mindray BS-200 | BioquÃ­mica | ASTM E1381/E1394 |
| **5002** | `Sysmex_XN550` | Sysmex XN-550 | Hematologia | ASTM E1381/E1394 |
| **5003** | `Roche_Cobas_e411` | Roche Cobas e411 | ImunoquÃ­mica | ASTM E1381/E1394 |
| **5004** | `Roche_Cobas_c311` | Roche Cobas c311 | QuÃ­mica ClÃ­nica | ASTM E1381/E1394 |
| **5005** | `BioRad_D10` | Bio-Rad D-10 | HbA1c | ASTM E1381/E1394 |

### Topologia de Rede (Middleware Gateway)

```
â”Œâ”€ Rede LaboratÃ³rio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                                                                  â”‚
â”‚   Analisadores                             Middleware (porta 8000)â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     TCP/IP:5001          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚   â”‚ Mindray BS200 â”‚â”€â”€â”€â”€ ENQ/ACK/STX/EOT â”€â”€â”€â–ºâ”‚                 â”‚  â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚  listener.py    â”‚  â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     TCP/IP:5002          â”‚  (daemon TCP    â”‚  â”‚
â”‚   â”‚ Sysmex XN550 â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚   assÃ­ncrono)   â”‚  â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚                 â”‚  â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     TCP/IP:5003          â”‚  â”€â”€ parseia     â”‚  â”‚
â”‚   â”‚ Cobas e411   â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  â”€â”€ audita      â”‚  â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚  â”€â”€ envia       â”‚  â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     TCP/IP:5004          â”‚       para      â”‚  â”‚
â”‚   â”‚ Cobas c311   â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚    SENAITE      â”‚  â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     TCP/IP:5005                   â”‚           â”‚
â”‚   â”‚ BioRad D10   â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º         â”‚           â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                                   â”‚           â”‚
â”‚                                                       â–¼           â”‚
â”‚                                            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                            â”‚  SENAITE LIMS   â”‚  â”‚
â”‚                                            â”‚   port 8083     â”‚  â”‚
â”‚                                            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                                                                  â”‚
â”‚   Gateway (porta 8000)                                           â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚   â”‚ POST /api/v1/sandra/ingestao  â† SANDRA (prontuÃ¡rio)       â”‚ â”‚
â”‚   â”‚ POST /api/v1/senaite/webhook/... â† SENAITE (laudo pub.)   â”‚ â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### ConfiguraÃ§Ã£o no Analisador

Cada equipamento deve ser configurado (via software do fabricante) com:

| ParÃ¢metro | Valor |
|-----------|-------|
| **IP destino** | IP do servidor middleware (`192.168.x.x` â€” conforme rede do laboratÃ³rio) |
| **Porta** | Conforme tabela acima (5001â€“5005) |
| **Protocolo** | ASTM E1381 (enquadramento) / E1394 (registros) |
| **Handshake** | Hardware (ENQ/ACK) |
| **Encoding** | ASCII |
| **Checksum** | XOR (2 hex chars ao final do frame) |
| **Terminador** | CR ou CRLF |

> **InstruÃ§Ã£o para engenharia clÃ­nica:** Ao conectar um novo analisador, cadastre a porta em `instruments/config.py` (dicionÃ¡rio `INSTRUMENTOS`), adicione a porta ao parÃ¢metro `--portas=` no `compose.local.yaml`, e configure o equipamento com o IP do middleware e a porta designada.

### Handshake (E1381)

| Byte | SÃ­mbolo | Quem Envia | Significado |
|------|---------|-----------|-------------|
| `0x05` | ENQ | Analisador | "Quer enviar dados" |
| `0x06` | ACK | Middleware | "Pronto para receber" |
| `0x02...0x03 + cks` | STX+ETX+chk | Analisador | Payload com checksum |
| `0x06` / `0x15` | ACK/NAK | Middleware | "Frame OK / Corrompido" |
| `0x04` | EOT | Analisador | "Fim da transmissÃ£o" |
| `0x06` | ACK | Middleware | "TransmissÃ£o recebida" |

---

## 4. Gateway API â€” De/Para Completo

### 4.1 `POST /api/v1/sandra/ingestao`

> Entrada: SANDRA â†’ Middleware. SaÃ­da: CADBEN + SIRE + SENAITE.

#### De/Para Campos

| Campo Input (SANDRA) | Tipo | ValidaÃ§Ã£o | Para Onde Vai | Campo Destino |
|---------------------|------|-----------|---------------|---------------|
| `id_pedido` | `str` | obrigatÃ³rio | SIRE (GET `/api/v1/guias/{id_pedido}`) | path param |
| `cpf_paciente` | `str` | regex `^\d{11}$` | CADBEN (GET `/api/v1/beneficiarios/{cpf}/elegibilidade`) | path param |
| `nome_paciente` | `str` | obrigatÃ³rio | _(log apenas)_ | â€” |
| `medico_solicitante` | `str` | obrigatÃ³rio | SENAITE (`create_analysis_request`) | `doctor_name` |
| `crm_solicitante` | `str` | obrigatÃ³rio | SENAITE (`create_analysis_request`) | `doctor_crm` |
| `data_solicitacao` | `datetime` | ISO 8601 | _(log apenas)_ | â€” |
| `exames[].codigo_catserv` | `str` | obrigatÃ³rio | SENAITE (`create_analysis_request`) | `services[]` |
| `exames[].descricao` | `str` | â€” | _(log apenas)_ | â€” |
| `exames[].urgente` | `bool` | default `false` | _(log apenas)_ | â€” |

#### Fluxo de ValidaÃ§Ã£o Interna

```
OrdemServicoSANDRA
  â”œâ”€â”€ CADBEN.validar_elegibilidade(cpf)       â†’  elegivel? (mock: sempre True)
  â”œâ”€â”€ SIRE.validar_guia(id_pedido)            â†’  autorizada? (mock: sempre True)
  â””â”€â”€ SENAITE.create_analysis_request(
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

> Entrada: SENAITE â†’ Middleware (via Event Subscriber ZCML). SaÃ­da: SANDRA.

#### Payload de Entrada (enviado pelo SENAITE)

| Campo | Tipo | ObrigatÃ³rio | DescriÃ§Ã£o |
|-------|------|-------------|-----------|
| `analysis_request_id` | `str` | sim | ID da AR publicada (ex: `HGU-AR-001`) |
| `client_id` | `str` | sim | Identificador do cliente (ex: `hgu`) |
| `patient_name` | `str?` | nÃ£o | Nome do paciente |
| `pdf_url` | `str?` | nÃ£o | URL do PDF (nÃ£o usado â€” middleware baixa direto) |
| `review_state` | `str` | sim | **Deve ser `"published"`** |
| `results` | `list[dict]?` | nÃ£o | Resultados dos exames |

#### CritÃ©rio de Filtro

```python
if payload.review_state != "published":
    â†’ {"status": "ignorado", "motivo": "Apenas laudos publicados sÃ£o processados"}
```

#### AÃ§Ãµes Disparadas

```
WebhookLaudoPayload
  â”‚
  â”œâ”€â”€ SENAITE.get_ar_pdf(ar_id)
  â”‚     GET /clients/hgu/{analysis_request_id}/@@cdm-pdf
  â”‚     â†’ bytes do PDF
  â”‚
  â””â”€â”€ SANDRA.notificar_sandra(ar_id, pdf_base64)
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

> Endpoint custom do add-on Zope. Bypassa a restriÃ§Ã£o do `@@API/create` que bloqueia AnalysisRequest.

| Aspecto | Detalhe |
|---------|---------|
| URL | `http://app:8080/senaite/@@hgumba-create-ar` |
| MÃ©todo | `POST` |
| Content-Type | `application/json` |
| AutenticaÃ§Ã£o | Basic Auth (mesmo admin:admin) |

#### Payload de Entrada

| Campo | Tipo | ObrigatÃ³rio | DescriÃ§Ã£o |
|-------|------|-------------|-----------|
| `client_id` | `str` | nÃ£o (default `"hgu"`) | Client onde criar a AR |
| `services` | `list[str]` | **sim** | Keywords dos AnalysisServices (ex: `["GLI001"]`) |
| `contact_id` | `str?` | nÃ£o | ID do Contact (mÃ©dico solicitante) |
| `patient_name` | `str?` | nÃ£o | Nome completo do paciente |
| `mrn` | `str?` | nÃ£o | Medical Record Number (ou CPF) |
| `ar_id` | `str?` | nÃ£o | ID desejado para a AR (ex: `HGU-AR-001`) |
| `title` | `str?` | nÃ£o | TÃ­tulo da AR (fallback: `ar_id` ou services[0]) |

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

1. LÃª o JSON body
2. Busca o Client por `client_id`
3. Percorre `bika_setup.bika_analysisservices` procurando cada `Keyword` correspondente â†’ extrai UID
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

### Sentido: Analisador â†’ SENAITE

```
Analisador (TCP:5001)
  â”‚ ASTM Frame (STX/ETX/checksum)
  â–¼
listener.py :: AnalisadorTCP.alimentar()
  â”‚ handshake ACK/NAK, valida checksum
  â–¼
astm.py :: ASTM1394Parser.alimentar()
  â”‚ decodifica registros H,P,O,R,L
  â–¼
AmostraProcessada (modelo)
  â”œâ”€â”€ sample_id    â† O[2]
  â”œâ”€â”€ machine_name â† do config (porta â†’ nome)
  â”œâ”€â”€ patient_id   â† P[2]   â”€â”€â”€â”€â”€â”€â†’ DESCARTADO no envio
  â”œâ”€â”€ patient_name â† P[3]   â”€â”€â”€â”€â”€â”€â†’ DESCARTADO
  â””â”€â”€ resultados[]
       â”œâ”€â”€ keyword  â† R[2] Ãºltimo elemento apÃ³s ^^^
       â”œâ”€â”€ valor    â† R[3]        â”€â”€â†’ SENAITE Result
       â”œâ”€â”€ unidade  â† R[5]        â”€â”€â†’ DESCARTADO
       â””â”€â”€ flag     â† R[7]        â”€â”€â†’ DESCARTADO
  â–¼
listener.py :: _enviar_para_senaite()
  â”‚ Envia para SENAITE apenas: (sample_id, keyword, valor)
  â–¼
senaite_api.py :: set_analysis_result()
  â”‚ GET /@@API/senaite/v1/search?portal_type=Analysis&getKeyword={keyword}&parent_path=/senaite/clients/hgu/{sample_id}
  â”‚ â†’ extrai uid do primeiro resultado
  â”‚ POST /@@API/senaite/v1/update?uid={uid}&Result={valor}
  â–¼
SENAITE â€” Analysis.Result atualizado
```

### Sentido: SANDRA â†’ SENAITE (via Gateway)

```
SANDRA (POST /api/v1/sandra/ingestao)
  â”‚ JSON body: OrdemServicoSANDRA
  â–¼
validar_elegibilidade(CADBEN) â†’ True/False
validar_guia(SIRE)             â†’ True/False
  â–¼
SENAITE.create_analysis_request()
  â”‚ POST /@@hgumba-create-ar
  â”‚   client_id     = "hgu"
  â”‚   services      = [codigos catserv...]
  â”‚   patient_name  = ordem.nome_paciente
  â”‚   mrn           = ordem.cpf_paciente
  â”‚   contact_id    = "contact-1"
  â”‚   ar_id         = ordem.id_pedido
  â”‚
  â”‚ (BrowserView custom â€” bypass do @@API/create)
  â”‚   â†’ invokeFactory + setField + commit
  â–¼
SENAITE â€” AnalysisRequest criada em estado "sample_registered"
```

### Sentido: SENAITE â†’ SANDRA (via Webhook)

```
SENAITE (Event Subscriber â€” IAfterTransitionEvent, state="published")
  â”‚ POST async via urllib2 para:
  â–¼
POST /api/v1/senaite/webhook/laudo_publicado
  â”‚ JSON body: WebhookLaudoPayload
  â”‚ review_state == "published" ?
  â–¼
get_ar_pdf(ar_id)
  â”‚ GET /clients/hgu/{ar_id}/@@cdm-pdf
  â”‚ â†’ PDF bytes â†’ base64
  â–¼
notificar_sandra(ar_id, pdf_base64)
  â”‚ POST /api/v1/resultados (SANDRA)
  â–¼
SANDRA â€” laudo registrado no prontuÃ¡rio
```

---

## 6. Mocks e Dados de Teste

### APIs ExÃ©rcito (modo DEV)

Quando as variÃ¡veis de ambiente `SANDRA_BASE_URL`, `CADBEN_BASE_URL` e `SIRE_BASE_URL` **estÃ£o vazias**, o client retorna respostas mock:

| API | Resposta Mock |
|-----|--------------|
| CADBEN | `{"cpf": "...", "elegivel": true, "beneficiario": {"nome": "Paciente DEV", "posto_graduacao": "Sd DEV", "organizacao_militar": "HGUMBA", "ativo": true}}` |
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
| `HGU-AR-002` | `HEM001` | `5.2` | `milhoes/mm3` | â€” | `CB MOURA^MARIA` |
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

O middleware registra todos os eventos crÃ­ticos do pipeline em formato JSON estruturado via `audit_logger`. Este log Ã© a principal ferramenta de troubleshooting para rastrear resultados rejeitados ou fluxos interrompidos.

### 7.1 Como Visualizar os Logs de Auditoria

```bash
# Gateway (FastAPI)
docker logs -f middleware_gateway 2>&1 | findstr "HGUMBA-Audit"

# Daemon de Instrumentos (TCP)
docker logs -f middleware_instruments 2>&1 | findstr "HGUMBA-Audit"

# Ambos â€” formataÃ§Ã£o JSON legÃ­vel
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

### 7.3 CatÃ¡logo de Eventos

| Evento | Message | Onde Ã© Gerado | Causa Comum |
|--------|---------|---------------|-------------|
| `gateway_iniciado` | "Gateway iniciado" | `main.py` startup | ServiÃ§o subiu |
| `gateway_finalizado` | "Gateway finalizado" | `main.py` shutdown | ServiÃ§o parou |
| `daemon_iniciado` | "Daemon de instrumentos iniciado" | `runner.py` | Daemon TCP subiu |
| `daemon_finalizado` | "Daemon de instrumentos finalizado" | `runner.py` | Daemon TCP parou |
| `resultado_importado` | "Resultado injetado no SENAITE" | `listener.py` | âœ… Sucesso â€” resultado enviado ao SENAITE |
| `resultado_falha` | "Falha ao injetar resultado" | `listener.py` | âŒ AR nÃ£o encontrada, keyword invÃ¡lida, SENAITE offline |
| `pedido_injetado` | "Pedido SANDRA injetado no SENAITE" | `ingestao.py` | âœ… Sucesso â€” AR criada via ingestÃ£o |
| `webhook_pdf_falha` | "Falha ao obter PDF do laudo" | `webhooks.py` | âŒ AR nÃ£o encontrada, SENAITE offline, PDF nÃ£o gerado |
| `laudo_publicado` | "Laudo publicado processado" | `webhooks.py` | Webhook recebido e encaminhado ao SANDRA |

### 7.4 Fluxo de Troubleshooting para Resultado Rejeitado

Quando um resultado nÃ£o aparece no SENAITE, siga estes passos:

```
Passo 1: Verificar se o frame chegou ao daemon
â””â”€ docker logs middleware_instruments 2>&1 | findstr "HGUMBA-Audit" | findstr "HGU-AR-001"
   â”œâ”€ Se encontrar "resultado_importado" â†’ o parse funcionou, o SENAITE recebeu
   â”œâ”€ Se encontrar "resultado_falha" â†’ o parse funcionou mas o envio falhou
   â”‚    â””â”€ Ver o campo "erro" no audit_data:
   â”‚       â”œâ”€ "Analysis not found" â†’ Keyword nÃ£o existe no SENAITE
   â”‚       â”œâ”€ "404" â†’ AR nÃ£o encontrada (sample_id errado?)
   â”‚       â””â”€ "Connection refused" â†’ SENAITE offline
   â””â”€ Se NÃƒO encontrar â†’ o frame nÃ£o chegou ou foi rejeitado no handshake
        â””â”€ Verificar logs do analisador + conectividade TCP

Passo 2: Se hÃ¡ "resultado_falha", checar o campo audit_data.erro

Passo 3: Verificar se a AR existe no SENAITE
â””â”€ curl -u admin:admin "http://localhost:8083/senaite/@@API/senaite/v1/search?portal_type=AnalysisRequest&getId=HGU-AR-001"

Passo 4: Verificar se o AnalysisService existe
â””â”€ curl -u admin:admin "http://localhost:8083/senaite/@@API/senaite/v1/search?portal_type=AnalysisService&getKeyword=GLI001"
```

### 7.5 Exemplos de JSON Reais e sua InterpretaÃ§Ã£o

#### Caso 1: Sucesso â€” resultado importado
```json
{"timestamp":"2026-05-19T14:30:00Z","level":"INFO","message":"Resultado injetado no SENAITE","audit_data":{"evento":"resultado_importado","sample_id":"HGU-AR-001","keyword":"GLI001","valor":"105.5","maquina":"Mindray_BS200"}}
```
> **InterpretaÃ§Ã£o:** A mÃ¡quina Mindray BS200 enviou glicemia 105.5 mg/dL para AR HGU-AR-001. O SENAITE aceitou e o remark de auditoria foi registrado.

#### Caso 2: Falha â€” AR nÃ£o encontrada
```json
{"timestamp":"2026-05-19T14:31:00Z","level":"ERROR","message":"Falha ao injetar resultado","audit_data":{"evento":"resultado_falha","sample_id":"HGU-AR-999","keyword":"GLI001","erro":"Analysis not found","maquina":"Mindray_BS200"}}
```
> **InterpretaÃ§Ã£o:** A AR `HGU-AR-999` nÃ£o existe no SENAITE. Verificar se o cÃ³digo de barras lido pelo analisador corresponde ao ID da AR.

#### Caso 3: Falha â€” SENAITE offline
```json
{"timestamp":"2026-05-19T14:32:00Z","level":"ERROR","message":"Falha ao injetar resultado","audit_data":{"evento":"resultado_falha","sample_id":"HGU-AR-001","keyword":"GLI001","erro":"ConnectError: Connection refused","maquina":"Sysmex_XN550"}}
```
> **InterpretaÃ§Ã£o:** O SENAITE nÃ£o estÃ¡ respondendo. Verificar `docker ps` e logs do container SENAITE.

#### Caso 4: IngestÃ£o de pedido SANDRA
```json
{"timestamp":"2026-05-19T14:33:00Z","level":"INFO","message":"Pedido SANDRA injetado no SENAITE","audit_data":{"evento":"pedido_injetado","id_pedido":"PED-001","cpf_paciente":"12345678901","exames":["GLI001"],"via":"sandra_ingestao"}}
```
> **InterpretaÃ§Ã£o:** Pedido PED-001 do SANDRA foi recebido e a AR foi criada no SENAITE com exame GLI001.

#### Caso 5: Webhook de laudo publicado
```json
{"timestamp":"2026-05-19T14:34:00Z","level":"INFO","message":"Laudo publicado processado","audit_data":{"evento":"laudo_publicado","analysis_request_id":"HGU-AR-001","sandra_notificado":true,"via":"webhook"}}
```
> **InterpretaÃ§Ã£o:** A AR HGU-AR-001 foi publicada no SENAITE, o PDF foi obtido e enviado ao SANDRA com sucesso.

### 7.6 Comandos Ãšteis para Troubleshooting RÃ¡pido

```bash
# Ãšltimos 10 eventos de auditoria
docker logs middleware_gateway 2>&1 | findstr "HGUMBA-Audit" | findstr /v "daemon" | python -c "import sys; [print(l) for l in sys.stdin.readlines()[-10:]]"

# Todas as falhas de resultado
docker logs middleware_instruments 2>&1 | findstr "HGUMBA-Audit" | findstr "resultado_falha"

# Filtrar por uma AR especÃ­fica
docker logs middleware_instruments 2>&1 | findstr "HGU-AR-001"

# Verificar se o remark de auditoria foi registrado na AR
curl -u admin:admin "http://localhost:8083/senaite/clients/hgu/HGU-AR-001/@@hgumba-debug" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('Remarks',''))"

# Acompanhar em tempo real eventos de erro
docker logs -f middleware_gateway 2>&1 | findstr "ERROR.*HGUMBA"
```

---

## Anexo: DerivaÃ§Ã£o dos Keywords

Os cÃ³digos de 3 letras + 3 dÃ­gitos (`GLI001`, `HEM001`, `LIP001`) sÃ£o **internos do SENAITE** (definidos como `Keyword` no AnalysisService). Eles sÃ£o usados como:

| Sistema | Como Usa |
|---------|----------|
| **ASTM** (R[2]) | CÃ³digo do exame no equipamento (`^^^GLI001`) |
| **SENAITE** | `getKeyword` do AnalysisService, identifica qual anÃ¡lise recebe o resultado |
| **CATSERV** | _(ainda nÃ£o mapeado)_ â€” a coluna `codigo` (`01.01.001` etc.) Ã© o cÃ³digo oficial do ExÃ©rcito |

Para produÃ§Ã£o, cada linha da `tabela_catserv` deve ter seu `codigo` mapeado para a `Keyword` SENAITE correspondente.

---

*Documento gerado em 2026-05-19 | v2.0.0*
