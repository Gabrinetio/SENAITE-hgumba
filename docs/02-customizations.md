> **Origem:** `SENAITE/customizations/spec-customizations.md`

# SENAITE HGU - Especificação Técnica de Customizações

## Sumário
1. [Arquitetura do Add-on](#1-arquitetura-do-add-on)
2. [Multiplus Profissionais Solicitantes](#2-multiplos-profissionais-solicitantes)
3. [Modulo de Faturamento e Impressao do CDM](#3-modulo-de-faturamento-e-impressao-do-cdm)
4. [Laudos com Historico Grafico e Sinalizadores](#4-laudos-com-historico-grafico-e-sinalizadores)

> **Ajustes Tecnicos Incorporados (v1.1):**
> - `cdm_view.py`: Variavel renomeada `request` -> `analysis_request` para evitar conflito com `self.request` (Zope)
> - `cdm_view.py`: Import `io` adicionado -> `from io import BytesIO`
> - `report_view.py`: Grafico alterado de `LinePlot` nativo para `matplotlib` (headless, suporte a datas)

---

## 1. Arquitetura do Add-on

### Nucleo do Add-on: `senaite.hgumba`

```text
src/
  senaite/
      hgumba/
          __init__.py
          configure.zcml
          extensions/
              __init__.py
              schema.py
          browser/
              __init__.py
              configure.zcml
              views/
                  __init__.py
                  cdm_view.py
                  report_view.py
          profiles/
              default/
                  metadata.xml
                  types/
                      Doctor.xml
              upgrade/
                  ...
          static/
              cdm_logo.png
```

### Registro ZCML Principal (`configure.zcml`)

```xml
<configure xmlns="http://namespaces.zope.org/zope"
           xmlns:five="http://namespaces.zope.org/five"
           xmlns:browser="http://namespaces.zope.org/browser"
           xmlns:genericsetup="http://namespaces.zope.org/genericsetup"
           xmlns:i18n="http://www.zope.org/i18n"
           i18n_domain="senaite.hgumba">

    <include package=".browser" />
    <include package=".extensions" />

    <genericsetup:registerProfile
        name="default"
        title="SENAITE HGU MBA"
        description="Customizacoes SENAITE para o Hospital Geral de Umba"
        directory="profiles/default"
        for="Products.CMFPlone.interfaces.IPloneSiteRoot"
        provides="Products.GenericSetup.interfaces.EXTENSION" />

</configure>
```

### Dependencias (`setup.py`)

```python
install_requires=[
    "senaite.core",
    "archetypes.schemaextender",
    "reportlab",
    "matplotlib",  # para graficos opcionais
]
```

---

## 2. Multiplos Profissionais Solicitantes

### 2.1. Estrategia

Utilizar `archetypes.schemaextender` para injetar um campo `CoPhysicians` no tipo `AnalysisRequest`, sem modificar o campo `Physician` original.

### 2.2. Registro do Extender

`extensions/__init__.py`:
```python
from archetypes.schemaextender.interfaces import ISchemaExtender
from zope.interface import implementer
from senaite.hgumba.extensions.schema import CoPhysiciansExtender
```

`extensions/configure.zcml`:
```xml
<configure xmlns="http://namespaces.zope.org/zope">
    <adapter
        name="CoPhysicians"
        factory=".schema.CoPhysiciansExtender"
        provides="archetypes.schemaextender.interfaces.ISchemaExtender" />
</configure>
```

### 2.3. Classe do Extender

`extensions/schema.py`:

```python
from archetypes.schemaextender.extender import BaseSchemaExtender
from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.Widget import AjaxSelectWidget
from senaite.core.content.analysisrequest import AnalysisRequest

class CoPhysiciansField(ExtensionField, ReferenceField):
    pass

class CoPhysiciansExtender(BaseSchemaExtender):
    fields = [
        CoPhysiciansField(
            "CoPhysicians",
            multiValued=True,
            allowed_types=("Doctor",),
            relationship="senaite_hgu_co_physician",
            widget=AjaxSelectWidget(
                label="Co-Profissionais Solicitantes",
                description="Medicos ou profissionais adicionais que solicitaram a analise",
                visible={"edit": "visible", "view": "invisible"},
            ),
        )
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields
```

### 2.4. Visibilidade na Tabela de Listing

Registrar coluna no `configure.zcml`:

```xml
<browser:viewlet
    name="senaite-hgumba-cophysicians-column"
    for="senaite.core.content.analysisrequest.AnalysisRequest"
    manager="senaite.core.listing"
    class=".views.CoPhysiciansColumn"
    permission="zope2.View" />
```

### 2.5. Impacto no CDM

Template ReportLab do CDM deve iterar ambos os campos:

```
Profissionais Solicitantes:
- Dr. {Physician.Title} (principal)
- Dr. {CoPhysician.Title} para cada CoPhysician
```

---

## 3. Modulo de Faturamento e Impressao do CDM

### 3.1. Estrategia

BrowserView registrada em `AnalysisRequest` que gera PDF do CDM via ReportLab, acionada manualmente ou via workflow.

### 3.2. Registro ZCML

`browser/configure.zcml`:
```xml
<configure xmlns="http://namespaces.zope.org/browser">
    <browser:page
        name="cdm-pdf"
        for="senaite.core.content.analysisrequest.AnalysisRequest"
        class=".views.cdm_view.CDMView"
        permission="senaite.core.permissions.ManageAnalysisRequests"
        layer="senaite.core.interfaces.ISenaiteCoreLayer" />
</configure>
```

### 3.3. Tabela de Custos (CATSERV)

Modelo de dados em `models.py`:

```python
from sqlalchemy import Column, String, Float, Integer
from senaite.core.schema import Base

class CatServItem(Base):
    __tablename__ = "hgumba_catserv"
    id = Column(Integer, primary_key=True)
    analysis_method_id = Column(String(128), unique=True, nullable=False)
    codigo_catserv = Column(String(20), nullable=False)
    valor_unitario = Column(Float, nullable=False)
    descricao = Column(String(256))
```

Ou alternativa mais enxuta (sem SQLAlchemy): dicionario em `config.py`:

```python
CATSERV_TABLE = {
    "AnaliseClinica_01": {"codigo": "01.01.001", "valor": 12.50, "descricao": "Hemograma completo"},
    "Microbiologia_02":  {"codigo": "02.03.010", "valor": 35.00, "descricao": "Urocultura"},
    "Bioquimica_03":    {"codigo": "03.02.005", "valor": 8.90,  "descricao": "Glicemia"},
}
```

### 3.4. Geracao do PDF (CDMView)

`browser/views/cdm_view.py`:

```python
from io import BytesIO
from Products.Five.browser import BrowserView
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from senaite.core.logger import get_logger

logger = get_logger("senaite.hgumba.cdm")

class CDMView(BrowserView):
    """Gera o Comprovante de Despesas Medicas em PDF"""

    def __call__(self):
        analysis_request = self.context
        pdf_data = self._render_cdm(analysis_request)

        logger.info(
            "CDM gerado - Request: %s, Paciente: %s, Usuario: %s",
            analysis_request.getId(),
            analysis_request.getPatient().Title() if analysis_request.getPatient() else "N/A",
            self.request.get("AUTHENTICATED_USER", "anonymous"),
        )

        return self._response_pdf(pdf_data)

    def _render_cdm(self, analysis_request):
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)

        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("COMPROVANTE DE DESPESAS MEDICAS", styles["Title"]))
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"Requisição: {analysis_request.getId()}", styles["Normal"]))
        story.append(Paragraph(f"Paciente: {analysis_request.getPatient().Title()}", styles["Normal"]))

        # Tabela de exames com valores
        data = [["Exame", "Codigo CATSERV", "Valor"]]
        for analysis in analysis_request.getAnalyses():
            catserv = CATSERV_TABLE.get(analysis.getAnalysisMethod(), {})
            data.append([
                analysis.Title(),
                catserv.get("codigo", "-"),
                f'R$ {catserv.get("valor", 0):.2f}',
            ])

        story.append(Table(data, colWidths=[80*mm, 40*mm, 30*mm]))
        doc.build(story)
        return buf.getvalue()

    def _response_pdf(self, data):
        self.request.response.setHeader("Content-Type", "application/pdf")
        self.request.response.setHeader(
            "Content-Disposition",
            f'attachment; filename="cdm_{self.context.getId()}.pdf"',
        )
        return data
```

### 3.5. Acionamento por Workflow

No `workflows/AnalysisRequest_workflow.xml`, adicionar script na transicao `publish`:

```xml
<action transition_id="publish">
    <action-progress>...</action-progress>
    <script-before>senaite.hgumba.cdm_trigger.generate_cdm</script-before>
</action>
```

Ou manter manual: botao "Gerar CDM" no viewlet da AnalysisRequest.

### 3.6. Trilha de Auditoria

```python
from senaite.core.logger import get_logger
logger = get_logger("senaite.hgumba")
logger.info(
    "CDM emitido | Req: %s | Paciente: %s | Profissional: %s | Data: %s",
    req_id, patient_name, user_name, datetime.utcnow().isoformat()
)
```

---

## 4. Laudos com Historico Grafico e Sinalizadores

### 4.1. Estrategia

Sobrescrever o servico de impressao padrao (`senaite.core.printing`) atraves do mecanismo de `BrowserView` customizada que estende o template ReportLab padrao.

### 4.2. Registro ZCML

```xml
<browser:page
    name="hgumba-report-pdf"
    for="senaite.core.content.analysisrequest.AnalysisRequest"
    class=".views.report_view.ReportWithHistoryView"
    permission="senaite.core.permissions.ManageAnalysisRequests"
    layer="senaite.core.interfaces.ISenaiteCoreLayer" />
```

### 4.3. Extracao do Historico e Sinalizadores

`browser/views/report_view.py`:

```python
from io import BytesIO
from datetime import datetime
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

class ReportWithHistoryView(BrowserView):

    def get_patient_history(self, patient, limit=10):
        """Busca ultimas N requisicoes publicadas do paciente"""
        if not patient:
            return []

        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog(
            portal_type="AnalysisRequest",
            getPatientUID=patient.UID(),
            review_state="published",
            sort_on="created",
            sort_order="descending",
            sort_limit=limit,
        )
        return [r.getObject() for r in results[:limit]]

    def get_out_of_range_flags(self, analysis):
        """Mapeia sinalizadores para resultados fora do intervalo"""
        result = analysis.getResult()
        min_ref = analysis.getMinRef()
        max_ref = analysis.getMaxRef()

        if result is None:
            return ""
        try:
            val = float(result)
            if min_ref is not None and val < float(min_ref):
                return "[BAIXO]"
            if max_ref is not None and val > float(max_ref):
                return "[ALTO]"
        except (ValueError, TypeError):
            pass
        return ""
```

### 4.4. Grafico via Matplotlib (Alternativa ao LinePlot Nativo)

O `LinePlot` nativo do ReportLab nao aceita objetos datetime no eixo X. Para plotar datas corretamente, utiliza-se o **Matplotlib** em modo headless, salvando o grafico em buffer de bytes e injetando como `Image` no story do PDF:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class ReportWithHistoryView(BrowserView):
    # ... (metodos anteriores)

    def render_history_chart(self, patient_results, analysis_key):
        """Gera grafico de evolucao via Matplotlib (headless)"""
        dates = []
        values = []

        for req in patient_results:
            for analysis in req.getAnalyses():
                if analysis.getKeyword() == analysis_key:
                    try:
                        val = float(analysis.getResult())
                        date_str = req.created().strftime('%Y-%m-%d')
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                        dates.append(dt)
                        values.append(val)
                    except (ValueError, TypeError):
                        pass

        if len(dates) < 2:
            return None

        points = sorted(zip(dates, values))
        x_dates, y_values = zip(*points)

        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(x_dates, y_values, marker='o', color='#1a5cbf', linewidth=1.5, markersize=4)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        fig.autofmt_xdate()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, linestyle='--', alpha=0.5)

        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        buf.seek(0)

        return Image(buf, width=120, height=60)
```

> **Nota:** O `matplotlib.use('Agg')` no topo do modulo garante funcionamento headless (sem display grafico), essencial em servidores Zope.

### 4.5. Sinalizadores no PDF

No loop de renderizacao das analises:

```python
for analysis in analyses:
    flag = self.get_out_of_range_flags(analysis)
    result_text = f"{analysis.getResult()} {analysis.getUnit()}"
    if flag:
        result_text += f" ** {flag} **"
    # renderizar no PDF com estilo destacado (cor vermelha se flag)
```

### 4.6. Template Completo do Laudo

```python
from reportlab.platypus import Image

def _render_report(self, analysis_request):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    story = []

    # Cabecalho
    story.append(Paragraph(f"LAUDO: {analysis_request.getId()}", styles["Title"]))
    story.append(Paragraph(f"Paciente: {analysis_request.getPatient().Title()}"))

    # Resultados atuais com sinalizadores
    for analysis in analysis_request.getAnalyses():
        flag = self.get_out_of_range_flags(analysis)
        text = f"{analysis.Title()}: {analysis.getResult()} {analysis.getUnit()}"
        if flag:
            text += f" {flag}"
        story.append(Paragraph(text))

    # Historico grafico (Matplotlib -> PNG -> ReportLab Image)
    history = self.get_patient_history(analysis_request.getPatient())
    for analysis in analysis_request.getAnalyses():
        keyword = analysis.getKeyword()
        chart = self.render_history_chart(history, keyword)
        if chart:
            story.append(Paragraph(f"Historico: {analysis.Title()}"))
            story.append(chart)

    doc.build(story)
    return buf.getvalue()
```

---

## 5. Endpoint Custom: @@hgumba-create-ar (Bypass @@API/create)

### Problema
O endpoint `POST /@@API/create` do SENAITE core (`bika/lims/jsonapi/create.py:168`) bloqueia explicitamente a criação de `AnalysisRequest`:
```python
raise BadRequest("Creation of Analysis Request through JSON API is not supported. Request aborted.")
```

### Solução
BrowserView custom registrada como `hgumba-create-ar` que recebe POST JSON e usa `invokeFactory` diretamente no contexto Zope, sem passar pelo validador do JSON API.

### Contrato

**Request:**
```json
{
  "client_id": "hgu",
  "services": ["GLI001", "HEM001"],
  "contact_id": "dr-admin",
  "patient_name": "Maria Silva",
  "mrn": "12345678901",
  "title": "AR-001",
  "remarks": "Auditoria: resultado recebido da maquina Mindray_BS200"
}
```

**Response (201):**
```json
{
  "success": true,
  "id": "GLI001",
  "uid": "abc123...",
  "url": "http://...",
  "warnings": []
}
```

### Implementação
- `browser/views/create_ar.py`:
  - `_find_service_by_keyword(site, keyword)` — função de módulo que busca AnalysisService pela Keyword no `bika_setup`
  - `_set_ar_fields(ar, mrn, patient_name, remarks)` — função de módulo que seta campos via `getField().set()`
  - `CreateAnalysisRequestView.__call__()` — valida payload, resolve servicios, invoca `invokeFactory`
  - `_ensure_ar()` — método da view que cria AR se não existir

## 6. Endpoint Custom: @@hgumba-set-remark (Bypass @@API/update)

### Problema
O `@@API/senaite/v1/update` exige **todos os campos obrigatórios** mesmo para atualizações parciais, impossibilitando setar apenas `Remarks` (necessário para trilha de auditoria).

### Solução
BrowserView `SetRemarkView` que acessa diretamente o campo `Remarks` da AR via Archetypes `getField().set()`, ignorando a validação do JSON API.

### Contrato

**Request:**
```json
{
  "ar_id": "HGU-AR-001",
  "client_id": "hgu",
  "remarks": "[2026-05-19 14:30] Resultado recebido da maquina Mindray_BS200"
}
```

**Response:**
```json
{
  "success": true,
  "id": "HGU-AR-001",
  "uid": "abc123..."
}
```

## 7. Checklist de Implantacao

- [ ] Criar estrutura do add-on `senaite.hgumba`
- [ ] Registrar profile GenericSetup
- [ ] Implementar `CoPhysiciansExtender` (Item 2)
- [ ] Criar BrowserView `cdm-pdf` (Item 3)
- [ ] Definir tabela CATSERV (config ou SQLite)
- [ ] Criar BrowserView `hgumba-report-pdf` (Item 4)
- [ ] Testar geracao de PDF com reportlab
- [ ] Configurar Nginx Proxy Manager para `senaite.gti.local`
- [ ] Testar workflow de publicacao + gatilho CDM
