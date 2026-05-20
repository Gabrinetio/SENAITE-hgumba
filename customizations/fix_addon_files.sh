#!/bin/sh
set -e
SRC=/opt/senaite/addons/src/senaite/hgumba

echo "=== Fix browser configure.zcml - remove template from CDMView ==="
cat > $SRC/browser/configure.zcml << 'ZEOF'
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:browser="http://namespaces.zope.org/browser"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="senaite.hgumba">

    <include package=".views" />

    <browser:page
        name="cdm-report"
        for="*"
        class=".views.cdm_view.CDMView"
        permission="zope2.View"
        layer="senaite.hgumba.browser.interfaces.ISenaiteHgumbaLayer" />

    <browser:page
        name="hgumba-report"
        for="*"
        class=".views.report_view.ReportView"
        template="hgumba_report.pt"
        permission="zope2.View"
        layer="senaite.hgumba.browser.interfaces.ISenaiteHgumbaLayer" />

</configure>
ZEOF

echo "=== Fix cdm_view.py - add PDF content-type ==="
cat > $SRC/browser/views/cdm_view.py << 'PYEOF'
import io
from base64 import b64encode

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime, timedelta

from Products.Five.browser import BrowserView
from zope.interface import implementer
from zope.component import getAdapters
from bika.lims import api
from senaite.app.listing.interfaces import IListingView
from Products.CMFPlone.utils import getToolByName

try:
    from archetypes.schemaextender.interfaces import ISchemaExtender
    HAS_EXTENDER = True
except ImportError:
    HAS_EXTENDER = False


@implementer(IListingView)
class CDMView(BrowserView):

    def __call__(self):
        self.request.response.setHeader("Content-Type", "application/pdf")
        return self.render_pdf()

    def render_pdf(self):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                         Spacer, Table, TableStyle)
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm,
                                 bottomMargin=2 * cm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("MAPA CDM - CONSULTAS", styles["Title"]))
        elements.append(Spacer(1, 0.5 * cm))

        bc = api.get_current_client()
        if bc:
            elements.append(Paragraph("Cliente: {}".format(
                api.get_title(bc)), styles["Normal"]))
        elements.append(Spacer(1, 0.3 * cm))

        data = [["Solicitacao", "Paciente", "Data", "Servicos", "Valor"]]
        total_geral = 0.0

        LIMIT = 100
        brains = api.search({"portal_type": "AnalysisRequest"}, LIMIT)
        for brain in brains:
            obj = brain.getObject()
            pid = api.get_id(obj)
            pac = obj.getPatient()
            pac_name = api.get_title(pac) if pac else "N/A"
            d = obj.getDate()
            ds = d.strftime("%d/%m/%Y") if d else ""
            svc_titles = []
            for an in obj.getAnalyses():
                svc = an.getService()
                if svc:
                    svc_titles.append(api.get_title(svc))
            servicos = ", ".join(svc_titles[:5])
            total = getattr(obj, "TotalPrice", 0) or 0
            total_geral += total
            data.append([pid, pac_name, ds, servicos, "KZ {:.0f}".format(total)])

        data.append(["", "", "", "TOTAL GERAL",
                      "KZ {:.0f}".format(total_geral)])
        t = Table(data, colWidths=[3 * cm, 4 * cm, 2.5 * cm, 5 * cm,
                                    3 * cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e1f2")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2efda")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        return buf.getvalue()

    def get_physicians_field(self):
        if not HAS_EXTENDER:
            return []
        out = []
        request = getattr(self, "request", None)
        context = getattr(self, "context", None)
        if not request or not context:
            return out
        patient = api.get_uid(context)
        if not patient:
            return out
        pc = getToolByName(context, "portal_catalog")
        brains = pc(
            portal_type="AnalysisRequest",
            getPatientUID=patient,
            sort_on="created",
            sort_order="descending",
            sort_limit=1,
        )
        if not brains:
            return out
        ar = brains[0].getObject()
        if hasattr(ar, "getPhysicians"):
            val = ar.getPhysicians()
            if val:
                out = val if isinstance(val, (list, tuple)) else [val]
        return out
PYEOF

echo "=== Fix extensions configure.zcml - remove generator gs registration here ==="
cat > $SRC/extensions/configure.zcml << 'ZEOF'
<configure
    xmlns="http://namespaces.zope.org/zope"
    i18n_domain="senaite.hgumba">
</configure>
ZEOF

echo "=== Fix extensions/schema.py - typo extender ==="
cat > $SRC/extensions/schema.py << 'PYEOF'
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.extender import BaseSchemaExtender
from zope.interface import implementer
from zope.component import adapts
from bika.lims.interfaces import IAnalysisRequest
from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes.public import StringField, StringWidget


class MultiPhysiciansField(ExtensionField, StringField):
    pass


@implementer(ISchemaExtender)
class CoPhysiciansExtender(BaseSchemaExtender):
    adapts(IAnalysisRequest)
    fields = [
        MultiPhysiciansField(
            "CoPhysicians",
            schemata="Description",
            widget=StringWidget(
                label="Solicitantes Multi-Profissionais",
                description="Nomes dos medicos solicitantes separados por virgula",
                size=60,
            ),
        ),
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields
PYEOF

echo "=== All fixes applied ==="
find $SRC -type f -name "*.py" -o -name "*.zcml" -o -name "*.pt" | sort
