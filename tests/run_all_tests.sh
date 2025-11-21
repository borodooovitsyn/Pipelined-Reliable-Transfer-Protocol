#!/bin/bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== RUNNING ALL PROTOCOL TESTS ==="
chmod +x tests/*.sh

tests/test_handshake.sh
tests/test_basic_transfer.sh
tests/test_low_loss.sh
tests/test_medium_loss.sh
tests/test_high_loss.sh
tests/test_corruption_only.sh
tests/test_congestion_control.sh
tests/test_flow_control.sh
tests/test_long_file.sh
tests/test_fairness.sh

echo "=== ALL TESTS COMPLETED ==="
