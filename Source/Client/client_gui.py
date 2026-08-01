import os
import sys
import socket
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Cấu hình đường dẫn import
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import TCP_CONTROL_PORT, BUFFER_SIZE, CMD_QUIT

HOST = "127.0.0.1"
PORT = TCP_CONTROL_PORT

# BẢNG MÀU HYBRID DARK MODE Flat (Không dùng thư viện ngoài)
BG_MAIN = "#1E1E2E"       # Màu nền chính (Tối)
BG_CARD = "#252538"       # Nền cho các khung điều khiển
BG_INPUT = "#11111B"      # Nền ô nhập liệu (Đen sẫm)
FG_TEXT = "#CDD6F4"       # Màu chữ chính (Trắng xám)
COLOR_GREEN = "#2ECC71"   # Màu xanh thành công
COLOR_RED = "#E74C3C"     # Màu đỏ báo lỗi
COLOR_BLUE = "#3498DB"    # Xanh đại diện cho các hành động chính

class FTPClientStandardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hybrid FTP Client - Standard Library Edition")
        self.root.geometry("900x650")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)

        # Cấu hình lưới grid
        self.root.grid_columnconfigure(0, weight=1, minsize=320)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0) # Tiến trình
        self.root.grid_rowconfigure(2, weight=1) # Log bảng tin

        # Tạo Style cho các phần tử ttk (Ví dụ Progressbar)
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("Custom.Horizontal.TProgressbar", 
                             thickness=15, 
                             troughcolor=BG_INPUT, 
                             background=COLOR_GREEN, 
                             bordercolor=BG_MAIN, 
                             lightcolor=COLOR_GREEN, 
                             darkcolor=COLOR_GREEN)

        self._build_connection_panel()
        self._build_file_browser_panel()
        self._build_progress_panel()
        self._build_log_panel()

    def _build_connection_panel(self):
        """Khung trái: Điều khiển kết nối"""
        panel = tk.Frame(self.root, bg=BG_CARD, bd=0, highlightthickness=0)
        panel.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        title = tk.Label(panel, text="KẾT NỐI HỆ THỐNG", bg=BG_CARD, fg=FG_TEXT,
                         font=("Arial", 14, "bold"))
        title.pack(pady=20)

        # Các trường thông tin kết nối
        self.ip_input = self._create_input_field(panel, "ĐỊA CHỈ IP SERVER:", "127.0.0.1")
        self.port_input = self._create_input_field(panel, "CỔNG TCP CONTROL:", "2121")
        self.user_input = self._create_input_field(panel, "TÊN ĐĂNG NHẬP:", "admin")
        self.pass_input = self._create_input_field(panel, "MẬT MÃ BẢO VỆ:", "admin123", show="*")

        # Nút kết nối (Phẳng, đổi màu hover)
        btn_connect = tk.Button(panel, text="KẾT NỐI", bg=COLOR_GREEN, fg="#FFFFFF",
                                activebackground="#27AE60", activeforeground="#FFFFFF",
                                font=("Arial", 11, "bold"), bd=0, cursor="hand2",
                                command=self.action_connect)
        btn_connect.pack(pady=(25, 8), padx=30, fill="x", ipady=8)

        btn_disconnect = tk.Button(panel, text="HỦY KẾT NỐI", bg=COLOR_RED, fg="#FFFFFF",
                                   activebackground="#C0392B", activeforeground="#FFFFFF",
                                   font=("Arial", 11, "bold"), bd=0, cursor="hand2",
                                   command=self.action_disconnect)
        btn_disconnect.pack(pady=5, padx=30, fill="x", ipady=8)

    def _build_file_browser_panel(self):
        """Khung phải: Thư mục ảo"""
        panel = tk.Frame(self.root, bg=BG_CARD, bd=0, highlightthickness=0)
        panel.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        title = tk.Label(panel, text="MÁY CHỦ FILE EXPLORER", bg=BG_CARD, fg=FG_TEXT,
                         font=("Arial", 14, "bold"))
        title.pack(pady=15)

        self.path_lbl = tk.Label(panel, text="Thư mục ảo trên Server: /", bg=BG_CARD, fg="#A6ADC8",
                                 font=("Arial", 10, "italic"))
        self.path_lbl.pack(pady=(0, 10))

        # Danh sách file (Sử dụng Listbox thuần của tk, styling lại biên)
        list_frame = tk.Frame(panel, bg=BG_INPUT, bd=0)
        list_frame.pack(fill="both", expand=True, padx=25, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.file_listbox = tk.Listbox(list_frame, bg=BG_INPUT, fg=FG_TEXT,
                                       selectbackground="#313244", selectforeground="#F5E0DC",
                                       highlightthickness=0, bd=0, font=("Consolas", 11),
                                       yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.config(command=self.file_listbox.yview)

        # Mẫu file
        self.file_listbox.insert(0, "📂 .. (Thư mục cha)")
        self.file_listbox.insert(1, "📄 image.png        [2.45 MB]")
        self.file_listbox.insert(2, "📄 document.pdf     [10.00 MB]")

        # Nút bấm hành vi
        btn_box = tk.Frame(panel, bg=BG_CARD)
        btn_box.pack(fill="x", padx=25, pady=15)

        btn_download = tk.Button(btn_box, text="📥 Tải xuống (RETR)", bg=COLOR_BLUE, fg="#FFFFFF",
                                 activebackground="#2980B9", activeforeground="#FFFFFF",
                                 font=("Arial", 10, "bold"), bd=0, cursor="hand2",
                                 command=self.action_download)
        btn_download.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)

        btn_upload = tk.Button(btn_box, text="📤 Tải lên (STOR)", bg="#9B59B6", fg="#FFFFFF",
                               activebackground="#8E44AD", activeforeground="#FFFFFF",
                               font=("Arial", 10, "bold"), bd=0, cursor="hand2",
                               command=self.action_upload)
        btn_upload.pack(side="right", fill="x", expand=True, padx=(10, 0), ipady=8)

    def _build_progress_panel(self):
        """Khung tiến độ: Progressbar"""
        self.progress_frame = tk.Frame(self.root, bg="#2D2D44", bd=0)
        self.progress_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")

        lbl = tk.Label(self.progress_frame, text="Tiến trình truyền file UDP RDT:", bg="#2D2D44", fg=FG_TEXT,
                       font=("Arial", 9, "bold"))
        lbl.pack(side="left", padx=15, pady=10)

        # Thanh tiến độ ttk
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", 
                                            style="Custom.Horizontal.TProgressbar", mode="determinate")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=15)
        self.progress_bar["value"] = 78 # Demo giá trị 78%

        self.progress_detail = tk.Label(self.progress_frame, text="7.80 MB / 10.0 MB | Rate: 1.85 MB/s", 
                                        bg="#2D2D44", fg=FG_TEXT, font=("Arial", 9))
        self.progress_detail.pack(side="right", padx=15)

    def _build_log_panel(self):
        """Khung thông báo phía dưới"""
        panel = tk.Frame(self.root, bg=BG_INPUT, bd=0)
        panel.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="nsew")

        scrollbar = tk.Scrollbar(panel)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(panel, bg=BG_INPUT, fg="#A6ADC8", bd=0, 
                                highlightthickness=0, font=("Consolas", 10),
                                yscrollcommand=scrollbar.set)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar.config(command=self.log_text.yview)

        # Nạp Log khởi tạo
        self.log_system("SUCCESS", "Mở Client GUI thành công (100% Standard Library).")
        self.log_system("INFO", "Hệ thống sẵn sàng. Vui lòng nhấn KẾT NỐI để bắt đầu.")

    # --- Các hàm phụ trợ ---
    def _create_input_field(self, parent, label_text, default_val, show=None):
        lbl = tk.Label(parent, text=label_text, bg=BG_CARD, fg="#BAC2DE",
                       font=("Arial", 8, "bold"), anchor="w")
        lbl.pack(fill="x", padx=30, pady=(5, 0))
        
        entry = tk.Entry(parent, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT,
                         font=("Consolas", 11), bd=0, highlightthickness=1, 
                         highlightcolor=COLOR_BLUE, highlightbackground="#313244")
        if show:
            entry.config(show=show)
        entry.insert(0, default_val)
        entry.pack(fill="x", padx=30, pady=(2, 5), ipady=5)
        return entry

    def log_system(self, status, msg):
        prefix = f"[{status}] "
        # Tự động tô màu thẻ text Log
        self.log_text.insert("end", prefix, status)
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.tag_config("SUCCESS", foreground=COLOR_GREEN)
        self.log_text.tag_config("ERROR", foreground=COLOR_RED)
        self.log_text.tag_config("INFO", foreground=COLOR_BLUE)
        self.log_text.tag_config("WARNING", foreground="#F9E2AF")
        self.log_text.see("end")

    # --- Sự kiện nút bấm ---
    def action_connect(self):
        self.log_system("INFO", f"Kết nối đến: {self.ip_input.get()}:{self.port_input.get()}")
        # Triển khai socket thực ở luồng phụ (threading) tại đây để tránh lag GUI
        self.log_system("SUCCESS", "Kết nối TCP Control Channel thành công.")

    def action_disconnect(self):
        self.log_system("WARNING", "Đang đóng các Socket kết nối...")
        self.log_system("INFO", "Đã rời phiên hoạt động.")

    def action_download(self):
        selected = self.file_listbox.get(tk.ACTIVE)
        self.log_system("INFO", f"Yêu cầu tải xuống: {selected}")

    def action_upload(self):
        self.log_system("INFO", "Mở hội thoại chọn file dưới máy cục bộ...")

if __name__ == "__main__":
    root = tk.Tk()
    app = FTPClientStandardGUI(root)
    root.mainloop()
