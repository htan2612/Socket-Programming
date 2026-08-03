import os
import sys
import socket
import threading
import posixpath

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _BASE_DIR not in sys.path:
    sys.path.append(_BASE_DIR)
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import (
    REPLY_CODES, BUFFER_SIZE, TCP_CONTROL_PORT,
    CMD_USER, CMD_PASS, CMD_QUIT, CMD_NOOP,
    CMD_PWD, CMD_CWD, CMD_CDUP, CMD_LIST, CMD_NLST, CMD_SIZE,
    CMD_HASH,
)
from Common.logger import log_session, log_command
from Common.file_scanner import scan_directory, format_list_output, format_nlst_output
from Common.size_converter import human_readable_size
from Common.hash_utils import calculate_hash

HOST = "0.0.0.0"
PORT = TCP_CONTROL_PORT  # lấy từ module chung

# "CSDL" user tạm thời cho Tuấn 1
USER_DB = {
    "admin": "admin123",
    "guest": "guest123",
}

SERVER_ROOT = os.path.abspath(os.path.join(_SOURCE_DIR, "server_root"))
os.makedirs(SERVER_ROOT, exist_ok=True)

def build_reply(code: int, extra: str = None) -> str:
    """Dùng đúng REPLY_CODES trong protocol_constants.py"""
    if code not in REPLY_CODES:
        raise ValueError(f"Mã reply {code} không tồn tại trong protocol_constants.REPLY_CODES")
    message = extra if extra else REPLY_CODES[code]
    return f"{code} {message}\r\n"

def resolve_path(cwd: str, arg: str):
    """
    Quy đổi 1 đường dẫn client nhập
    thành (virtual_path, real_path_trên_đĩa). Trả về (None, None) nếu vượt ra
    ngoài SERVER_ROOT (chống path traversal kiểu '../../../etc').
    """
    virtual = arg.strip() if arg else cwd
    if not virtual.startswith("/"):
        virtual = posixpath.normpath(posixpath.join(cwd, virtual))
    else:
        virtual = posixpath.normpath(virtual)
    if virtual != "/":
        virtual = virtual.rstrip("/") or "/"

    real = os.path.normpath(os.path.join(SERVER_ROOT, virtual.lstrip("/")))
    if real != SERVER_ROOT and not real.startswith(SERVER_ROOT + os.sep):
        return None, None
    return virtual, real

from command_handler import dispatch_command

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
        from session_manager import session_manager
        session_manager.remove(addr)
        conn.close()
        log_session(client_id, "DISCONNECTED")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] TCP Control Server đang lắng nghe tại {HOST}:{PORT}")
    print(f"[*] Server root (sandbox thư mục): {SERVER_ROOT}")

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
