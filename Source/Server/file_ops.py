"""
server_file_ops.py
"""

import os
import sys
import posixpath
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.file_scanner import scan_directory, format_list_output, format_nlst_output
from Common.size_converter import human_readable_size

SERVER_ROOT = os.path.abspath(os.path.join(_SOURCE_DIR, "server_root"))
os.makedirs(SERVER_ROOT, exist_ok=True)


def resolve_path(cwd: str, arg: str):
    virtual = arg.strip() if arg else cwd
    if not virtual.startswith("/"):
        virtual = posixpath.normpath(posixpath.join(cwd, virtual))
    else:
        virtual = posixpath.normpath(virtual)
    if virtual != "/":
        virtual = virtual.rstrip("/") or "/"

    real = os.path.normpath(os.path.join(SERVER_ROOT, virtual.lstrip("/")))
    if real != SERVER_ROOT and not real.startswith(SERVER_ROOT + os.sep):
        return None, None
    return virtual, real



def pwd(cwd: str) -> str:
    return cwd


def cwd_change(cwd: str, arg: str):

    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.isdir(real):
        return False, "Directory unavailable"
    return True, virtual


def cdup(cwd: str):
    return cwd_change(cwd, "..")



def make_directory(cwd: str, arg: str):
    virtual, real = resolve_path(cwd, arg)
    if virtual is None:
        return False, "Path escapes server root"
    if os.path.exists(real):
        return False, "Directory already exists"
    try:
        os.makedirs(real)
        return True, virtual
    except OSError as e:
        return False, f"Cannot create directory: {e}"


def remove_directory(cwd: str, arg: str):
    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.isdir(real):
        return False, "Directory unavailable"
    if real == SERVER_ROOT:
        return False, "Cannot remove server root"
    try:
        os.rmdir(real)  
        return True, virtual
    except OSError as e:
        return False, f"Cannot remove directory (co the khong rong): {e}"


def list_directory(cwd: str, arg: str, name_only: bool = False):
    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.isdir(real):
        return False, "Directory unavailable"
    entries = scan_directory(real)
    if name_only:
        body = format_nlst_output(entries) if entries else ""
    else:
        body = format_list_output(entries) if entries else "(empty directory)"
    return True, (virtual, body)


def stat_path(cwd: str, arg: str):

    if not arg:
        return True, None
    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.exists(real):
        return False, "File or directory unavailable"
    st = os.stat(real)
    kind = "directory" if os.path.isdir(real) else "file"
    modified = datetime.fromtimestamp(st.st_mtime).strftime("%Y%m%d%H%M%S")
    info = f"{virtual} - {kind}, {st.st_size} bytes, modified {modified}"
    return True, info




def file_size(cwd: str, arg: str):
    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.isfile(real):
        return False, "File unavailable"
    size_bytes = os.path.getsize(real)
    return True, f"{size_bytes} bytes ({human_readable_size(size_bytes)})"


def file_mdtm(cwd: str, arg: str):
    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.isfile(real):
        return False, "File unavailable"
    ts = datetime.fromtimestamp(os.path.getmtime(real)).strftime("%Y%m%d%H%M%S")
    return True, ts




def delete_file(cwd: str, arg: str):
    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.isfile(real):
        return False, "File unavailable"
    try:
        os.remove(real)
        return True, virtual
    except OSError as e:
        return False, f"Cannot delete file: {e}"



def check_rename_from(cwd: str, arg: str):

    virtual, real = resolve_path(cwd, arg)
    if virtual is None or not os.path.exists(real):
        return False, "File or directory unavailable"
    return True, virtual


def do_rename(cwd: str, old_virtual: str, new_arg: str):

    _, old_real = resolve_path(cwd, old_virtual)
    new_virtual, new_real = resolve_path(cwd, new_arg)
    if new_virtual is None:
        return False, "New path escapes server root"
    if os.path.exists(new_real):
        return False, "Target name already exists"
    try:
        os.rename(old_real, new_real)
        return True, f"{old_virtual} -> {new_virtual}"
    except OSError as e:
        return False, f"Cannot rename: {e}"




def generate_unique_filename(cwd: str, base_name: str = "upload"):

    _, real_dir = resolve_path(cwd, "")
    n = 1
    while True:
        candidate = f"{base_name}_{n}.dat"
        if not os.path.exists(os.path.join(real_dir, candidate)):
            return candidate
        n += 1