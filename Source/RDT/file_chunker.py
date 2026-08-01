import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from RDT.rdt_sender import RDTSender

DEFAULT_CHUNK_SIZE = 1024


def read_file_chunks(file_path: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
    """
    Generator đọc file và cắt thành từng khối (chunk) bytes.
    Trả về tuple dạng: (chunk_bytes, is_last_flag)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    file_size = os.path.getsize(file_path)

    if file_size == 0:
        yield b"", True
        return

    with open(file_path, "rb") as f:
        bytes_read = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            bytes_read += len(chunk)
            is_last = (bytes_read >= file_size)
            yield chunk, is_last


def send_file_via_rdt(sender: RDTSender, file_path: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> bool:
    """
    Đọc tệp tin và truyền toàn bộ các chunk qua kết nối RDTSender bằng Sliding Window.
    """
    print(f"[FileChunker] Bắt đầu đọc và gửi file qua Sliding Window: {file_path}")
    
    try:
        chunks_gen = read_file_chunks(file_path, chunk_size)
        success = sender.send_file_stream(chunks_gen)
        if not success:
            print(f"[FileChunker ERROR] Đã xảy ra lỗi khi truyền file {file_path}.")
            return False
                
        print(f"[FileChunker] Đã hoàn thành gửi file: {file_path}")
        return True
    except Exception as e:
        print(f"[FileChunker ERROR] Lỗi hệ thống tệp: {e}")
        return False