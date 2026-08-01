import os
import sys
import struct

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import HEADER_FORMAT, HEADER_SIZE, FLAG_ACK, FLAG_FIN, FLAG_DATA

def calculate_checksum(data : bytes) -> int:
    if len(data) % 2 == 1:
        data += b'\x00'
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        checksum += word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    return ~checksum & 0xFFFF

def pack_packet(seq: int, ack: int, flags: int, payload: bytes) -> bytes:
    length = len(payload)
    dummy_header = struct.pack(HEADER_FORMAT, seq, ack, 0, flags, length)
    checksum = calculate_checksum(dummy_header + payload)
    return struct.pack(HEADER_FORMAT, seq, ack, checksum, flags, length) + payload

def unpack_packet(raw_bytes : bytes):
    if len(raw_bytes) < HEADER_SIZE:
        return 0, 0, 0, 0, b"", False
    header_bytes = raw_bytes[:HEADER_SIZE]
    payload = raw_bytes[HEADER_SIZE:]
    seq, ack, checksum, flags, length = struct.unpack(HEADER_FORMAT, header_bytes)

    verify_header = struct.pack(HEADER_FORMAT, seq, ack, 0, flags, length)
    calc_cksum = calculate_checksum(verify_header + payload)

    is_valid = (calc_cksum == checksum)
    return seq, ack, flags, length, payload, is_valid
