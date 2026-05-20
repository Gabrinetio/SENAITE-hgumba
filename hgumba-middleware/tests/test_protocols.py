from instruments.protocols.hl7 import HL7Parser
from instruments.protocols.rs232 import RS232Parser, extrair_linhas


class TestHL7Parser:
    """Parser HL7 v2.x para ORU^R01 (resultados laboratoriais)"""

    def test_parse_oru_completo(self):
        msg = (
            "MSH|^~\\&|SYS|LAB|REC|LAB|202605201200||ORU^R01|MSG001|P|2.3\r"
            "PID|1||PAT123^^^LAB||SMITH^JOHN^^^||19800101|M\r"
            "OBR|1|SMP001^^^LAB||GLU^Glucose|||202605201200\r"
            "OBX|1|NM|GLU^Glucose||95|mg/dL|70-110|N||F\r"
        )
        parser = HL7Parser("Testador_HL7")
        amostras = parser.alimentar(msg)
        assert len(amostras) == 1
        a = amostras[0]
        assert a.sample_id == "SMP001"
        assert a.machine_name == "Testador_HL7"
        assert a.patient_name == "JOHN SMITH"
        assert a.patient_id == "PAT123"
        assert len(a.resultados) == 1
        r = a.resultados[0]
        assert r.keyword == "Glucose"
        assert r.valor == "95"
        assert r.unidade == "mg/dL"
        assert r.flag_anormalidade == "N"

    def test_multiplos_resultados(self):
        msg = (
            "MSH|^~\\&|SYS|LAB|REC|LAB|202605201200||ORU^R01|M001|P|2.3\r"
            "PID|1||P123||DOE^JANE\r"
            "OBR|1|SMP001||BIO^Bioquimica\r"
            "OBX|1|NM|GLU^Glucose||90|mg/dL|70-110|N\r"
            "OBX|2|NM|CREA^Creatinina||1.0|mg/dL|0.5-1.2|N\r"
            "OBX|3|NM|URE^Ureia||35|mg/dL|10-50|N\r"
        )
        parser = HL7Parser("Testador_HL7")
        amostras = parser.alimentar(msg)
        assert len(amostras) == 1
        assert len(amostras[0].resultados) == 3

    def test_sem_obr_retorna_vazio(self):
        msg = "MSH|^~\\&|SYS|LAB|REC|LAB|202605201200||ORU^R01|M001|P|2.3\r"
        parser = HL7Parser("Testador_HL7")
        amostras = parser.alimentar(msg)
        assert len(amostras) == 0

    def test_parse_com_lf(self):
        msg = (
            "MSH|^~\\&|SYS|LAB|REC|LAB|202605201200||ORU^R01|M001|P|2.3\n"
            "PID|1||P123||DOE^JANE\n"
            "OBR|1|SMP001||GLU^Glucose\n"
            "OBX|1|NM|GLU^Glucose||120|mg/dL|70-110|H\n"
        )
        parser = HL7Parser("Testador_HL7")
        amostras = parser.alimentar(msg)
        assert len(amostras) == 1
        assert amostras[0].resultados[0].valor == "120"
        assert amostras[0].resultados[0].flag_anormalidade == "H"

    def test_sample_id_via_obr(self):
        """sample_id extraido do campo OBR-2 (placer order number)"""
        msg = (
            "MSH|^~\\&|SYS|LAB|REC|LAB|202605201200||ORU^R01|M001|P|2.3\r"
            "PID|1||P456||TEST^NAME\r"
            "OBR|1|AR-2026-0001^^^LAB||HEM^Hemograma\r"
            "OBX|1|NM|HEM^Hemoglobina||14.5|g/dL|12-16|N\r"
        )
        parser = HL7Parser("Testador_HL7")
        amostras = parser.alimentar(msg)
        assert len(amostras) == 1
        assert amostras[0].sample_id == "AR-2026-0001"


