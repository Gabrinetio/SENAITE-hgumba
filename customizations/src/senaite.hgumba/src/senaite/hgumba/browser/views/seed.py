# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
import transaction
import json


class SeedView(BrowserView):
    """Seed all test data for development."""

    def __call__(self):
        results = {"created": [], "errors": []}
        site = self.context

        # 1. Client
        try:
            client = self._ensure(site.clients, 'Client', 'hgu',
                                  title='HGU - Hospital Gumarba', ClientID='HGU')
            if client:
                results["created"].append("Client HGU")
        except Exception as e:
            results["errors"].append("Client: %s" % str(e))
            client = None

        # 2. AnalysisServices
        svcs = {}
        for sid, title, kw, unit in [
            ('glicose', 'Glicose', 'GLI001', 'mg/dL'),
            ('hemograma', 'Hemograma', 'HEM001', 'milhoes/mm3'),
            ('lipidograma', 'Lipidograma', 'LIP001', 'mg/dL'),
        ]:
            try:
                svc = self._ensure(site.bika_setup.bika_analysisservices,
                                   'AnalysisService', sid,
                                   title=title, Keyword=kw, Unit=unit)
                if svc:
                    svcs[sid] = svc
                    results["created"].append("Service %s" % sid)
            except Exception as e:
                results["errors"].append("Service %s: %s" % (sid, str(e)))

        # 3. Contact
        contact = None
        if client:
            try:
                contact = self._ensure(client, 'Contact', 'contact-1',
                                        title='Dr Teste')
                if contact:
                    results["created"].append("Contact contact-1")
            except Exception as e:
                results["errors"].append("Contact: %s" % str(e))
                contact = None

        # 4. AnalysisRequests
        if client and contact and 'glicose' in svcs:
            try:
                ar = self._ensure_ar(client, contact, svcs['glicose'],
                                     'HGU-AR-001', 'GLI001', 'MRN-001',
                                     'Paciente Teste A')
                if ar:
                    results["created"].append("AR HGU-AR-001 (Paciente Teste A)")
            except Exception as e:
                results["errors"].append("AR HGU-AR-001: %s" % str(e))

        if client and contact and 'hemograma' in svcs:
            try:
                ar = self._ensure_ar(client, contact, svcs['hemograma'],
                                     'HGU-AR-002', 'HEM001', 'MRN-002',
                                     'Paciente Teste B')
                if ar:
                    results["created"].append("AR HGU-AR-002 (Paciente Teste B)")
            except Exception as e:
                results["errors"].append("AR HGU-AR-002: %s" % str(e))

        if client and contact and 'lipidograma' in svcs:
            try:
                ar = self._ensure_ar(client, contact, svcs['lipidograma'],
                                     'HGU-AR-003', 'LIP001', 'MRN-003',
                                     'Paciente Teste C')
                if ar:
                    results["created"].append("AR HGU-AR-003 (Paciente Teste C)")
            except Exception as e:
                results["errors"].append("AR HGU-AR-003: %s" % str(e))

        return self._response(results)

    def _ensure(self, container, portal_type, obj_id, **kwargs):
        existing = getattr(container, obj_id, None)
        if existing:
            return existing
        container.invokeFactory(portal_type, obj_id, **kwargs)
        obj = container[obj_id]
        obj.reindexObject()
        transaction.commit()
        return obj

    def _ensure_ar(self, client, contact, service, ar_id, title, mrn, fullname):
        existing = getattr(client, ar_id, None)
        if existing:
            return None
        client.invokeFactory('AnalysisRequest', ar_id,
                             title=title,
                             Analyses=[service.UID()],
                             Contact=contact.UID())
        ar = client[ar_id]
        if hasattr(ar, 'getField'):
            mrn_field = ar.getField('MedicalRecordNumber')
            if mrn_field:
                mrn_field.set(ar, {"value": mrn, "temporary": False})
            name_field = ar.getField('PatientFullName')
            if name_field:
                parts = fullname.split(None, 2)
                name_data = {"firstname": parts[0]}
                if len(parts) > 2:
                    name_data["middlename"] = parts[1]
                    name_data["lastname"] = parts[2]
                elif len(parts) > 1:
                    name_data["lastname"] = parts[1]
                name_field.set(ar, name_data)
        ar.reindexObject()
        transaction.commit()
        return ar

    def _response(self, data):
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(data, indent=2, ensure_ascii=False)
