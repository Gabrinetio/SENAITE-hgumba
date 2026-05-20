"""
Runner CLI para o Daemon de Instrumentos.

Uso:
  uv run instrumentos                       # Inicia todos os listeners
  uv run instrumentos --dry-run             # Mostra configuração sem iniciar
  uv run instrumentos --list                # Lista equipamentos configurados
  uv run instrumentos --portas 5001,5003    # Apenas portas específicas
"""

import asyncio
import logging
import signal
import sys
from typing import List

from instruments.config import INSTRUMENTOS
from instruments.listener import AnalisadorTCP
from logger import audit_logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("instruments.runner")


def _listar_equipamentos():
    print("Equipamentos configurados:")
    print(f"{'Nome':<25} {'Porta':<8} {'Protocolo':<10} {'Descrição'}")
    print("-" * 70)
    for inst in INSTRUMENTOS:
        status = "[ativo]" if inst.enabled else "[desativado]"
        print(f"{inst.nome:<25} {inst.porta:<8} {inst.protocolo:<10} {inst.description}  [{status}]")
    print(f"\nTotal: {len(INSTRUMENTOS)} equipamento(s)")


async def _run_listeners(indices: List[int]):
    listeners = [AnalisadorTCP(inst) for i, inst in enumerate(INSTRUMENTOS) if i in indices and inst.enabled]

    if not listeners:
        logger.warning("Nenhum listener ativo para iniciar.")
        return

    # Inicia todos concorrentemente
    await asyncio.gather(*(l.iniciar() for l in listeners))
    audit_logger.info("Daemon de instrumentos iniciado", extra={
        "audit_data": {
            "evento": "daemon_start",
            "listeners": len(listeners),
            "portas": [l.porta for l in listeners],
        }
    })

    # Graceful shutdown
    stop_event = asyncio.Event()

    def _shutdown():
        logger.info("Parando listeners...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            break

    await stop_event.wait()

    # Para todos
    await asyncio.gather(*(l.parar() for l in listeners), return_exceptions=True)
    logger.info("Daemon de instrumentos finalizado.")
    audit_logger.info("Daemon de instrumentos finalizado", extra={
        "audit_data": {
            "evento": "daemon_stop",
            "listeners": len(listeners),
        }
    })


def main():
    args = [a.lower() for a in sys.argv[1:]]

    if "--list" in args or "-l" in args:
        _listar_equipamentos()
        return

    if "--dry-run" in args:
        _listar_equipamentos()
        return

    # Filtra por portas específicas
    indices = list(range(len(INSTRUMENTOS)))
    for arg in args:
        if arg.startswith("--portas") or arg.startswith("-p"):
            try:
                eq = arg.split("=") if "=" in arg else [arg, args[args.index(arg) + 1]]
                portas_str = eq[1] if len(eq) > 1 else ""
                portas = set(int(p.strip()) for p in portas_str.split(",") if p.strip().isdigit())
                indices = [i for i, inst in enumerate(INSTRUMENTOS) if inst.porta in portas]
            except (ValueError, IndexError):
                logger.error("Formato inválido para --portas. Use: --portas=5001,5002")
                sys.exit(1)

    asyncio.run(_run_listeners(indices))


if __name__ == "__main__":
    main()
