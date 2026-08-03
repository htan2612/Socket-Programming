"""
command_handler.py
"""

import os
import sys
import socket

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import (
    CMD_USER, CMD_PASS, CMD_QUIT, CMD_NOOP,
    CMD_PWD, CMD_CWD, CMD_CDUP, CMD_MKD, CMD_RMD,
    CMD_LIST, CMD_NLST, CMD_STAT, CMD_SIZE, CMD_MDTM,
    CMD_TYPE, CMD_MODE, CMD_PORT, CMD_PASV,
    CMD_RETR, CMD_STOR, CMD_STOU, CMD_APPE, CMD_DELE,
    CMD_RNFR, CMD_RNTO, CMD_HASH, CMD_ABOR, CMD_HELP,
    UDP_TIMEOUT,
)
from Common.hash_utils import calculate_hash
from Common.logger import log_transfer

from reply_codes import build_reply
from session_manager import session_manager
import file_ops as fops
import active_passive as ap

from RDT.rdt_sender import RDTSender
from RDT.rdt_receiver import RDTReceiver
from RDT.file_chunker import send_file_via_rdt

USER_DB = {
    "admin": "admin123",
    "guest": "guest123",
}

_NO_AUTH_REQUIRED = {CMD_USER, CMD_PASS, CMD_QUIT, CMD_NOOP, CMD_HELP}

_ALL_COMMANDS_HELP = {
    CMD_USER: "USER <username> - dang nhap buoc 1",
    CMD_PASS: "PASS <password> - dang nhap buoc 2",
    CMD_QUIT: "QUIT - dong ket noi",
    CMD_NOOP: "NOOP - giu ket noi song (keep-alive)",
    CMD_PWD: "PWD - in thu muc hien tai",
    CMD_CWD: "CWD <path> - doi thu muc",
    CMD_CDUP: "CDUP - len thu muc cha",
    CMD_MKD: "MKD <dirname> - tao thu muc",
    CMD_RMD: "RMD <dirname> - xoa thu muc rong",
    CMD_LIST: "LIST [path] - liet ke chi tiet",
    CMD_NLST: "NLST [path] - liet ke ten file",
    CMD_STAT: "STAT [path] - trang thai server hoac file/thu muc",
    CMD_SIZE: "SIZE <filename> - kich thuoc file",
    CMD_MDTM: "MDTM <filename> - thoi gian sua doi cuoi",
    CMD_TYPE: "TYPE {A|I} - kieu du lieu ASCII/Binary",
    CMD_MODE: "MODE {S|B|C} - kieu truyen Stream/Block/Compressed",
    CMD_PORT: "PORT h1,h2,h3,h4,p1,p2 - Active Mode (dung cho RETR)",
    CMD_PASV: "PASV - Passive Mode (dung cho STOR/APPE/STOU)",
    CMD_RETR: "RETR <filename> - tai file ve (can PORT truoc)",
    CMD_STOR: "STOR <filename> - tai file len (can PASV truoc)",
    CMD_STOU: "STOU - tai file len voi ten duy nhat (can PASV truoc)",
    CMD_APPE: "APPE <filename> - noi them du lieu (can PASV truoc)",
    CMD_DELE: "DELE <filename> - xoa file",
    CMD_RNFR: "RNFR <oldname> - buoc 1 doi ten",
    CMD_RNTO: "RNTO <newname> - buoc 2 doi ten",
    CMD_HASH: "HASH <filename> - tinh hash SHA-256",
    CMD_ABOR: "ABOR - huy phien PORT/PASV chua bat dau truyen",
    CMD_HELP: "HELP [command] - xem huong dan",
}


def dispatch_command(line: str, addr, conn: socket.socket) -> str:
    session = session_manager.get_or_create(addr)
    session.commands_executed += 1

    parts = line.split(" ", 1)
    cmd = parts[0].upper()
    arg = parts[1].strip() if len(parts) > 1 else ""

    handler = _HANDLERS.get(cmd)
    if handler is None:
        return build_reply(502, f"Command '{cmd}' not implemented (yet)")

    if cmd not in _NO_AUTH_REQUIRED and not session.is_authenticated():
        return build_reply(530, "Please login first")

    return handler(session, arg, conn)


# ==================== Nhóm: Xác thực ====================

