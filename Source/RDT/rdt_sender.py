import os
import sys
import socket
import time
from typing import Dict, Tuple, Iterable

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.udp_header import pack_packet, unpack_packet
from Common.protocol_constants import (
    FLAG_DATA,
    FLAG_ACK,
    FLAG_FIN,
    DEFAULT_WINDOW_SIZE,
    MAX_WINDOW_SIZE,
    UDP_TIMEOUT,
    MAX_RETRIES,
)

class RDTSender:
    """
    RDTSender triển khai thuật toán Sliding Window (Go-Back-N - GBN)
    kết hợp kiểm soát tắc nghẽn (AIMD Congestion Control).
    """
    def __init__(self, sock: socket.socket, dest_ip: str, dest_port: int, timeout=UDP_TIMEOUT, max_retries=MAX_RETRIES, initial_window=DEFAULT_WINDOW_SIZE):
        self.sock = sock
        self.dest_addr = (dest_ip, dest_port)
        self.timeout = timeout
        self.max_retries = max_retries
        self.window_size = initial_window
        self.max_window_size = MAX_WINDOW_SIZE
        self.base = 0
        self.next_seq_num = 0
        # window_buffer lưu trữ {seq_num: [packet_bytes, send_timestamp, retry_count]}
        self.window_buffer: Dict[int, list] = {}

    def send_file_stream(self, chunk_generator: Iterable[Tuple[bytes, bool]]) -> bool:
        """
        Truyền luồng file (dạng generator yielding (chunk_bytes, is_last)) qua Go-Back-N Sliding Window.
        :param chunk_generator: Generator/Iterable trả về (payload, is_last)
        :return: True nếu tất cả các gói tin được truyền và nhận ACK thành công.
        """
        chunk_iter = iter(chunk_generator)
        has_more_chunks = True
        self.base = 0
        self.next_seq_num = 0
        self.window_buffer.clear()

        print(f"[RDT Sender (GBN)] Bắt đầu truyền dữ liệu qua cửa sổ trượt (N={self.window_size})...")

        while has_more_chunks or self.base < self.next_seq_num:
            # 1. Nạp và gửi các gói tin mới nếu cửa sổ trượt còn chỗ trống
            while has_more_chunks and (self.next_seq_num < self.base + self.window_size):
                try:
                    payload, is_last = next(chunk_iter)
                    flags = FLAG_FIN if is_last else FLAG_DATA
                    packet = pack_packet(self.next_seq_num, 0, flags, payload)

                    # Gửi gói tin qua UDP Socket
                    self.sock.sendto(packet, self.dest_addr)

                    # Lưu gói tin vào cửa sổ để chờ ACK
                    self.window_buffer[self.next_seq_num] = [packet, time.time(), 0]
                    self.next_seq_num += 1

                    if is_last:
                        has_more_chunks = False
                except StopIteration:
                    has_more_chunks = False

            # 2. Lắng nghe ACK phản hồi từ Receiver (dùng socket timeout ngắn)
            self.sock.settimeout(0.01)
            try:
                ack_bytes, _ = self.sock.recvfrom(1024)
                ack_seq, ack_num, ack_flags, _, _, is_valid = unpack_packet(ack_bytes)

                # Kiểm tra đúng cờ ACK và không bị lỗi Checksum
                if is_valid and (ack_flags & FLAG_ACK):
                    # Cumulative ACK (ACK cộng dồn): Nếu ACK nhận được lớn hơn hoặc bằng base
                    if ack_num >= self.base:
                        # Trượt cửa sổ: Xóa các gói đã nhận ACK an toàn từ base đến ack_num
                        for seq in range(self.base, ack_num + 1):
                            if seq in self.window_buffer:
                                del self.window_buffer[seq]
                        
                        self.base = ack_num + 1

                        # AIMD Congestion Control: Tăng tuyến tính kích thước cửa sổ khi nhận ACK tốt
                        if self.window_size < self.max_window_size:
                            self.window_size += 1

            except socket.timeout:
                pass  # Không nhận được ACK trong 10ms -> Chuyển sang kiểm tra timeout gói base

            # 3. Xử lý Timeout & GBN Retransmission
            if self.base in self.window_buffer:
                packet_info = self.window_buffer[self.base]
                send_time = packet_info[1]
                retries = packet_info[2]

                if time.time() - send_time > self.timeout:
                    if retries >= self.max_retries:
                        print(f"[RDT Sender ERROR] Vượt quá số lần thử lại tối đa ({self.max_retries}) tại Seq={self.base}. Hủy truyền!")
                        return False

                    # AIMD Congestion Control: Giảm một nửa kích thước cửa sổ khi xảy ra nghẽn/timeout
                    self.window_size = max(1, self.window_size // 2)
                    print(f"[RDT Sender GBN] Timeout tại Seq={self.base}! Thu hẹp Window={self.window_size}. Retransmit cửa sổ [{self.base}..{self.next_seq_num - 1}] (Lần {retries + 1}/{self.max_retries})...")

                    # Go-Back-N Retransmit: Gửi lại TOÀN BỘ các gói đang có trong cửa sổ từ base đến next_seq_num - 1
                    current_time = time.time()
                    for seq in range(self.base, self.next_seq_num):
                        if seq in self.window_buffer:
                            pkt = self.window_buffer[seq][0]
                            self.sock.sendto(pkt, self.dest_addr)
                            self.window_buffer[seq][1] = current_time # Cập nhật thời gian gửi
                            self.window_buffer[seq][2] += 1            # Tăng số lần retransmit

        print(f"[RDT Sender (GBN)] Hoàn thành truyền toàn bộ {self.next_seq_num} gói tin!")
        return True

    def send_chunk(self, data: bytes, is_last=False) -> bool:
        """
        Phương thức tương thích ngược để gửi 1 chunk đơn lẻ.
        """
        def single_chunk_gen():
            yield data, is_last

        return self.send_file_stream(single_chunk_gen())
