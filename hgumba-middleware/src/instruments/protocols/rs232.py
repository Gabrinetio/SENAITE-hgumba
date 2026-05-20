# -*- coding: utf-8 -*-
import logging
from typing import List, Optional, Tuple

from instruments.models import AmostraProcessada, ResultadoExameInstrumento

logger = logging.getLogger("rs232.parser")

LF = b"\x0A"
CR = b"\x0D"
CRLF = b"\x0D\x0A"


def extrair_linhas(data: bytes) -> Tuple[List[bytes], bytes]:
    """Extrai linhas completas de dados RS-232, retornando (linhas, residuo).

    Lida com CR, LF, CRLF como terminadores de linha.
    """
    linhas = []
    buf = data
    while buf:
        idx_crlf = buf.find(CRLF)
        idx_lf = buf.find(LF)
        idx_cr = buf.find(CR)

        if idx_crlf != -1 and (idx_crlf <= idx_lf or idx_lf == -1) and (idx_crlf <= idx_cr or idx_cr == -1):
            linha = buf[:idx_crlf]
            if linha:
                linhas.append(linha)
            buf = buf[idx_crlf + 2 :]
        elif idx_lf != -1 and (idx_lf <= idx_cr or idx_cr == -1):
            linha = buf[:idx_lf]
            if linha:
                linhas.append(linha)
            buf = buf[idx_lf + 1 :]
        elif idx_cr != -1:
            linha = buf[:idx_cr]
            if linha:
                linhas.append(linha)
            buf = buf[idx_cr + 1 :]
        else:
            break
    return linhas, buf


def _parse_valor(raw: str) -> str:
    return raw.strip()


class RS232Parser:
    """Parser para instrumentos que usam protocolo RS-232 raw (linhas de texto).

    Sem framing STX/ETX — cada linha terminada por CR/LF é um registro.
    Formato esperado por linha: TIPO,<dados>
    Onde TIPO pode ser: H (header), P (patient), O (order), R (result), L (terminator)
    Formato similar ao ASTM E1394 sem a camada de enlace E1381.
    """

    def __init__(self, machine_name: str):
        self.machine_name = machine_name
        self._reset()

    def _reset(self) -> None:
        self._header = {}
        self._patient = {}
        self._order = {}
        self._results = []
        self._comment = {}

    def alimentar(self, payload: str) -> List[AmostraProcessada]:
        """Processa payload RS-232 (texto), retornando amostras."""
        amostras = []
        payload = payload.replace("\r\n", "\n").replace("\r", "\n")
        linhas = [l.strip() for l in payload.split("\n") if l.strip()]

        for linha in linhas:
            if not linha:
                continue
            tipo = linha.strip().upper()
            dados = ""
            if "," in linha:
                tipo, _, dados = linha.partition(",")
                tipo = tipo.strip().upper()

            if tipo == "H":
                self._reset()
                self._header = {"modelo": _parse_valor(dados)}
            elif tipo == "P":
                parts = [p.strip() for p in dados.split(",")]
                self._patient = {
                    "patient_id": parts[0] if len(parts) > 0 else "",
                    "patient_name": parts[1] if len(parts) > 1 else "",
                }
            elif tipo == "O":
                parts = [p.strip() for p in dados.split(",")]
                self._order = {
                    "sample_id": parts[0] if len(parts) > 0 else "",
                }
            elif tipo == "R":
                parts = [p.strip() for p in dados.split(",")]
                resultado = ResultadoExameInstrumento(
                    keyword=parts[0] if len(parts) > 0 else "",
                    valor=parts[1] if len(parts) > 1 else "",
                    unidade=parts[2] if len(parts) > 2 else None,
                    flag_anormalidade=parts[3] if len(parts) > 3 else None,
                )
                self._results.append(resultado)
                if not self._order.get("sample_id") and parts:
                    self._order["sample_id"] = f"RS232-{self.machine_name}"
            elif tipo == "L":
                amostra = self.extrair_amostra()
                if amostra:
                    amostras.append(amostra)
                self._reset()

        amostra = self.extrair_amostra()
        if amostra:
            amostras.append(amostra)
        return amostras

    def extrair_amostra(self) -> Optional[AmostraProcessada]:
        sample_id = self._order.get("sample_id", "")
        if not sample_id and not self._results:
            return None
        if not sample_id:
            sample_id = f"RS232-{self.machine_name}"
        return AmostraProcessada(
            sample_id=sample_id,
            machine_name=self.machine_name,
            patient_name=self._patient.get("patient_name"),
            patient_id=self._patient.get("patient_id"),
            resultados=self._results,
        )
