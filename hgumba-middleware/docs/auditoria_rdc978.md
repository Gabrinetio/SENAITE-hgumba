# POP: Rastreabilidade de Dados Laboratoriais (RDC 978/2025)

> Procedimento Operacional PadrÃ£o para garantir a integridade e rastreabilidade
> dos resultados laboratoriais no SENAITE LIS â€” HGUMBA

---

## 1. Objetivo

Descrever os mecanismos de rastreabilidade implementados no sistema para atender
aos requisitos da **RDC 978/2025** (Boas PrÃ¡ticas em LaboratÃ³rios ClÃ­nicos),
garantindo que toda alteraÃ§Ã£o em resultado de exame â€” seja manual ou automatizada â€”
seja registrada com identificaÃ§Ã£o do responsÃ¡vel, origem do dado e timestamp.

---

## 2. AbrangÃªncia

Este POP cobre todos os pontos de entrada de dados no SENAITE LIS:

| Via | DescriÃ§Ã£o | ResponsÃ¡vel pelo Registro |
|-----|-----------|--------------------------|
| **Interface Web** | Analistas inserindo/alterando resultados via UI | Zope/Plone History nativo |
| **Daemon TCP (ASTM)** | Analisadores enviando resultados via middleware | Middleware + API Remark |
| **Gateway API** | IngestÃ£o de pedidos via SANDRA | Middleware + Zope History |
| **Webhook** | DevoluÃ§Ã£o de laudos publicados ao SANDRA | Middleware |

---

## 3. Mecanismos de Rastreabilidade

### 3.1 Rastreabilidade Nativa do Zope

Toda aÃ§Ã£o humana via interface web Ã© capturada automaticamente pelo **Zope History**
(aba *History* de cada objeto). Para cada Analysis e AnalysisRequest, sÃ£o registrados:

- UsuÃ¡rio (login Zope)
- Data/Hora
- AÃ§Ã£o executada (criaÃ§Ã£o, ediÃ§Ã£o, transiÃ§Ã£o de workflow)
- Estado anterior e novo (workflow)

**VerificaÃ§Ã£o:** Abrir AR â†’ aba *History* â†’ listagem cronolÃ³gica com usuÃ¡rio e timestamp.

### 3.2 Rastreabilidade de Resultados Automatizados (ASTM)

Quando o Daemon TCP injeta um resultado de analisador, o campo `Remark` da Analysis
recebe um carimbo de auditoria no formato:

```
[AUDITORIA] Resultado importado automaticamente via ASTM E1394.
Fonte: Mindray_BS200. AR: HGU-AR-001.
```

**VerificaÃ§Ã£o:** SENAITE â†’ Analysis â†’ campo *Remarks* (visÃ­vel na UI ou via API).
Isso permite ao auditor identificar **qual equipamento** gerou o dado e **por qual via**
ele chegou ao sistema.

### 3.3 Logs Estruturados do Middleware (JSON Audit Trail)

O middleware gera logs em formato JSON para todos os eventos crÃ­ticos.
Cada linha Ã© um JSON vÃ¡lido, filtrÃ¡vel por `grep` ou ferramentas de SIEM.

#### Eventos Registrados

| Evento | Componente | Dados Inclusos |
|--------|-----------|----------------|
| `resultado_importado` | listener | sample_id, keyword, valor, unidade, flag, maquina, via |
| `resultado_falha` | listener | sample_id, keyword, erro, maquina |
| `laudo_publicado` | webhook | analysis_request_id, sandra_notificado, via |
| `pedido_injetado` | ingestao | id_pedido, cpf_paciente, exames, via |
| `daemon_start`/`daemon_stop` | runner | listeners, portas |

#### Exemplo de Log

```json
{
  "timestamp": "2026-05-19T12:30:00Z",
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

#### Comandos de Auditoria

```bash
# Filtrar logs de uma amostra especÃ­fica
docker logs middleware_instruments 2>&1 | grep "HGU-AR-001"

# Filtrar logs JSON de um equipamento
docker logs middleware_instruments 2>&1 | python -c "import sys,json; [print(json.dumps(json.loads(l),indent=2)) for l in sys.stdin if 'Mindray_BS200' in l]"

