import os
import sys
import socket
import threading
import time

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn thư mục Source vào sys.path
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.rdt_sender import RDTSender
from RDT.udp_header import unpack_packet, pack_packet
from Common.protocol_constants import FLAG_ACK, FLAG_FIN

def mock_receiver_service(port=9999):
    """
    Một Receiver giả lập đơn giản: Nhận gói tin UDP và phản hồi ACK.
    Cố tình bỏ qua gói tin seq=3 lần đầu tiên để test tính năng Retransmit & Window Reduction của Sender!
    """
    rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx_sock.bind(("127.0.0.1", port))
    rx_sock.settimeout(3.0)

    dropped_seq_3_once = False

    print(f"[Mock Receiver] Đang lắng nghe tại cổng UDP {port}...")
    while True:
        try:
            data, addr = rx_sock.recvfrom(2048)
            seq, ack, flags, length, payload, is_valid = unpack_packet(data)

            if not is_valid:
                continue

            # Giả lập rớt gói: Cố tình drop gói seq=3 một lần để test Sender Timeout
            if seq == 3 and not dropped_seq_3_once:
                dropped_seq_3_once = True
                print(f"🔥 [Mock Receiver - Giả lập rớt gói] Cố tình BỎ GÓI Seq={seq} để ép Sender Timeout!")
                continue

            print(f"   [Mock Receiver] Nhận thành công gói Seq={seq} -> Phản hồi ACK={seq}")
            ack_pkt = pack_packet(0, seq, FLAG_ACK, b'')
            rx_sock.sendto(ack_pkt, addr)

            if flags & FLAG_FIN:
                print("[Mock Receiver] Đã nhận được gói cờ FIN. Kết thúc!")
                break
        except socket.timeout:
            break

    rx_sock.close()

def run_test_sender():
    print("=" * 60)
    print("        KIỂM THỬ ĐỘC LẬP RDT SENDER (GO-BACK-N)        ")
    print("=" * 60)

    # 1. Bật Receiver giả lập ở luồng riêng
    rx_thread = threading.Thread(target=mock_receiver_service, args=(9999,))
    rx_thread.start()
    time.sleep(0.3)

    # 2. Khởi tạo Socket phía Sender
    tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender = RDTSender(tx_sock, "127.0.0.1", 9999, timeout=0.8, max_retries=3, initial_window=4)

    # 3. Tạo một luồng dữ liệu giả lập gồm 8 khối dữ liệu (chunks)
    def dummy_chunk_generator():
        for i in range(8):
            payload = f"Payload Chunk #{i}".encode('utf-8')
            is_last = (i == 7)
            yield payload, is_last

    print(f"\n[Sender] Chuẩn bị gửi luồng 8 chunks qua Sliding Window (Window Size ban đầu = 4)...\n")

    # 4. Thực thi truyền dữ liệu
    start_time = time.time()
    success = sender.send_file_stream(dummy_chunk_generator())
    total_time = time.time() - start_time

    rx_thread.join(timeout=3.0)
    tx_sock.close()

    print("\n" + "=" * 60)
    if success:
        print(f"✅ KIỂM THỬ SENDER THÀNH CÔNG!")
        print(f"    - Thời gian truyền : {total_time:.3f} giây")
        print(f"    - Window Size cuối  : {sender.window_size}")
    else:
        print("❌ KIỂM THỬ THẤT BẠI!")
    print("=" * 60)

if __name__ == "__main__":
    run_test_sender()
