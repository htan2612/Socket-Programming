"""
active_passive.py
<<<<<<< HEAD

=======
>>>>>>> f139de225dd3fd8e0985106c0b882d5e0a82a494
"""

import socket

<<<<<<< HEAD

=======
>>>>>>> f139de225dd3fd8e0985106c0b882d5e0a82a494
PASV_PORT_RANGE = (50000, 51000)


def parse_port_command(arg: str):

    try:
        parts = [int(x) for x in arg.strip().split(",")]
        if len(parts) != 6 or any(not (0 <= p <= 255) for p in parts):
            return None
        h1, h2, h3, h4, p1, p2 = parts
        ip = f"{h1}.{h2}.{h3}.{h4}"
        port = (p1 << 8) + p2
        if not (0 < port <= 65535):
            return None
        return ip, port
    except (ValueError, AttributeError):
        return None


def handle_port(session, arg: str):

    parsed = parse_port_command(arg)
    if parsed is None:
        return False, "Syntax error: PORT requires h1,h2,h3,h4,p1,p2"


    session.close_data_channel()

    ip, port = parsed
    session.data_mode = "active"
    session.data_addr = (ip, port)
    return True, f"PORT command successful ({ip}:{port})"


def handle_pasv(session, server_public_host: str = "127.0.0.1"):

<<<<<<< HEAD
    session.close_data_channel() 

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
=======
    session.close_data_channel()  

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
>>>>>>> f139de225dd3fd8e0985106c0b882d5e0a82a494
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    bound = False
    for port in range(*PASV_PORT_RANGE):
        try:
            sock.bind(("0.0.0.0", port))
            bound = True
            break
        except OSError:
            continue

    if not bound:
        sock.close()
        return False, "Can't open data connection (no free port in PASV range)"

<<<<<<< HEAD
    sock.listen(1)
    _, actual_port = sock.getsockname()

    session.data_mode = "passive"
    session.pasv_socket = sock
=======
    _, actual_port = sock.getsockname()

    session.data_mode = "passive"
    session.pasv_socket = sock      
>>>>>>> f139de225dd3fd8e0985106c0b882d5e0a82a494
    session.pasv_port = actual_port

    h1, h2, h3, h4 = server_public_host.split(".")
    p1, p2 = actual_port >> 8, actual_port & 0xFF
    message = f"Entering Passive Mode ({h1},{h2},{h3},{h4},{p1},{p2})"
    return True, message