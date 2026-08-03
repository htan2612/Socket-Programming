"""
abcdzzz

"""

import os
import sys
import socket
import threading
import posixpath

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_COMMON_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "..", "Common"))
if _COMMON_DIR not in sys.path:
    sys.path.append(_COMMON_DIR)

from protocol_constants import (
    REPLY_CODES, BUFFER_SIZE, TCP_CONTROL_PORT,
    CMD_USER, CMD_PASS, CMD_QUIT, CMD_NOOP,
    CMD_PWD, CMD_CWD, CMD_CDUP, CMD_LIST, CMD_NLST, CMD_SIZE,
)
from logger import log_session, log_command
from file_scanner import scan_directory, format_list_output, format_nlst_output
from size_converter import human_readable_size

HOST = "0.0.0.0"
PORT = TCP_CONTROL_PORT  # lay tu module chung

# "CSDL" user tam thoi cho Tuan 1 (co the thay bang co che xac thuc that o cac tuan sau)
USER_DB = {
    "admin": "admin123",
    "guest": "guest123",
}

_SOURCE_CODE_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", ".."))
SERVER_ROOT = os.path.abspath(os.path.join(_SOURCE_CODE_DIR, "server_root"))
os.makedirs(SERVER_ROOT, exist_ok=True)


def build_reply(code: int, extra: str = None) -> str:
    """Dung dung REPLY_CODES trong protocol_constants.py -> 1 nguon du lieu duy nhat,
    tranh viec moi thanh vien tu dinh nghia 1 bo ma reply khac nhau."""
    if code not in REPLY_CODES:
        raise ValueError(f"Ma reply {code} khong ton tai trong protocol_constants.REPLY_CODES")
    message = extra if extra else REPLY_CODES[code]
    return f"{code} {message}\r\n"


def resolve_path(cwd: str, arg: str):
    """
    Quy doi 1 duong dan client nhap (co the tuong doi hoac tuyet doi, kieu Unix)
    thanh (virtual_path, real_path_tren_dia). Tra ve (None, None) neu vuot ra
    ngoai SERVER_ROOT (chong path traversal kieu '../../../etc').
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


_sessions = {}  # addr -> {"pending_user", "authenticated_user", "cwd"}


def dispatch_command(line: str, addr) -> str:
    session = _sessions.setdefault(
        addr, {"pending_user": None, "authenticated_user": None, "cwd": "/"}
    )

    parts = line.split(" ", 1)
    cmd = parts[0].upper()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == CMD_USER:
        if not arg:
            return build_reply(501, "Syntax error: USER requires a username")
        session["pending_user"] = arg
        session["authenticated_user"] = None
        return build_reply(331)

    elif cmd == CMD_PASS:
        if session["pending_user"] is None:
            return build_reply(500, "Bad sequence of commands: send USER first")
        if not arg:
            return build_reply(501, "Syntax error: PASS requires a password")
        if USER_DB.get(session["pending_user"]) == arg:
            session["authenticated_user"] = session["pending_user"]
            return build_reply(230)
        session["pending_user"] = None
        return build_reply(530)

    elif cmd == CMD_NOOP:
        return build_reply(200)

    elif cmd == CMD_QUIT:
        _sessions.pop(addr, None)
        return build_reply(221)

    # ---- Nhom lenh bo sung: tich hop file_scanner / size_converter cua Thanh An ----
    elif cmd in (CMD_PWD, CMD_CWD, CMD_CDUP, CMD_LIST, CMD_NLST, CMD_SIZE):
        if not session["authenticated_user"]:
            return build_reply(530, "Please login first")

        if cmd == CMD_PWD:
            return build_reply(250, f'"{session["cwd"]}" is the current directory')

        if cmd == CMD_CDUP:
            arg = ".."  # CDUP = CWD ".."

        if cmd in (CMD_CWD, CMD_CDUP):
            if cmd == CMD_CWD and not arg:
                return build_reply(501, "Syntax error: CWD requires a path")
            virtual, real = resolve_path(session["cwd"], arg)
            if virtual is None or not os.path.isdir(real):
                return build_reply(550, "Directory unavailable")
            session["cwd"] = virtual
            return build_reply(250, f'Directory changed to "{virtual}"')

        if cmd in (CMD_LIST, CMD_NLST):
            virtual, real = resolve_path(session["cwd"], arg)
            if virtual is None or not os.path.isdir(real):
                return build_reply(550, "Directory unavailable")
            entries = scan_directory(real)
            if cmd == CMD_LIST:
                body = format_list_output(entries) if entries else "(empty directory)"
            else:
                body = format_nlst_output(entries) if entries else ""
            # Ghep toan bo listing vao 1 reply duy nhat de khop voi client hien tai
            # (client hien chi lam 1 lan recv() cho moi lenh). O cac tuan sau, neu
            # thu muc lon, nen chuyen sang dang FTP multi-line that (150 ... 226).
            return build_reply(226, f'Listing for "{virtual}":\n{body}')

        if cmd == CMD_SIZE:
            if not arg:
                return build_reply(501, "Syntax error: SIZE requires a filename")
            virtual, real = resolve_path(session["cwd"], arg)
            if virtual is None or not os.path.isfile(real):
                return build_reply(550, "File unavailable")
            size_bytes = os.path.getsize(real)
            readable = human_readable_size(size_bytes)
            return build_reply(250, f"{size_bytes} bytes ({readable})")

    # ---- Cac lenh chua trien khai (RETR/STOR se can ket hop voi UDP data channel cua Minh Trung) ----
    return build_reply(502, f"Command '{cmd}' not implemented (yet)")


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

                reply = dispatch_command(line, addr)
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
        _sessions.pop(addr, None)
        conn.close()
        log_session(client_id, "DISCONNECTED")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] TCP Control Server dang lang nghe tai {HOST}:{PORT}")
    print(f"[*] Server root (sandbox thu muc): {SERVER_ROOT}")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Dang tat server...")
    finally:
        server.close()


if __name__ == "__main__":
    main()