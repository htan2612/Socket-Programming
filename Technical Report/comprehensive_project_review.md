# BÁO CÁO ĐÁNH GIÁ VÀ KẾ HOẠCH HÀNH ĐỘNG TOÀN DIỆN (COMPREHENSIVE PROJECT REVIEW & ACTION PLAN)
**Dự án**: Thiết kế và Hiện thực hóa Ứng dụng Hybrid FTP (Hybrid FTP Application)  
**Tập tin đối chiếu**:
1. Đề bài yêu cầu: [25C10_Project1_SocketProgramming_2026.pdf](file:///c:/Users/ASUS/Downloads/Socket/Socket_ref/25C10_Project1_SocketProgramming_2026.pdf)
2. Slide bài giảng: [Socket_Programming_Seminar_2026.pdf](file:///c:/Users/ASUS/Downloads/Socket/Socket_ref/Socket_Programming_Seminar_2026.pdf)
3. Báo cáo nháp: [Demo Report (2).docx](file:///c:/Users/ASUS/Downloads/Socket/Technical%20Report/Demo%20Report%20(2).docx)

---

## MỤC LỤC
1. [Tóm tắt đánh giá chung (Executive Summary)](#1-tóm-tắt-đánh-giá-chung-executive-summary)
2. [Đánh giá sự phù hợp của báo cáo (Compliance Analysis & Checklist)](#2-đánh-giá-sự-phù-hợp-của-báo-cáo-compliance-analysis--checklist)
3. [Hiện trạng mã nguồn: Việc đã làm & Việc cần làm (Done vs. To-Do Checklist)](#3-hiện-trạng-mã-nguồn-việc-đã-làm--việc-cần-làm-done-vs-to-do-checklist)
4. [Đối chiếu mã nguồn với tài liệu mẫu tham khảo (Code Comparison vs. References)](#4-đối-chiếu-mã-nguồn-với-tài-liệu-mẫu-tham-khảo-code-comparison-vs-references)
5. [Kế hoạch rút ngắn tiến độ còn 10 ngày (Compressed 10-Day Action Plan)](#5-kế-hoạch-rút-ngắn-tiến-độ-còn-10-ngày-compressed-10-day-action-plan)
6. [Tài liệu tham khảo chuyên biệt & Phương án xác thực (References Map & Verification Plan)](#6-tài-liệu-tham-khảo-chuyên-biệt--phương-án-xác-thực-references-map--verification-plan)

---

## 1. Tóm tắt đánh giá chung (Executive Summary)

Sau khi đối chiếu mã nguồn và phân tích toàn diện yêu cầu đặc tả của đồ án, tôi rút ra kết luận:

1. **Về Báo cáo (`Demo Report (2).docx`)**: Cấu trúc khung đã soạn đủ **7 phần bắt buộc**. Tiêu đề các mục được phân bổ hợp lý, tuy nhiên văn bản hiện tại chỉ là **Dàn ý chi tiết (Outline)** và **Bảng phân công công việc**, chưa có nội dung kỹ thuật thực tế hay sơ đồ tương tác.
2. **Về Mã nguồn (`Source Code`)**: Đã viết xong luồng điều khiển TCP cơ bản (có cơ chế đăng nhập và duyệt file an toàn). Nhóm đang viết dở phần gửi nhận dữ liệu UDP RDT. Các tính năng quan trọng như đàm phán địa chỉ (`PORT`/`PASV`), tích hợp truyền file thực tế (`RETR`/`STOR`), thanh tiến độ và bảng giám sát session client song song vẫn chưa được bắt đầu.
3. **Giải pháp đẩy nhanh tiến độ**: Kế hoạch công việc 3 tuần đã được nén lại còn **10 ngày** để tăng tốc hoàn tất dự án, tối ưu hóa thời gian phát triển và tập trung lực lượng hoàn thiện các phần chưa xong.

---

## 2. Đánh giá sự phù hợp của báo cáo (Compliance Analysis & Checklist)

Dưới đây là bảng đối chiếu mức độ đáp ứng của báo cáo nháp với yêu cầu bắt buộc ghi trong tài liệu đặc tả đồ án (PDF):

| Tiêu chuẩn trong yêu cầu đồ án (PDF Specification) | Nội dung tương ứng trong Dàn ý Báo cáo (DOCX Outline) | Mức độ đáp ứng (Compliance Status) | Đánh giá & Rủi ro cần lưu ý |
| :--- | :--- | :--- | :--- |
| **7 Phần bắt buộc** (Section 2.4):<br>1. Scenario & Interaction<br>2. Project-Wide Data Structures<br>3. Workflows (Flowcharts)<br>4. Task Assignment Matrix<br>5. Self-Assessment<br>6. GenAI Appendix<br>7. Demo Evidence | Đầy đủ tên các phần từ 1 đến 7 trong "I. Dàn ý report". | **Đạt về mặt phân bổ cấu trúc** | **Thiếu nội dung chi tiết.** Tất cả 7 phần mới chỉ ghi gợi ý những gì cần điền chứ chưa có nội dung chuyên môn viết tay hay sơ đồ tương ứng. |
| **Giao thức Hybrid FTP** (decoupling):<br>Control Plane truyền lệnh qua TCP,<br>Data Plane truyền file qua UDP. | Phần 1 phác thảo bài toán Hybrid FTP và lý do tách biệt control/data đúng triết lý RFC 959. | **Đạt về mặt định hướng thiết kế** | Mã nguồn hiện tại **chưa hề** thiết kế theo mô hình này. Luồng chuyển cổng truyền dữ liệu điều khiển qua UDP vẫn chưa được lập trình. |
| **28 Lệnh FTP chuẩn** (Mục 2.2):<br>USER, PASS, QUIT, NOOP, PWD, CWD, CDUP, MKD, RMD, LIST, NLST, STAT, SIZE, MDTM, TYPE, MODE, PORT, PASV, RETR, STOR, STOU, APPE, DELE, RNFR, RNTO, HASH, ABOR, HELP. | Phụ lục trang bìa của báo cáo nháp liệt kê đủ checklist 28 lệnh này. File `Common/protocol_constants.py` cũng đã khai báo hằng số cho cả 28 lệnh. | **Đạt trên lý thuyết / Hằng số** | **Code chưa triển khai**. Server mới phân tích được 8 lệnh. 20 lệnh còn lại (bao gồm PORT/PASV dữ liệu) chưa được lập trình bộ xử lý tương ứng. |
| **19 Mã Reply Code** (Mục 2.3):<br>125, 150, 200, 220, 221, 226, 230, 250, 331, 350, 421, 425, 426, 450, 500, 501, 502, 530, 550. | Đã liệt kê đủ 19 mã trong dàn ý phần 2. File `Common/protocol_constants.py` cũng đã khai báo từ điển chứa mô tả cho cả 19 mã này. | **Đạt trên lý thuyết / Hằng số** | **Code chưa triển khai đầy đủ**. Cần xây dựng động cơ phản hồi mã trạng thái trên kênh TCP control tương ứng với luồng xử lý của từng lệnh mới. |
| **UDP Custom Header (5 trường)**:<br>- Sequence Number (4 Bytes)<br>- ACK Number (4 Bytes)<br>- Checksum (2 Bytes)<br>- Flags (1 Byte)<br>- Payload Length (2 Bytes).<br>*(Tổng cộng = 13 Bytes)* | Phần 2 mục "UDP custom header" ghi nhận đúng bảng bố cục bit đủ 5 trường này. File `Common/protocol_constants.py` định nghĩa `HEADER_FORMAT = "!IIHBH"` (tổng 13 bytes). | **Đạt thiết kế gói tin** | Đạt yêu cầu đóng gói nhị phân. |
| **Tầng UDP Đáng tin cậy tự chế (RDT)**:<br>Không dùng thư viện ngoài, xử lý mất gói, trùng lặp và sai thứ tự nhờ seq/ack/timeout. (Đạt mức **Excellent**) | Dàn ý Phần 3 liệt kê 2 flowchart cho máy trạng thái RDT Sender và RDT Receiver. Kế hoạch tuần 2 phân công viết Stop-and-Wait RDT. | **Đạt kế hoạch** | **Chưa tích hợp hoàn chỉnh**. Đang trong quá trình tích hợp vào luồng truyền file chính. |

---

## 3. Hiện trạng mã nguồn: Việc đã làm & Việc cần làm (Done vs. To-Do Checklist)

### ✅ ĐÃ LÀM (Done)
- **Cấu hình dùng chung**: Khai báo hằng số lệnh và reply codes (`protocol_constants.py`), module Logger (`logger.py`), quét thư mục (`file_scanner.py`), đổi đơn vị size file (`size_converter.py`).
- **Kênh TCP điều khiển**: Khung sườn Server đa luồng. Chấp nhận đăng nhập cơ bản (`USER`/`PASS`), bảo mật thư mục chống path traversal (`resolve_path`), xử lý các lệnh duyệt thư mục chuẩn (`PWD`, `CWD`, `CDUP`, `LIST`, `NLST`, `SIZE`). Client TCP CLI thô gửi/nhận lệnh hoạt động ổn định.
- **Kênh UDP dữ liệu**: Tạo file định nghĩa giao thức header nhị phân (`udp_header.py`) và viết sườn máy trạng thái gửi/nhận (`rdt_sender.py`, `rdt_receiver.py`).

### ❌ CẦN LÀM (To-Do) - Kế hoạch rút ngắn 10 ngày
- **Logic đọc/ghi file nhị phân**: Viết logic đọc/ghi block bytes cho `file_chunker.py` và `file_reassembler.py` hỗ trợ 2 chiều (Upload & Download).
- **Bộ đàm phán liên kết TCP-UDP**: Viết logic lệnh `PORT` và `PASV` trên TCP Server để liên kết địa chỉ sang socket truyền tải UDP.
- **Động cơ truyền file tích hợp**: Gọi `RDTSender`/`RDTReceiver` bên dưới khi nhận lệnh `RETR` hoặc `STOR` trên luồng TCP chính.
- **20 Lệnh FTP còn lại**: Viết xử lý các lệnh mở rộng như `STOU`, `APPE`, `DELE`, `RNFR/RNTO` (đổi tên), `ABOR` (hủy), `HELP`.
- **Session Table & Giám sát**: In hiển thị danh sách client kết nối thời gian thực trên giao diện console Server.
- **Kiểm thử chịu lỗi (Fault Tolerance)**: Thiết lập giả lập tự động bỏ rơi gói tin ngẫu nhiên trên UDP để xác minh chất lượng tầng RDT.
- **Tài liệu Báo cáo kỹ thuật**: Vẽ sơ đồ tuần tự và sơ đồ lưu đồ, ghi chép nhật ký GenAI Log 3 cột, chụp ảnh kết quả test MD5 đưa vào Báo cáo.

---

## 4. Đối chiếu mã nguồn với tài liệu mẫu tham khảo (Code Comparison vs. References)

Bảng so sánh đối chiếu kỹ thuật cho thấy những điểm nhóm làm tốt vượt trội so với tài liệu mẫu:

| Cấu phần kỹ thuật | Đặc tả lý thuyết / Mẫu trong References | Hiện trạng trong Mã nguồn của nhóm | Đánh giá so với References |
| :--- | :--- | :--- | :--- |
| **TCP Control Socket** | **Code mẫu chat thô**:<br>Chỉ coi mỗi một lần `recv` thô là một lệnh, dễ bị lỗi dính gói khi gõ nhanh. | **Cải tiến vượt trội**:<br>Dùng bộ đệm tích lũy dòng chữ `buffer.split("\n", 1)` gom chính xác từng lệnh kết thúc bằng dữ liệu xuống dòng `\r\n`. | Rất chuyên nghiệp, đúng nguyên lý hoạt động luồng byte stream của TCP. |
| **Quản lý đa luồng** | **Code mẫu `sample_code/03_server.py`**:<br>Dùng module thread cũ `_thread` để spawn cổng lắng nghe. | **Cải tiến vượt trội**:<br>Dùng module cao cấp `threading.Thread(..., daemon=True)` giúp luồng tự hủy an toàn khi máy chủ tắt. | Tối ưu hóa tài nguyên hệ thống rất tốt. |
| **Bảo mật thư mục chia sẻ** | **References**:<br>Không đề cập, client tự do điều hướng bằng các lệnh dạng `CWD ../../` | **Cải tiến vượt trội**:<br>Tự phát phát triển hàm `resolve_path` chặn đứng tấn công Path Traversal. | Đảm bảo tính an toàn thư mục ở mức công nghiệp thực tế. |
| **Cơ chế tính toán Checksum** | **Slide 75 & 151**:<br>Mô phỏng thuật toán tính toán 16-bit Internet Checksum bằng cách cộng dồn. | **Hiện thực lý thuyết tốt**:<br>Hàm `calculate_checksum` viết cộng dồn phần dư bit tràn chính xác. | Thuật toán viết chuẩn, checksum được truyền nhận nhị phân, kiểm tra toàn vẹn dữ liệu thành công. |

---

## 5. Kế hoạch rút ngắn tiến độ còn 10 ngày (Compressed 10-Day Action Plan)

Để hoàn thiện toàn bộ hệ thống Hybrid FTP sạch sẽ, hiệu quả và đúng thời hạn, nhóm 3 người sẽ phân công công việc chi tiết theo chu trình 10 ngày như dưới đây:

### 🗓️ Giai đoạn 1: Thiết lập kênh truyền song hành RDT & Đọc/ghi Nhị phân (Ngày 1 - Ngày 4)
*Mục tiêu: Đọc ghi file nhị phân thành công ở mức RDT và kết nối thành công điều hợp TCP-UDP.*

* **Ngày 1 - 2**:
  * **Người A (TCP)**: Thiết lập logic hai lệnh `PORT` và `PASV` trên Server chính (trong phần `active_passive.py`). Khởi tạo socket và lắng nghe cổng dữ liệu UDP thích hợp khi client đàm phán thành công.
  * **Người B (UDP)**: Viết các hàm đọc/ghi tệp nhị phân chia khối (dưới dạng mode `'rb'` và `'wb'`) cho hai module tiện ích `file_chunker.py` và `file_reassembler.py`.
  * **Người C (Client)**: Triển khai framework tích hợp cổng RDT ở phía Client để client có thể bắt tay truyền nhận dữ liệu thô qua UDP.
* **Ngày 3 - 4**:
  * **Người B (UDP)**: Hoàn tất máy trạng thái RDT 3.0 (Stop-and-Wait) và tích hợp các module `file_chunker` / `file_reassembler`.
  * **Người A + Người B**: Ghép nối kênh dữ liệu: Khi người dùng gõ lệnh download `RETR` hoặc upload `STOR` trên kết nối TCP, Server sẽ kích hoạt và chuyển dữ liệu qua RDT Sender/Receiver trên cổng UDP tương ứng.
  * **Người C (Chung)**: Viết module tính mã băm MD5/SHA-256 (`hash_utils.py` trong thư mục `Common/`) để phía gửi và nhận tự động đối chiếu sau khi hoàn tất.

---

### 🗓️ Giai đoạn 2: Lập trình 20 lệnh điều khiển FTP còn lại & Progress Bar (Ngày 5 - Ngày 7)
*Mục tiêu: Server hỗ trợ đầy đủ 28 lệnh FTP tiêu chuẩn và hiển thị trạng thái kết nối trực quan.*

* **Ngày 5 - 6**:
  * **Người A (TCP)**: Lập trình các lệnh điều khiển quản lý thư mục và tệp tin mở rộng còn thiếu: `STOU`, `APPE` (ghi nối tiếp), `DELE` (xóa file), `MKD`/`RMD` (tạo/xóa thư mục), `RNFR`/`RNTO` (đổi tên file), `ABOR` (hủy phiên truyền tải) và `HELP`.
  * **Người B (RDT)**: Tích hợp bộ giả lập lỗi rớt gói tin (Packet Loss/Delay Simulator) trong `rdt_sender.py` (tự động bỏ rơi ngẫu nhiên 5%-10% số gói tin gửi) để sẵn sàng cho việc test chịu lỗi.
  * **Người C (Client)**: Lập trình in thanh tiến trình tiến độ truyền tải động (`progress_bar.py` dạng text CLI `[██████░░░░] 60%`) để hiển thị tốc độ và phần trăm tải file theo thời gian thực trên màn hình Client.
* **Ngày 7**:
  * **Người A (TCP)**: Thiết lập bảng trạng thái session table (`session_manager.py`) hiển thị danh sách tất cả các client đang online thời gian thực trên console của Server.
  * **Người C (Báo cáo)**: Bắt đầu vẽ sơ đồ tương tác tuần tự các lệnh (Sequence Diagram) và vẽ lưu đồ máy trạng thái RDT Sender / Receiver.

---

### 🗓️ Giai đoạn 3: Kiểm thử chịu lỗi cực hạn, Tối ưu & Đóng gói Báo cáo (Ngày 8 - Ngày 10)
*Mục tiêu: Đạt tỷ lệ bảo toàn dữ liệu tuyệt đối (mã MD5 trùng khớp 100%) dưới điều kiện mạng rớt gói và hoàn tất báo cáo kỹ thuật.*

* **Ngày 8 - 9**:
  * **Cả nhóm**: Chạy thử nghiệm truyền tải các file dữ liệu lớn (file nén `.zip`/`.rar` dung lượng từ 20MB đến 50MB) trong điều kiện rớt gói 10%. Đối chiếu mã băm MD5 ở hai đầu, đảm bảo tính toàn vẹn của tệp tin.
  * **Người B (RDT)**: Triển khai logic chờ ngắn `TIME_WAIT` (khoảng 1-2 giây) trong `rdt_receiver.py` sau khi hoàn thành gói FIN để tự động re-ACK các gói FIN cũ gửi lại, khắc phục triệt để lỗi thất lạc ACK cuối.
  * **Người C (Báo cáo)**: Tổng hợp ảnh chụp màn hình kiểm thử thiết lập, nhật thực phiên truyền log, và điền đầy đủ nội dung kỹ thuật vào báo cáo nháp, đặc biệt là nhật ký GenAI Log 3 cột bắt buộc theo quy định.
* **Ngày 10**:
  * **Cả nhóm**: Rà soát, dọn dẹp mã nguồn, tối ưu hóa comment code, biên dịch báo cáo nhầm thành file PDF chính thức (`Report.pdf`) và nộp bài.

---

## 6. Tài liệu tham khảo chuyên biệt & Phương án xác thực (References Map & Verification Plan)

### 📂 BẢN ĐỒ TRA CỨU TÀI LIỆU (REFERENCE LOOKUPS)
* **28 Lệnh FTP & 19 Reply Codes**: Xem [25C10_Project1_SocketProgramming_2026.pdf](file:///c:/Users/ASUS/Downloads/Socket/Socket_ref/25C10_Project1_SocketProgramming_2026.pdf) (mục 2.2 và 2.3).
* **Đàm phán cổng Active / Passive (PORT/PASV)**: Xem [Socket_Programming_Seminar_2026.pdf](file:///c:/Users/ASUS/Downloads/Socket/Socket_ref/Socket_Programming_Seminar_2026.pdf) (trang 326 đến 358).
* **Đóng gói RDT Header & Tính Checksum**: Xem [Socket_Programming_Seminar_2026.pdf](file:///c:/Users/ASUS/Downloads/Socket/Socket_ref/Socket_Programming_Seminar_2026.pdf) (phần 02 và 03).
* **Mẫu Socket đa luồng (Multi-threading server trong Python)**: Đọc file mẫu [Tai_lieu_Socket/sample_code/03_server.py](file:///c:/Users/ASUS/Downloads/Socket/Socket_ref/Tai_lieu_Socket/sample_code).

### 🛠️ PHƯƠNG ÁN XÁC THỰC KỸ THUẬT (VERIFICATION PLAN)
1. **Kiểm thử đa kết nối**: Chạy song song nhiều Client kết nối điều khiển đến Server độc lập để xác minh Session hiển thị đúng luồng tiến trình.
2. **Kiểm thử chịu lỗi truyền tin (RDT Check)**: Kích hoạt mô phỏng đánh rơi 10% gói tin UDP, tiến hành truyền tải file nén `test.zip` dung lượng 20MB. Tiến hành chạy hàm hashing MD5 để verify:
   `checksum_source == checksum_destination` => Nếu bằng nhau, kết quả kiểm thử đạt chất lượng bảo toàn dữ liệu.
3. **Kiểm thử danh sách lệnh**: Chạy script gọi tuần tự 28 lệnh điều khiển của FTP để kiểm tra tính thích ứng của mã reply code trên TCP Control.
