# -*- coding: utf-8 -*-
import logging

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.sandra import OrdemServicoSANDRA
from clients.exercito_api import exercito
from clients.senaite_api import senaite
from logger import audit_logger
from auth import verify_api_key

logger = logging.getLogger("router.ingestao")
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1/sandra", tags=["SANDRA Ingestão"],
                   dependencies=[Depends(verify_api_key)])


async def processar_pedido(ordem: OrdemServicoSANDRA) -> None:
    """Processa o pedido em background: validações + criação da AR no SENAITE"""
    logger.info("Processando pedido %s em background...", ordem.id_pedido)

    # Validação CADBEN
    elegibilidade = await exercito.validar_elegibilidade(ordem.cpf_paciente)
    if not elegibilidade.elegivel:
        logger.error("Pedido %s: paciente inelegível (%s)", ordem.id_pedido, elegibilidade.motivo)
        audit_logger.error("Pedido rejeitado: paciente inelegível", extra={
            "audit_data": {
                "evento": "pedido_falha", "id_pedido": ordem.id_pedido,
                "motivo": elegibilidade.motivo, "cpf": ordem.cpf_paciente,
            }
        })
        return

    # Validação SIRE
    guia_valida = await exercito.validar_guia(ordem.id_pedido)
    if not guia_valida:
        logger.error("Pedido %s: guia não autorizada pelo SIRE", ordem.id_pedido)
        audit_logger.error("Pedido rejeitado: guia não autorizada pelo SIRE", extra={
            "audit_data": {
                "evento": "pedido_falha", "id_pedido": ordem.id_pedido,
                "motivo": "guia_nao_autorizada",
            }
        })
        return

    # Cria AR no SENAITE
    # TODO: mapear codigo_catserv -> UID do AnalysisService
    services = [ex.codigo_catserv for ex in ordem.exames]
    result = await senaite.create_analysis_request(
        client_id="hgu",
        services=services,
        patient_fullname=ordem.nome_paciente,
        mrn=ordem.cpf_paciente,
        doctor_name=ordem.medico_solicitante,
        doctor_crm=ordem.crm_solicitante,
        ar_id=ordem.id_pedido,
    )
    audit_logger.info("Pedido SANDRA injetado no SENAITE", extra={
        "audit_data": {
            "evento": "pedido_injetado",
            "id_pedido": ordem.id_pedido,
            "cpf_paciente": ordem.cpf_paciente,
            "exames": services,
            "via": "sandra_ingestao",
        }
    })
    logger.info("Pedido %s -> AR criada: %s", ordem.id_pedido, result)


@router.post("/ingestao", status_code=202)
@limiter.limit("100/minute")
async def ingerir_pedido_sandra(
    ordem: OrdemServicoSANDRA,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """
    Endpoint chamado pelo SANDRA quando um médico solicita exames.
    Fluxo:
    1. Recebe o payload validado pelo Pydantic.
    2. (background) Consulta CADBEN para validar elegibilidade.
    3. (background) Consulta SIRE para validar autorização.
    4. (background) Injeta a AnalysisRequest no SENAITE via JSON API.
    """
    logger.info("Ordem SANDRA recebida: %s (paciente %s)", ordem.id_pedido, ordem.cpf_paciente)
    background_tasks.add_task(processar_pedido, ordem)
    return {"status": "aceito", "id_pedido": ordem.id_pedido, "mensagem": "Pedido em processamento"}


@router.get("/health")
async def health_check() -> dict:
    """Health check do router de ingestão SANDRA"""
    return {"status": "ok"}
