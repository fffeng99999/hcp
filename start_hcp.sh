#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
LOG_DIR="$PROJECT_ROOT/logs"
PIDS_DIR="$PROJECT_ROOT/pids"
TIMEOUT=60 # Seconds to wait for service startup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize directories
mkdir -p "$LOG_DIR"
mkdir -p "$PIDS_DIR"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

check_port() {
    local port=$1
    if lsof -i :$port > /dev/null; then
        return 0
    else
        return 1
    fi
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

        sleep 1
    done
}

stop_service() {
    local service=$1
    local pid_file="$PIDS_DIR/$service.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            log_warn "Stopping $service (PID: $pid)..."
            kill $pid
            # Wait for process to exit
            tail --pid=$pid -f /dev/null 2>/dev/null || sleep 2
            log_info "$service stopped."
        else
            log_warn "$service PID file exists but process is not running. Cleaning up."
        fi
        rm "$pid_file"
    fi
}

cleanup() {
    log_warn "Stopping all services..."
    stop_service "hcp-ui"
    stop_service "hcp-gateway"
    stop_service "hcp-consensus"
    stop_service "hcp-server"
    log_info "All services stopped."
}

start_service() {
    local service_name=$1
    local service_dir=$2
    local command=$3
    local port=$4
    local log_file="$LOG_DIR/$service_name.log"
    local pid_file="$PIDS_DIR/$service_name.pid"

    if check_port $port; then
        log_warn "Port $port is already in use. Checking if it's $service_name..."
        # Optional: Check if it's actually our service or something else
        # For now, we assume if the port is taken, we shouldn't start another instance
        log_error "Port $port is occupied. Aborting start of $service_name."
        return 1
    fi

    log_info "Starting $service_name..."
    
    cd "$service_dir" || { log_error "Directory $service_dir not found"; return 1; }

    # Run command in background
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    if wait_for_port $port $service_name; then
        return 0
    else
        log_error "Failed to start $service_name. Check logs at $log_file"
        kill $pid 2>/dev/null
        return 1
    fi
}

# Main startup sequence
main() {
    # Trap interrupts for cleanup
    trap cleanup SIGINT SIGTERM

    log_info "Starting HCP System..."

    # 0. Check External Dependencies (DB & Redis)
    # Using nc (netcat) to check connectivity if available, or just warn.
    # Assuming these are critical.
    DB_HOST="192.168.58.102"
    DB_PORT=5432
    REDIS_PORT=6379
    
    log_info "Checking external dependencies..."
    if command -v nc >/dev/null 2>&1; then
        if ! nc -z -w 5 $DB_HOST $DB_PORT; then
            log_error "Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT"
            exit 1
        fi
        if ! nc -z -w 5 $DB_HOST $REDIS_PORT; then
            log_error "Cannot connect to Redis at $DB_HOST:$REDIS_PORT"
            exit 1
        fi
        log_info "External dependencies (PostgreSQL, Redis) are reachable."
    else
        log_warn "netcat (nc) not found. Skipping external dependency connectivity check."
    fi

    # 1. Start HCP Server (Backend)
    # Port 8081
    if ! start_service "hcp-server" "$PROJECT_ROOT/hcp-server" "go run cmd/server/main.go" 8081; then
        cleanup
        exit 1
    fi

    # 2. Start HCP Consensus
    # Port 26657 (RPC)
    # Note: Assuming 'init' has been run. If not, this might fail or need init check.
    # We use 'start' command.
    if ! start_service "hcp-consensus" "$PROJECT_ROOT/hcp-consensus" "go run cmd/hcpd/main.go start" 26657; then
        cleanup
        exit 1
    fi

    # 3. Start HCP Gateway
    # Port 8080
    if ! start_service "hcp-gateway" "$PROJECT_ROOT/hcp-gateway" "cargo run" 8080; then
        cleanup
        exit 1
    fi

    # 4. Start HCP UI
    # Port 5173
    if ! start_service "hcp-ui" "$PROJECT_ROOT/hcp-ui" "npm run dev -- --port 5173 --host" 5173; then
        cleanup
        exit 1
    fi

    log_info "=================================================="
    log_info "HCP System Started Successfully!"
    log_info "UI: http://localhost:5173"
    log_info "Gateway: http://localhost:8080"
    log_info "Server: http://localhost:8081"
    log_info "Consensus RPC: http://localhost:26657"
    log_info "Logs are available in $LOG_DIR"
    log_info "PIDs are stored in $PIDS_DIR"
    log_info "Run './stop_hcp.sh' (to be created) or Ctrl+C to stop."
    log_info "=================================================="

    # Wait indefinitely to keep script running and trap signals
    wait
}

main
