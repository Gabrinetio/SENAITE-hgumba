# -*- coding: utf-8 -*-
import json
import logging
import time
from threading import Thread

import urllib2

from zope.component import adapter
from bika.lims.interfaces import IAnalysisRequest
from Products.DCWorkflow.interfaces import IAfterTransitionEvent

logger = logging.getLogger("senaite.hgumba.webhook")


def _post_webhook(url, payload, retries=3):
    data = json.dumps(payload)
    for attempt in range(retries):
        try:
            req = urllib2.Request(url, data, {"Content-Type": "application/json"})
            urllib2.urlopen(req, timeout=5)
            logger.info("Webhook enviado para %s", payload.get("analysis_request_id"))
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error("Webhook falhou apos %d tentativas: %s", retries, e)


@adapter(IAnalysisRequest, IAfterTransitionEvent)
def notify_middleware_on_publish(obj, event):
    if getattr(event.new_state, "id", "") != "published":
        return

    webhook_url = "http://middleware_gateway:8000/api/v1/senaite/webhook/laudo_publicado"

    patient_name = ""
    if hasattr(obj, "getPatientFullName"):
        try:
            patient_name = obj.getPatientFullName()
        except Exception:
            pass

    payload = {
        "analysis_request_id": obj.getId(),
        "client_id": obj.aq_parent.getId(),
        "patient_name": patient_name,
        "review_state": "published",
        "pdf_url": "%s/@@hgumba-report-pdf" % obj.absolute_url(),
    }

    Thread(target=_post_webhook, args=(webhook_url, payload)).start()
