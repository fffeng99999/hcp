#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
HCP_CONSENSUS_DIR="$PROJECT_ROOT/hcp-consensus"
DATA_ROOT="$PROJECT_ROOT/.hcp_4nodes"
LOG_DIR="$PROJECT_ROOT/logs/4nodes"
CHAIN_ID="hcp-testnet-1"
BINARY="$PROJECT_ROOT/build/hcpd"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO] $1${NC}"; }
log_warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
log_error() { echo -e "${RED}[ERROR] $1${NC}"; }

# Cleanup function
cleanup() {
    log_info "Stopping all nodes..."
    pkill -f "hcpd"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Setup directories
rm -rf "$DATA_ROOT"
mkdir -p "$DATA_ROOT"
mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$BINARY")"

# Build binary
log_info "Building hcpd binary..."
cd "$HCP_CONSENSUS_DIR" || exit 1
go build -o "$BINARY" cmd/hcpd/main.go
if [ $? -ne 0 ]; then
    log_error "Failed to build hcpd"
    exit 1
fi

# Node Configuration
# Node 1: RPC 26657, P2P 26656, gRPC 9090
# Node 2: RPC 26667, P2P 26666, gRPC 9092
# Node 3: RPC 26677, P2P 26676, gRPC 9094
# Node 4: RPC 26687, P2P 26686, gRPC 9096

init_node() {
    local id=$1
    local rpc_port=$2
    local p2p_port=$3
    local grpc_port=$4
    local node_dir="$DATA_ROOT/node$id"
    
    log_info "Initializing Node $id..."
    
    # Init
    "$BINARY" init "node$id" --chain-id "$CHAIN_ID" --home "$node_dir" > /dev/null 2>&1
    
    # Config keys
    "$BINARY" keys add "node$id" --keyring-backend test --home "$node_dir" --output json > "$node_dir/key_info.json" 2>&1
    local key_address=$(jq -r .address "$node_dir/key_info.json")
    echo "$key_address" > "$node_dir/address"
    
    # Add genesis account
    "$BINARY" genesis add-genesis-account "$key_address" 1000000000000000000stake --home "$node_dir"
    
    # GenTx
    "$BINARY" genesis gentx "node$id" 1000000000000000stake --chain-id "$CHAIN_ID" --keyring-backend test --home "$node_dir" > "$LOG_DIR/gentx_node$id.log" 2>&1
    
    # Configure config.toml
    local config_file="$node_dir/config/config.toml"
    local app_file="$node_dir/config/app.toml"
    
    # Update ports in config.toml
    sed -i "s#tcp://127.0.0.1:26657#tcp://127.0.0.1:$rpc_port#g" "$config_file"
    sed -i "s#tcp://0.0.0.0:26656#tcp://0.0.0.0:$p2p_port#g" "$config_file"
    sed -i "s#allow_duplicate_ip = false#allow_duplicate_ip = true#g" "$config_file"
    
    # Update ports in app.toml (gRPC and API)
    sed -i "s#0.0.0.0:9090#0.0.0.0:$grpc_port#g" "$app_file"
    # Disable API server for simplicity or assign unique port (we'll just let it conflict/fail or disable it if not needed, 
    # but better to assign unique. Default is 1317. Let's make it 1317 + id - 1 -> 1317, 1318, 1319, 1320)
    local api_port=$((1317 + id - 1))
    sed -i "s#0.0.0.0:1317#0.0.0.0:$api_port#g" "$app_file"
    
    # Enable API
    sed -i "s#enable = false#enable = true#g" "$app_file"
}

# Initialize 4 nodes
init_node 1 26657 26656 9090
init_node 2 26667 26666 9092
init_node 3 26677 26676 9094
init_node 4 26687 26686 9096

# Collect GenTXs
log_info "Collecting GenTXs..."
mkdir -p "$DATA_ROOT/node1/config/gentx"

# Add other nodes' accounts to node1 genesis
log_info "Adding other nodes' accounts to node1 genesis..."
for i in 2 3 4; do
    addr=$(cat "$DATA_ROOT/node$i/address")
    "$BINARY" genesis add-genesis-account "$addr" 1000000000000000000stake --home "$DATA_ROOT/node1"
done

for i in 2 3 4; do
    cp "$DATA_ROOT/node$i/config/gentx"/*.json "$DATA_ROOT/node1/config/gentx/"
done

"$BINARY" genesis collect-gentxs --home "$DATA_ROOT/node1" > "$LOG_DIR/collect_gentxs.log" 2>&1

# Distribute Genesis
log_info "Distributing genesis.json..."
for i in 2 3 4; do
    cp "$DATA_ROOT/node1/config/genesis.json" "$DATA_ROOT/node$i/config/genesis.json"
done

# Configure Peers
log_info "Configuring Persistent Peers..."
get_node_id() {
    "$BINARY" tendermint show-node-id --home "$DATA_ROOT/node$1"
}

NODE1_ID=$(get_node_id 1)
NODE2_ID=$(get_node_id 2)
NODE3_ID=$(get_node_id 3)
NODE4_ID=$(get_node_id 4)

# P2P Ports: 26656, 26666, 26676, 26686
PEERS="${NODE1_ID}@127.0.0.1:26656,${NODE2_ID}@127.0.0.1:26666,${NODE3_ID}@127.0.0.1:26676,${NODE4_ID}@127.0.0.1:26686"

for i in 1 2 3 4; do
    sed -i "s#persistent_peers = \"\"#persistent_peers = \"$PEERS\"#g" "$DATA_ROOT/node$i/config/config.toml"
done

# Start Nodes
start_node() {
    local id=$1
    local home="$DATA_ROOT/node$id"
    log_info "Starting Node $id..."
    "$BINARY" start --home "$home" --minimum-gas-prices 0stake > "$LOG_DIR/node$id.log" 2>&1 &
}

start_node 1
start_node 2
start_node 3
start_node 4

log_info "All 4 nodes started. Logs in $LOG_DIR"
log_info "Tail logs with: tail -f $LOG_DIR/node*.log"

# Keep script running
wait
