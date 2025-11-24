#!/bin/bash
cd "$(dirname "$0")"

echo "[+] Killing old PRTP processes..."
pkill -f prtp_receiver.py 2>/dev/null
pkill -f prtp_sender.py 2>/dev/null
sleep 0.3

FILE="test.bin"
RECV_A="recv_A.bin"
RECV_B="recv_B.bin"

PORT_A=6000
PORT_B=6001

LOG="fairness_parallel.log"

echo "============================" | tee $LOG
echo " PARALLEL EXACT-START FAIRNESS TEST " | tee -a $LOG
echo "============================" | tee -a $LOG
echo "" | tee -a $LOG

echo "[+] Creating 1MB test.bin..." | tee -a $LOG
dd if=/dev/urandom of=$FILE bs=200K count=1 status=none
ls -lh $FILE | tee -a $LOG
echo "" | tee -a $LOG

rm -f $RECV_A $RECV_B

echo "[+] Starting receivers..." | tee -a $LOG

python3 ../prtp_receiver.py --bind-ip 127.0.0.1 --bind-port $PORT_A --out $RECV_A &
PID_RX_A=$!

python3 ../prtp_receiver.py --bind-ip 127.0.0.1 --bind-port $PORT_B --out $RECV_B &
PID_RX_B=$!

sleep 0.4
echo "Receiver A PID: $PID_RX_A" | tee -a $LOG
echo "Receiver B PID: $PID_RX_B" | tee -a $LOG
echo "" | tee -a $LOG

echo "[+] Starting live file size logging..." | tee -a $LOG

(
    while kill -0 $PID_RX_A 2>/dev/null || kill -0 $PID_RX_B 2>/dev/null; do
        SA=$(stat -f%z "$RECV_A" 2>/dev/null || echo 0)
        SB=$(stat -f%z "$RECV_B" 2>/dev/null || echo 0)
        echo "[LIVE] A: $SA bytes | B: $SB bytes" | tee -a $LOG
        sleep 1
    done
) &
PID_LOG=$!

echo "[+] Starting senders IN PARALLEL..." | tee -a $LOG

START=$(date +%s)

python3 ../prtp_sender.py --server-ip 127.0.0.1 --server-port $PORT_A --file $FILE &
PID_SND_A=$!

python3 ../prtp_sender.py --server-ip 127.0.0.1 --server-port $PORT_B --file $FILE &
PID_SND_B=$!

wait $PID_SND_A
END_A=$(date +%s)
wait $PID_SND_B
END_B=$(date +%s)

TIME_A=$((END_A - START))
TIME_B=$((END_B - START))

echo "[+] Sender A finished in $TIME_A sec" | tee -a $LOG
echo "[+] Sender B finished in $TIME_B sec" | tee -a $LOG
echo "" | tee -a $LOG

kill $PID_LOG 2>/dev/null

SIZE_BITS=$(($(stat -f%z $FILE) * 8))

THR_A=$(echo "scale=3; $SIZE_BITS / $TIME_A / 1000000" | bc)
THR_B=$(echo "scale=3; $SIZE_BITS / $TIME_B / 1000000" | bc)

echo "[+] Throughput A: $THR_A Mbps" | tee -a $LOG
echo "[+] Throughput B: $THR_B Mbps" | tee -a $LOG
echo "" | tee -a $LOG

echo "[+] Verifying checksums..." | tee -a $LOG
SHA_ORIG=$(shasum $FILE | awk '{print $1}')
SHA_A=$(shasum $RECV_A | awk '{print $1}')
SHA_B=$(shasum $RECV_B | awk '{print $1}')

echo "Original: $SHA_ORIG" | tee -a $LOG
echo "Flow A:  $SHA_A" | tee -a $LOG
echo "Flow B:  $SHA_B" | tee -a $LOG

if [[ "$SHA_ORIG" == "$SHA_A" && "$SHA_ORIG" == "$SHA_B" ]]; then
    echo " Checksums match — both transfers correct." | tee -a $LOG
else
    echo " ERROR: Checksum mismatch." | tee -a $LOG
fi

DIFF=$(echo "($THR_A - $THR_B)" | bc | tr -d '-')

echo "" | tee -a $LOG
echo "============================" | tee -a $LOG
echo "       FAIRNESS RESULT       " | tee -a $LOG
echo "============================" | tee -a $LOG
echo "A = $THR_A Mbps" | tee -a $LOG
echo "B = $THR_B Mbps" | tee -a $LOG

if [[ $(echo "$DIFF < 1.0" | bc -l) -eq 1 ]]; then
    echo "Fair — Throughputs are similar." | tee -a $LOG
else
    echo " Not fair — Throughputs differ too much." | tee -a $LOG
fi

echo "" | tee -a $LOG
echo "[+] Log saved to $LOG"
