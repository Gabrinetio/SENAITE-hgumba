"""
Parser ASTM E1381/E1394 para interfaceamento com analisadores laboratoriais.

E1381 (enlace):
  STX (0x02) ... ETX (0x03) + checksum 2 hex

E1394 (mensagem):
  Registros separados por <CR> (0x0D)
  Campos separados por "|", subcampos por "^"
  Tipos de registro: H, P, O, R, C, L, Q, M
"""

import logging
from typing import List, Optional, Tuple

from instruments.models import AmostraProcessada, ResultadoExameInstrumento

logger = logging.getLogger("astm.parser")

# Constantes de framing
STX = b"\x02"
ETX = b"\x03"
ACK = b"\x06"
NAK = b"\x15"
ENQ = b"\x05"
EOT = b"\x04"
CR = b"\x0D"
LF = b"\x0A"


def _calc_checksum(frame: bytes) -> str:
    """Calcula checksum ASTM: soma de todos os bytes entre STX e ETX, pega low byte, formata hex"""
    soma = sum(frame)
    return f"{soma & 0xFF:02X}"


def validar_frame(data: bytes) -> Tuple[bool, Optional[bytes]]:
    """Valida um frame ASTM E1381: STX ... ETX + checksum.
    Retorna (valido, payload_sem_stx_etx_checksum ou None)
    """
    if not data.startswith(STX):
        return False, None
    etx_pos = data.find(ETX, 1)
    if etx_pos == -1:
        return False, None
    payload = data[1:etx_pos]
    received_cs = data[etx_pos + 1 : etx_pos + 3].decode("ascii", errors="ignore").upper()
    expected_cs = _calc_checksum(payload)
    if received_cs != expected_cs:
        logger.warning("Checksum mismatch: received=%s expected=%s", received_cs, expected_cs)
        return False, None
    return True, payload


def montar_frame(payload: bytes) -> bytes:
    """Monta um frame ASTM E1381 completo (STX + payload + ETX + checksum)"""
    cs = _calc_checksum(payload)
    return STX + payload + ETX + cs.encode("ascii")


def _parse_campo(campo: str, nivel: int = 0) -> str:
    """Limpa e normaliza um campo ASTM"""
    return campo.strip() if campo else ""


class ASTM1394Parser:
    """Parser de mensagens ASTM E1394 (conteúdo semântico)"""

    def __init__(self, machine_name: str):
        self.machine_name = machine_name
        self.records = []  # lista de (tipo, campos)
        self._reset()

    def _reset(self) -> None:
        self.records = []
        self._header = {}
        self._patient = {}
        self._order = {}
        self._results = []
        self._comment = {}

    @staticmethod
    def _extrair_tipo(linha: str) -> Tuple[str, str]:
        """Extrai (tipo, resto_da_linha) de um registro ASTM.
        O tipo é a primeira letra após o(s) dígito(s) de sequência.
        Ex: '5L|1|N' → ('L', '|1|N')
            '15H|...' → ('H', '|...')
        """
        body = linha
        while body and body[0].isdigit():
            body = body[1:]
        if not body:
            return "", ""
        return body[0], body[1:]

    def alimentar(self, payload: str) -> List[AmostraProcessada]:
        """Alimenta o parser com o payload UTF-8 decodificado.
        Retorna lista de amostras completas encontradas (uma por grupo H...L).
        """
        amostras = []
        linhas = payload.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            tipo, resto = self._extrair_tipo(linha)
            if not tipo:
                continue
            campos = resto.split("|") if resto else [""]
            campos = [_parse_campo(c) for c in campos]
            self.records.append((tipo, campos))
            self._dispatch(tipo, campos)
            # Terminator L: extrai amostra e reseta para o próximo grupo
            if tipo == "L":
                amostra = self.extrair_amostra()
                if amostra:
                    amostras.append(amostra)
                self._reset()
        return amostras

    def _dispatch(self, tipo: str, campos: List[str]) -> None:
        if tipo == "H":
            self._parse_header(campos)
        elif tipo == "P":
            self._parse_patient(campos)
        elif tipo == "O":
            self._parse_order(campos)
        elif tipo == "R":
            self._parse_result(campos)
        elif tipo == "C":
            self._parse_comment(campos)
        elif tipo == "L":
            self._parse_terminator(campos)
        elif tipo == "Q":
            self._parse_query(campos)
        elif tipo == "M":
            self._parse_manufacturer(campos)

    def _parse_header(self, c: List[str]) -> None:
        r"""H|^&|delimitador_def|sender_id|..."""
        # c[0] é vazio (antes do primeiro |), campos começam em c[1]
        self._header = {
            "tipo_mensagem": c[1] if len(c) > 1 else "",
            "delimitadores": c[2] if len(c) > 2 else "",
            "sender_id": c[4] if len(c) > 4 else "",
        }

    def _parse_patient(self, c: List[str]) -> None:
        """P|seq|patient_id|patient_name|mother_maiden|birth_date|sex|..."""
        # ASTM E1394: Field 3=PatientID, Field 4=PatientName
        self._patient = {
            "sequence": c[1],
            "patient_id": c[2] if len(c) > 2 else "",
            "patient_name": c[3] if len(c) > 3 else "",
        }

    def _parse_order(self, c: List[str]) -> None:
        """O|1|sample_id|...|universal_test_id|..."""
        # c[0]=vazio, c[1]=sequence, c[2]=sample_id, c[4]=universal_test_id
        utid = c[4] if len(c) > 4 else ""
        parts = utid.split("^") if utid else ["", ""]
        self._order = {
            "sequence": c[1],
            "sample_id": c[2] if len(c) > 2 else "",
            "codigo_exame": parts[0] if len(parts) > 0 else "",
            "nome_exame": parts[1] if len(parts) > 1 else "",
        }

    def _parse_result(self, c: List[str]) -> None:
        """R|seq|universal_test_id|valor|result_type|unidade|ref_range|flag|..."""
        # ASTM E1394: c[1]=seq, c[2]=test_id, c[3]=valor, c[4]=type,
        # c[5]=unidade, c[6]=ref_range, c[7]=abnormal_flag
        utid = c[2] if len(c) > 2 else ""
        parts = utid.split("^") if utid else ["", ""]
        resultado = ResultadoExameInstrumento(
            keyword=parts[-1] if parts else "",
            valor=c[3] if len(c) > 3 else "",
            unidade=c[5] if len(c) > 5 else "",
            flag_anormalidade=c[7] if len(c) > 7 else None,
        )
        self._results.append(resultado)

    def _parse_comment(self, c: List[str]) -> None:
        self._comment = {"texto": c[1] if len(c) > 1 else ""}

    def _parse_terminator(self, c: List[str]) -> None:
        pass

    def _parse_query(self, c: List[str]) -> None:
        pass

    def _parse_manufacturer(self, c: List[str]) -> None:
        pass

    def extrair_amostra(self) -> Optional[AmostraProcessada]:
        """Constrói AmostraProcessada a partir dos registros parseados"""
        sample_id = self._order.get("sample_id", "")
        if not sample_id:
            return None
        return AmostraProcessada(
            sample_id=sample_id,
            machine_name=self.machine_name,
            patient_name=self._patient.get("patient_name"),
            patient_id=self._patient.get("patient_id"),
            resultados=self._results,
        )
