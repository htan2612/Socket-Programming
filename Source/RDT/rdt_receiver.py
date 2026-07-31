import os
import sys
import socket

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.udp_header import pack_packet, unpack_packet
from Common.protocol_constants import FLAG_ACK, FLAG_FIN

class RDTReceiver:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.expected_seq = 0
        self.buffer = {}  # Bộ đệm lưu {seq_num: payload}

    def receive_file(self):
        while True:
            raw_bytes, sender_addr = self.sock.recvfrom(2048)
            seq, ack, flags, length, payload, is_valid = unpack_packet(raw_bytes)

            # 1. Nếu gói tin bị hỏng Checksum -> Bỏ qua
            if not is_valid:
                continue

            # 2. Gửi ACK phản hồi ngay lập tức cho bên gửi
            ack_packet = pack_packet(0, seq, FLAG_ACK, b'')
            self.sock.sendto(ack_packet, sender_addr)

            # 3. Xử lý lưu dữ liệu (Chống trùng lặp)
            if seq == self.expected_seq:
                self.buffer[seq] = payload
                self.expected_seq += 1

            # 4. Kiểm tra cờ FIN (kết thúc file)
            if flags & FLAG_FIN and seq == self.expected_seq - 1:
                break

        # Sắp xếp và nối toàn bộ mảng byte theo đúng thứ tự
        complete_data = b''.join([self.buffer[i] for i in sorted(self.buffer.keys())])
        return complete_data
