
#!/bin/bash
cd "$(dirname "$0")/.."

TESTNAME="high_loss"
LOGDIR="logs/$TESTNAME"
OUT="tests/received_${TESTNAME}.bin"

echo "=== HIGH LOSS TEST ==="

rm -rf "$LOGDIR"
mkdir -p "$LOGDIR"
rm -f "$OUT" logs/*.log

python3 prtp_receiver.py \
  --bind-ip 127.0.0.1 --bind-port 9205 \
  --out "$OUT" --loss-ack 0.20 --corrupt-ack 0.05 &
RPID=$!

sleep 0.3

python3 prtp_sender.py \
  --server-ip 127.0.0.1 --server-port 9205 \
  --file test.bin --loss 0.20 --corrupt 0.05

kill "$RPID" 2>/dev/null

mv logs/sender.log "$LOGDIR/sender.log"
mv logs/receiver.log "$LOGDIR/receiver.log"

echo "MD5 original: $(md5sum test.bin | awk '{print $1}')"
echo "MD5 received: $(md5sum $OUT | awk '{print $1}')"
