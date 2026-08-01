"""
test_server_commands.py
Chay (sau khi da bat Server/server_main.py o 1 terminal khac):
    python test_server_commands.py
"""

import os
import sys
import socket

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.append(_BASE_DIR)

from Common.protocol_constants import TCP_CONTROL_PORT, BUFFER_SIZE

HOST = "127.0.0.1"
PORT = TCP_CONTROL_PORT

results = []


def send_and_recv(sock, command):
    sock.sendall((command + "\r\n").encode("utf-8"))
    return sock.recv(BUFFER_SIZE).decode(errors="ignore").strip()


def get_code(reply):
    try:
        return int(reply.split(" ", 1)[0])
    except (ValueError, IndexError):
        return -1


def check(name, expected_code, reply):
    actual = get_code(reply)
    ok = actual == expected_code
    results.append((name, expected_code, actual, ok, reply.splitlines()[0] if reply else ""))
    return ok


def run_test():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    banner = s.recv(BUFFER_SIZE).decode(errors="ignore").strip()
    check("Banner ket noi", 220, banner)

    # --- Truoc khi login: cac lenh can auth phai bi tu choi (530) ---
    check("PWD truoc khi login -> 530", 530, send_and_recv(s, "PWD"))

    # --- Login ---
    check("USER admin", 331, send_and_recv(s, "USER admin"))
    check("PASS admin123 (dung)", 230, send_and_recv(s, "PASS admin123"))

    # --- Duyet thu muc ---
    check("PWD", 250, send_and_recv(s, "PWD"))
    check("MKD testdir", 250, send_and_recv(s, "MKD testdir"))
    check("MKD testdir (trung, phai loi)", 550, send_and_recv(s, "MKD testdir"))
    check("CWD testdir", 250, send_and_recv(s, "CWD testdir"))
    check("PWD sau CWD", 250, send_and_recv(s, "PWD"))
    check("CDUP", 250, send_and_recv(s, "CDUP"))
    check("LIST", 226, send_and_recv(s, "LIST"))
    check("NLST", 226, send_and_recv(s, "NLST"))
    check("STAT (server status)", 250, send_and_recv(s, "STAT"))
    check("STAT testdir", 250, send_and_recv(s, "STAT testdir"))
    check("RMD testdir", 250, send_and_recv(s, "RMD testdir"))
    check("RMD testdir (da xoa, phai loi)", 550, send_and_recv(s, "RMD testdir"))

    # --- File thao tac: tao file that qua HASH/SIZE de test (dung file co san) ---
    # welcome.txt da duoc seed san trong server_root/
    check("SIZE welcome.txt", 250, send_and_recv(s, "SIZE welcome.txt"))
    check("MDTM welcome.txt", 250, send_and_recv(s, "MDTM welcome.txt"))
    check("HASH welcome.txt", 250, send_and_recv(s, "HASH welcome.txt"))
    check("SIZE khongtontai.txt -> 550", 550, send_and_recv(s, "SIZE khongtontai.txt"))

    # --- RNFR/RNTO: doi ten welcome.txt -> welcome_renamed.txt roi doi lai ---
    check("RNFR welcome.txt", 350, send_and_recv(s, "RNFR welcome.txt"))
    check("RNTO welcome_renamed.txt", 250, send_and_recv(s, "RNTO welcome_renamed.txt"))
    check("RNFR welcome_renamed.txt", 350, send_and_recv(s, "RNFR welcome_renamed.txt"))
    check("RNTO welcome.txt (doi lai ten cu)", 250, send_and_recv(s, "RNTO welcome.txt"))
    check("RNTO khong RNFR truoc -> 500", 500, send_and_recv(s, "RNTO abc.txt"))

    # --- TYPE / MODE ---
    check("TYPE I", 200, send_and_recv(s, "TYPE I"))
    check("TYPE X (sai) -> 501", 501, send_and_recv(s, "TYPE X"))
    check("MODE S", 200, send_and_recv(s, "MODE S"))

    # --- PORT / PASV ---
    check("PORT 127,0,0,1,200,10", 200, send_and_recv(s, "PORT 127,0,0,1,200,10"))
    check("PASV", 200, send_and_recv(s, "PASV"))

    # --- RETR/STOR/STOU/APPE: preview control-channel (cho ghep RDT) ---
    check("RETR welcome.txt (co PASV) -> 150", 150, send_and_recv(s, "RETR welcome.txt"))
    check("RETR khongtontai.txt -> 550", 550, send_and_recv(s, "RETR khongtontai.txt"))
    check("STOR newfile.txt (co PASV) -> 150", 150, send_and_recv(s, "STOR newfile.txt"))
    check("STOU (co PASV) -> 150", 150, send_and_recv(s, "STOU"))
    check("APPE welcome.txt (co PASV) -> 150", 150, send_and_recv(s, "APPE welcome.txt"))

    # --- ABOR / HELP ---
    check("ABOR", 226, send_and_recv(s, "ABOR"))
    check("RETR sau ABOR (mat data_mode) -> 425", 425, send_and_recv(s, "RETR welcome.txt"))
    check("HELP", 200, send_and_recv(s, "HELP"))
    check("HELP RETR", 200, send_and_recv(s, "HELP RETR"))

    # --- DELE (xoa file test, tao truoc do qua STOR khong that su tao file
    #     vi chua co RDT, nen test DELE tren 1 file khong ton tai de xem loi) ---
    check("DELE khongtontai.txt -> 550", 550, send_and_recv(s, "DELE khongtontai.txt"))

    # --- Lenh khong ton tai ---
    check("XYZ (lenh la) -> 502", 502, send_and_recv(s, "XYZ"))

    # --- NOOP / QUIT ---
    check("NOOP", 200, send_and_recv(s, "NOOP"))
    check("QUIT", 221, send_and_recv(s, "QUIT"))

    s.close()

    print("=" * 90)
    print(f"{'Buoc kiem tra':45}{'Mong doi':10}{'Nhan duoc':10}{'KQ':6}{'Reply dong dau'}")
    print("=" * 90)
    all_pass = True
    for name, expected, actual, ok, first_line in results:
        all_pass &= ok
        status = "PASS" if ok else "FAIL"
        print(f"{name:45}{expected:<10}{actual:<10}{status:6}{first_line}")
    print("=" * 90)
    total = len(results)
    passed = sum(1 for r in results if r[3])
    print(f"KET QUA: {passed}/{total} PASS")
    if all_pass:
        print(">>> TAT CA CAC LENH DA TRIEN KHAI HOAT DONG DUNG <<<")
    else:
        print(">>> CO LENH SAI, XEM LAI CAC DONG FAIL O TREN <<<")


if __name__ == "__main__":
    run_test()