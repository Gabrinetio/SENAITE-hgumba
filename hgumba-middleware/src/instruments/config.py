# -*- coding: utf-8 -*-
from typing import List
from instruments.models import InstrumentoConfig


# Mapeamento dos 5 equipamentos exigidos pelo Item 3.2 do TR
# Portas TCP por máquina (ajustar conforme rack serial-to-Ethernet)
INSTRUMENTOS: List[InstrumentoConfig] = [
    InstrumentoConfig(
        nome="Mindray_BS200",
        porta=5001,
        protocolo="ASTM",
        description="Bioquímica - Mindray BS-200",
    ),
    InstrumentoConfig(
        nome="Sysmex_XN550",
        porta=5002,
        protocolo="ASTM",
        description="Hematologia - Sysmex XN-550",
    ),
    InstrumentoConfig(
        nome="Roche_Cobas_e411",
        porta=5003,
        protocolo="ASTM",
        description="Imunoquímica - Roche Cobas e411",
    ),
    InstrumentoConfig(
        nome="Roche_Cobas_c311",
        porta=5004,
        protocolo="ASTM",
        description="Química Clínica - Roche Cobas c311",
    ),
    InstrumentoConfig(
        nome="BioRad_D10",
        porta=5005,
        protocolo="ASTM",
        description="HbA1c - Bio-Rad D-10",
    ),
]
