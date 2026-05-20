import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import settings
from routers import ingestao, webhooks
from logger import audit_logger

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("hgumba-gateway")

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="Middleware H Gu Marabá",
    description="API Gateway entre SENAITE LIS e Sistemas do Exército (SANDRA, SIRE, CADBEN)",
    version="1.0.0",
    on_startup=[lambda: audit_logger.info("Gateway iniciado", extra={
        "audit_data": {"evento": "gateway_iniciado", "versao": "1.0.0"}
    })],
    on_shutdown=[lambda: audit_logger.info("Gateway finalizado", extra={
        "audit_data": {"evento": "gateway_finalizado"}
    })],
)

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)


class RequestBodySizeMiddleware(BaseHTTPMiddleware):
    """Rejeita payloads acima de 10MB antes de chegar ao router"""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload too large (max 10MB)"},
            )
        return await call_next(request)


app.add_middleware(RequestBodySizeMiddleware)

app.include_router(ingestao.router)
app.include_router(webhooks.router)


@app.get("/health")
async def root_health() -> dict:
    return {"status": "healthy", "service": "hgumba-middleware", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.host, port=settings.port, reload=True)
