import base64
import logging
from fastapi import APIRouter, HTTPException, Depends
from models.senaite import WebhookLaudoPayload
from clients.senaite_api import senaite
from clients.exercito_api import exercito
from logger import audit_logger
from auth import verify_api_key

logger = logging.getLogger("router.webhooks")
router = APIRouter(prefix="/api/v1/senaite", tags=["SENAITE Webhooks"],
                   dependencies=[Depends(verify_api_key)])


@router.post("/webhook/laudo_publicado")
async def senaite_laudo_publicado(payload: WebhookLaudoPayload) -> dict:
    """
    Webhook chamado pelo SENAITE quando um exame muda para o estado 'published'.
    Fluxo:
    1. Captura o ID da AR.
    2. Busca o PDF do laudo no SENAITE.
    3. Envia o PDF e dados estruturados de volta para o prontuário no SANDRA.
    """
    logger.info("Webhook laudo publicado: AR %s (status: %s)", payload.analysis_request_id, payload.review_state)

    if payload.review_state != "published":
        return {"status": "ignorado", "motivo": "Apenas laudos publicados são processados"}

    # Obtém o PDF do laudo
    try:
        pdf_bytes = await senaite.get_ar_pdf(payload.analysis_request_id)
        pdf_b64 = base64.b64encode(pdf_bytes).decode()
    except Exception as e:
        logger.error("Falha ao obter PDF da AR %s: %s", payload.analysis_request_id, e)
        audit_logger.error("Falha ao obter PDF do laudo", extra={
            "audit_data": {
                "evento": "webhook_pdf_falha",
                "analysis_request_id": payload.analysis_request_id,
                "erro": str(e),
            }
        })
        raise HTTPException(status_code=502, detail="Falha ao obter PDF do SENAITE")

    # Envia de volta ao SANDRA
    sucesso = await exercito.notificar_sandra(
        id_pedido=payload.analysis_request_id,
        pdf_base64=pdf_b64,
        ar_id=payload.analysis_request_id,
    )
    audit_logger.info("Laudo publicado processado", extra={
        "audit_data": {
            "evento": "laudo_publicado",
            "analysis_request_id": payload.analysis_request_id,
            "sandra_notificado": sucesso,
            "via": "webhook",
        }
    })
    if not sucesso:
        logger.warning("Falha ao notificar SANDRA para AR %s", payload.analysis_request_id)

    return {
        "status": "processado",
        "analysis_request_id": payload.analysis_request_id,
        "sandra_notificado": sucesso,
    }


@router.get("/health")
async def health_senaite() -> dict:
    """Health check da conexão com o SENAITE"""
    ok = await senaite.check_health()
    return {"senaite_online": ok}
