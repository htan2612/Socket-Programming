# file_scanner.py
import os
from datetime import datetime

def scan_directory(path):
    """Trả về list dict, mỗi dict là 1 file/thư mục — A sẽ dùng để build LIST/NLST"""
    result = []
    for entry in os.scandir(path):
        stat = entry.stat()
        result.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d%H%M%S"),
            "permissions": oct(stat.st_mode)[-3:],
        })
    return result

def format_list_output(entries):
    """Dạng chi tiết cho LIST"""
    lines = []
    for e in entries:
        typ = "d" if e["is_dir"] else "-"
        lines.append(f"{typ}rw-r--r-- {e['size']:>10} {e['modified']} {e['name']}")
    return "\n".join(lines)

def format_nlst_output(entries):
    """Chỉ tên, cho NLST"""
    return "\n".join(e["name"] for e in entries)