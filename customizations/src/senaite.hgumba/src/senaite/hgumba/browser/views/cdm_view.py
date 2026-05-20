import logging
import os
from io import BytesIO
from Products.Five.browser import BrowserView
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet

logger = logging.getLogger("senaite.hgumba.cdm")

FALLBACK_CATSERV = {
    "Hemograma": {"codigo": "01.01.001", "valor": 12.50, "descricao": "Hemograma completo"},
    "Urocultura": {"codigo": "02.03.010", "valor": 35.00, "descricao": "Urocultura"},
    "Glicemia": {"codigo": "03.02.005", "valor": 8.90, "descricao": "Glicemia em jejum"},
}


def _load_catserv():
    """Load CATSERV table from PostgreSQL. Falls back to hardcoded dict."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "db"),
            port=int(os.environ.get("DB_PORT", 5432)),
            dbname=os.environ.get("DB_NAME", "financeiro"),
            user=os.environ.get("DB_USER", "catserv"),
            password=os.environ.get("DB_PASSWORD", ""),
            connect_timeout=3,
            sslmode=os.environ.get("DB_SSLMODE", "prefer"),
        )
        cur = conn.cursor()
        cur.execute("SELECT exame, codigo, valor, descricao FROM tabela_catserv")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        table = {}
        for exame, codigo, valor, descricao in rows:
            table[exame] = {"codigo": codigo, "valor": float(valor), "descricao": descricao}
        logger.info("CATSERV loaded from DB: %d entries", len(table))
        return table
    except Exception as e:
        logger.warning("CATSERV usando fallback hardcoded — dados financeiros podem estar desatualizados (erro: %s)", e)
        return dict(FALLBACK_CATSERV)


CATSERV_TABLE = _load_catserv()


class CDMView(BrowserView):
    """Gera o Comprovante de Despesas Medicas em PDF"""

    def __call__(self):
        ar = self.context
        pdf_data = self._render_cdm(ar)
        logger.info(
            "CDM gerado - Request: %s, Paciente: %s, Usuario: %s",
            ar.getId(),
            self._get_patient_name(ar),
            self.request.get("AUTHENTICATED_USER", "anonymous"),
        )
        return self._response_pdf(pdf_data, ar)

    def _get_patient_name(self, ar):
        name = getattr(ar, 'getPatientFullName', None)
        if name:
            return name()
        mrn = getattr(ar, 'getMedicalRecordNumberValue', None)
        if mrn:
            return "MRN: %s" % mrn()
        return getattr(ar, 'Title', lambda: 'N/A')()

    def _render_cdm(self, ar):
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
            "Requisicao: %s" % ar.getId(), styles["Normal"]))
        story.append(Paragraph(
            "Paciente: %s" % self._get_patient_name(ar), styles["Normal"]))

        story.append(Spacer(1, 5*mm))

        data = [["Exame", "Codigo CATSERV", "Valor"]]
        for analysis in ar.getAnalyses():
            t = analysis.Title
            title = t() if callable(t) else t
            catserv = CATSERV_TABLE.get(title, {})
            data.append([
                title,
                catserv.get("codigo", "-"),
                "R$ %.2f" % catserv.get("valor", 0),
            ])

        story.append(Table(data, colWidths=[80*mm, 40*mm, 30*mm]))
        doc.build(story)
        return buf.getvalue()

    def _response_pdf(self, data, ar):
        self.request.response.setHeader("Content-Type", "application/pdf")
        self.request.response.setHeader(
            "Content-Disposition",
            'attachment; filename="cdm_%s.pdf"' % ar.getId(),
        )
        return data
