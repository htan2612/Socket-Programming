"""
client_main.py
"""

import os
import sys
import re
import time
import socket
import getpass
import threading

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import TCP_CONTROL_PORT, BUFFER_SIZE, CMD_QUIT
from Common.hash_utils import calculate_hash
from Common.progress_bar import print_progress

from RDT.rdt_sender import RDTSender
from RDT.rdt_receiver import RDTReceiver
from RDT.file_chunker import send_file_via_rdt, DEFAULT_CHUNK_SIZE

from cli_interface import (
    print_success, print_error, print_info, print_warning, print_header,
    print_client_prompt,
)

HOST = "127.0.0.1"
PORT = TCP_CONTROL_PORT
DOWNLOAD_DIR = "downloads"


class ControlConnection:

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = ""

    def recv_reply(self) -> str:
        while "\r\n" not in self.buffer:
            data = self.sock.recv(BUFFER_SIZE)
            if not data:
                return ""
            self.buffer += data.decode(errors="ignore")
        line, self.buffer = self.buffer.split("\r\n", 1)
        return line.strip()

    def send_command(self, command: str) -> str:
        self.sock.sendall((command + "\r\n").encode("utf-8"))
        return self.recv_reply()


def get_code(reply: str) -> int:
    try:
        return int(reply.split(" ", 1)[0])
    except (ValueError, IndexError):
        return -1


def print_reply(reply: str):
    if not reply:
        print_error("Mat ket noi toi server.")
        return
    code = get_code(reply)
    if 200 <= code < 400:
        print_success(reply)
    elif code >= 400:
        print_error(reply)
    else:
        print_info(reply)


def send_and_print(conn: ControlConnection, command: str) -> str:
    reply = conn.send_command(command)
    print_reply(reply)
    return reply


def guided_login(conn: ControlConnection):
    print_info("Dang nhap (Enter de bo qua va tu go lenh USER/PASS sau)")
    username = input("Username: ").strip()
    if not username:
        print_warning("Da bo qua dang nhap tu dong.")
        return
    reply = send_and_print(conn, f"USER {username}")
    if get_code(reply) != 331:
        return
    try:
        password = getpass.getpass("Password: ")
    except Exception:
        print_warning("Terminal khong ho tro an mat khau, se hien thi ro.")
        password = input("Password: ")
    send_and_print(conn, f"PASS {password}")


def format_port_command(ip: str, port: int) -> str:
    h1, h2, h3, h4 = ip.split(".")
    p1, p2 = port >> 8, port & 0xFF
    return f"PORT {h1},{h2},{h3},{h4},{p1},{p2}"


def parse_data_addr(reply: str):
    m = re.search(r"\(([\d,]+)\)", reply)
    if not m:
        return None
    parts = [int(x) for x in m.group(1).split(",")]
    if len(parts) != 6:
        return None
    h1, h2, h3, h4, p1, p2 = parts
    return f"{h1}.{h2}.{h3}.{h4}", (p1 << 8) + p2


def verify_hash(conn: ControlConnection, remote_filename: str, local_path: str, local_hash: str = None):
    print_info("Dang doi soat tinh toan ven file (HASH)...")
    if local_hash is None:
        local_hash = calculate_hash(local_path, algorithm="sha256")
    hash_reply = send_and_print(conn, f"HASH {remote_filename}")
    if get_code(hash_reply) != 250:
        print_warning("Khong lay duoc hash tu server de doi soat.")
        return
    parts = hash_reply.split()
    remote_hash = parts[2] if len(parts) > 2 else ""
    if local_hash and remote_hash and local_hash.lower() == remote_hash.lower():
        print_success(f"Hash khop nhau - file nguyen ven ({local_hash[:20]}...)")
    else:
        print_error("Hash KHONG khop - file co the bi loi trong qua trinh truyen!")


