import os
import sys
import hashlib
from typing import Optional, Dict

class FileReassembler:
    """
    FileReassembler chịu trách nhiệm nhận các khối dữ liệu (chunks/payloads) từ RDTReceiver,
    xử lý các gói tin đến không đúng thứ tự (Out-of-Order), ghi tuần tự trực tiếp xuống ổ đĩa (Streaming)
    để tránh tràn bộ nhớ RAM, và kiểm tra tính toàn vẹn Hash của file sau khi hoàn tất.
    """
    def __init__(self, output_path: Optional[str] = None):
        """
        :param output_path: Đường dẫn file đầu ra. Nếu None, reassembler sẽ lưu dữ liệu vào RAM (cho các lệnh như LIST/NLST).
        """
        self.output_path = output_path
        self.next_expected_seq = 0
        self.buffer: Dict[int, bytes] = {}  # Lưu trữ out-of-order chunks: {seq_num: payload}
        self.total_chunks: Optional[int] = None
        self.is_last_received = False
        self._file_handle = None
        self._in_memory_bytes = bytearray()

        if self.output_path:
            # Tạo thư mục cha nếu chưa tồn tại
            dir_name = os.path.dirname(self.output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            # Mở file ở chế độ ghi nhị phân (wb)
            self._file_handle = open(self.output_path, "wb")

    def add_chunk(self, seq_num: int, payload: bytes, is_last: bool = False) -> bool:
        """
        Thêm một chunk dữ liệu nhận được vào bộ ghép file.
        :param seq_num: Số thứ tự gói tin (0, 1, 2, ...)
        :param payload: Nội dung bytes của khối dữ liệu
        :param is_last: Cờ báo đây là gói tin cuối cùng (FLAG_FIN)
        :return: True nếu chunk mới (chấp nhận), False nếu chunk lặp lại (duplicate)
        """
        if is_last:
            self.is_last_received = True
            self.total_chunks = seq_num + 1

        # Bỏ qua nếu gói tin đã được xử lý và ghi xuống đĩa trước đó (gói lặp)
        if seq_num < self.next_expected_seq:
            return False

        # Bỏ qua nếu gói đã có trong buffer chờ
        if seq_num in self.buffer:
            return False

        # Lưu chunk vào bộ đệm tạm
        self.buffer[seq_num] = payload

        # Tiến hành xả (flush) các chunk liên tục theo đúng thứ tự seq_num
        self._flush_buffer()

        return True

    def _flush_buffer(self):
        """
        Ghi các chunk liên tiếp bắt đầu từ next_expected_seq xuống đĩa/RAM và giải phóng bộ đệm.
        """
        while self.next_expected_seq in self.buffer:
            chunk_data = self.buffer.pop(self.next_expected_seq)
            if self._file_handle:
                self._file_handle.write(chunk_data)
                self._file_handle.flush()
            else:
                self._in_memory_bytes.extend(chunk_data)
            
            self.next_expected_seq += 1

    def is_complete(self) -> bool:
        """
        Kiểm tra xem toàn bộ file đã được nhận trọn vẹn và đúng thứ tự chưa.
        """
        if not self.is_last_received:
            return False
        return self.total_chunks is not None and self.next_expected_seq == self.total_chunks

    def close(self):
        """
        Đóng file stream sau khi hoàn tất hoặc hủy bỏ.
        """
        if self._file_handle and not self._file_handle.closed:
            self._file_handle.close()

    def get_data(self) -> bytes:
        """
        Lấy toàn bộ dữ liệu dưới dạng bytes (chỉ dùng khi output_path là None).
        """
        return bytes(self._in_memory_bytes)

    def calculate_hash(self, algo: str = "sha256") -> str:
        """
        Tính toán Hash SHA-256 hoặc MD5 của file đã ghép xong để đối soát tính toàn vẹn (End-to-End Hash).
        """
        self.close()

        if not self.output_path or not os.path.exists(self.output_path):
            hasher = hashlib.sha256() if algo.lower() == "sha256" else hashlib.md5()
            hasher.update(self._in_memory_bytes)
            return hasher.hexdigest()

        hasher = hashlib.sha256() if algo.lower() == "sha256" else hashlib.md5()
        with open(self.output_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def abort(self):
        """
        Hủy bỏ quá trình ghép file và dọn dẹp file tạm nếu bị lỗi giữa chừng.
        """
        self.close()
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass

