import hashlib
import os

def calculate_hash(file_path, algorithm='md5'):
    """
    Calculates the hash of a file using MD5 or SHA-256.
    Reads file in blocks of 8192 bytes to handle large files.
    """
    if algorithm.lower() not in ('md5', 'sha256', 'sha-256'):
        raise ValueError("Unsupported hashing algorithm. Choose 'md5' or 'sha256'.")
    
    algo_name = 'sha256' if algorithm.lower() in ('sha256', 'sha-256') else 'md5'
    hasher = hashlib.new(algo_name)
    
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        return ""

def verify_file_hash(file_path, expected_hash, algorithm='md5'):
    """
    Compares the calculated hash of the file with the expected hash.
    Returns True if they match, False otherwise.
    """
    actual_hash = calculate_hash(file_path, algorithm)
    if not actual_hash:
        return False
    return actual_hash.lower() == expected_hash.strip().lower()
