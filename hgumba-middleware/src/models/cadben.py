from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class BeneficiarioCADBEN(BaseModel):
    """Dados do beneficiário no CADBEN (Sistema de Cadastro de Beneficiários)"""
    cpf: str = Field(..., pattern=r"^\d{11}$")
    nome: str
    posto_graduacao: Optional[str] = None
    organizacao_militar: Optional[str] = None
    ativo: bool = True
    data_nascimento: Optional[date] = None


class ElegibilidadeResponse(BaseModel):
    cpf: str
    elegivel: bool
    motivo: Optional[str] = None
    beneficiario: Optional[BeneficiarioCADBEN] = None
