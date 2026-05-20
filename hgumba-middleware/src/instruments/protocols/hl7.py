# -*- coding: utf-8 -*-
import logging
from typing import List, Optional

from instruments.models import AmostraProcessada, ResultadoExameInstrumento

logger = logging.getLogger("hl7.parser")

CR = "\r"
LF = "\n"
SEGMENT_TERM = "\r"


class HL7Parser:
    """Parser de mensagens HL7 v2.x para resultados laboratoriais (ORU^R01).

    Estrutura típica:
      MSH|^~\\&|sender|...|ORU^R01|...
      PID|1|patient_id|||name^...||...
      OBR|1|sample_id^...||test_code^desc|||...
      OBX|1|NM|test_code^desc||value|unit|ref|flag|...
    """

    def __init__(self, machine_name: str):
        self.machine_name = machine_name
        self._reset()

    def _reset(self) -> None:
        self._patient = {}
        self._order = {}
        self._results = []
        self._sample_id = None

    def alimentar(self, payload: str) -> List[AmostraProcessada]:
        """Processa payload HL7. Retorna lista de amostras encontradas."""
        amostras = []
        payload = payload.replace("\r\n", "\r").replace("\n", "\r")
        segments = [s.strip() for s in payload.split(SEGMENT_TERM) if s.strip()]

        for seg in segments:
            if not seg:
                continue
            tipo = seg[:3] if len(seg) >= 3 else ""
            campos = seg.split("|")

            if tipo == "MSH":
                self._reset()
                self._parse_msh(campos)
            elif tipo == "PID":
                self._parse_pid(campos)
            elif tipo == "OBR":
                self._parse_obr(campos)
            elif tipo == "OBX":
                self._parse_obx(campos)

        if self._sample_id:
            amostra = self.extrair_amostra()
            if amostra:
                amostras.append(amostra)
        return amostras

    def _parse_msh(self, c: List[str]) -> None:
        """MSH|^~\\&|sender|...|receiver|...|datetime|||ORU^R01|..."""
        msg_type_full = c[8] if len(c) > 8 else ""
        parts = msg_type_full.split("^")
        self._msg_type = parts[0] if parts else ""
        self._trigger = parts[1] if len(parts) > 1 else ""

    def _parse_pid(self, c: List[str]) -> None:
        """PID|1|patient_id_ext||patient_id_int||name^...|..."""
        name_field = c[5] if len(c) > 5 else ""
        name_parts = name_field.split("^")
        given = name_parts[1] if len(name_parts) > 1 else ""
        family = name_parts[0] if name_parts else ""
        full_name = f"{given} {family}".strip() if given or family else name_field
        raw_id = c[3] if len(c) > 3 else (c[2] if len(c) > 2 else "")
        # PID-3 is a list of CX: first repetition's first component is the ID
        patient_id = raw_id.split("^")[0] if raw_id else ""
        self._patient = {
            "patient_id": patient_id,
            "patient_name": full_name,
        }

    def _parse_obr(self, c: List[str]) -> None:
        """OBR|1|sample_id^...||test_code^desc|..."""
        sample_field = c[2] if len(c) > 2 else ""
        sample_parts = sample_field.split("^")
        self._sample_id = sample_parts[0] if sample_parts else sample_field
        self._results = []
        self._order = {
            "sample_id": self._sample_id,
        }

    def _parse_obx(self, c: List[str]) -> None:
        """OBX|seq|type|test_code^desc||value|unit|ref|flag|..."""
        test_field = c[3] if len(c) > 3 else ""
        test_parts = test_field.split("^")
        keyword = test_parts[-1] if test_parts else ""
        resultado = ResultadoExameInstrumento(
            keyword=keyword,
            valor=c[5] if len(c) > 5 else "",
            unidade=c[6] if len(c) > 6 else "",
            flag_anormalidade=c[8] if len(c) > 8 else None,
        )
        self._results.append(resultado)

    def extrair_amostra(self) -> Optional[AmostraProcessada]:
        if not self._sample_id:
            return None
        return AmostraProcessada(
            sample_id=self._sample_id,
            machine_name=self.machine_name,
            patient_name=self._patient.get("patient_name"),
            patient_id=self._patient.get("patient_id"),
            resultados=self._results,
        )
