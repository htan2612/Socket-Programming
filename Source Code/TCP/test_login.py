"""
abcdzzzz
Chay (sau khi da bat tcp_server.py o 1 terminal khac):
    python test_login.py
"""

import os
import sys
import socket

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_COMMON_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "Common"))
if _COMMON_DIR not in sys.path:
    sys.path.append(_COMMON_DIR)

from Common.protocol_constants import TCP_CONTROL_PORT, BUFFER_SIZE

HOST = "127.0.0.1"
PORT = TCP_CONTROL_PORT


def send_and_recv(sock: socket.socket, command: str) -> str:
    sock.sendall((command + "\r\n").encode("utf-8"))
    return sock.recv(BUFFER_SIZE).decode(errors="ignore").strip()


def get_code(reply: str) -> int:
    try:
        return int(reply.split(" ", 1)[0])
    except (ValueError, IndexError):
        return -1


def run_test():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    results = []

    banner = s.recv(BUFFER_SIZE).decode(errors="ignore").strip()
    results.append(("Banner khi ket noi", 220, get_code(banner), banner))

    r1 = send_and_recv(s, "USER admin")
    results.append(("USER admin", 331, get_code(r1), r1))

    r2 = send_and_recv(s, "PASS admin123")
    results.append(("PASS admin123 (dung)", 230, get_code(r2), r2))

    r3 = send_and_recv(s, "USER admin")
    results.append(("USER admin (lan 2)", 331, get_code(r3), r3))

    r4 = send_and_recv(s, "PASS sai_mat_khau")
    results.append(("PASS sai (login that bai)", 530, get_code(r4), r4))

    r5 = send_and_recv(s, "NOOP")
    results.append(("NOOP", 200, get_code(r5), r5))

    # Luu y: sau khi test "PASS sai" o tren, phien da bi dang xuat (dung FTP semantics:
    # goi lai USER se huy trang thai authenticated cu). Can dang nhap lai truoc khi
    # test cac lenh yeu cau da login (PWD/LIST).
    r_relogin_user = send_and_recv(s, "USER admin")
    results.append(("USER admin (dang nhap lai)", 331, get_code(r_relogin_user), r_relogin_user))
    r_relogin_pass = send_and_recv(s, "PASS admin123")
    results.append(("PASS admin123 (dang nhap lai)", 230, get_code(r_relogin_pass), r_relogin_pass))

    # --- preview tich hop voi Thanh An: PWD / LIST / SIZE ---
    r6 = send_and_recv(s, "PWD")
    results.append(("PWD", 250, get_code(r6), r6))

    r7 = send_and_recv(s, "LIST")
    results.append(("LIST", 226, get_code(r7), r7))

    r8 = send_and_recv(s, "QUIT")
    results.append(("QUIT", 221, get_code(r8), r8))

    s.close()

    print("=" * 78)
    print(f"{'Buoc kiem tra':32}{'Mong doi':10}{'Nhan duoc':12}{'Ket qua'}")
    print("=" * 78)
    all_pass = True
    for name, expected, actual, raw in results:
        ok = expected == actual
        all_pass &= ok
        status = "PASS" if ok else "FAIL"
        print(f"{name:32}{expected:<10}{actual:<12}{status}")
        print(f"    -> {raw}")
    print("=" * 78)
    if all_pass:
        print("KET QUA TONG: DAT MILESTONE (Login TCP thanh cong + tich hop minh trung OK)")
    else:
        print("KET QUA TONG: CHUA DAT -- kiem tra lai server / module cua ming trung")


if __name__ == "__main__":
    run_test()