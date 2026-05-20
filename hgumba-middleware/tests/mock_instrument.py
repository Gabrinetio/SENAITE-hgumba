# -*- coding: utf-8 -*-
"""
Emulador ASTM E1381/E1394 — simula analisador Mindray BS200 para testes end-to-end.

Uso:
  uv run python tests/mock_instrument.py                  # localhost:5001
  uv run python tests/mock_instrument.py --port 5002      # porta específica
  uv run python tests/mock_instrument.py --host 192.168.x.x  # container remoto
"""

import argparse
import socket
import sys
import time

# Constantes do protocolo E1381
ENQ = b"\x05"
ACK = b"\x06"
NAK = b"\x15"
EOT = b"\x04"
STX = b"\x02"
ETX = b"\x03"


def _calc_checksum(payload: bytes) -> str:
    return f"{sum(payload) & 0xFF:02X}"


def send_frame_e1381(sock: socket.socket, frame_str: str):
    """Envelopa o frame E1394 com STX/ETX/checksum E1381 e envia"""
    payload = frame_str.encode("ascii")
    cs = _calc_checksum(payload)
    frame = STX + payload + ETX + cs.encode("ascii") + b"\r\n"
    print(f"[MAQUINA] TX: {frame_str[:80]}...")
    sock.sendall(frame)

    resp = sock.recv(1024)
    if resp == ACK:
        print("[MAQUINA] ACK OK")
    elif resp == NAK:
        print("[MAQUINA] NAK — servidor rejeitou frame")
    elif resp:
        print(f"[MAQUINA] Resposta inesperada: {resp.hex()}")
    time.sleep(0.3)


def emular_instrumento(host: str, port: int, nome: str, analises: list):
    """
    Emula um analisador clínico enviando dados ASTM E1381/E1394.

    Args:
        host: IP do listener
        port: Porta TCP do listener
        nome: Nome fantasia do equipamento (log)
        analises: Lista de dicts com sample_id, keyword, valor, unidade, flag
    """
    print(f"=== Iniciando emulação: {nome} ({host}:{port}) ===")
    print(f"  Amostras a enviar: {len(analises)}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        try:
            sock.connect((host, port))
            print("[MAQUINA] Conectado ao servidor TCP.")
        except ConnectionRefusedError:
            print(f"ERRO: {host}:{port} recusou conexao. O listener esta rodando?")
            return
        except socket.timeout:
            print(f"ERRO: Timeout conectando em {host}:{port}")
            return
        except Exception as e:
            print(f"ERRO: {e}")
            return

        # Handshake: ENQ -> ACK
        print("[MAQUINA] ENQ -> ", end="", flush=True)
        sock.sendall(ENQ)
        resp = sock.recv(1024)
        if resp == ACK:
            print("ACK")
        else:
            print(f"FALHA (resposta: {resp.hex()})")
            return

        # Prepara registros ASTM E1394
        seq = 0

        def seq_next():
            nonlocal seq
            seq += 1
            return seq

        for idx, analise in enumerate(analises):
            sid = analise.get("sample_id", f"AR-TEST-{idx+1:03d}")
            keyword = analise.get("keyword", "GLI001")
            valor = analise.get("valor", "100.0")
            unidade = analise.get("unidade", "mg/dL")
            flag = analise.get("flag", "")
            paciente = analise.get("paciente", "PACIENTE TESTE^H GUMARABA")
            patient_id = analise.get("patient_id", f"MRN{idx+1:06d}")

            seq_num = seq_next()
            send_frame_e1381(sock, f"{seq_num}H|\\^&|||{nome}||||||||")
            seq_num = seq_next()
            send_frame_e1381(sock, f"{seq_num}P|1||{patient_id}||{paciente}|||19800101|M|||||||||||||||||||")
            seq_num = seq_next()
            send_frame_e1381(sock, f"{seq_num}O|1|{sid}||^^^{keyword}||||||||||||||||||||||")
            seq_num = seq_next()
            send_frame_e1381(sock, f"{seq_num}R|1|^^^{keyword}|{valor}|N|{unidade}||{flag}||F||user||20260519080000")
            seq_num = seq_next()
            send_frame_e1381(sock, f"{seq_num}L|1|N")

            print(f"  [OK] Amostra {sid}: {keyword} = {valor} {unidade}")

        # EOT
        print("[MAQUINA] EOT (fim da transmissao)")
        sock.sendall(EOT)
        try:
            resp = sock.recv(1024)
            if resp == ACK:
                print("[MAQUINA] EOT confirmado com ACK")
        except socket.timeout:
            pass

    print(f"=== Emulação {nome} finalizada ===")


def main():
    parser = argparse.ArgumentParser(description="Emulador ASTM E1381/E1394")
    parser.add_argument("--host", default="127.0.0.1", help="IP do listener")
    parser.add_argument("--port", type=int, default=5001, help="Porta TCP")
    parser.add_argument("--machine", default="Mindray_BS200", help="Nome do equipamento")
    args = parser.parse_args()

    analises = [
        {
            "sample_id": "HGU-AR-001",
            "keyword": "GLI001",
            "valor": "105.5",
            "unidade": "mg/dL",
            "flag": "H",
            "paciente": "SGT MENDES^JOAO",
            "patient_id": "MRN000001",
        },
        {
            "sample_id": "HGU-AR-002",
            "keyword": "HEM001",
            "valor": "5.2",
            "unidade": "milhoes/mm3",
            "flag": "",
            "paciente": "CB MOURA^MARIA",
            "patient_id": "MRN000002",
        },
        {
            "sample_id": "HGU-AR-003",
            "keyword": "LIP001",
            "valor": "320",
            "unidade": "mg/dL",
            "flag": "HH",
            "paciente": "CAP OLIVEIRA^CARLOS",
            "patient_id": "MRN000003",
        },
    ]

    emular_instrumento(args.host, args.port, args.machine, analises)


if __name__ == "__main__":
    main()
