#!/bin/bash

# ============================
#  TEST: HANDSHAKE ONLY
# ============================

cd "$(dirname "$0")/.."

TESTNAME="handshake"
LOGDIR="logs/$TESTNAME"

echo "=== HANDSHAKE TEST ==="

# Prepare log folder
rm -rf "$LOGDIR"
mkdir -p "$LOGDIR"

# Clear main log files
rm -f logs/sender.log logs/receiver.log

OUT="tests/received_handshake.bin"
rm -f "$OUT"

# Start receiver
python3 prtp_receiver.py \
    --bind-ip 127.0.0.1 \
    --bind-port 9201 \
    --out "$OUT" \
    &

RPID=$!

sleep 0.2

# Run sender
python3 prtp_sender.py \
    --server-ip 127.0.0.1 \
    --server-port 9201 \
    --file test.bin \
    --loss 0 \
    --corrupt 0

kill $RPID 2>/dev/null

# Move logs to test folder
mv logs/sender.log "$LOGDIR/sender.log" 2>/dev/null
mv logs/receiver.log "$LOGDIR/receiver.log" 2>/dev/null

echo "[DONE] Logs saved in → $LOGDIR/"
