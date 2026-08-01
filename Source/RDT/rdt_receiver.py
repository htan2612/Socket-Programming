import os
import sys
import socket
from typing import Optional

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.udp_header import pack_packet, unpack_packet
from RDT.file_reassembler import FileReassembler
from Common.protocol_constants import FLAG_ACK, FLAG_FIN

class RDTReceiver:
    """
    RDTReceiver nhận luồng gói tin UDP theo chuẩn Cumulative ACK (Go-Back-N / Selective Repeat),
    phản hồi ACK và chuyển payload cho FileReassembler xử lý lắp ráp file.
    """
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def receive_file(self, output_path: Optional[str] = None) -> FileReassembler:
        """
        Nhận toàn bộ file qua UDP RDT và sử dụng FileReassembler để ghi xuống đĩa hoặc RAM.
        :param output_path: Đường dẫn lưu file. Nếu None, lưu dữ liệu trong RAM.
        :return: Đối tượng FileReassembler đã hoàn tất (chứa data hoặc đường dẫn file + Hash)
        """
        reassembler = FileReassembler(output_path=output_path)
        last_sender_addr = None

        while True:
            try:
                raw_bytes, sender_addr = self.sock.recvfrom(4096)
                last_sender_addr = sender_addr
                seq, ack, flags, length, payload, is_valid = unpack_packet(raw_bytes)

                # 1. Nếu gói tin bị hỏng Checksum -> Bỏ qua không phản hồi ACK (Sender sẽ timeout & retransmit)
                if not is_valid:
                    print(f"[RDT Receiver] Bỏ qua gói tin hỏng Checksum (Seq={seq})")
                    continue

                # 2. Thêm mẩu dữ liệu vào FileReassembler
                is_last = bool(flags & FLAG_FIN)
                accepted = reassembler.add_chunk(seq_num=seq, payload=payload, is_last=is_last)

                # 3. Phản hồi ACK: Gửi ACK với ack_num là gói tin đã ghép liên tục mới nhất
                # Phản hồi ACK(seq) cho gói vừa nhận thành công
                ack_packet = pack_packet(0, seq, FLAG_ACK, b'')
                self.sock.sendto(ack_packet, sender_addr)

                # 4. Kiểm tra hoàn tất ghép file
                if reassembler.is_complete():
                    # Gửi thêm 3 gói ACK dự phòng cho cờ FIN để đảm bảo Sender nhận được ACK gói cuối
                    for _ in range(3):
                        self.sock.sendto(ack_packet, sender_addr)
                    break

            except socket.timeout:
                # Nếu đã hoàn tất file thì thoát vòng lặp
                if reassembler.is_complete():
                    break

        return reassembler