def do_retr(conn: ControlConnection, remote_filename: str):
    size_reply = send_and_print(conn, f"SIZE {remote_filename}")
    if get_code(size_reply) != 250:
        return
    try:
        total_size = int(size_reply.split()[1])
    except (IndexError, ValueError):
        total_size = 0

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_path = os.path.join(DOWNLOAD_DIR, os.path.basename(remote_filename))

    data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_sock.bind(("0.0.0.0", 0))
    _, local_port = data_sock.getsockname()

    port_reply = send_and_print(conn, format_port_command("127.0.0.1", local_port))
    if get_code(port_reply) != 200:
        data_sock.close()
        return

    reply = send_and_print(conn, f"RETR {remote_filename}")
    if get_code(reply) != 150:
        data_sock.close()
        return

    data_sock.settimeout(0.5)
    result = {}

    def receiver_job():
        receiver = RDTReceiver(data_sock)
        result["reassembler"] = receiver.receive_file(output_path=output_path)

    t = threading.Thread(target=receiver_job)
    start = time.time()
    t.start()
    while t.is_alive():
        time.sleep(0.1)
        completed = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        print_progress(completed, max(total_size, 1), start, prefix="Downloading")
    t.join()
    print_progress(total_size, max(total_size, 1), start, prefix="Downloading")
    data_sock.close()

    final_reply = conn.recv_reply()
    print_reply(final_reply)

    reassembler = result.get("reassembler")
    if reassembler:
        reassembler.close()

    if get_code(final_reply) == 226 and os.path.exists(output_path):
        print_success(f"Da luu ve: {output_path}")
        verify_hash(conn, remote_filename, output_path)


def do_upload(conn: ControlConnection, ftp_command: str, local_path: str):
    if not os.path.isfile(local_path):
        print_error(f"Khong tim thay file local: {local_path}")
        return

    pasv_reply = send_and_print(conn, "PASV")
    if get_code(pasv_reply) != 200:
        return
    addr = parse_data_addr(pasv_reply)
    if addr is None:
        print_error("Khong doc duoc dia chi PASV tu server.")
        return
    server_ip, server_port = addr

    remote_filename = os.path.basename(local_path)
    if ftp_command == "STOU":
        cmd_reply = send_and_print(conn, "STOU")
    else:
        cmd_reply = send_and_print(conn, f"{ftp_command} {remote_filename}")

    if get_code(cmd_reply) != 150:
        return

    m = re.search(r"FILE:(\S+)", cmd_reply)
    if m:
        remote_filename = m.group(1)

    total_size = os.path.getsize(local_path)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender = RDTSender(data_sock, server_ip, server_port)

    result = {}

    def sender_job():
        result["ok"] = send_file_via_rdt(sender, local_path)

    t = threading.Thread(target=sender_job)
    start = time.time()
    t.start()
    while t.is_alive():
        time.sleep(0.1)
        completed = min(sender.base * DEFAULT_CHUNK_SIZE, total_size)
        print_progress(completed, max(total_size, 1), start, prefix="Uploading  ")
    t.join()
    print_progress(total_size, max(total_size, 1), start, prefix="Uploading  ")
    data_sock.close()

    final_reply = conn.recv_reply()
    print_reply(final_reply)

    if get_code(final_reply) == 226:
        print_success(f"Da upload xong voi ten tren server: {remote_filename}")
        verify_hash(conn, remote_filename, local_path)


def main():
    print_header("HYBRID FTP CLIENT")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except (ConnectionRefusedError, OSError) as e:
        print_error(f"Khong ket noi duoc toi server {HOST}:{PORT} ({e})")
        return

    conn = ControlConnection(sock)
    print_reply(conn.recv_reply())
    guided_login(conn)

    try:
        while True:
            print_client_prompt()
            msg = input().strip()
            if not msg:
                continue

            parts = msg.split(" ", 1)
            cmd = parts[0].upper()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == "RETR" and arg:
                do_retr(conn, arg)
            elif cmd in ("STOR", "APPE") and arg:
                do_upload(conn, cmd, arg)
            elif cmd == "STOU":
                local_path = arg or input("Duong dan file local can upload: ").strip()
                do_upload(conn, "STOU", local_path)
            else:
                reply = send_and_print(conn, msg)
                if cmd == CMD_QUIT or not reply:
                    break

    except (ConnectionResetError, BrokenPipeError):
        print_error("Mat ket noi toi server.")
    except KeyboardInterrupt:
        print_warning("\nDa ngat ket noi (Ctrl+C).")
    finally:
        sock.close()


if __name__ == "__main__":
    main()