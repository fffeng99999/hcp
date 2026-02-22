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

log_error() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
}

kill_pid() {
    local pid=$1
    local service=$2
    local timeout=${3:-10}

    if ! ps -p "$pid" > /dev/null 2>&1; then
        return 1
    fi

    log_info "Stopping $service (PID: $pid)..."
    local pgid
    pgid=$(ps -o pgid= "$pid" 2>/dev/null | tr -d ' ')
    if [ -n "$pgid" ]; then
        kill -TERM -"$pgid" 2>/dev/null || true
    fi
    kill -TERM "$pid" 2>/dev/null || true

    while ps -p "$pid" > /dev/null 2>&1 && [ $timeout -gt 0 ]; do
        sleep 1
        ((timeout--))
    done

    if ps -p "$pid" > /dev/null 2>&1; then
        log_warn "$service did not stop gracefully. Forcing kill..."
        if [ -n "$pgid" ]; then
            kill -KILL -"$pgid" 2>/dev/null || true
        fi
        kill -KILL "$pid" 2>/dev/null || true
    fi

    return 0
}

stop_service() {
    local service=$1
    local port=$2
    local pid_file="$PIDS_DIR/$service.pid"
    local stopped=0

    # 1. Try stopping via PID file
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill_pid "$pid" "$service" 10; then
            stopped=1
        else
            log_warn "$service PID file exists but process is not running."
        fi
        rm -f "$pid_file"
    fi

    # 2. Fallback: Check Port
    if [ -n "$port" ]; then
        # Check if port is still in use (ignoring our own just-killed process if race condition, but lsof checks current)
        local pids=$(lsof -t -i:$port 2>/dev/null)
        if [ -n "$pids" ]; then
            log_warn "Port $port ($service) is still in use by PIDs: $pids. Cleaning up..."
            echo "$pids" | xargs kill -KILL
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
stop_service "hcp-server" 8081
stop_service "hcp-nodes" 26657

monitoring_dir="$PROJECT_ROOT/hcp-deploy/monitoring"
if [ -d "$monitoring_dir" ]; then
    if command -v docker >/dev/null 2>&1; then
        log_info "Stopping hcp-monitoring containers..."
        (cd "$monitoring_dir" && docker compose down --remove-orphans) || log_warn "hcp-monitoring 停止失败"
    else
        log_warn "docker 未安装，无法停止 hcp-monitoring"
    fi
else
    log_warn "hcp-monitoring 目录不存在，跳过"
fi

stop_service "hcp-monitoring" 9090
stop_service "hcp-monitoring-grafana" 3001

log_info "All services stopped."
log_info "Cleanup complete."
