#!/bin/bash
cd "$(dirname "$0")/.."

TESTNAME="medium_loss"
LOGDIR="logs/$TESTNAME"
OUT="tests/received_${TESTNAME}.bin"

echo "=== MEDIUM LOSS TEST ==="

rm -rf "$LOGDIR"
mkdir -p "$LOGDIR"
rm -f "$OUT" logs/*.log

python3 prtp_receiver.py \
  --bind-ip 127.0.0.1 --bind-port 9204 \
  --out "$OUT" --loss-ack 0.05 --corrupt-ack 0.01 &
RPID=$!

sleep 0.2

python3 prtp_sender.py \
  --server-ip 127.0.0.1 --server-port 9204 \
  --file test.bin --loss 0.05 --corrupt 0.01

kill "$RPID" 2>/dev/null

mv logs/sender.log "$LOGDIR/sender.log"
mv logs/receiver.log "$LOGDIR/receiver.log"

echo "MD5 original: $(md5sum test.bin | awk '{print $1}')"
echo "MD5 received: $(md5sum $OUT | awk '{print $1}')"
