import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.rdt_receiver import RDTReceiver
from Common.hash_utils import calculate_hash


def receive_file_via_rdt(receiver: RDTReceiver, save_path: str, expected_hash: str = None) -> bool:
    """Nhận toàn bộ file qua RDTReceiver rồi ghi ra đĩa, có thể verify hash."""
    print(f"[FileReassembler] Đang nhận file, sẽ lưu tại: {save_path}")

    try:
        data = receiver.receive_file()

        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(data)

        print(f"[FileReassembler] Đã ghi xong {len(data)} bytes vào {save_path}")

        if expected_hash:
            actual_hash = calculate_hash(save_path)
            if actual_hash.lower() != expected_hash.strip().lower():
                print(f"[FileReassembler ERROR] Hash không khớp! "
                      f"expected={expected_hash} actual={actual_hash}")
                return False
            print("[FileReassembler] Hash khớp, file toàn vẹn.")

        return True
    except Exception as e:
        print(f"[FileReassembler ERROR] Lỗi khi ghi file: {e}")
        return False