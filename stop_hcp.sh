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
    local pid_file="$PIDS_DIR/$service.pid"

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
            
            log_info "$service stopped."
        else
            log_warn "$service PID file exists but process is not running."
        fi
        rm "$pid_file"
    else
        log_info "No PID file for $service. Assuming stopped."
    fi
}

# Stop in reverse order of startup
log_info "Stopping HCP System..."

stop_service "hcp-ui"
stop_service "hcp-gateway"
stop_service "hcp-consensus"
stop_service "hcp-server"

log_info "All services stopped."
log_info "Cleanup complete."
