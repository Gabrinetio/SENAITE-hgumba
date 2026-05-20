from typing import Optional, Union

from instruments.protocols.astm import ASTM1394Parser
from instruments.protocols.hl7 import HL7Parser
from instruments.protocols.rs232 import RS232Parser


def criar_parser(protocolo: str, machine_name: str) -> Optional[Union[ASTM1394Parser, HL7Parser, RS232Parser]]:
    """Factory: retorna parser apropriado conforme protocolo (ASTM, HL7, RS232)."""
    p = protocolo.upper()
    if p == "ASTM":
        return ASTM1394Parser(machine_name)
    elif p == "HL7":
        return HL7Parser(machine_name)
    elif p == "RS232":
        return RS232Parser(machine_name)
    return None
