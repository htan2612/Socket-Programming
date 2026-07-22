import struct

HEADER_FORMAT = "!IIBHH" 
# chuỗi định dạng để encode với decode, 
# I = unsigned int (4Byte) seq_num, ack_num
# B = unsigned char (1Byte) flags
# H = unsigned short(2Byte) payload_size/length, checksum
HEADER_SIZE = struct.calcsize(HEADER_FORMAT) #13 bytes

FLAG_DATA = 0x01 #packet data
FLAG_ACK = 0x02 #packet ACK
FLAG_FIN = 0x04 #end packet

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

