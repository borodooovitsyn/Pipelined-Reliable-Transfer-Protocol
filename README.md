# Pipelined Reliable Transfer Protocol

This project implements a TCP-like reliable, connection-oriented, pipelined transport protocol over UDP.  
Features included:

- 3-way handshake  
- Go-Back-N pipelining  
- Sliding window  
- Retransmissions + timeout  
- Flow control (rwnd)  
- Congestion control (Slow Start + AIMD)  
- Loss & corruption simulation  
- Logging for sender/receiver  
- Automated testing scripts  

---

# Project Files

prtp_sender.py # Sender
prtp_receiver.py # Receiver
prtp_packet.py # Packet format + checksum
prtp_channel.py # Loss + corruption simulator
tests/ # Automated test scripts
logs/ # Auto-generated logs


---

# Requirements

- Python 3.10+
- macOS / Linux recommended

---

# Running Manually

### 1. Start receiver
```bash
python3 prtp_receiver.py --bind-ip 127.0.0.1 --bind-port 9000 --out received.bin
```
### 2. Start sender
```bash
python3 prtp_sender.py --server-ip 127.0.0.1 --server-port 9000 --file test.bin
```

---

# Running Automated Tests

Make scripts executable (once):
```bash
chmod +x tests/*.sh
```

Run all tests:
```bash
./tests/run_all_tests.sh
```
---

# Output Locations

Test logs: logs/<testname>/

Received files: tests/received_<testname>.bin

MD5 validation printed automatically

---

# Wireshark Capture

To record traffic:

Start receiver

Start Wireshark (lo0 on macOS, any on Linux)

Run sender

Filter: udp.port == 9000

---

# Troubleshooting

Port already in use:

```bash
pkill -f prtp_receiver.py
pkill -f prtp_sender.py
```

test.bin missing:

```bash
head -c 1M </dev/urandom > test.bin
```
