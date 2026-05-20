from io import BytesIO
from Products.Five.browser import BrowserView
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from senaite.core.logger import get_logger

logger = get_logger("senaite.hgumba.cdm")

CATSERV_TABLE = {
    "Hemograma": {"codigo": "01.01.001", "valor": 12.50, "descricao": "Hemograma completo"},
    "Urocultura": {"codigo": "02.03.010", "valor": 35.00, "descricao": "Urocultura"},
    "Glicemia": {"codigo": "03.02.005", "valor": 8.90, "descricao": "Glicemia em jejum"},
}


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
        story.append(Paragraph(
            "Hospital Geral de Umba - Seccao de Financas", styles["Normal"]))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "Requisicao: %s" % analysis_request.getId(), styles["Normal"]))
        story.append(Paragraph(
            "Paciente: %s" % analysis_request.getPatient().Title(), styles["Normal"]))

        story.append(Spacer(1, 5*mm))

        data = [["Exame", "Codigo CATSERV", "Valor"]]
        for analysis in analysis_request.getAnalyses():
            catserv = CATSERV_TABLE.get(analysis.Title(), {})
            data.append([
                analysis.Title(),
                catserv.get("codigo", "-"),
                "R$ %.2f" % catserv.get("valor", 0),
            ])

        story.append(Table(data, colWidths=[80*mm, 40*mm, 30*mm]))
        doc.build(story)
        return buf.getvalue()

    def _response_pdf(self, data):
        self.request.response.setHeader("Content-Type", "application/pdf")
        self.request.response.setHeader(
            "Content-Disposition",
            'attachment; filename="cdm_%s.pdf"' % self.context.getId(),
        )
        return data
