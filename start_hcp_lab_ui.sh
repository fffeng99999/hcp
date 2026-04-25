#!/bin/bash

# HCP Lab UI 启动脚本
# 同时启动 hcp-lab-server (后端) 和 hcp-ui-lab (前端)

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_DIR="$PROJECT_ROOT/hcp-lab/hcp-lab-server"
UI_DIR="$PROJECT_ROOT/hcp-ui-lab"
LOG_DIR="$PROJECT_ROOT/hcp-lab/hcp-lab-server/logs"
PIDS_DIR="$PROJECT_ROOT/hcp-lab/hcp-lab-server/pids"
SERVER_PORT=9090
UI_PORT=5174
TIMEOUT=30

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Ensure directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$PIDS_DIR"

check_port() {
    lsof -i:$1 -t >/dev/null 2>&1
}

wait_for_port() {
    local port=$1
    local service=$2
    local timeout=${3:-$TIMEOUT}
    local start_time=$(date +%s)

    log_info "等待 $service 在端口 $port 启动..."
    while true; do
        if check_port $port; then
            log_info "$service 已启动 (端口 $port)"
            return 0
        fi
        local now=$(date +%s)
        if (( now - start_time >= timeout )); then
            log_error "$service 启动超时 (端口 $port)"
            return 1
        fi
        sleep 1
    done
}

kill_port_process() {
    local port=$1
    local pids
    pids=$(lsof -i:$port -t 2>/dev/null || true)
    if [ -z "$pids" ]; then
        return 0
    fi
    log_warn "端口 $port 被占用，正在终止进程: $pids"
    for pid in $pids; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null || true
        fi
    done
    sleep 1
    pids=$(lsof -i:$port -t 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_warn "强制终止端口 $port 进程: $pids"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || true
        done
        sleep 1
    fi
}

start_server() {
    log_step "启动 hcp-lab-server (后端)..."

    if check_port $SERVER_PORT; then
        log_warn "端口 $SERVER_PORT 已被占用，尝试释放..."
        kill_port_process $SERVER_PORT
    fi

    if [ ! -f "$SERVER_DIR/bin/hcp-lab-server" ]; then
        log_info "编译 hcp-lab-server..."
        cd "$SERVER_DIR"
        go build -o bin/hcp-lab-server .
    fi

    cd "$SERVER_DIR"
    nohup ./bin/hcp-lab-server -root "$PROJECT_ROOT" \
        > "$LOG_DIR/server.log" 2>&1 &
    local pid=$!
    echo $pid > "$PIDS_DIR/server.pid"
    log_info "hcp-lab-server PID: $pid"

    if ! wait_for_port $SERVER_PORT "hcp-lab-server"; then
        log_error "后端启动失败，查看日志: $LOG_DIR/server.log"
        exit 1
    fi
}

start_ui() {
    log_step "启动 hcp-ui-lab (前端)..."

    if check_port $UI_PORT; then
        log_warn "端口 $UI_PORT 已被占用，尝试释放..."
        kill_port_process $UI_PORT
    fi

    cd "$UI_DIR"
    nohup npm run dev \
        > "$LOG_DIR/ui.log" 2>&1 &
    local pid=$!
    echo $pid > "$PIDS_DIR/ui.pid"
    log_info "hcp-ui-lab PID: $pid"

    if ! wait_for_port $UI_PORT "hcp-ui-lab"; then
        log_error "前端启动失败，查看日志: $LOG_DIR/ui.log"
        exit 1
    fi
}

print_status() {
    echo ""
    echo "========================================"
    log_info "HCP Lab UI 启动成功!"
    echo ""
    echo -e "  ${GREEN}前端界面${NC}: http://localhost:$UI_PORT/experiments"
    echo -e "  ${GREEN}后端 API${NC}: http://localhost:$SERVER_PORT/api/health"
    echo -e "  ${GREEN}WebSocket${NC}: ws://localhost:$SERVER_PORT/ws"
    echo ""
    echo -e "  ${YELLOW}日志目录${NC}: $LOG_DIR"
    echo -e "  ${YELLOW}停止命令${NC}: $(dirname "$0")/stop_hcp_lab_ui.sh"
    echo "========================================"
    echo ""
}

# Main
log_info "项目根目录: $PROJECT_ROOT"
start_server
start_ui
print_status
