import os
import sys
import socket
import time
from typing import Optional

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.udp_header import pack_packet, unpack_packet
from RDT.file_reassembler import FileReassembler
from Common.protocol_constants import FLAG_ACK, FLAG_FIN, UDP_TIMEOUT

class RDTReceiver:
    """
    RDTReceiver nhận luồng gói tin UDP theo chuẩn Cumulative ACK (Go-Back-N),
    phản hồi ACK cộng dồn (Cumulative ACK) và chuyển payload cho FileReassembler xử lý.
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

        while True:
            try:
                raw_bytes, sender_addr = self.sock.recvfrom(4096)
                seq, ack, flags, length, payload, is_valid = unpack_packet(raw_bytes)

                # 1. Nếu gói tin bị hỏng Checksum -> Bỏ qua không phản hồi ACK (Sender sẽ timeout & retransmit)
                if not is_valid:
                    print(f"[RDT Receiver] Bỏ qua gói tin hỏng Checksum (Seq={seq})")
                    continue

                # 2. Thêm mẩu dữ liệu vào FileReassembler
                is_last = bool(flags & FLAG_FIN)
                accepted = reassembler.add_chunk(seq_num=seq, payload=payload, is_last=is_last)

                # 3. Phản hồi Cumulative ACK (ACK cộng dồn):
                # ACK báo hiệu số gói tin đúng thứ tự liên tục lớn nhất đã nhận và ghép được
                cum_ack = reassembler.next_expected_seq - 1
                if cum_ack >= 0:
                    ack_packet = pack_packet(0, cum_ack, FLAG_ACK, b'')
                    self.sock.sendto(ack_packet, sender_addr)

                # 4. Kiểm tra hoàn tất ghép file
                if reassembler.is_complete():
                    # Linger State (TIME_WAIT): Lắng nghe 1.5s để sẵn sàng phản hồi ACK cho bất kỳ gói FIN retransmit nào nếu ACK cuối bị mất
                    self.sock.settimeout(0.3)
                    start_linger = time.time()
                    linger_duration = max(1.5, UDP_TIMEOUT * 3)

                    while time.time() - start_linger < linger_duration:
                        try:
                            l_bytes, l_addr = self.sock.recvfrom(4096)
                            l_seq, l_ack, l_flags, _, _, l_valid = unpack_packet(l_bytes)
                            if l_valid and (reassembler.next_expected_seq - 1 >= 0):
                                # Phản hồi lại ACK cho gói cuối để Sender kết thúc an toàn
                                l_ack_pkt = pack_packet(0, reassembler.next_expected_seq - 1, FLAG_ACK, b'')
                                self.sock.sendto(l_ack_pkt, l_addr)
                        except (socket.timeout, OSError):
                            # Nếu timeout ngắn 0.3s trôi qua mà không có thêm gói FIN nào, tiếp tục kiểm tra tổng linger_duration
                            continue
                        except Exception:
                            break
                    break

            except (socket.timeout, OSError):
                if reassembler.is_complete():
                    break
                break

        return reassembler
