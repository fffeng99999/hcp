#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
HCP_HOME="$PROJECT_ROOT/.hcp_data"
LOG_DIR="$PROJECT_ROOT/logs"
PIDS_DIR="$PROJECT_ROOT/pids"
TIMEOUT=60 # Increased timeout for compilation/builds

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Ensure directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$PIDS_DIR"

log_info() { echo -e "${GREEN}[INFO] $1${NC}"; }
log_warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
log_error() { echo -e "${RED}[ERROR] $1${NC}"; }

check_port() {
    lsof -i:$1 -t >/dev/null 2>&1
}

wait_for_port() {
    local port=$1
    local service=$2
    local timeout=$TIMEOUT
    local start_time=$(date +%s)

    log_info "Waiting for $service to start on port $port..."

    while true; do
        if check_port $port; then
            log_info "$service started successfully on port $port."
            return 0
        fi

        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ $elapsed -ge $timeout ]; then
            log_error "Timeout waiting for $service on port $port."
            return 1
        fi

        sleep 2
    done
}

cleanup() {
    log_info "Stopping all services..."
    # Kill processes by PID
    for pid_file in "$PIDS_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            # Check if process exists before killing
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                log_info "Stopped process $pid"
            fi
            rm "$pid_file"
        fi
    done
    exit 0
}

start_service() {
    local service_name=$1
    local service_dir=$2
    local command=$3
    local port=$4
    local log_file="$LOG_DIR/$service_name.log"
    local pid_file="$PIDS_DIR/$service_name.pid"

    if check_port $port; then
        log_warn "Port $port is already in use. Skipping $service_name start."
        return 0
    fi

    log_info "Starting $service_name..."
    cd "$service_dir" || { log_error "Directory $service_dir not found"; return 1; }

    # Run command in background
    nohup $command > "$log_file" 2>&1 &
    echo $! > "$pid_file"

    if wait_for_port $port "$service_name"; then
        return 0
    else
        log_error "Failed to start $service_name. Check logs at $log_file"
        return 1
    fi
}

main() {
    trap cleanup SIGINT SIGTERM

    log_info "Starting HCP System..."

    # 0. Check Dependencies
    # Check if nc is installed
    if command -v nc >/dev/null 2>&1; then
        if ! nc -z -w 5 192.168.58.102 5432; then
            log_error "PostgreSQL (192.168.58.102:5432) is not reachable."
            exit 1
        fi
        if ! nc -z -w 5 192.168.58.102 6379; then
            log_error "Redis (192.168.58.102:6379) is not reachable."
            exit 1
        fi
        log_info "External dependencies (PostgreSQL, Redis) are reachable."
    else
        log_warn "netcat (nc) not found. Skipping external dependency connectivity check."
    fi

    # 1. Start Consensus (Go)
    # Use dedicated node startup script
    # Default to 4 nodes, configurable via NUM_NODES env var
    NUM_NODES=${NUM_NODES:-4}
    if ! start_service "hcp-nodes" "$PROJECT_ROOT/hcp" "bash start_nodes.sh $NUM_NODES" 26657; then
        cleanup
    fi

    # 2. Start Server (Go)
    if ! start_service "hcp-server" "$PROJECT_ROOT/hcp-server" "go run cmd/server/main.go --config configs" 8081; then
        cleanup
    fi

    # 3. Start Gateway (Rust)
    export HCP_CONSENSUS_GRPC_ADDR="http://127.0.0.1:9090"
    export HCP_SERVER_GRPC_ADDR="http://127.0.0.1:8081"
    if ! start_service "hcp-gateway" "$PROJECT_ROOT/hcp-gateway" "cargo run --bin hcp-gateway" 8080; then
        cleanup
    fi

    # 4. Start UI (Vue)
    if ! start_service "hcp-ui" "$PROJECT_ROOT/hcp-ui" "npm run dev -- --port 5173 --host" 5173; then
        cleanup
    fi

    log_info "=================================================="
    log_info "HCP System Started Successfully!"
    log_info "UI: http://localhost:5173"
    log_info "Gateway: http://localhost:8080"
    log_info "Server (gRPC): localhost:8081"
    log_info "Consensus (RPC): http://localhost:26657"
    log_info "Logs are available in $LOG_DIR"
    log_info "PIDs are stored in $PIDS_DIR"
    log_info "Press Ctrl+C to stop all services."
    log_info "=================================================="

    wait
}

main
