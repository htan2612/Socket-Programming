"""
server_main.py
"""

import os
import sys
import socket
import threading

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import BUFFER_SIZE, TCP_CONTROL_PORT, CMD_QUIT
from Common.logger import log_session, log_command

from reply_codes import build_reply
from session_manager import session_manager
from command_handler import dispatch_command

HOST = "0.0.0.0"
PORT = TCP_CONTROL_PORT


def handle_client(conn: socket.socket, addr):
    client_id = f"{addr[0]}:{addr[1]}"
    log_session(client_id, "CONNECTED")
    conn.sendall(build_reply(220).encode())

    buffer = ""
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            buffer += data.decode(errors="ignore")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip("\r\n").strip()
                if not line:
                    continue

                reply = dispatch_command(line, addr, conn)
                code = int(reply.split(" ", 1)[0])
                log_command(client_id, line, code)

                conn.sendall(reply.encode())

                if line.split(" ")[0].upper() == CMD_QUIT:
                    log_session(client_id, "DISCONNECTED")
                    conn.close()
                    return

    except ConnectionResetError:
        log_session(client_id, "CONNECTION RESET")
    finally:
        session_manager.remove(addr)
        conn.close()
        log_session(client_id, "DISCONNECTED")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] TCP Control Server đang lắng nghe tại {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Đang tắt server...")
    finally:
        server.close()


if __name__ == "__main__":
    main()