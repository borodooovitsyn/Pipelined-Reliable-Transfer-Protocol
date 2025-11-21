import socket
import argparse
import os
import time

from prtp_packet import make_packet, parse_packet, FLAG_SYN, FLAG_ACK, FLAG_FIN
from prtp_channel import unreliable_send

os.makedirs("logs", exist_ok=True)

MAX_RWND_SEGMENTS = 64


def log_receiver(msg):
    with open("logs/receiver.log", "a") as f:
        f.write(f"{time.time():.6f} [RECEIVER] {msg}\n")


def server_handshake(sock):
    client_addr = None
    client_isn = None
    server_isn = 100
    while True:
        data, addr = sock.recvfrom(4096)
        parsed = parse_packet(data)
        if not parsed:
            continue
        seq, ack, wnd, flags, payload, corrupted = parsed
        if corrupted:
            log_receiver("Corrupted SYN received → ignoring")
            continue
        if flags & FLAG_SYN:
            log_receiver("RECV SYN")
            client_addr = addr
            client_isn = seq
            synack = make_packet(server_isn, client_isn + 1, MAX_RWND_SEGMENTS, FLAG_SYN | FLAG_ACK, b"")
            sock.sendto(synack, client_addr)
            log_receiver("SEND SYN/ACK")
            break
    sock.settimeout(2.0)
    while True:
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            synack = make_packet(server_isn, client_isn + 1, MAX_RWND_SEGMENTS, FLAG_SYN | FLAG_ACK, b"")
            sock.sendto(synack, client_addr)
            log_receiver("RETX SYN/ACK")
            continue
        parsed = parse_packet(data)
        if not parsed:
            continue
        seq, ack, wnd, flags, payload, corrupted = parsed
        if corrupted:
            continue
        if addr != client_addr:
            continue
        if flags & FLAG_ACK and ack == server_isn + 1:
            log_receiver("Handshake complete")
            break
    sock.settimeout(None)
    start_seq = client_isn + 1
    return client_addr, start_seq

def receive_file(sock, client_addr, start_seq, out_file, loss_prob, corrupt_prob):
    f = open(out_file, "wb")
    expected_seq = start_seq
    last_acked = expected_seq - 1
    rwnd = MAX_RWND_SEGMENTS
    while True:
        data, addr = sock.recvfrom(65535)
        if addr != client_addr:
            continue
        parsed = parse_packet(data)
        if not parsed:
            continue
        seq, ack, wnd, flags, payload, corrupted = parsed
        log_receiver(f"RECV seq={seq} corrupted={corrupted}")
        if corrupted:
            log_receiver(f"CORRUPTED seq={seq} → SEND ACK={last_acked}")
            ack_pkt = make_packet(0, last_acked, rwnd, FLAG_ACK, b"")
            unreliable_send(sock, ack_pkt, client_addr, loss_prob, corrupt_prob)
            continue
        if flags & FLAG_FIN:
            log_receiver("RECV FIN → SEND FIN/ACK")
            fin_ack = make_packet(0, seq, rwnd, FLAG_FIN | FLAG_ACK, b"")
            unreliable_send(sock, fin_ack, client_addr, loss_prob, corrupt_prob)
            break
        if len(payload) == 0:
            continue
        if seq == expected_seq:
            log_receiver(f"WRITE seq={seq}")
            f.write(payload)
            last_acked = seq
            expected_seq += 1
        elif seq < expected_seq:
            last_acked = expected_seq - 1
        ack_pkt = make_packet(0, last_acked, rwnd, FLAG_ACK, b"")
        unreliable_send(sock, ack_pkt, client_addr, loss_prob, corrupt_prob)
        log_receiver(f"SEND ACK={last_acked}")
    f.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind-ip", type=str, default="0.0.0.0")
    parser.add_argument("--bind-port", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--loss-ack", type=float, default=0.05)
    parser.add_argument("--corrupt-ack", type=float, default=0.02)
    args = parser.parse_args()
    open("logs/receiver.log", "w").close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind_ip, args.bind_port))
    client_addr, start_seq = server_handshake(sock)
    receive_file(sock, client_addr, start_seq, args.out, args.loss_ack, args.corrupt_ack)
    sock.close()

if __name__ == "__main__":
    main()
