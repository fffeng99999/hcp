#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
HCP_CONSENSUS_DIR="$PROJECT_ROOT/hcp-consensus"
DATA_ROOT="${DATA_ROOT:-$PROJECT_ROOT/.hcp_nodes}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/nodes}"
CHAIN_ID="hcp-testnet-1"
BINARY="$PROJECT_ROOT/build/hcpd"
NUM_NODES=${1:-4} # Default to 4 nodes

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
    pkill -f "$BINARY"
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

init_node() {
    local id=$1
    local rpc_port=$((26657 + (id-1)*10))
    local p2p_port=$((26656 + (id-1)*10))
    local grpc_port=$((9090 + (id-1)*2))
    local api_port=$((1317 + id - 1))
    local pprof_port=$((6060 + id))
    
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
    sed -i "s#addr_book_strict = true#addr_book_strict = false#g" "$config_file"
    sed -i "s#pprof_laddr = \"localhost:6060\"#pprof_laddr = \"localhost:$pprof_port\"#g" "$config_file"
    
    # Update ports in app.toml (gRPC and API)
    sed -i "s#0.0.0.0:9090#0.0.0.0:$grpc_port#g" "$app_file"
    sed -i "s#0.0.0.0:1317#0.0.0.0:$api_port#g" "$app_file"
    sed -i "s#enable = false#enable = true#g" "$app_file"
}

# Initialize Nodes
for (( i=1; i<=NUM_NODES; i++ )); do
    init_node $i
done

# Collect GenTXs
log_info "Collecting GenTXs..."
mkdir -p "$DATA_ROOT/node1/config/gentx"

# Add other nodes' accounts to node1 genesis
log_info "Adding other nodes' accounts to node1 genesis..."
for (( i=2; i<=NUM_NODES; i++ )); do
    addr=$(cat "$DATA_ROOT/node$i/address")
    "$BINARY" genesis add-genesis-account "$addr" 1000000000000000000stake --home "$DATA_ROOT/node1"
done

for (( i=2; i<=NUM_NODES; i++ )); do
    cp "$DATA_ROOT/node$i/config/gentx"/*.json "$DATA_ROOT/node1/config/gentx/"
done

"$BINARY" genesis collect-gentxs --home "$DATA_ROOT/node1" > "$LOG_DIR/collect_gentxs.log" 2>&1

# Distribute Genesis
log_info "Distributing genesis.json..."
for (( i=2; i<=NUM_NODES; i++ )); do
    cp "$DATA_ROOT/node1/config/genesis.json" "$DATA_ROOT/node$i/config/genesis.json"
done

# Configure Peers
log_info "Configuring Persistent Peers..."
get_node_id() {
    "$BINARY" tendermint show-node-id --home "$DATA_ROOT/node$1"
}

PEERS=""
for (( i=1; i<=NUM_NODES; i++ )); do
    NODE_ID=$(get_node_id $i)
    P2P_PORT=$((26656 + (i-1)*10))
    if [ -n "$PEERS" ]; then
        PEERS="${PEERS},"
    fi
    PEERS="${PEERS}${NODE_ID}@127.0.0.1:${P2P_PORT}"
done

for (( i=1; i<=NUM_NODES; i++ )); do
    sed -i "s#persistent_peers = \".*\"#persistent_peers = \"$PEERS\"#g" "$DATA_ROOT/node$i/config/config.toml"
done

# Start Nodes
start_node() {
    local id=$1
    local home="$DATA_ROOT/node$id"
    log_info "Starting Node $id..."
    "$BINARY" start --home "$home" --minimum-gas-prices 0stake > "$LOG_DIR/node$id.log" 2>&1 &
}

for (( i=1; i<=NUM_NODES; i++ )); do
    start_node $i
done

log_info "All $NUM_NODES nodes started. Logs in $LOG_DIR"
log_info "Tail logs with: tail -f $LOG_DIR/node*.log"

# Keep script running
wait
