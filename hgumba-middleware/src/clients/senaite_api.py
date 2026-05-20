import base64
import logging
from typing import Optional

import httpx
from config import settings

logger = logging.getLogger("senaite_api")


class SenaiteClient:
    """Cliente HTTP assíncrono para a JSON API do SENAITE"""

    def __init__(self):
        self.base_url = settings.senaite_url.rstrip("/")
        self.auth_header = self._build_auth()

    def _build_auth(self) -> str:
        raw = f"{settings.senaite_user}:{settings.senaite_password}"
        return f"Basic {base64.b64encode(raw.encode()).decode()}"

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}{path}",
                headers={"Authorization": self.auth_header},
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, data: dict = None, params: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                headers={"Authorization": self.auth_header},
                params=params,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def check_health(self) -> bool:
        try:
            await self._get("/")
            return True
        except Exception as e:
            logger.warning("SENAITE health check failed: %s", e)
            return False

    async def get_service_uid(self, service_id: str) -> Optional[str]:
        """Busca UID de um AnalysisService pelo ID (via v1 API)"""
        data = await self._get("/@@API/senaite/v1/search", params={
            "portal_type": "AnalysisService",
            "id": service_id,
        })
        items = data.get("items", [])
        if items:
            return items[0].get("uid")
        return None

    async def create_analysis_request(
        self,
        client_id: str,
        services: list[str],
        contact_uid: Optional[str] = None,
        patient_uid: Optional[str] = None,
        doctor_name: Optional[str] = None,
        doctor_crm: Optional[str] = None,
        patient_fullname: Optional[str] = None,
        mrn: Optional[str] = None,
        ar_id: Optional[str] = None,
    ) -> dict:
        """Cria uma AnalysisRequest via endpoint custom (bypass @@API/create)"""
        payload = {
            "client_id": client_id,
            "services": services,
            "contact_id": None,
            "patient_name": patient_fullname,
            "mrn": mrn,
            "title": doctor_name,
            "ar_id": ar_id,
        }
        result = await self._post("/@@hgumba-create-ar", data=payload)
        logger.info("AR criada: %s", result.get("id", result))
        return result

    async def set_analysis_result(
        self,
        analysis_request_id: str,
        service_keyword: str,
        result_value: str,
        client_id: str = "hgu",
        machine_name: str = "desconhecido",
    ) -> dict:
        """Define o resultado de uma análise via v1 API, com rastro de auditoria"""
        search = await self._get("/@@API/senaite/v1/search", params={
            "portal_type": "Analysis",
            "getKeyword": service_keyword,
            "parent_path": f"/senaite/clients/{client_id}/{analysis_request_id}",
        })
        items = search.get("items", [])
        if not items:
            logger.warning("Analysis não encontrada: AR=%s keyword=%s", analysis_request_id, service_keyword)
            return {"success": False, "message": "Analysis not found"}
        uid = items[0].get("uid")
        result = await self._post("/@@API/senaite/v1/update", params={
            "uid": uid,
            "Result": str(result_value),
        })
        machine_remark = f"[AUDITORIA] Resultado importado automaticamente via ASTM E1394. Fonte: {machine_name}."
        try:
            await self._post("/@@hgumba-set-remark", data={
                "client_id": client_id,
                "ar_id": analysis_request_id,
                "remarks": machine_remark,
            })
        except Exception as e:
            logger.warning("Falha ao registrar Remark de auditoria: %s", e)
        logger.info("Result set: AR=%s keyword=%s valor=%s fonte=%s uid=%s", analysis_request_id, service_keyword, result_value, machine_name, uid)
        return result

    async def get_ar_pdf(self, ar_id: str, client_id: str = "hgu") -> bytes:
        """Obtém o PDF do CDM de uma AnalysisRequest"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/clients/{client_id}/{ar_id}/@@cdm-pdf",
                headers={"Authorization": self.auth_header},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.content


senaite = SenaiteClient()