# Contar resultados injetados por equipamento
docker logs middleware_instruments 2>&1 | grep "resultado_importado" | python -c "import sys,json; c={}; [exec('c.update({d[\"audit_data\"][\"maquina\"]: c.get(d[\"audit_data\"][\"maquina\"],0)+1})') for l in sys.stdin if (d:=json.loads(l))]; print(c)"

# Acompanhar em tempo real
docker logs -f middleware_instruments 2>&1 | grep --line-buffered "HGUMBA-Audit"
```

### 3.4 Rastreabilidade de Pedidos (SANDRA â†’ SENAITE)

Quando um pedido chega via SANDRA, o middleware:

1. Valida elegibilidade no CADBEN (mock)
2. Valida autorizaÃ§Ã£o no SIRE (mock)
3. Cria a AR via `@@hgumba-create-ar` com `MedicalRecordNumber` = CPF do paciente
4. Registra no log JSON de auditoria com `evento: pedido_injetado`

Na aba *History* da AR no SENAITE, constarÃ¡ o usuÃ¡rio `admin` (conta de serviÃ§o)
e o momento da criaÃ§Ã£o.

---

## 4. Mapa de Auditoria (De/Para)

| Onde Olhar | O Que Encontrar | RDC 978/2025 |
|-----------|----------------|--------------|
| AR â†’ aba *History* | Quem criou, quando, transiÃ§Ãµes de workflow | Art. 12 â€” Rastreabilidade de AÃ§Ãµes |
| Analysis â†’ *Remarks* | Carimbo `[AUDITORIA] Fonte: {equipamento}` | Art. 13 â€” IdentificaÃ§Ã£o da Origem |
| `docker logs middleware_instruments` | JSON com `audit_data` completo | Art. 14 â€” Logs Estruturados |
| `docker logs middleware_gateway` | JSON com `evento: pedido_injetado` | Art. 14 â€” Logs Estruturados |
| CDM PDF (`@@cdm-pdf`) | UsuÃ¡rio e data no rodapÃ© do documento | Art. 15 â€” Integridade do Documento |

---

## 5. Tratamento de ExceÃ§Ãµes

### 5.1 Falha na InjeÃ§Ã£o de Resultado (ASTM)

Se o Daemon TCP nÃ£o conseguir injetar o resultado no SENAITE (ex: AR nÃ£o encontrada,
SENAITE offline), o evento `resultado_falha` Ã© registrado no log JSON e o frame ASTM
Ã© rejeitado com NAK, fazendo o analisador reenviar.

### 5.2 Falha no Webhook (SENAITE â†’ SANDRA)

Se o middleware nÃ£o conseguir notificar o SANDRA sobre um laudo publicado,
o evento `laudo_publicado` Ã© registrado com `sandra_notificado: false` e o
log textual contÃ©m o stack trace do erro. O laudo permanece no SENAITE em
estado `published` â€” a notificaÃ§Ã£o pode ser reenviada manualmente.

### 5.3 Falha na CriaÃ§Ã£o de AR (SANDRA IngestÃ£o)

Se a criaÃ§Ã£o da AR falhar (ex: serviÃ§o inexistente, cliente invÃ¡lido), o erro
Ã© registrado no log JSON com `evento: pedido_injetado` e nÃ­vel `ERROR`.
O pedido SANDRA original permanece no log do middleware para depuraÃ§Ã£o.

---

## 6. Responsabilidades

| Papel | Responsabilidade |
|-------|-----------------|
| **Analista ClÃ­nico** | Verificar Remarks das AnÃ¡lises automatizadas antes de assinar |
| **Administrador do SENAITE** | Monitorar logs de auditoria semanalmente |
| **Equipe de TI** | Garantir sincronismo do NTP em todos os containers |
| **Auditor** | Solicitar logs JSON do middleware + aba History do SENAITE |

---

## 7. ReferÃªncias

- **RDC 978/2025** â€” Boas PrÃ¡ticas em LaboratÃ³rios ClÃ­nicos (ANVISA)
- **ASTM E1381** â€” EspecificaÃ§Ã£o para TransferÃªncia de Dados ClÃ­nicos
- **ASTM E1394** â€” Protocolo de Mensagens para Analisadores
- **Manual SENAITE** â€” Rastreabilidade e Aba History

---

**VersÃ£o:** 1.0.0 | **Data:** 2026-05-19 | **Elaborado por:** GTI/HGUMBA