class TestRS232Parser:
    """Parser RS-232 raw (linhas de texto, sem STX/ETX)"""

    def test_parse_simple(self):
        payload = (
            "H,Mindray BS200\n"
            "P,PAT001,John Smith\n"
            "O,SMP001\n"
            "R,GLU,95,mg/dL,N\n"
            "L\n"
        )
        parser = RS232Parser("RS232_Test")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        a = amostras[0]
        assert a.sample_id == "SMP001"
        assert a.patient_id == "PAT001"
        assert a.patient_name == "John Smith"
        assert len(a.resultados) == 1
        assert a.resultados[0].keyword == "GLU"
        assert a.resultados[0].valor == "95"

    def test_multiplos_resultados_por_amostra(self):
        payload = (
            "H,Sysmex XN550\r"
            "P,PAT002,Jane Doe\r"
            "O,SMP002\r"
            "R,WBC,7.5,10^3/uL,N\r"
            "R,RBC,5.2,10^6/uL,N\r"
            "R,HGB,15.0,g/dL,N\r"
            "L\r"
        )
        parser = RS232Parser("RS232_Test")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert len(amostras[0].resultados) == 3

    def test_varias_amostras(self):
        payload = (
            "H,Roche Cobas\n"
            "P,PAT001,Patient A\n"
            "O,SMP001\n"
            "R,GLU,90,mg/dL,N\n"
            "L\n"
            "P,PAT002,Patient B\n"
            "O,SMP002\n"
            "R,GLU,110,mg/dL,H\n"
            "L\n"
        )
        parser = RS232Parser("RS232_Test")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 2
        assert amostras[0].sample_id == "SMP001"
        assert amostras[1].sample_id == "SMP002"
        assert amostras[0].resultados[0].valor == "90"
        assert amostras[1].resultados[0].valor == "110"

    def test_payload_vazio(self):
        parser = RS232Parser("RS232_Test")
        amostras = parser.alimentar("")
        assert len(amostras) == 0

    def test_sem_terminator_extrai_ao_final(self):
        """sem 'L', parser extrai amostra no final do payload"""
        payload = "R,GLU,100,mg/dL,N\n"
        parser = RS232Parser("RS232_Test")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert amostras[0].sample_id.startswith("RS232-")

    def test_linha_malformada_ignorada(self):
        payload = (
            "H,Test\n"
            "P,PAT001,Name\n"
            "O,SMP001\n"
            "esta linha nao tem virgula\n"
            "R,GLU,100,mg/dL,N\n"
            "L\n"
        )
        parser = RS232Parser("RS232_Test")
        amostras = parser.alimentar(payload)
        assert len(amostras) == 1
        assert len(amostras[0].resultados) == 1


class TestExtrairLinhasRS232:
    """Utilitario de framing RS-232 (extrair_linhas)"""

    def test_lf_terminator(self):
        data = b"linha1\nlinha2\nlinha3\n"
        linhas, resto = extrair_linhas(data)
        assert linhas == [b"linha1", b"linha2", b"linha3"]
        assert resto == b""

    def test_crlf_terminator(self):
        data = b"linha1\r\nlinha2\r\n"
        linhas, resto = extrair_linhas(data)
        assert linhas == [b"linha1", b"linha2"]
        assert resto == b""

    def test_crlf_e_lf_misturado(self):
        data = b"linha1\r\nlinha2\nlinha3\r\n"
        linhas, resto = extrair_linhas(data)
        assert linhas == [b"linha1", b"linha2", b"linha3"]

    def test_residuo_sem_terminador(self):
        data = b"linha1\nlinha2\nlinha"
        linhas, resto = extrair_linhas(data)
        assert linhas == [b"linha1", b"linha2"]
        assert resto == b"linha"

    def test_dados_vazios(self):
        linhas, resto = extrair_linhas(b"")
        assert linhas == []
        assert resto == b""

    def test_linhas_vazias_ignoradas(self):
        data = b"linha1\n\n\nlinha2\n"
        linhas, resto = extrair_linhas(data)
        assert linhas == [b"linha1", b"linha2"]
