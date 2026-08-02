import os
import sys
import socket
import threading
import time
import hashlib
# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn thư mục Source vào sys.path
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common import protocol_constants
from RDT.rdt_sender import RDTSender
from RDT.rdt_receiver import RDTReceiver
from RDT.file_chunker import send_file_via_rdt


def run_demo():
    print("=" * 60)
    print("      DEMO KIEM THU TRUYEN FILE QUA UDP RDT PROTOCOL      ")
    print("=" * 60)

    # 1. Tạo file test (chứa văn bản + dữ liệu nhị phân)
    test_dir = os.path.join(_BASE_DIR, "test_output")
    os.makedirs(test_dir, exist_ok=True)

    input_file = os.path.join(test_dir, "input_demo.txt")
    output_file = os.path.join(test_dir, "output_demo.txt")

    # Ghi dữ liệu mẫu 20KB
    sample_text = ("Hello UDP RDT Protocol! HCMUS Computer Networking Project.\n" * 400).encode('utf-8')
    with open(input_file, "wb") as f:
        f.write(sample_text)

    # Tính Hash SHA-256 ban đầu
    src_hash = hashlib.sha256(sample_text).hexdigest()
    print(f"\n[1] Da tao file nguon  : {input_file}")
    print(f"    - Kich thuoc        : {len(sample_text)} bytes")
    print(f"    - SHA-256 File Nguon: {src_hash}")

    # 2. Thiết lập Socket UDP (Localhost 127.0.0.1)
    HOST = "127.0.0.1"
    PORT = 9999

    rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx_sock.bind((HOST, PORT))
    rx_sock.settimeout(protocol_constants.UDP_TIMEOUT)

    tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    rx_result = {}

    # 3. Luồng lắng nghe phía Receiver
    def receiver_job():
        print(f"\n[2] Phia Receiver: Dang lang nghe goi tin tai UDP {HOST}:{PORT}...")
        receiver = RDTReceiver(rx_sock)
        res = receiver.receive_file(output_path=output_file)
        rx_result["reassembler"] = res

    rx_thread = threading.Thread(target=receiver_job)
    rx_thread.start()

    time.sleep(0.3) # Bật receiver trước

    # 4. Phía Sender gửi file
    print("\n[3] Phia Sender: Bat dau doc file va gui tung chunk qua RDT...")
    sender = RDTSender(tx_sock, HOST, PORT, timeout=0.5, max_retries=5)
    success = send_file_via_rdt(sender, input_file, chunk_size=512)

    # 5. Chờ luồng nhận xong
    rx_thread.join(timeout=5.0)

    tx_sock.close()
    rx_sock.close()

    # 6. Đánh giá kết quả
    print("\n" + "=" * 60)
    print("                    KET QUA KIEM THU                    ")
    print("=" * 60)

    if not success or "reassembler" not in rx_result:
        print("[FAILED] KIEM THU THAT BAI: Truyền file bị gián đoạn!")
        return

    res = rx_result["reassembler"]
    dst_hash = res.calculate_hash("sha256")

    print(f"    - File Dich         : {output_file}")
    print(f"    - SHA-256 File Dich : {dst_hash}")

    if src_hash == dst_hash:
        print("\n[SUCCESS] THANH CONG RUC RO: 2 chuoi HASH khop nhau 100%!")
        print("    File da duoc gui va ghep chinh xac tuyet doi qua UDP RDT.")
    else:
        print("\n[FAILED] THAT BAI: Ma Hash khong khop, file nhan bi loi du lieu!")

if __name__ == "__main__":
    run_demo()
