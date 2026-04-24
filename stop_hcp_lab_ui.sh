#!/bin/bash

# HCP Lab UI 停止脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDS_DIR="$PROJECT_ROOT/hcp-lab-server/pids"
LOG_DIR="$PROJECT_ROOT/hcp-lab-server/logs"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

stop_by_pid_file() {
    local name=$1
    local pid_file=$2

    if [ ! -f "$pid_file" ]; then
        log_warn "未找到 $name 的 PID 文件"
        return 0
    fi

    local pid
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        log_info "停止 $name (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            log_warn "强制终止 $name (PID: $pid)..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    else
        log_warn "$name 进程 (PID: $pid) 已不存在"
    fi

    rm -f "$pid_file"
}

stop_by_port() {
    local port=$1
    local name=$2
    local pids
    pids=$(lsof -i:$port -t 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_info "停止端口 $port ($name)..."
        for pid in $pids; do
            kill "$pid" 2>/dev/null || true
        done
        sleep 1
        pids=$(lsof -i:$port -t 2>/dev/null || true)
        if [ -n "$pids" ]; then
            for pid in $pids; do
                kill -9 "$pid" 2>/dev/null || true
            done
        fi
    fi
}

log_info "停止 HCP Lab UI 服务..."

stop_by_pid_file "hcp-lab-server" "$PIDS_DIR/server.pid"
stop_by_pid_file "hcp-ui-lab" "$PIDS_DIR/ui.pid"

# Fallback: stop by port
stop_by_port 9090 "hcp-lab-server"
stop_by_port 5174 "hcp-ui-lab"

log_info "HCP Lab UI 已停止"
