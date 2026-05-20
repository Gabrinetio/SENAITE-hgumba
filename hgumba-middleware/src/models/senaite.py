# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AnalysisRequestPayload(BaseModel):
    """Payload para criar uma AnalysisRequest no SENAITE via JSON API"""
    client_id: str = "hgu"
    contact_uid: Optional[str] = None
    patient_uid: Optional[str] = None
    services: List[str] = Field(..., description="Lista de UIDs ou IDs dos serviços/análises")
    title: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_crm: Optional[str] = None


class WebhookLaudoPayload(BaseModel):
    """Payload recebido do webhook do SENAITE quando um laudo é publicado"""
    analysis_request_id: str
    client_id: str
    patient_name: Optional[str] = None
    pdf_url: Optional[str] = None
    review_state: str
    results: Optional[List[dict]] = None
