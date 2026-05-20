# -*- coding: utf-8 -*-
import pytest

from instruments.protocols.astm import (
    STX, ETX,
    _calc_checksum, validar_frame, montar_frame,
    ASTM1394Parser,
)
from instruments.models import AmostraProcessada, ResultadoExameInstrumento


class TestCalcChecksum:
    def test_simple_payload(self):
        cs = _calc_checksum(b"H|^&|||BS200||||||||")
        assert isinstance(cs, str)
        assert len(cs) == 2
        assert all(c in "0123456789ABCDEF" for c in cs)

    def test_empty_payload(self):
        cs = _calc_checksum(b"")
        assert cs == "00"

    def test_known_value(self):
        cs = _calc_checksum(b"1H|^&|||BS200||||||||")
        assert cs == f"{sum(b'1H|^&|||BS200||||||||') & 0xFF:02X}"


class TestValidarFrame:
    def test_valid_frame(self):
        payload = b"H|^&|||BS200||||||||"
        frame = montar_frame(payload)
        valido, parsed = validar_frame(frame)
        assert valido is True
        assert parsed == payload

    def test_invalid_no_stx(self):
        valido, parsed = validar_frame(b"no_stx")
        assert valido is False
        assert parsed is None

    def test_invalid_no_etx(self):
        valido, parsed = validar_frame(STX + b"no etx")
        assert valido is False
        assert parsed is None

    def test_invalid_checksum(self):
        frame = STX + b"payload" + ETX + b"FF"
        valido, parsed = validar_frame(frame)
        assert valido is False
        assert parsed is None

    def test_checksum_mismatch(self):
        payload = b"test"
        frame = montar_frame(payload)
        # Corrupt: troca o meio do payload (muda checksum esperado)
        corrupted = frame[:2] + b"X" + frame[3:]
        valido, parsed = validar_frame(corrupted)
        assert valido is False
        assert parsed is None

    def test_multi_byte_payload(self):
        payload = b"1H|^&|||BS200||||||||\r2P|1||PAT001||JOAO^SILVA\r"
        frame = montar_frame(payload)
        valido, parsed = validar_frame(frame)
        assert valido is True
        assert parsed == payload


class TestMontarFrame:
    def test_roundtrip(self):
        payload = b"H|^&|||BS200"
        frame = montar_frame(payload)
        assert frame.startswith(STX)
        assert ETX in frame
        valido, parsed = validar_frame(frame)
        assert valido is True
        assert parsed == payload

    def test_structure(self):
        payload = b"test"
        frame = montar_frame(payload)
        assert frame[0:1] == STX
        assert frame[1:-3] == payload
        assert frame[-3:-2] == ETX
        assert len(frame[-2:]) == 2


