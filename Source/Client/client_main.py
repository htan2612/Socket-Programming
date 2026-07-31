import os
import sys
import socket

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import TCP_CONTROL_PORT, BUFFER_SIZE, CMD_QUIT

HOST = "127.0.0.1"
PORT = TCP_CONTROL_PORT

def recv_reply(sock: socket.socket) -> str:
    data = sock.recv(BUFFER_SIZE)
    if not data:
        return ""
    return data.decode(errors="ignore").strip()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    print(f"Server: {recv_reply(s)}")

    try:
        while True:
            msg = input("Client: ").strip()
            if not msg:
                continue

            s.sendall((msg + "\r\n").encode("utf-8"))

            reply = recv_reply(s)
            print(f"Server: {reply}")

            if msg.split(" ")[0].upper() == CMD_QUIT or not reply:
                break

    except (ConnectionResetError, BrokenPipeError):
        print("Mat ket noi toi server.")
    finally:
        s.close()

if __name__ == "__main__":
    main()
