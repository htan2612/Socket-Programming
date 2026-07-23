import datetime
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def _timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_session(client_ip, event):
    """VD: log_session('127.0.0.1', 'CONNECTED')"""
    line = f"[{_timestamp()}] [SESSION] {client_ip} - {event}"
    _write(line, "session.log")
    print(line)

def log_command(client_ip, command, reply_code):
    line = f"[{_timestamp()}] [CMD] {client_ip} -> {command} -> {reply_code}"
    _write(line, "command.log")
    print(line)

def log_transfer(client_ip, filename, direction, status):
    """direction: 'UPLOAD'/'DOWNLOAD', status: 'START'/'DONE'/'FAILED'"""
    line = f"[{_timestamp()}] [TRANSFER] {client_ip} {direction} {filename} - {status}"
    _write(line, "transfer.log")
    print(line)

def _write(line, filename):
    with open(os.path.join(LOG_DIR, filename), "a", encoding="utf-8") as f:
        f.write(line + "\n")