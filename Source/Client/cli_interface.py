import sys

# ANSI Colors
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_SUCCESS = "\033[92m"  # Light Green
COLOR_ERROR = "\033[91m"    # Light Red
COLOR_INFO = "\033[96m"     # Light Cyan
COLOR_WARNING = "\033[93m"  # Light Yellow

def enable_windows_ansi():
    """
    Enables ANSI escape sequence processing on Windows Command Prompt if needed.
    """
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # 0xfffffff5 is STD_OUTPUT_HANDLE
            h_out = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING is 0x0004
                kernel32.SetConsoleMode(h_out, mode.value | 0x0004)
        except Exception:
            pass

# Enable ANSI on initialization
enable_windows_ansi()

def print_success(message):
    print(f"{COLOR_SUCCESS}[SUCCESS] {message}{COLOR_RESET}")

def print_error(message):
    print(f"{COLOR_ERROR}[ERROR] {message}{COLOR_RESET}", file=sys.stderr)

def print_info(message):
    print(f"{COLOR_INFO}[INFO] {message}{COLOR_RESET}")

def print_warning(message):
    print(f"{COLOR_WARNING}[WARNING] {message}{COLOR_RESET}")

def print_header(title):
    border = "=" * (len(title) + 8)
    print(f"\n{COLOR_BOLD}{COLOR_INFO}{border}")
    print(f"|   {title}   |")
    print(f"{border}{COLOR_RESET}\n")

def print_client_prompt():
    """
    Prints a clean, styled client input prompt.
    """
    sys.stdout.write(f"{COLOR_BOLD}{COLOR_SUCCESS}ftp-client> {COLOR_RESET}")
    sys.stdout.flush()
