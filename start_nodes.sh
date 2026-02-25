#!/bin/bash

# Configuration
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$SCRIPT_DIR/.."
HCP_CONSENSUS_DIR="$PROJECT_ROOT/hcp-consensus"
DATA_ROOT="${DATA_ROOT:-$PROJECT_ROOT/.hcp_nodes}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/nodes}"
CHAIN_ID="${CHAIN_ID:-hcp-testnet-1}"
PORT_OFFSET="${PORT_OFFSET:-0}"
BINARY="${HCPD_BINARY:-$PROJECT_ROOT/hcp-consensus-build/hcpd}"
BUILD_TAGS="${BUILD_TAGS:-rocksdb}"
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
    pkill -f "$BINARY start"
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
go build -tags "$BUILD_TAGS" -o "$BINARY" cmd/hcpd/main.go
if [ $? -ne 0 ]; then
    log_error "Failed to build hcpd"
    exit 1
fi

init_node() {
    local id=$1
    local rpc_port=$((26657 + PORT_OFFSET + (id-1)*10))
    local p2p_port=$((26656 + PORT_OFFSET + (id-1)*10))
    local grpc_port=$((9090 + PORT_OFFSET + (id-1)*2))
    local api_port=$((1317 + PORT_OFFSET + id - 1))
    local pprof_port=$((6060 + PORT_OFFSET + id))
    local metrics_port=$((26660 + PORT_OFFSET + id - 1))
    
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
    sed -i "s#prometheus = false#prometheus = true#g" "$config_file"
    sed -i "s#prometheus_listen_addr = \":26660\"#prometheus_listen_addr = \":$metrics_port\"#g" "$config_file"
    
    # Update ports in app.toml (gRPC and API)
    # Handle both 0.0.0.0 and localhost defaults
    sed -i "s#0.0.0.0:9090#0.0.0.0:$grpc_port#g" "$app_file"
    sed -i "s#localhost:9090#0.0.0.0:$grpc_port#g" "$app_file"
    
    sed -i "s#0.0.0.0:1317#0.0.0.0:$api_port#g" "$app_file"
    sed -i "s#localhost:1317#0.0.0.0:$api_port#g" "$app_file"
    
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

EXTRA_ACCOUNT_COUNT="${EXTRA_ACCOUNT_COUNT:-100}"
ACCOUNTS_FILE="$DATA_ROOT/accounts.jsonl"
if [ "$EXTRA_ACCOUNT_COUNT" -gt 0 ]; then
    log_info "Creating $EXTRA_ACCOUNT_COUNT loadgen accounts..."
    : > "$ACCOUNTS_FILE"
    for (( i=1; i<=EXTRA_ACCOUNT_COUNT; i++ )); do
        name=$(printf "account%03d" "$i")
        key_json=$("$BINARY" keys add "$name" --keyring-backend test --home "$DATA_ROOT/node1" --output json 2>/dev/null)
        addr=$(echo "$key_json" | jq -r .address)
        echo "{\"name\":\"$name\",\"address\":\"$addr\"}" >> "$ACCOUNTS_FILE"
        "$BINARY" genesis add-genesis-account "$addr" 100000000000stake --home "$DATA_ROOT/node1"
    done
fi

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
    P2P_PORT=$((26656 + PORT_OFFSET + (i-1)*10))
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

    local start_args=("$BINARY" "start" "--home" "$home" "--minimum-gas-prices" "0stake")
    if [ -n "$CONSENSUS_ENGINE" ]; then
        start_args+=("--consensus-engine" "$CONSENSUS_ENGINE")
    fi
    if [ -z "$HIERARCHICAL_NODE_COUNT" ]; then
        HIERARCHICAL_NODE_COUNT="$NUM_NODES"
    fi
    if [ -n "$HIERARCHICAL_NODE_COUNT" ]; then
        start_args+=("--hierarchical-node-count" "$HIERARCHICAL_NODE_COUNT")
    fi
    if [ -n "$HIERARCHICAL_GROUP_COUNT" ]; then
        start_args+=("--hierarchical-group-count" "$HIERARCHICAL_GROUP_COUNT")
    fi
    if [ -n "$HIERARCHICAL_GROUP_SIZE" ]; then
        start_args+=("--hierarchical-group-size" "$HIERARCHICAL_GROUP_SIZE")
    fi
    if [ -n "$HIERARCHICAL_MESSAGE_BYTES" ]; then
        start_args+=("--hierarchical-message-bytes" "$HIERARCHICAL_MESSAGE_BYTES")
    fi
    if [ -n "$HIERARCHICAL_BASE_LATENCY_MS" ]; then
        start_args+=("--hierarchical-base-latency-ms" "$HIERARCHICAL_BASE_LATENCY_MS")
    fi
    if [ -n "$HIERARCHICAL_PHASE_WEIGHT_INNER" ]; then
        start_args+=("--hierarchical-phase-weight-inner" "$HIERARCHICAL_PHASE_WEIGHT_INNER")
    fi
    if [ -n "$HIERARCHICAL_PHASE_WEIGHT_OUTER" ]; then
        start_args+=("--hierarchical-phase-weight-outer" "$HIERARCHICAL_PHASE_WEIGHT_OUTER")
    fi
    if [ -n "$HIERARCHICAL_SIG_ALGO" ]; then
        start_args+=("--hierarchical-sig-algo" "$HIERARCHICAL_SIG_ALGO")
    fi
    if [ -n "$HIERARCHICAL_SIG_GEN_MS" ]; then
        start_args+=("--hierarchical-sig-gen-ms" "$HIERARCHICAL_SIG_GEN_MS")
    fi
    if [ -n "$HIERARCHICAL_SIG_VERIFY_MS" ]; then
        start_args+=("--hierarchical-sig-verify-ms" "$HIERARCHICAL_SIG_VERIFY_MS")
    fi
    if [ -n "$HIERARCHICAL_SIG_AGG_MS" ]; then
        start_args+=("--hierarchical-sig-agg-ms" "$HIERARCHICAL_SIG_AGG_MS")
    fi
    if [ -n "$HIERARCHICAL_OUTER_MODE" ]; then
        start_args+=("--hierarchical-outer-mode" "$HIERARCHICAL_OUTER_MODE")
    fi
    if [ -n "$HIERARCHICAL_OUTER_SIG_ALGO" ]; then
        start_args+=("--hierarchical-outer-sig-algo" "$HIERARCHICAL_OUTER_SIG_ALGO")
    fi
    if [ -n "$HIERARCHICAL_OUTER_SIG_GEN_MS" ]; then
        start_args+=("--hierarchical-outer-sig-gen-ms" "$HIERARCHICAL_OUTER_SIG_GEN_MS")
    fi
    if [ -n "$HIERARCHICAL_OUTER_SIG_VERIFY_MS" ]; then
        start_args+=("--hierarchical-outer-sig-verify-ms" "$HIERARCHICAL_OUTER_SIG_VERIFY_MS")
    fi
    if [ -n "$HIERARCHICAL_OUTER_SIG_AGG_MS" ]; then
        start_args+=("--hierarchical-outer-sig-agg-ms" "$HIERARCHICAL_OUTER_SIG_AGG_MS")
    fi
    if [ -n "$HIERARCHICAL_BATCH_VERIFY" ]; then
        start_args+=("--hierarchical-batch-verify" "$HIERARCHICAL_BATCH_VERIFY")
    fi
    if [ -n "$HIERARCHICAL_BATCH_VERIFY_GAIN" ]; then
        start_args+=("--hierarchical-batch-verify-gain" "$HIERARCHICAL_BATCH_VERIFY_GAIN")
    fi
    if [ -n "$HIERARCHICAL_SIG_GEN_PARALLELISM" ]; then
        start_args+=("--hierarchical-sig-gen-parallelism" "$HIERARCHICAL_SIG_GEN_PARALLELISM")
    fi
    if [ -n "$HIERARCHICAL_SIG_VERIFY_PARALLELISM" ]; then
        start_args+=("--hierarchical-sig-verify-parallelism" "$HIERARCHICAL_SIG_VERIFY_PARALLELISM")
    fi
    if [ -n "$HIERARCHICAL_SIG_AGG_PARALLELISM" ]; then
        start_args+=("--hierarchical-sig-agg-parallelism" "$HIERARCHICAL_SIG_AGG_PARALLELISM")
    fi
    if [ -n "$HIERARCHICAL_BATCH_SIZE" ]; then
        start_args+=("--hierarchical-batch-size" "$HIERARCHICAL_BATCH_SIZE")
    fi
    if [ -n "$MERKLE_TX_COUNT" ]; then
        start_args+=("--merkle-tx-count" "$MERKLE_TX_COUNT")
    fi
    if [ -n "$MERKLE_TX_SIZE" ]; then
        start_args+=("--merkle-tx-size" "$MERKLE_TX_SIZE")
    fi
    if [ -n "$MERKLE_K" ]; then
        start_args+=("--merkle-k" "$MERKLE_K")
    fi
    if [ -n "$MERKLE_REPEAT" ]; then
        start_args+=("--merkle-repeat" "$MERKLE_REPEAT")
    fi

    if [ -n "$USE_CPU_AFFINITY" ]; then
        local core=$(( (id - 1) % $(nproc) ))
        log_info "Binding Node $id to CPU core $core"
        taskset -c "$core" "${start_args[@]}" > "$LOG_DIR/node$id.log" 2>&1 &
    else
        "${start_args[@]}" > "$LOG_DIR/node$id.log" 2>&1 &
    fi
}

for (( i=1; i<=NUM_NODES; i++ )); do
    start_node $i
done

log_info "All $NUM_NODES nodes started. Logs in $LOG_DIR"
log_info "Tail logs with: tail -f $LOG_DIR/node*.log"

# Keep script running
wait
