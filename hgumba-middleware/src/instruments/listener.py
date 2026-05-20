# -*- coding: utf-8 -*-
import asyncio
import logging
from typing import Optional

from instruments.models import AmostraProcessada, InstrumentoConfig
from instruments.protocols.astm import (
    STX, ETX, ACK, NAK, ENQ, EOT,
    validar_frame, ASTM1394Parser,
)
from instruments.protocols.hl7 import HL7Parser
from instruments.protocols.rs232 import RS232Parser, extrair_linhas
from clients.senaite_api import senaite
from logger import audit_logger

logger = logging.getLogger("instruments.listener")

_CHUNK_SIZE = 65536


class AnalisadorTCP:
    """Servidor TCP assíncrono para receber dados de analisadores laboratoriais.

    Suporta os protocolos ASTM E1381/E1394, HL7 v2.x e RS-232 raw.
    O protocolo é selecionado por ``config.protocolo``.
    """

    def __init__(self, config: InstrumentoConfig):
        self.config = config
        self._server: Optional[asyncio.AbstractServer] = None

    @property
    def nome(self) -> str:
        return self.config.nome

    @property
    def porta(self) -> int:
        return self.config.porta

    async def _processar_astm(self, reader, writer) -> None:
        """Handler para protocolo ASTM E1381/E1394 com STX/ETX/checksum."""
        buf = b""
        parser = ASTM1394Parser(self.nome)

        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break

            stx_pos = chunk.find(STX)
            if stx_pos > 0 and not buf:
                chunk = chunk[stx_pos:]

            for byte in chunk:
                buf += bytes([byte])

                if len(buf) > _CHUNK_SIZE:
                    logger.warning("[%s] Buffer excedeu %d bytes, resetando", self.nome, _CHUNK_SIZE)
                    buf = b""
                    parser = ASTM1394Parser(self.nome)
                    continue

                if not buf.startswith(STX) and STX in buf:
                    buf = buf[buf.find(STX):]

                if buf == ENQ:
                    writer.write(ACK)
                    await writer.drain()
                    buf = b""
                    continue

                if buf == EOT:
                    writer.write(ACK)
                    await writer.drain()
                    amostra = parser.extrair_amostra()
                    if amostra:
                        await self._enviar_para_senaite(amostra)
                    parser = ASTM1394Parser(self.nome)
                    buf = b""
                    continue

                if buf.startswith(STX):
                    etx_idx = buf.find(ETX, 1)
                    if etx_idx != -1 and len(buf) >= etx_idx + 3:
                        frame = buf[:etx_idx + 3]
                        valido, payload = validar_frame(frame)
                        if valido:
                            writer.write(ACK)
                            await writer.drain()
                            amostras = parser.alimentar(payload.decode("utf-8", errors="ignore"))
                            for amostra in amostras:
                                await self._enviar_para_senaite(amostra)
                        else:
                            writer.write(NAK)
                            await writer.drain()
                        buf = buf[etx_idx + 3:]
                    continue

    async def _processar_hl7(self, reader, writer) -> None:
        """Handler para protocolo HL7 v2.x — mensagens delimitadas por \\r."""
        buf = b""
        parser = HL7Parser(self.nome)

        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buf += chunk

            if len(buf) > _CHUNK_SIZE:
                logger.warning("[%s] Buffer HL7 excedeu %d bytes, resetando", self.nome, _CHUNK_SIZE)
                buf = b""
                parser = HL7Parser(self.nome)
                continue

            payload = buf.decode("utf-8", errors="ignore")
            if "\r" in payload or "\n" in payload:
                amostras = parser.alimentar(payload)
                buf = b""
                for amostra in amostras:
                    await self._enviar_para_senaite(amostra)

    async def _processar_rs232(self, reader, writer) -> None:
        """Handler para protocolo RS-232 raw — linhas delimitadas por CR/LF."""
        buf = b""
        parser = RS232Parser(self.nome)

        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buf += chunk

            if len(buf) > _CHUNK_SIZE:
                logger.warning("[%s] Buffer RS-232 excedeu %d bytes, resetando", self.nome, _CHUNK_SIZE)
                buf = b""
                parser = RS232Parser(self.nome)
                continue

            linhas, buf = extrair_linhas(buf)
            for linha in linhas:
                text = linha.decode("utf-8", errors="ignore")
                amostras = parser.alimentar(text)
                for amostra in amostras:
                    await self._enviar_para_senaite(amostra)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peername = writer.get_extra_info("peername")
        logger.info("[%s] Conexão estabelecida: %s (protocolo=%s)", self.nome, peername, self.config.protocolo)

        proto = self.config.protocolo.upper()
        try:
            if proto == "ASTM":
                await self._processar_astm(reader, writer)
            elif proto == "HL7":
                await self._processar_hl7(reader, writer)
            elif proto == "RS232":
                await self._processar_rs232(reader, writer)
            else:
                logger.error("[%s] Protocolo desconhecido: %s", self.nome, proto)

            logger.info("[%s] Conexão encerrada por %s", self.nome, peername)

        except asyncio.CancelledError:
            logger.info("[%s] Conexão cancelada", self.nome)
        except Exception as e:
            logger.error("[%s] Erro: %s", self.nome, e, exc_info=True)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _enviar_para_senaite(self, amostra: AmostraProcessada) -> None:
        """Envia resultados para o SENAITE via JSON API, com rastro de auditoria"""
        sample_id = amostra.sample_id
        logger.info("[%s] Injetando %d resultados na AR %s", self.nome, len(amostra.resultados), sample_id)
        for res in amostra.resultados:
            try:
                await senaite.set_analysis_result(
                    sample_id, res.keyword, res.valor,
                    machine_name=self.nome,
                )
                audit_logger.info("Resultado injetado no SENAITE", extra={
                    "audit_data": {
                        "evento": "resultado_importado",
                        "sample_id": sample_id,
                        "keyword": res.keyword,
                        "valor": res.valor,
                        "unidade": res.unidade,
                        "flag": res.flag_anormalidade,
                        "maquina": self.nome,
                        "via": self.config.protocolo.upper(),
                    }
                })
            except Exception as e:
                logger.error("  → Falha AR=%s keyword=%s: %s", sample_id, res.keyword, e)
                audit_logger.error("Falha ao injetar resultado", extra={
                    "audit_data": {
                        "evento": "resultado_falha",
                        "sample_id": sample_id,
                        "keyword": res.keyword,
                        "erro": str(e),
                        "maquina": self.nome,
                    }
                })

    async def iniciar(self) -> None:
        """Inicia o servidor TCP para este analisador"""
        self._server = await asyncio.start_server(
            self.handle_client,
            host=self.config.host,
            port=self.porta,
        )
        logger.info(
            "[%s] Escutando em %s:%d (protocolo=%s)",
            self.nome, self.config.host, self.porta, self.config.protocolo,
        )

    async def parar(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("[%s] Servidor parado", self.nome)
