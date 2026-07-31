import sys
import time

def print_progress(completed_bytes, total_bytes, start_time, prefix='', suffix='', decimals=1, bar_length=30):
    """
    Displays an interactive CLI progress bar with transfer speed and ETA.
    
    :param completed_bytes: Number of bytes transferred so far.
    :param total_bytes: Total number of bytes to transfer.
    :param start_time: Epoch time (time.time()) when the transfer started.
    :param prefix: Text prefix before progress bar.
    :param suffix: Text suffix after progress bar.
    :param decimals: Percent decimal precision.
    :param bar_length: Width of the progress bar in characters.
    """
    if total_bytes <= 0:
        return
    
    # Clamp completed_bytes to not exceed total_bytes
    if completed_bytes > total_bytes:
        completed_bytes = total_bytes

    # Calculate percentage
    percent = (completed_bytes / total_bytes) * 100
    format_str = f"{{0:.{decimals}f}}"
    percent_str = format_str.format(percent)
    
    # Calculate progress bar length
    filled_length = int(round(bar_length * completed_bytes / float(total_bytes)))
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Calculate speed
    elapsed_time = time.time() - start_time
    if elapsed_time > 0:
        speed = completed_bytes / elapsed_time  # Bytes/sec
        if speed < 1024:
            speed_str = f"{speed:.2f} B/s"
        elif speed < 1024 * 1024:
            speed_str = f"{speed / 1024:.2f} KB/s"
        else:
            speed_str = f"{speed / (1024 * 1024):.2f} MB/s"
            
        # Calculate ETA
        if speed > 0:
            remaining_bytes = total_bytes - completed_bytes
            eta = remaining_bytes / speed
            eta_minutes = int(eta // 60)
            eta_seconds = int(eta % 60)
            eta_str = f"ETA: {eta_minutes:02d}:{eta_seconds:02d}"
        else:
            eta_str = "ETA: --:--"
    else:
        speed_str = "0.00 B/s"
        eta_str = "ETA: --:--"
        
    # Human readable size conversion
    def get_readable_size(size_val):
        if size_val < 1024:
            return f"{size_val} B"
        elif size_val < 1024 * 1024:
            return f"{size_val / 1024:.2f} KB"
        else:
            return f"{size_val / (1024 * 1024):.2f} MB"
            
    completed_size_str = get_readable_size(completed_bytes)
    total_size_str = get_readable_size(total_bytes)
    
    # Construct output
    prefix_part = f"{prefix} " if prefix else ""
    suffix_part = f" {suffix}" if suffix else ""
    
    sys.stdout.write(
        f"\r{prefix_part}[{bar}] {percent_str}% | {completed_size_str}/{total_size_str} | {speed_str} | {eta_str}{suffix_part}"
    )
    sys.stdout.flush()
    
    # Print newline if complete
    if completed_bytes >= total_bytes:
        sys.stdout.write('\n')
        sys.stdout.flush()
