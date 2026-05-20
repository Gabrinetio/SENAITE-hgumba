import logging
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

logger = logging.getLogger("auth")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)) -> str:
    if not settings.api_key:
        return "dev_mode"
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado",
        )
    return key