class TestASTM1394Parser:
    def test_parse_header(self):
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar("1H|^&|||BS200||||||||\r")
        assert len(amostras) == 0
        assert len(parser.records) == 1
        assert parser.records[0][0] == "H"

    def test_parse_complete_sample(self):
        payload = (
            "1H|^&|||BS200||||||||\r"
            "2P|1|MRN001|MARIA^SILVA||19800101|F\r"
            "3O|1|HGU-AR-001||^^^GLI001||||||||||||||||||||||\r"
            "4R|1|^^^GLI001|105.5|N|mg/dL||H||F||user||20260519080000\r"
            "5L|1|N\r"
        )
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        amostra = amostras[0]
        assert isinstance(amostra, AmostraProcessada)
        assert amostra.sample_id == "HGU-AR-001"
        assert amostra.machine_name == "BS200"
        assert amostra.patient_name == "MARIA^SILVA"
        assert amostra.patient_id == "MRN001"
        assert len(amostra.resultados) == 1
        res = amostra.resultados[0]
        assert isinstance(res, ResultadoExameInstrumento)
        assert res.keyword == "GLI001"
        assert res.valor == "105.5"
        assert res.unidade == "mg/dL"
        assert res.flag_anormalidade == "H"

    def test_multiple_samples(self):
        payload = (
            "1H|^&|||BS200||||||||\r"
            "2P|1||MRN001||MARIA^SILVA\r"
            "3O|1|HGU-AR-001||^^^GLI001\r"
            "4R|1|^^^GLI001|105.5|N|mg/dL\r"
            "5L|1|N\r"
            "6H|^&|||BS200||||||||\r"
            "7P|1||MRN002||JOSE^SANTOS\r"
            "8O|1|HGU-AR-002||^^^HEM001\r"
            "9R|1|^^^HEM001|5.2|N|milhoes/mm3\r"
            "10L|1|N\r"
        )
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 2
        assert amostras[0].sample_id == "HGU-AR-001"
        assert amostras[1].sample_id == "HGU-AR-002"
        assert amostras[0].resultados[0].keyword == "GLI001"
        assert amostras[1].resultados[0].keyword == "HEM001"

    def test_parse_with_crlf(self):
        payload = "1O|1|SAMPLE||^^^TEST\r\n2R|1|^^^TEST|10\r\n3L|1|N\r\n"
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert amostras[0].sample_id == "SAMPLE"

    def test_extrair_tipo_com_sequencia(self):
        parser = ASTM1394Parser("test")
        tipo, resto = parser._extrair_tipo("5L|1|N")
        assert tipo == "L"
        assert resto == "|1|N"

    def test_extrair_tipo_sem_sequencia(self):
        parser = ASTM1394Parser("test")
        tipo, resto = parser._extrair_tipo("H|^&")
        assert tipo == "H"
        assert resto == "|^&"

    def test_extrair_tipo_vazio(self):
        parser = ASTM1394Parser("test")
        tipo, resto = parser._extrair_tipo("")
        assert tipo == ""
        assert resto == ""

    def test_extrair_tipo_apenas_digitos(self):
        parser = ASTM1394Parser("test")
        tipo, resto = parser._extrair_tipo("123")
        assert tipo == ""
        assert resto == ""

    def test_order_sample_id(self):
        payload = "1O|1|HGU-AR-001||^^^GLI001\r2L|1|N\r"
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert amostras[0].sample_id == "HGU-AR-001"

    def test_result_with_flag_anormalidade(self):
        payload = (
            "1O|1|SAMPLE001||^^^GLU\r"
            "2R|1|^^^GLU|320|N|mg/dL|70-110|HH\r"
            "3L|1|N\r"
        )
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        res = amostras[0].resultados[0]
        assert res.flag_anormalidade == "HH"

    def test_empty_payload(self):
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar("")
        assert len(amostras) == 0

    def test_no_terminator(self):
        payload = (
            "1H|^&|||BS200\r"
            "2P|1||MRN001||MARIA\r"
            "3O|1|HGU-AR-001||^^^GLI001\r"
        )
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 0

    def test_multiple_results_per_sample(self):
        payload = (
            "1O|1|SAMPLE001||^^^PANEL\r"
            "2R|1|^^^GLU|100|N|mg/dL\r"
            "3R|2|^^^HDL|45|N|mg/dL\r"
            "4R|3|^^^LDL|120|N|mg/dL\r"
            "5L|1|N\r"
        )
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert len(amostras[0].resultados) == 3
        assert amostras[0].resultados[0].keyword == "GLU"
        assert amostras[0].resultados[1].keyword == "HDL"
        assert amostras[0].resultados[2].keyword == "LDL"

    def test_manufacturer_record_ignored(self):
        payload = "1M|1|VENDOR|EQUIP\r2O|1|SAMPLE||^^^TEST\r3L|1|N\r"
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert amostras[0].sample_id == "SAMPLE"

    def test_query_record_ignored(self):
        payload = "1Q|1|U||ALL\r2O|1|SAMPLE||^^^TEST\r3L|1|N\r"
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert amostras[0].sample_id == "SAMPLE"

    def test_incomplete_frame_after_etx(self):
        payload = "1O|1|SAMPLE001||^^^TEST\r2L|1|N\r"
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert amostras[0].sample_id == "SAMPLE001"

    def test_parser_lida_com_buffer_grande(self):
        """Payload grande não deve crashar o parser"""
        many = "\r".join(f"{i}R|{i}|^^^TEST{i}|{i}.{i}" for i in range(500))
        payload = f"1O|1|SAMPLE||^^^PANEL\r{many}\r501L|1|N\r"
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert len(amostras[0].resultados) == 500

    def test_reset_between_groups(self):
        payload = (
            "1O|1|SAMPLE-A||^^^GLU\r"
            "2R|1|^^^GLU|100\r"
            "3L|1|N\r"
            "4O|1|SAMPLE-B||^^^HDL\r"
            "5L|1|N\r"
        )
        parser = ASTM1394Parser("BS200")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 2
        assert amostras[0].sample_id == "SAMPLE-A"
        assert amostras[1].sample_id == "SAMPLE-B"
        assert len(amostras[0].resultados) == 1
        assert amostras[1].resultados == []
