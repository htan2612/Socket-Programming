import socket
from UDP.Server.udp_header import pack_packet, unpack_packet, FLAG_DATA, FLAG_ACK, FLAG_FIN

class RDTSender:
    def __init__(self, sock: socket.socket, dest_ip: str, dest_port: int, timeout=0.5, max_retries = 10):
        self.sock = sock
        self.dest_addr = (dest_ip, dest_port)
        self.sock.settimeout(timeout)
        self.seq_num = 0
        self.max_retries = max_retries

    def send_chunk(self, data: bytes, is_last=False):
        flags = FLAG_FIN if is_last else FLAG_DATA
        packet = pack_packet(self.seq_num, 0, flags, data)
        retries = 0

        while retries < self.max_retries:
            try:
                # Gửi gói dữ liệu qua UDP
                self.sock.sendto(packet, self.dest_addr)

                # Lắng nghe ACK phản hồi
                ack_bytes, _ = self.sock.recvfrom(1024)
                ack_seq, ack_num, ack_flags, _, _, is_valid = unpack_packet(ack_bytes)

                # Kiểm tra đúng ACK và không bị lỗi Checksum
                if is_valid and (ack_flags & FLAG_ACK) and ack_num == self.seq_num:
                    self.seq_num += 1  # Tăng sequence number cho gói tiếp theo
                    return True  # Truyền thành công gói này!
            except socket.timeout:
                # Hết thời gian chờ ACK -> Tự động gửi lại (Retransmit)

                retries+=1
                print(f"[RDT Sender] Timeout! Gửi lại lần {retries}/{self.max_retries} (Seq={self.seq_num})...")

        print(f"[RDT Sender ERROR] Vượt quá số lần thử lại tối đa ({self.max_retries}). Hủy truyền tệp!")
        return False