import pytest
from fastapi.testclient import TestClient

from main import app
from config import settings

_SAVED_PW = settings.senaite_password
_SAVED_KEY = settings.api_key

client = TestClient(app)


class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_body(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hgumba-middleware"
        assert "version" in data


class TestWebhookLaudoPublicado:
    WEBHOOK_URL = "/api/v1/senaite/webhook/laudo_publicado"

    @pytest.fixture(autouse=True)
    def setup(self):
        settings.senaite_password = "test-admin"
        yield
        settings.senaite_password = _SAVED_PW

    def test_valid_payload(self):
        payload = {
            "analysis_request_id": "HGU-AR-001",
            "client_id": "hgu",
            "patient_name": "Maria Silva",
            "review_state": "published",
            "pdf_url": "http://app:8080/senaite/clients/hgu/HGU-AR-001/@@cdm-pdf",
        }
        resp = client.post(self.WEBHOOK_URL, json=payload)
        assert resp.status_code in (200, 502), f"Esperado 200/502, obtido {resp.status_code}: {resp.text[:200]}"
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "processado"
            assert data["analysis_request_id"] == "HGU-AR-001"

    def test_payload_sem_patient_name(self):
        payload = {
            "analysis_request_id": "HGU-AR-002",
            "client_id": "hgu",
            "review_state": "published",
        }
        resp = client.post(self.WEBHOOK_URL, json=payload)
        assert resp.status_code in (200, 502), f"Esperado 200/502, obtido {resp.status_code}: {resp.text[:200]}"
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "processado"

    def test_nao_publicado_ignorado(self):
        payload = {
            "analysis_request_id": "HGU-AR-003",
            "client_id": "hgu",
            "review_state": "registered",
        }
        resp = client.post(self.WEBHOOK_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ignorado"

    def test_missing_required_fields(self):
        resp = client.post(self.WEBHOOK_URL, json={})
        assert resp.status_code == 422

    def test_invalid_json(self):
        resp = client.post(
            self.WEBHOOK_URL,
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


class TestSandraIngestao:
    URL = "/api/v1/sandra/ingestao"

    def test_valid_payload(self):
        payload = {
            "id_pedido": "PED-001",
            "cpf_paciente": "00000000000",
            "nome_paciente": "Maria Silva",
            "medico_solicitante": "Dr. Admin",
            "crm_solicitante": "12345",
            "data_solicitacao": "2026-05-19T10:00:00",
            "exames": [{"codigo_catserv": "GLI001", "descricao": "Glicose"}],
        }
        resp = client.post(self.URL, json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert "id_pedido" in data
