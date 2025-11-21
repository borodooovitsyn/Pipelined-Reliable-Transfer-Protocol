import struct
import zlib

HEADER_FORMAT = "!IIHHBH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

FLAG_SYN = 0x01
FLAG_ACK = 0x02
FLAG_FIN = 0x04

def _crc16(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFF

def make_packet(seq: int, ack: int, wnd: int, flags: int, payload: bytes) -> bytes:
    length = len(payload)
    header = struct.pack(HEADER_FORMAT, seq, ack, wnd, length, flags, 0)
    checksum = _crc16(header + payload)
    header = struct.pack(HEADER_FORMAT, seq, ack, wnd, length, flags, checksum)
    return header + payload

def parse_packet(data: bytes):
    if len(data) < HEADER_SIZE:
        return None
    header = data[:HEADER_SIZE]
    seq, ack, wnd, length, flags, checksum = struct.unpack(HEADER_FORMAT, header)
    payload = data[HEADER_SIZE:]
    if len(payload) != length:
        corrupted = True
    else:
        header_zero = struct.pack(HEADER_FORMAT, seq, ack, wnd, length, flags, 0)
        calc = _crc16(header_zero + payload)
        corrupted = calc != checksum
    return seq, ack, wnd, flags, payload, corrupted
