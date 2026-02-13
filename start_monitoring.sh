#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
MONITORING_DIR="$PROJECT_ROOT/hcp-deploy/monitoring"
NETWORK_NAME="hcp-deploy_hcp-net"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[INFO] Starting Monitoring System (Prometheus + Grafana)...${NC}"

if [ ! -d "$MONITORING_DIR" ]; then
    echo -e "${RED}[ERROR] Monitoring directory not found at $MONITORING_DIR${NC}"
    exit 1
fi

# Check and create network if missing
if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo -e "${YELLOW}[WARN] Network '$NETWORK_NAME' not found.${NC}"
    echo -e "${GREEN}[INFO] Creating network '$NETWORK_NAME' so monitoring can start...${NC}"
    docker network create "$NETWORK_NAME"
fi

cd "$MONITORING_DIR" || exit 1

# Start services
# Using --quiet-pull to keep logs clean, but it will pull if images are missing
echo -e "${GREEN}[INFO] Bringing up monitoring services...${NC}"
if docker compose up -d; then
    echo -e "${GREEN}✅ Monitoring System started successfully!${NC}"
    echo -e "${GREEN}   - Prometheus: http://localhost:9090${NC}"
    echo -e "${GREEN}   - Grafana:    http://localhost:3001${NC}"
else
    echo -e "${RED}[ERROR] Failed to start monitoring services${NC}"
    # Fallback: Try to build/pull explicitly if up failed (e.g. missing images)
    echo -e "${YELLOW}[WARN] Attempting to pull/build and retry...${NC}"
    docker compose pull
    if docker compose up -d; then
        echo -e "${GREEN}✅ Monitoring System started successfully on retry!${NC}"
        echo -e "${GREEN}   - Prometheus: http://localhost:9090${NC}"
        echo -e "${GREEN}   - Grafana:    http://localhost:3001${NC}"
    else
        echo -e "${RED}[ERROR] Retry failed. Please check docker logs.${NC}"
        exit 1
    fi
fi
