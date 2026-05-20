from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ResultadoExameInstrumento(BaseModel):
    """Resultado individual vindo do parser ASTM/HL7"""
    keyword: str = Field(..., description="Código do exame (LOINC ou interno do analisador)")
    codigo_catserv: Optional[str] = None
    valor: str
    unidade: Optional[str] = None
    flag_anormalidade: Optional[str] = None  # H=High, L=Low, HH=Critical High, etc.
    data_hora: Optional[datetime] = None


class AmostraProcessada(BaseModel):
    """Payload completo de uma amostra processada por um analisador"""
    sample_id: str = Field(..., description="ID da amostra (código de barras da AR)")
    machine_name: str = Field(..., description="Nome do analisador que gerou o resultado")
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    resultados: List[ResultadoExameInstrumento]
    raw_payload: Optional[str] = None


class InstrumentoConfig(BaseModel):
    nome: str
    host: str = "0.0.0.0"
    porta: int
    protocolo: str = "ASTM"  # ASTM ou HL7
    enabled: bool = True
    description: Optional[str] = None
