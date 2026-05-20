# -*- coding: utf-8 -*-
import logging
from typing import Optional

import httpx
from config import settings
from models.cadben import ElegibilidadeResponse, BeneficiarioCADBEN

logger = logging.getLogger("exercito_api")


class ExercitoAPIClient:
    """Cliente HTTP para APIs mock do Exército (SANDRA, CADBEN, SIRE)"""

    def __init__(self):
        self.sandra_base = settings.sandra_base_url
        self.cadben_base = settings.cadben_base_url
        self.sire_base = settings.sire_base_url
        self.headers = {}

    def _configure_auth(self, base_url: str, api_key: str) -> dict:
        """Monta header de autenticação Bearer se api_key estiver presente"""
        if api_key:
            return {"Authorization": f"Bearer {api_key}"}
        return {}

    async def validar_elegibilidade(self, cpf: str) -> ElegibilidadeResponse:
        """Consulta CADBEN para validar elegibilidade do paciente"""
        if not self.cadben_base:
            logger.info("CADBEN mock: paciente %s elegível (modo desenvolvimento)", cpf)
            return ElegibilidadeResponse(
                cpf=cpf,
                elegivel=True,
                beneficiario=BeneficiarioCADBEN(
                    cpf=cpf,
                    nome="Paciente Mock",
                    posto_graduacao="Sd Mock",
                    organizacao_militar="OM Exemplo",
                    ativo=True,
                ),
            )
        try:
            headers = self._configure_auth(self.cadben_base, settings.cadben_api_key)
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.cadben_base}/api/v1/beneficiarios/{cpf}/elegibilidade",
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                return ElegibilidadeResponse(**resp.json())
        except Exception as e:
            logger.error("CADBEN error: %s", e)
            return ElegibilidadeResponse(cpf=cpf, elegivel=False, motivo="Indisponível")

    async def validar_guia(self, id_pedido: str) -> bool:
        """Consulta SIRE para validar autorização/verba do pedido"""
        if not self.sire_base:
            logger.info("SIRE mock: pedido %s autorizado (modo desenvolvimento)", id_pedido)
            return True
        try:
            headers = self._configure_auth(self.sire_base, settings.sire_api_key)
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.sire_base}/api/v1/guias/{id_pedido}",
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("autorizada", False)
        except Exception as e:
            logger.error("SIRE error: %s", e)
            return False

    async def notificar_sandra(
        self, id_pedido: str, pdf_base64: str, ar_id: str, observacoes: Optional[str] = None
    ) -> bool:
        """Envia o laudo processado de volta ao SANDRA"""
        if not self.sandra_base:
            logger.info(
                "SANDRA mock: laudo %s devolvido para pedido %s (modo desenvolvimento)",
                ar_id, id_pedido,
            )
            return True
        try:
            headers = self._configure_auth(self.sandra_base, settings.sandra_api_key)
            payload = {
                "id_pedido": id_pedido,
                "analysis_request_id": ar_id,
                "pdf_laudo_base64": pdf_base64,
                "observacoes": observacoes,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.sandra_base}/api/v1/resultados",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("SANDRA notification error: %s", e)
            return False


exercito = ExercitoAPIClient()
