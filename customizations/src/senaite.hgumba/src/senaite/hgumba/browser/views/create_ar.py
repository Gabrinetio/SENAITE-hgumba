# -*- coding: utf-8 -*-
import re
from Products.Five.browser import BrowserView
import transaction
import json
import logging

logger = logging.getLogger("senaite.hgumba.create_ar")


def _find_service_by_keyword(site, keyword):
    """Busca um AnalysisService pela Keyword no bika_setup."""
    bika_setup = site.bika_setup
    folder = bika_setup.bika_analysisservices
    for obj_id in folder.objectIds():
        svc = folder[obj_id]
        if hasattr(svc, 'getKeyword') and callable(svc.getKeyword):
            if svc.getKeyword() == keyword:
                return svc
        elif hasattr(svc, 'Keyword'):
            kw_val = svc.Keyword
            if callable(kw_val):
                kw_val = kw_val()
            if kw_val == keyword:
                return svc
    return None


def _set_ar_fields(ar, mrn, patient_name, remarks):
    """Define campos customizados na AR (MRN, PatientName, Remarks)."""
    if not hasattr(ar, 'getField'):
        return
    if mrn:
        f = ar.getField('MedicalRecordNumber')
        if f:
            f.set(ar, {"value": mrn, "temporary": False})
    if patient_name:
        f = ar.getField('PatientFullName')
        if f:
            parts = patient_name.split(None, 2)
            name_data = {"firstname": parts[0]}
            if len(parts) > 2:
                name_data["middlename"] = parts[1]
                name_data["lastname"] = parts[2]
            elif len(parts) > 1:
                name_data["lastname"] = parts[1]
            f.set(ar, name_data)
    if remarks:
        f = ar.getField('Remarks')
        if f:
            f.set(ar, remarks)


class CreateAnalysisRequestView(BrowserView):
    """Endpoint custom para criar AnalysisRequest via POST JSON.

    Bypass da restricao explicita em @@API/create que bloqueia
    AnalysisRequest com 'not supported'.
    """

    def __call__(self):
        self.request.response.setHeader('Content-Type', 'application/json')
        try:
            raw = self.request.get('BODY', '{}')
            data = json.loads(raw)
        except Exception:
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "JSON invalido"})

        client_id = data.get("client_id", "hgu")
        if not re.match(r'^[a-zA-Z0-9_-]+$', client_id):
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "client_id deve ser alfanumerico"})

        services = data.get("services", [])
        if not isinstance(services, list) or not services or not all(isinstance(s, str) and s.strip() for s in services):
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "services deve ser uma lista nao vazia de strings"})

        ar_id = data.get("id") or data.get("ar_id")
        if ar_id and len(ar_id) > 64:
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "ar_id nao pode exceder 64 caracteres"})

        contact_id = data.get("contact_id")
        patient_name = data.get("patient_name")
        mrn = data.get("mrn")
        title = data.get("title", "")
        remarks = data.get("remarks")

        site = self.context
        errors = []

        client = getattr(site.clients, client_id, None)
        if not client:
            self.request.response.setStatus(404)
            return json.dumps({"success": False, "message": "Client %s nao encontrado" % client_id})

        svc_uids = []
        for kw in services:
            svc = _find_service_by_keyword(site, kw)
            if svc:
                svc_uids.append(svc.UID())
            else:
                errors.append("Servico %s nao encontrado" % kw)

        if not svc_uids:
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "Nenhum servico valido", "errors": errors})

        contact_uid = None
        if contact_id:
            contact = getattr(client, contact_id, None)
            if contact:
                contact_uid = contact.UID()
            else:
                errors.append("Contact %s nao encontrado" % contact_id)

        try:
            obj_id = data.get("id") or data.get("ar_id")
            kw = obj_id or services[0]
            ar = self._ensure_ar(client, svc_uids, kw, mrn, patient_name, contact_uid, title, remarks)
            if not ar:
                ar = getattr(client, obj_id, None) if obj_id else None
                if ar:
                    return json.dumps({
                        "success": True,
                        "message": "AR ja existe",
                        "id": ar.getId(),
                        "url": ar.absolute_url(),
                    })
                self.request.response.setStatus(400)
                return json.dumps({"success": False, "message": "Falha ao criar AR"})

            result = {
                "success": True,
                "id": ar.getId(),
                "uid": ar.UID(),
                "url": ar.absolute_url(),
            }
            if errors:
                result["warnings"] = errors
            return json.dumps(result, ensure_ascii=False)

        except Exception:
            logger.exception("Erro ao criar AR")
            self.request.response.setStatus(500)
            return json.dumps({"success": False, "message": "Erro interno ao criar AR"})

    def _ensure_ar(self, client, svc_uids, ar_id, mrn, patient_name, contact_uid, title=None, remarks=None):
        existing = getattr(client, ar_id, None)
        if existing:
            return None
        params = {
            "title": title or ar_id,
            "Analyses": svc_uids,
        }
        if contact_uid:
            params["Contact"] = contact_uid
        client.invokeFactory('AnalysisRequest', ar_id, **params)
        ar = client[ar_id]
        _set_ar_fields(ar, mrn, patient_name, remarks)
        ar.reindexObject()
        transaction.commit()
        return ar


class SetRemarkView(BrowserView):
    """Endpoint para definir Remarks em uma AnalysisRequest existente.

    Bypass da validacao do @@API/senaite/v1/update que exige
    todos os campos obrigatorios mesmo para updates parciais.
    """

    def __call__(self):
        self.request.response.setHeader('Content-Type', 'application/json')
        try:
            raw = self.request.get('BODY', '{}')
            data = json.loads(raw)
        except Exception:
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "JSON invalido"})

        ar_id = data.get("ar_id") or data.get("id")
        client_id = data.get("client_id", "hgu")
        remarks = data.get("remarks")
        if not ar_id or not remarks:
            self.request.response.setStatus(400)
            return json.dumps({"success": False, "message": "ar_id e remarks sao obrigatorios"})

        site = self.context
        client = getattr(site.clients, client_id, None)
        if not client:
            self.request.response.setStatus(404)
            return json.dumps({"success": False, "message": "Client %s nao encontrado" % client_id})

        ar = getattr(client, ar_id, None)
        if not ar:
            self.request.response.setStatus(404)
            return json.dumps({"success": False, "message": "AR %s nao encontrada" % ar_id})

        try:
            if hasattr(ar, 'getField'):
                r_field = ar.getField('Remarks')
                if r_field:
                    existing = r_field.get(ar) or ""
                    r_field.set(ar, existing + ("\n" if existing else "") + remarks)
                    ar.reindexObject()
                    transaction.commit()
                    return json.dumps({"success": True, "id": ar_id, "uid": ar.UID()})
            self.request.response.setStatus(500)
            return json.dumps({"success": False, "message": "AR nao possui campo Remarks"})
        except Exception:
            logger.exception("Erro ao definir Remarks")
            self.request.response.setStatus(500)
            return json.dumps({"success": False, "message": "Erro interno ao definir Remarks"})
