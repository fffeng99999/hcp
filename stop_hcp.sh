#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
PIDS_DIR="$PROJECT_ROOT/pids"
LOG_DIR="$PROJECT_ROOT/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

stop_service() {
    local service=$1
    local port=$2
    local pid_file="$PIDS_DIR/$service.pid"
    local stopped=0

    # 1. Try stopping via PID file
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            log_info "Stopping $service (PID: $pid)..."
            kill $pid
            
            # Wait loop
            local timeout=10
            while ps -p $pid > /dev/null && [ $timeout -gt 0 ]; do
                sleep 1
                ((timeout--))
            done

            if ps -p $pid > /dev/null; then
                log_warn "$service did not stop gracefully. Forcing kill..."
                kill -9 $pid
            fi
            stopped=1
        else
            log_warn "$service PID file exists but process is not running."
        fi
        rm "$pid_file"
    fi

    # 2. Fallback: Check Port
    if [ -n "$port" ]; then
        # Check if port is still in use (ignoring our own just-killed process if race condition, but lsof checks current)
        local pids=$(lsof -t -i:$port 2>/dev/null)
        if [ -n "$pids" ]; then
            log_warn "Port $port ($service) is still in use by PIDs: $pids. Cleaning up..."
            echo "$pids" | xargs kill -9
            stopped=1
        fi
    fi

    if [ $stopped -eq 1 ]; then
        log_info "$service stopped."
    else
        log_info "$service was not running."
    fi
}

# Stop in reverse order of startup
log_info "Stopping HCP System..."

stop_service "hcp-ui" 5173
stop_service "hcp-gateway" 8080
stop_service "hcp-consensus" 26657
stop_service "hcp-server" 8081

log_info "All services stopped."
log_info "Cleanup complete."
