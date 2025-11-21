import socket
import argparse
import time
from prtp_packet import make_packet, parse_packet, FLAG_SYN, FLAG_ACK, FLAG_FIN
from prtp_channel import unreliable_send

MSS = 1000
RTO = 0.5

def client_handshake(sock, server_addr):
    sock.settimeout(1.0)
    client_isn = 0
    syn_pkt = make_packet(client_isn, 0, 0, FLAG_SYN, b"")
    server_isn = None
    while True:
        sock.sendto(syn_pkt, server_addr)
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        parsed = parse_packet(data)
        if not parsed:
            continue
        seq, ack, wnd, flags, payload, corrupted = parsed
        if corrupted:
            continue
        if flags & FLAG_SYN and flags & FLAG_ACK and ack == client_isn + 1:
            server_isn = seq
            break
    ack_pkt = make_packet(client_isn + 1, server_isn + 1, 0, FLAG_ACK, b"")
    sock.sendto(ack_pkt, server_addr)
    sock.settimeout(None)
    return client_isn + 1

def load_segments(filename):
    with open(filename, "rb") as f:
        data = f.read()
    segments = []
    i = 0
    n = len(data)
    while i < n:
        segments.append(data[i:i + MSS])
        i += MSS
    return segments

def send_file(sock, server_addr, filename, start_seq, loss_prob, corrupt_prob):
    segments = load_segments(filename)
    num_segments = len(segments)
    if num_segments == 0:
        return start_seq
    final_seq = start_seq + num_segments - 1
    send_base = start_seq
    next_seq = start_seq
    last_acked = start_seq - 1
    cwnd = 1.0
    ssthresh = 32.0
    ack_count = 0.0
    remote_rwnd = 1000
    unacked = {}
    timer_start = None
    sock.settimeout(0.05)
    while last_acked < final_seq:
        send_window = int(min(cwnd, remote_rwnd))
        if send_window < 1:
            send_window = 1
        while next_seq <= final_seq and next_seq < send_base + send_window:
            idx = next_seq - start_seq
            payload = segments[idx]
            pkt = make_packet(next_seq, 0, 0, 0, payload)
            unreliable_send(sock, pkt, server_addr, loss_prob, corrupt_prob)
            now = time.time()
            unacked[next_seq] = (pkt, now)
            if send_base == next_seq:
                timer_start = now
            next_seq += 1
        try:
            data, addr = sock.recvfrom(65535)
            parsed = parse_packet(data)
            if not parsed:
                continue
            seq, ack, wnd, flags, payload, corrupted = parsed
            if corrupted:
                continue
            if not (flags & FLAG_ACK):
                continue
            ack_num = ack
            if wnd >= 0:
                remote_rwnd = wnd
            if ack_num > last_acked:
                last_acked = ack_num
            if ack_num >= send_base:
                to_delete = [s for s in unacked if s <= ack_num]
                for s in to_delete:
                    del unacked[s]
                send_base = ack_num + 1
                if cwnd < ssthresh:
                    cwnd += 1.0
                else:
                    ack_count += 1.0
                    if ack_count >= cwnd:
                        cwnd += 1.0
                        ack_count = 0.0
                if unacked:
                    timer_start = time.time()
                else:
                    timer_start = None
        except socket.timeout:
            pass
        if unacked and timer_start is not None:
            now = time.time()
            if now - timer_start >= RTO:
                ssthresh = max(cwnd / 2.0, 1.0)
                cwnd = 1.0
                ack_count = 0.0
                for s in sorted(unacked):
                    pkt, _ = unacked[s]
                    unreliable_send(sock, pkt, server_addr, loss_prob, corrupt_prob)
                    unacked[s] = (pkt, time.time())
                timer_start = time.time()
    return final_seq + 1

def teardown(sock, server_addr, seq_for_fin, loss_prob, corrupt_prob):
    fin_pkt = make_packet(seq_for_fin, 0, 0, FLAG_FIN, b"")
    sock.settimeout(1.0)
    attempts = 0
    while attempts < 3:
        unreliable_send(sock, fin_pkt, server_addr, loss_prob, corrupt_prob)
        attempts += 1
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        parsed = parse_packet(data)
        if not parsed:
            continue
        seq, ack, wnd, flags, payload, corrupted = parsed
        if corrupted:
            continue
        if flags & FLAG_ACK and flags & FLAG_FIN:
            break
    sock.settimeout(None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", type=str, required=True)
    parser.add_argument("--server-port", type=int, required=True)
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--loss", type=float, default=0.1)
    parser.add_argument("--corrupt", type=float, default=0.05)
    args = parser.parse_args()
    addr = (args.server_ip, args.server_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_seq = client_handshake(sock, addr)
    next_seq = send_file(sock, addr, args.file, start_seq, args.loss, args.corrupt)
    teardown(sock, addr, next_seq, args.loss, args.corrupt)
    sock.close()

if __name__ == "__main__":
    main()
