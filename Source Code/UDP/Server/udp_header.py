import struct
from Common.protocol_constants import  HEADER_FORMAT,HEADER_SIZE,FLAG_ACK,FLAG_FIN,FLAG_DATA

def calculate_checksum(data : bytes) -> int:
    if len(data) % 2 == 1:
        data+=b'\x00'
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        checksum += word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    return ~checksum & 0xFFFF

def pack_packet(seq:int, ack:int, flags:int,payload:bytes) -> bytes:
    length = len(payload)
    dummy_header = struct.pack(HEADER_FORMAT,seq,ack,flags,length,0)
    checksum = calculate_checksum(dummy_header + payload)

    return struct.pack(HEADER_FORMAT,seq,ack,flags,checksum) + payload

def unpack_packet(raw_bytes : bytes):
    header_bytes = raw_bytes[:HEADER_SIZE]
    payload = raw_bytes[HEADER_SIZE:]
    seq,ack,flags,length,checksum = struct.unpack(HEADER_FORMAT, header_bytes)

    verify_header = struct.pack(HEADER_FORMAT, seq, ack, flags, length, 0)
    calc_cksum = calculate_checksum(verify_header + payload)

    is_valid = (calc_cksum == checksum)
    return seq, ack, flags, length, payload, is_valid

