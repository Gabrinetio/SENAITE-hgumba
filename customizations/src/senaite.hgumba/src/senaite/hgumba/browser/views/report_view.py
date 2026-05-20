# -*- coding: utf-8 -*-
from io import BytesIO
from datetime import datetime
from Products.Five.browser import BrowserView
from bika.lims import api as bika_api

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def _val(obj, attr, default="—"):
    """Get value from object, handle both attribute and method."""
    v = getattr(obj, attr, default)
    return v() if callable(v) else v


class ReportWithHistoryView(BrowserView):
    """Laudo com historico grafico e sinalizadores fora-do-intervalo"""

    def get_patient_history(self, patient, limit=10):
        if not patient:
            return []
        catalog = bika_api.get_tool('portal_catalog')
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
        result = _val(analysis, 'getResult')
        min_ref = _val(analysis, 'getMinRef')
        max_ref = _val(analysis, 'getMaxRef')
        if result in (None, "", "—"):
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

    def render_history_chart(self, patient_results, analysis_key):
        dates = []
        values = []
        for req in patient_results:
            for analysis in req.getAnalyses():
                kw = _val(analysis, 'getKeyword')
                if kw == analysis_key:
                    try:
                        val = float(_val(analysis, 'getResult'))
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
        return Image(buf, width=400, height=200)

    def __call__(self):
        ar = self.context
        pdf_data = self._render_report(ar)
        self.request.response.setHeader("Content-Type", "application/pdf")
        self.request.response.setHeader(
            "Content-Disposition",
            'attachment; filename="laudo_%s.pdf"' % ar.getId(),
        )
        return pdf_data

    def _render_report(self, ar):
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        patient_name = self._get_patient_name(ar)
        story.append(Paragraph("LAUDO: %s" % ar.getId(), styles["Title"]))
        story.append(Paragraph("Paciente: %s" % patient_name))
        story.append(Spacer(1, 5))
        for analysis in ar.getAnalyses():
            flag = self.get_out_of_range_flags(analysis)
            text = "%s: %s %s" % (
                _val(analysis, 'Title'),
                _val(analysis, 'getResult', "-"),
                _val(analysis, 'getUnit', ""),
            )
            if flag:
                text += " ** %s **" % flag
            story.append(Paragraph(text))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Historico do Paciente:", styles["Heading2"]))
        patient = None
        mrn_val = _val(ar, 'getMedicalRecordNumberValue')
        if mrn_val:
            from senaite.patient import api as patient_api
            patient = patient_api.get_patient_by_mrn(mrn_val)
        history = self.get_patient_history(patient) if patient else []
        for analysis in ar.getAnalyses():
            keyword = _val(analysis, 'getKeyword')
            chart = self.render_history_chart(history, keyword)
            if chart:
                story.append(Paragraph(
                    "Evolucao: %s" % _val(analysis, 'Title'), styles["Normal"]))
                story.append(chart)
                story.append(Spacer(1, 5))
        doc.build(story)
        return buf.getvalue()

    def _get_patient_name(self, ar):
        name = _val(ar, 'getPatientFullName')
        if name and name != "—":
            return name
        mrn = _val(ar, 'getMedicalRecordNumberValue')
        if mrn:
            return "MRN: %s" % mrn
        return _val(ar, 'Title', 'N/A')
