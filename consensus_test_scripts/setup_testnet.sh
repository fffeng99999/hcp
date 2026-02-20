#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
HCP_DIR="$PROJECT_ROOT/hcp"
START_SCRIPT="$HCP_DIR/start_nodes.sh"
LOG_DIR="$PROJECT_ROOT/logs/consensus_test"
NUM_NODES=${1:-12}

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "Initializing ${NUM_NODES}-node testnet..."

# Clean up previous runs
pkill -f hcpd
rm -rf "$PROJECT_ROOT/.hcp_nodes"

# Start the nodes (using the existing robust script)
# We run it in the background and redirect output
# The start_nodes.sh script is blocking, so we need to handle it.
# However, for the test, we want it to run.
# We will just execute it. The user/python script will handle the lifecycle.

# If we run this script directly, it should just start the nodes.
bash "$START_SCRIPT" "$NUM_NODES"