def _h_user(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: USER requires a username")
    session.pending_user = arg
    session.authenticated_user = None
    return build_reply(331)


def _h_pass(session, arg, conn):
    if session.pending_user is None:
        return build_reply(500, "Bad sequence of commands: send USER first")
    if not arg:
        return build_reply(501, "Syntax error: PASS requires a password")
    if USER_DB.get(session.pending_user) == arg:
        session.authenticated_user = session.pending_user
        return build_reply(230)
    session.pending_user = None
    return build_reply(530)


def _h_quit(session, arg, conn):
    session.close_data_channel()
    session_manager.remove(session.addr)
    return build_reply(221)


def _h_noop(session, arg, conn):
    return build_reply(200)


# ==================== Nhóm: Duyệt thư mục (server_file_ops) ====================

def _h_pwd(session, arg, conn):
    return build_reply(250, f'"{fops.pwd(session.cwd)}" is the current directory')


def _h_cwd(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: CWD requires a path")
    ok, result = fops.cwd_change(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    session.cwd = result
    return build_reply(250, f'Directory changed to "{result}"')


def _h_cdup(session, arg, conn):
    ok, result = fops.cdup(session.cwd)
    if not ok:
        return build_reply(550, result)
    session.cwd = result
    return build_reply(250, f'Directory changed to "{result}"')


def _h_mkd(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: MKD requires a directory name")
    ok, result = fops.make_directory(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    return build_reply(250, f'Directory created: "{result}"')


def _h_rmd(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: RMD requires a directory name")
    ok, result = fops.remove_directory(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    return build_reply(250, f'Directory removed: "{result}"')


def _h_list(session, arg, conn):
    ok, result = fops.list_directory(session.cwd, arg, name_only=False)
    if not ok:
        return build_reply(550, result)
    virtual, body = result
    return build_reply(226, f'Listing for "{virtual}":\n{body}')


def _h_nlst(session, arg, conn):
    ok, result = fops.list_directory(session.cwd, arg, name_only=True)
    if not ok:
        return build_reply(550, result)
    virtual, body = result
    return build_reply(226, f'Listing for "{virtual}":\n{body}')


def _h_stat(session, arg, conn):
    ok, result = fops.stat_path(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    if result is None:
        return build_reply(250, session_manager.session_table_text())
    return build_reply(250, result)


def _h_size(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: SIZE requires a filename")
    ok, result = fops.file_size(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    return build_reply(250, result)


def _h_mdtm(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: MDTM requires a filename")
    ok, result = fops.file_mdtm(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    return build_reply(250, result)


def _h_dele(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: DELE requires a filename")
    ok, result = fops.delete_file(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    return build_reply(250, f'File deleted: "{result}"')


def _h_rnfr(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: RNFR requires a filename")
    ok, result = fops.check_rename_from(session.cwd, arg)
    if not ok:
        return build_reply(550, result)
    session.rename_from = result
    return build_reply(350)


def _h_rnto(session, arg, conn):
    if session.rename_from is None:
        return build_reply(500, "Bad sequence of commands: send RNFR first")
    if not arg:
        return build_reply(501, "Syntax error: RNTO requires a new name")
    ok, result = fops.do_rename(session.cwd, session.rename_from, arg)
    session.rename_from = None
    if not ok:
        return build_reply(550, result)
    return build_reply(250, f"Renamed: {result}")


def _h_hash(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: HASH requires a filename")
    virtual, real = fops.resolve_path(session.cwd, arg)
    if virtual is None or not os.path.isfile(real):
        return build_reply(550, "File unavailable")
    digest = calculate_hash(real, algorithm="sha256")
    if not digest:
        return build_reply(550, "Cannot compute hash (file unavailable)")
    return build_reply(250, f"SHA256 {digest} {virtual}")


# ==================== Nhóm: TYPE / MODE ====================

def _h_type(session, arg, conn):
    value = arg.strip().upper()
    if value not in ("A", "I"):
        return build_reply(501, "Syntax error: TYPE must be A or I")
    session.transfer_type = value
    label = "ASCII" if value == "A" else "Binary/Image"
    return build_reply(200, f"Type set to {value} ({label})")


def _h_mode(session, arg, conn):
    value = arg.strip().upper()
    if value not in ("S", "B", "C"):
        return build_reply(501, "Syntax error: MODE must be S, B or C")
    session.transfer_mode = value
    return build_reply(200, f"Mode set to {value}")


# ==================== Nhóm: PORT / PASV / ABOR ====================

def _h_port(session, arg, conn):
    ok, message = ap.handle_port(session, arg)
    if not ok:
        return build_reply(501, message)
    return build_reply(200, message)


def _h_pasv(session, arg, conn):
    ok, message = ap.handle_pasv(session)
    if not ok:
        return build_reply(425, message)
    return build_reply(200, message)


def _h_abor(session, arg, conn):
    session.close_data_channel()
    return build_reply(226, "ABOR command successful; no active transfer")


# ==================== Nhóm: RETR/STOR/STOU/APPE  ====================

def _h_retr(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: RETR requires a filename")
    virtual, real = fops.resolve_path(session.cwd, arg)
    if virtual is None or not os.path.isfile(real):
        return build_reply(550, "File unavailable")
    if session.data_mode != "active" or session.data_addr is None:
        return build_reply(425, "RETR requires Active Mode: send PORT first")

    file_size = os.path.getsize(real)
    conn.sendall(build_reply(150, f"Opening data connection for {virtual} ({file_size} bytes)").encode())
    log_transfer(session.client_id, virtual, "DOWNLOAD", "START")

    client_ip, client_port = session.data_addr
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sender = RDTSender(data_sock, client_ip, client_port)
        ok = send_file_via_rdt(sender, real)
    finally:
        data_sock.close()
        session.close_data_channel()

    if ok:
        log_transfer(session.client_id, virtual, "DOWNLOAD", "DONE")
        return build_reply(226, f"Transfer complete: {virtual} ({file_size} bytes)")
    else:
        log_transfer(session.client_id, virtual, "DOWNLOAD", "FAILED")
        return build_reply(426, f"Connection closed; transfer aborted for {virtual}")


def _receive_upload(session, conn, virtual, real, append=False):

    if session.data_mode != "passive" or session.pasv_socket is None:
        return build_reply(425, "Requires Passive Mode: send PASV first")

    direction = "UPLOAD" if not append else "APPEND"
    log_transfer(session.client_id, virtual, direction, "START")

    data_sock = session.pasv_socket
    data_sock.settimeout(UDP_TIMEOUT)

    receive_target = None if append else real

    try:
        receiver = RDTReceiver(data_sock)
        reassembler = receiver.receive_file(output_path=receive_target)
    finally:
        session.close_data_channel()

    complete = reassembler.is_complete()

    if complete and append:
        data = reassembler.get_data()
        reassembler.close()
        try:
            with open(real, "ab") as f:
                f.write(data)
        except OSError as e:
            log_transfer(session.client_id, virtual, direction, "FAILED")
            return build_reply(426, f"Cannot append to file: {e}")
    else:
        reassembler.close()

    if not complete:
        reassembler.abort()
        log_transfer(session.client_id, virtual, direction, "FAILED")
        return build_reply(426, f"Connection closed; transfer aborted for {virtual}")

    size = os.path.getsize(real) if os.path.exists(real) else 0
    log_transfer(session.client_id, virtual, direction, "DONE")
    return build_reply(226, f"Transfer complete: {virtual} ({size} bytes)")


def _h_stor(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: STOR requires a filename")
    if session.data_mode != "passive" or session.pasv_socket is None:
        return build_reply(425, "STOR requires Passive Mode: send PASV first")
    virtual, real = fops.resolve_path(session.cwd, arg)
    if virtual is None:
        return build_reply(501, "Path escapes server root")

    conn.sendall(build_reply(150, f"Ready to receive {virtual}").encode())
    return _receive_upload(session, conn, virtual, real, append=False)


def _h_appe(session, arg, conn):
    if not arg:
        return build_reply(501, "Syntax error: APPE requires a filename")
    if session.data_mode != "passive" or session.pasv_socket is None:
        return build_reply(425, "APPE requires Passive Mode: send PASV first")
    virtual, real = fops.resolve_path(session.cwd, arg)
    if virtual is None:
        return build_reply(501, "Path escapes server root")

    if not os.path.exists(real):
        open(real, "wb").close()

    conn.sendall(build_reply(150, f"Ready to append to {virtual}").encode())
    return _receive_upload(session, conn, virtual, real, append=True)


def _h_stou(session, arg, conn):
    if session.data_mode != "passive" or session.pasv_socket is None:
        return build_reply(425, "STOU requires Passive Mode: send PASV first")
    unique_name = fops.generate_unique_filename(session.cwd)
    virtual, real = fops.resolve_path(session.cwd, unique_name)

    conn.sendall(build_reply(150, f"FILE:{unique_name} Ready to receive").encode())
    return _receive_upload(session, conn, virtual, real, append=False)


# ==================== HELP ====================

def _h_help(session, arg, conn):
    if arg:
        cmd = arg.strip().upper()
        text = _ALL_COMMANDS_HELP.get(cmd, f"Unknown command '{cmd}'")
        return build_reply(200, text)
    lines = ["Supported commands:"] + [f"  {c}: {t}" for c, t in _ALL_COMMANDS_HELP.items()]
    return build_reply(200, "\n".join(lines))


_HANDLERS = {
    CMD_USER: _h_user,
    CMD_PASS: _h_pass,
    CMD_QUIT: _h_quit,
    CMD_NOOP: _h_noop,
    CMD_PWD: _h_pwd,
    CMD_CWD: _h_cwd,
    CMD_CDUP: _h_cdup,
    CMD_MKD: _h_mkd,
    CMD_RMD: _h_rmd,
    CMD_LIST: _h_list,
    CMD_NLST: _h_nlst,
    CMD_STAT: _h_stat,
    CMD_SIZE: _h_size,
    CMD_MDTM: _h_mdtm,
    CMD_TYPE: _h_type,
    CMD_MODE: _h_mode,
    CMD_PORT: _h_port,
    CMD_PASV: _h_pasv,
    CMD_DELE: _h_dele,
    CMD_RNFR: _h_rnfr,
    CMD_RNTO: _h_rnto,
    CMD_HASH: _h_hash,
    CMD_ABOR: _h_abor,
    CMD_HELP: _h_help,
    CMD_RETR: _h_retr,
    CMD_STOR: _h_stor,
    CMD_STOU: _h_stou,
    CMD_APPE: _h_appe,
}