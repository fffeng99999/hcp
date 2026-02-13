#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "============================================"
echo "   HCP Consensus 12-Node Performance Test   "
echo "============================================"

# Ensure cleanup on exit
cleanup() {
    echo "Stopping network nodes..."
    pkill -f hcpd
    echo "Cleanup complete."
}
trap cleanup EXIT

# 1. Start Network
echo "[1/3] Launching 12-node network..."
# We run setup in background. 
# Note: setup_testnet.sh runs start_nodes.sh which blocks.
./setup_testnet.sh > network.log 2>&1 &
SETUP_PID=$!

echo "Network process running (PID: $SETUP_PID). Logs in network.log"

# 2. Wait for Network Readiness
echo "[2/3] Waiting for network initialization..."
echo "Waiting for Node 1 (RPC 26657) and Node 12 (RPC 26767)..."

MAX_RETRIES=60
count=0
while [ $count -lt $MAX_RETRIES ]; do
    # Check if process died
    if ! kill -0 $SETUP_PID 2>/dev/null; then
        echo "Network setup script failed! Check network.log"
        exit 1
    fi

    # Check ports using python one-liner to avoid nc dependency issues
    if python3 -c "import socket; s = socket.socket(); s.settimeout(1); exit(0) if s.connect_ex(('localhost', 26657)) == 0 and s.connect_ex(('localhost', 26767)) == 0 else exit(1)"; then
        echo "RPC ports are open."
        break
    fi
    
    echo -n "."
    sleep 2
    count=$((count+1))
done

if [ $count -eq $MAX_RETRIES ]; then
    echo "Timeout waiting for nodes to start."
    exit 1
fi

# Wait for first block (give it 10s extra)
echo "Waiting 10s for block production..."
sleep 10

# 3. Run Test
echo "[3/3] Executing Performance Test Script..."
if python3 perf_test.py; then
    echo "Test executed successfully."
else
    echo "Test script failed."
    exit 1
fi

echo "============================================"
echo "Analysis Report: $(pwd)/consensus_perf_report.md"
echo "============================================"
