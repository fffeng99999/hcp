#!/bin/bash

# Configuration
PROJECT_ROOT="/home/hcp-dev/hcp-project"
MONITORING_DIR="$PROJECT_ROOT/hcp-deploy/monitoring"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[INFO] Stopping Monitoring System...${NC}"

if [ ! -d "$MONITORING_DIR" ]; then
    echo -e "${RED}[ERROR] Monitoring directory not found at $MONITORING_DIR${NC}"
    exit 1
fi

cd "$MONITORING_DIR" || exit 1

# Stop services
if docker compose down; then
    echo -e "${GREEN}✅ Monitoring System stopped successfully!${NC}"
else
    echo -e "${RED}[ERROR] Failed to stop monitoring services${NC}"
    exit 1
fi
