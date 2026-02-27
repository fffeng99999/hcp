#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
HCP_HOME="$PROJECT_ROOT/.hcp_data"
LOG_DIR="$PROJECT_ROOT/logs"
PIDS_DIR="$PROJECT_ROOT/pids"
TIMEOUT=60 # Increased timeout for compilation/builds
NUM_NODES=8

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

kill_port_process() {
    local port=$1
    local pids
    pids=$(lsof -i:$port -t 2>/dev/null || true)
    if [ -z "$pids" ]; then
        return 0
    fi
    log_warn "Port $port is in use. Stopping process(es): $pids"
    for pid in $pids; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid
        fi
    done
    sleep 1
    pids=$(lsof -i:$port -t 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_error "Port $port still in use after termination: $pids"
        return 1
    fi
    return 0
}

wait_for_port() {
    local port=$1
    local service=$2
    local timeout=${3:-$TIMEOUT}
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

wait_for_monitoring() {
    local monitoring_dir=$1
    local timeout=${2:-$TIMEOUT}
    local start_time=$(date +%s)

    log_info "Waiting for hcp-monitoring containers to be running..."

    while true; do
        local running
        running=$(cd "$monitoring_dir" && docker compose ps --status running --services 2>/dev/null | tr '\n' ' ')
        if [[ "$running" == *"prometheus"* && "$running" == *"grafana"* ]]; then
            log_info "hcp-monitoring containers are running."
            return 0
        fi

        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ $elapsed -ge $timeout ]; then
            log_error "Timeout waiting for hcp-monitoring containers to be running."
            return 1
        fi

        sleep 2
    done
}

start_service() {
    local service_name=$1
    local service_dir=$2
    local command=$3
    local port=$4
    local timeout=${5:-$TIMEOUT}
    local log_file="$LOG_DIR/$service_name.log"
    local pid_file="$PIDS_DIR/$service_name.pid"

    if check_port $port; then
        if ! kill_port_process $port; then
            return 1
        fi
    fi

    log_info "Starting $service_name..."
    cd "$service_dir" || { log_error "Directory $service_dir not found"; return 1; }

    # Run command in background
    nohup $command > "$log_file" 2>&1 &
    echo $! > "$pid_file"

    if wait_for_port $port "$service_name" "$timeout"; then
        return 0
    else
        log_error "Failed to start $service_name. Check logs at $log_file"
        return 1
    fi
}

start_monitoring_service() {
    local service_name="hcp-monitoring"
    local service_dir="$PROJECT_ROOT/hcp"
    local monitoring_dir="$PROJECT_ROOT/hcp-deploy/monitoring"
    local command="bash start_monitoring.sh"
    local log_file="$LOG_DIR/$service_name.log"
    local pid_file="$PIDS_DIR/$service_name.pid"
    local timeout=${1:-180}

    if check_port 9090; then
        if ! kill_port_process 9090; then
            return 1
        fi
    fi
    if check_port 3001; then
        if ! kill_port_process 3001; then
            return 1
        fi
    fi

    log_info "Starting $service_name..."
    cd "$service_dir" || { log_error "Directory $service_dir not found"; return 1; }

    nohup $command > "$log_file" 2>&1 &
    echo $! > "$pid_file"

    if wait_for_monitoring "$monitoring_dir" "$timeout"; then
        return 0
    else
        log_error "Failed to start $service_name. Check logs at $log_file"
        return 1
    fi
}

check_consensus_startup() {
    local check_nodes="${CONSENSUS_CHECK_NODES:-1}"
    if check_port 26657; then
        log_info "hcp-consensus already running on port 26657."
        return 0
    fi
    if ! CHECK_ONLY=1 CHECK_TIMEOUT="$TIMEOUT" USE_CPU_AFFINITY=1 bash "$PROJECT_ROOT/hcp/start_nodes.sh" "$check_nodes"; then
        log_error "hcp-consensus startup check failed."
        return 1
    fi
    log_info "hcp-consensus startup check succeeded."
    return 0
}

check_loadgen_startup() {
    local loadgen_dir="$PROJECT_ROOT/hcp-loadgen"
    local loadgen_bin="${HCP_LOADGEN_BIN:-$loadgen_dir/target/release/hcp-loadgen}"
    if [ ! -x "$loadgen_bin" ]; then
        log_warn "hcp-loadgen binary not found. Building..."
        cd "$loadgen_dir" || { log_error "Directory $loadgen_dir not found"; return 1; }
        if ! cargo build --release --bin hcp-loadgen; then
            log_error "hcp-loadgen build failed."
            return 1
        fi
    fi
    if ! "$loadgen_bin" --help >/dev/null 2>&1; then
        log_error "hcp-loadgen startup check failed."
        return 1
    fi
    log_info "hcp-loadgen startup check succeeded."
    return 0
}

main() {
    trap cleanup SIGINT SIGTERM

    log_info "Starting HCP System..."

    if ! check_consensus_startup; then
        exit 1
    fi
    if ! check_loadgen_startup; then
        exit 1
    fi

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

    # 1. Start Server (Go)
    if ! start_service "hcp-server" "$PROJECT_ROOT/hcp-server" "go run cmd/server/main.go --config configs" 8081; then
        cleanup
    fi

    # 2. Start Gateway (Rust)
    export HCP_CONSENSUS_GRPC_ADDR="http://127.0.0.1:9090"
    export HCP_SERVER_GRPC_ADDR="http://127.0.0.1:8081"
    if ! start_service "hcp-gateway" "$PROJECT_ROOT/hcp-gateway" "cargo run --bin hcp-gateway" 8080; then
        cleanup
    fi

    # 3. Start UI (Vue)
    if ! start_service "hcp-ui" "$PROJECT_ROOT/hcp-ui" "npm run dev -- --port 5173 --host" 5173; then
        cleanup
    fi

    if ! start_monitoring_service 180; then
        cleanup
    fi

    log_info "=================================================="
    log_info "HCP System Started Successfully!"
    log_info "UI: http://localhost:5173"
    log_info "Gateway: http://localhost:8080"
    log_info "Server (gRPC): localhost:8081"
    log_info "Consensus (RPC): http://localhost:26657"
    log_info "Prometheus: http://localhost:9090"
    log_info "Grafana: http://localhost:3001"
    log_info "Logs are available in $LOG_DIR"
    log_info "PIDs are stored in $PIDS_DIR"
    log_info "Press Ctrl+C to stop all services."
    log_info "=================================================="

    wait
}

main
