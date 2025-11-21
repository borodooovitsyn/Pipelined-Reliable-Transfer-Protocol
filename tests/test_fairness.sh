#!/bin/bash
cd "$(dirname "$0")/.."

TESTNAME="fairness"
LOGDIR="logs/$TESTNAME"

echo "=== FAIRNESS TEST ==="

rm -rf "$LOGDIR"
mkdir -p "$LOGDIR"
rm -f logs/*.log tests/received_fair*

# Receiver A
python3 prtp_receiver.py --bind-ip 127.0.0.1 --bind-port 9311 \
  --out tests/received_fair1.bin &
R1=$!

# Receiver B
python3 prtp_receiver.py --bind-ip 127.0.0.1 --bind-port 9312 \
  --out tests/received_fair2.bin &
R2=$!

sleep 0.3

# Sender A
python3 prtp_sender.py --server-ip 127.0.0.1 --server-port 9311 \
  --file test.bin --loss 0.05 --corrupt 0.02 &
S1=$!

# Sender B
python3 prtp_sender.py --server-ip 127.0.0.1 --server-port 9312 \
  --file test.bin --loss 0.05 --corrupt 0.02 &
S2=$!

wait $S1
wait $S2

kill $R1 2>/dev/null
kill $R2 2>/dev/null

mv logs/*.log "$LOGDIR"/

echo "[DONE] fairness logs → $LOGDIR/"
