import random

def corrupt_bytes(data: bytes) -> bytes:
    if not data:
        return data
    b = bytearray(data)
    i = random.randint(0, len(b) - 1)
    b[i] ^= 0xFF
    return bytes(b)

def unreliable_send(sock, data: bytes, addr, loss_prob: float, corrupt_prob: float):
    r = random.random()
    if r < loss_prob:
        return
    if random.random() < corrupt_prob:
        data = corrupt_bytes(data)
    sock.sendto(data, addr)
