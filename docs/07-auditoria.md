> **Origem:** `SENAITE/hgumba-middleware/docs/auditoria_rdc978.md`

# POP: Rastreabilidade de Dados Laboratoriais (RDC 978/2025)

> Procedimento Operacional Padrão para garantir a integridade e rastreabilidade
> dos resultados laboratoriais no SENAITE LIS — H Gu Marabá.

---

## 1. Objetivo

Descrever os mecanismos de rastreabilidade implementados no sistema para atender
aos requisitos da **RDC 978/2025** (Boas Práticas em Laboratórios Clínicos),
garantindo que toda alteração em resultado de exame — seja manual ou automatizada —
seja registrada com identificação do responsável, origem do dado e timestamp.

---

## 2. Abrangência

Este POP cobre todos os pontos de entrada de dados no SENAITE LIS:

| Via | Descrição | Responsável pelo Registro |
|-----|-----------|--------------------------|
| **Interface Web** | Analistas inserindo/alterando resultados via UI | Zope/Plone History nativo |
| **Daemon TCP (ASTM)** | Analisadores enviando resultados via middleware | Middleware + API Remark |
| **Gateway API** | Ingestão de pedidos via SANDRA | Middleware + Zope History |
| **Webhook** | Devolução de laudos publicados ao SANDRA | Middleware |

---

## 3. Mecanismos de Rastreabilidade

### 3.1 Rastreabilidade Nativa do Zope

Toda ação humana via interface web é capturada automaticamente pelo **Zope History**
(aba *History* de cada objeto). Para cada Analysis e AnalysisRequest, são registrados:

- Usuário (login Zope)
- Data/Hora
- Ação executada (criação, edição, transição de workflow)
- Estado anterior e novo (workflow)

**Verificação:** Abrir AR → aba *History* → listagem cronológica com usuário e timestamp.

### 3.2 Rastreabilidade de Resultados Automatizados (ASTM)

Quando o Daemon TCP injeta um resultado de analisador, o campo `Remark` da Analysis
recebe um carimbo de auditoria no formato:

```
[AUDITORIA] Resultado importado automaticamente via ASTM E1394.
Fonte: Mindray_BS200. AR: HGU-AR-001.
```

**Verificação:** SENAITE → Analysis → campo *Remarks* (visível na UI ou via API).
Isso permite ao auditor identificar **qual equipamento** gerou o dado e **por qual via**
ele chegou ao sistema.

### 3.3 Logs Estruturados do Middleware (JSON Audit Trail)

O middleware gera logs em formato JSON para todos os eventos críticos.
Cada linha é um JSON válido, filtrável por `grep` ou ferramentas de SIEM.

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
# Filtrar logs de uma amostra específica
docker logs middleware_instruments 2>&1 | grep "HGU-AR-001"

# Filtrar logs JSON de um equipamento
docker logs middleware_instruments 2>&1 | python -c "import sys,json; [print(json.dumps(json.loads(l),indent=2)) for l in sys.stdin if 'Mindray_BS200' in l]"

# Contar resultados injetados por equipamento
docker logs middleware_instruments 2>&1 | grep "resultado_importado" | python -c "import sys,json; c={}; [exec('c.update({d[\"audit_data\"][\"maquina\"]: c.get(d[\"audit_data\"][\"maquina\"],0)+1})') for l in sys.stdin if (d:=json.loads(l))]; print(c)"

# Acompanhar em tempo real
docker logs -f middleware_instruments 2>&1 | grep --line-buffered "HGUMBA-Audit"
```

### 3.4 Rastreabilidade de Pedidos (SANDRA → SENAITE)

Quando um pedido chega via SANDRA, o middleware:

1. Valida elegibilidade no CADBEN (mock)
2. Valida autorização no SIRE (mock)
3. Cria a AR via `@@hgumba-create-ar` com `MedicalRecordNumber` = CPF do paciente
4. Registra no log JSON de auditoria com `evento: pedido_injetado`

Na aba *History* da AR no SENAITE, constará o usuário `admin` (conta de serviço)
e o momento da criação.

---

## 4. Mapa de Auditoria (De/Para)

| Onde Olhar | O Que Encontrar | RDC 978/2025 |
|-----------|----------------|--------------|
| AR → aba *History* | Quem criou, quando, transições de workflow | Art. 12 — Rastreabilidade de Ações |
| Analysis → *Remarks* | Carimbo `[AUDITORIA] Fonte: {equipamento}` | Art. 13 — Identificação da Origem |
| `docker logs middleware_instruments` | JSON com `audit_data` completo | Art. 14 — Logs Estruturados |
| `docker logs middleware_gateway` | JSON com `evento: pedido_injetado` | Art. 14 — Logs Estruturados |
| CDM PDF (`@@cdm-pdf`) | Usuário e data no rodapé do documento | Art. 15 — Integridade do Documento |

---

## 5. Tratamento de Exceções

### 5.1 Falha na Injeção de Resultado (ASTM)

Se o Daemon TCP não conseguir injetar o resultado no SENAITE (ex: AR não encontrada,
SENAITE offline), o evento `resultado_falha` é registrado no log JSON e o frame ASTM
é rejeitado com NAK, fazendo o analisador reenviar.

### 5.2 Falha no Webhook (SENAITE → SANDRA)

Se o middleware não conseguir notificar o SANDRA sobre um laudo publicado,
o evento `laudo_publicado` é registrado com `sandra_notificado: false` e o
log textual contém o stack trace do erro. O laudo permanece no SENAITE em
estado `published` — a notificação pode ser reenviada manualmente.

### 5.3 Falha na Criação de AR (SANDRA Ingestão)

Se a criação da AR falhar (ex: serviço inexistente, cliente inválido), o erro
é registrado no log JSON com `evento: pedido_injetado` e nível `ERROR`.
O pedido SANDRA original permanece no log do middleware para depuração.

---

## 6. Responsabilidades

| Papel | Responsabilidade |
|-------|-----------------|
| **Analista Clínico** | Verificar Remarks das Análises automatizadas antes de assinar |
| **Administrador do SENAITE** | Monitorar logs de auditoria semanalmente |
| **Equipe de TI** | Garantir sincronismo do NTP em todos os containers |
| **Auditor** | Solicitar logs JSON do middleware + aba History do SENAITE |

---

## 7. Referências

- **RDC 978/2025** — Boas Práticas em Laboratórios Clínicos (ANVISA)
- **ASTM E1381** — Especificação para Transferência de Dados Clínicos
- **ASTM E1394** — Protocolo de Mensagens para Analisadores
- **Manual SENAITE** — Rastreabilidade e Aba History

---

**Versão:** 1.0.0 | **Data:** 2026-05-19 | **Elaborado por:** GTI/H Gu Marabá
