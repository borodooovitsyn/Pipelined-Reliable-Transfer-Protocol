#!/bin/bash
cd "$(dirname "$0")/.."

TESTNAME="long_file"
LOGDIR="logs/$TESTNAME"
OUT="tests/received_${TESTNAME}.bin"
LONGFILE="tests/long_test.bin"

echo "=== LONG FILE (10MB) TEST ==="

dd if=/dev/urandom of="$LONGFILE" bs=1M count=10 status=none

rm -rf "$LOGDIR"
mkdir -p "$LOGDIR"
rm -f "$OUT" logs/*.log

python3 prtp_receiver.py \
  --bind-ip 127.0.0.1 --bind-port 9209 --out "$OUT" &
RPID=$!

sleep 0.3

python3 prtp_sender.py \
  --server-ip 127.0.0.1 --server-port 9209 \
  --file "$LONGFILE" --loss 0.05 --corrupt 0.02

kill "$RPID" 2>/dev/null

mv logs/sender.log "$LOGDIR/sender.log"
mv logs/receiver.log "$LOGDIR/receiver.log"

echo "MD5 original: $(md5sum $LONGFILE | awk '{print $1}')"
echo "MD5 received: $(md5sum $OUT | awk '{print $1}')"
