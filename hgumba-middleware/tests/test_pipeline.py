"""Teste de integração: frames ASTM → parser → AmostraProcessada"""
import pytest

from instruments.protocols.astm import (
    STX, ETX,
    montar_frame, validar_frame, ASTM1394Parser,
)


def _frame_from_string(payload_str: str) -> bytes:
    """Monta frame E1381 a partir de string"""
    return montar_frame(payload_str.encode("utf-8"))


def _frame_emulador_3_amostras() -> list[bytes]:
    """Gera os 15 frames do emulador BS200 (3 grupos H/P/O/R/L)"""
    grupo1 = (
        "1H|^&|||BS200||||||||\r"
        "2P|1|MRN000001|SGT MENDES^JOAO||19800101|M\r"
        "3O|1|HGU-AR-001||^^^GLI001\r"
        "4R|1|^^^GLI001|105.5|N|mg/dL||H\r"
        "5L|1|N\r"
    )
    grupo2 = (
        "6H|^&|||BS200||||||||\r"
        "7P|1|MRN000002|CB MOURA^MARIA||19800101|M\r"
        "8O|1|HGU-AR-002||^^^HEM001\r"
        "9R|1|^^^HEM001|5.2|N|milhoes/mm3\r"
        "10L|1|N\r"
    )
    grupo3 = (
        "11H|^&|||BS200||||||||\r"
        "12P|1|MRN000003|CAP OLIVEIRA^CARLOS||19800101|M\r"
        "13O|1|HGU-AR-003||^^^LIP001\r"
        "14R|1|^^^LIP001|320|N|mg/dL||HH\r"
        "15L|1|N\r"
    )
    return [
        _frame_from_string(grupo1),
        _frame_from_string(grupo2),
        _frame_from_string(grupo3),
    ]


class TestPipelineEmuladorCompleto:
    """Testa o pipeline completo com dados reais do emulador"""

    def test_3_frames_validos(self):
        frames = _frame_emulador_3_amostras()
        assert len(frames) == 3
        for i, frame in enumerate(frames):
            valido, payload = validar_frame(frame)
            assert valido is True, f"Frame {i+1} invalido"

    def test_parse_3_amostras(self):
        parser = ASTM1394Parser("BS200")
        todas_amostras = []

        frames = _frame_emulador_3_amostras()
        for frame in frames:
            valido, payload = validar_frame(frame)
            assert valido is True
            amostras = parser.alimentar(payload.decode("utf-8"))
            todas_amostras.extend(amostras)

        assert len(todas_amostras) == 3

        # Verifica primeira amostra
        a1 = todas_amostras[0]
        assert a1.sample_id == "HGU-AR-001"
        assert a1.machine_name == "BS200"
        assert a1.patient_id == "MRN000001"
        assert a1.patient_name == "SGT MENDES^JOAO"
        assert len(a1.resultados) == 1
        assert a1.resultados[0].keyword == "GLI001"
        assert a1.resultados[0].valor == "105.5"
        assert a1.resultados[0].unidade == "mg/dL"
        assert a1.resultados[0].flag_anormalidade == "H"

        # Verifica segunda amostra
        a2 = todas_amostras[1]
        assert a2.sample_id == "HGU-AR-002"
        assert a2.patient_id == "MRN000002"
        assert a2.resultados[0].keyword == "HEM001"
        assert a2.resultados[0].valor == "5.2"
        assert a2.resultados[0].unidade == "milhoes/mm3"

        # Verifica terceira amostra
        a3 = todas_amostras[2]
        assert a3.sample_id == "HGU-AR-003"
        assert a3.patient_id == "MRN000003"
        assert a3.resultados[0].keyword == "LIP001"
        assert a3.resultados[0].valor == "320"
        assert a3.resultados[0].unidade == "mg/dL"
        assert a3.resultados[0].flag_anormalidade == "HH"


class TestPipelineBuffering:
    """Testa o comportamento do buffer no listener"""

    def test_frame_com_residuos_crlf(self):
        """
        Simula o bug corrigido: \r\n residual de frames anteriores
        no buffer antes do STX.
        """
        dados_brutos = b"\r\n" + montar_frame(b"1O|1|SAMPLE||^^^GLU\r2L|1|N\r")

        stx_pos = dados_brutos.find(STX)
        if stx_pos > 0:
            chunk = dados_brutos[stx_pos:]
        else:
            chunk = dados_brutos

        valido, payload = validar_frame(chunk)
        assert valido is True
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload.decode("utf-8"))
        assert len(amostras) == 1
        assert amostras[0].sample_id == "SAMPLE"

    def test_envia_sequencial_3_grupos(self):
        """Simula o envio real: ENQ → frames → EOT para cada amostra"""
        grupos = [
            ("HGU-AR-001", [("GLI001", "105.5")]),
            ("HGU-AR-002", [("HEM001", "5.2")]),
            ("HGU-AR-003", [("LIP001", "320")]),
        ]
        payloads_bytes = []
        for g in grupos:
            linhas = [f"1O|1|{g[0]}||^^^{g[1][0][0]}"]
            for i, (kw, val) in enumerate(g[1], 1):
                linhas.append(f"{i+1}R|{i}|^^^{kw}|{val}")
            linhas.append(f"{len(linhas)+1}L|1|N")
            payload_str = "\r".join(linhas)
            payloads_bytes.append(montar_frame(payload_str.encode()))

        for i, fb in enumerate(payloads_bytes):
            valido, payload = validar_frame(fb)
            assert valido is True, f"Frame {i} invalido"

        parser = ASTM1394Parser("BS200")
        todas = []
        for fb in payloads_bytes:
            valido, payload = validar_frame(fb)
            amostras = parser.alimentar(payload.decode("utf-8"))
            todas.extend(amostras)

        assert len(todas) == 3
        assert todas[0].sample_id == "HGU-AR-001"
        assert todas[1].sample_id == "HGU-AR-002"
        assert todas[2].sample_id == "HGU-AR-003"
