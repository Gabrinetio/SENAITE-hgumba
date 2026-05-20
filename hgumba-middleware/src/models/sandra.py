from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ExameSolicitado(BaseModel):
    codigo_catserv: str = Field(..., description="Código do exame na tabela do Exército")
    descricao: str
    urgente: bool = False


class OrdemServicoSANDRA(BaseModel):
    """Payload recebido quando um médico pede exames no SANDRA"""
    id_pedido: str
    cpf_paciente: str = Field(..., pattern=r"^\d{11}$")
    nome_paciente: str
    medico_solicitante: str
    crm_solicitante: str
    data_solicitacao: datetime
    exames: List[ExameSolicitado]


class ResultadoExameSANDRA(BaseModel):
    """Payload enviado de volta ao SANDRA com o laudo"""
    id_pedido: str
    cpf_paciente: str
    analysis_request_id: str
    pdf_laudo_base64: str
    data_publicacao: datetime
    observacoes: Optional[str] = None
