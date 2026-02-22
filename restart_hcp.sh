#!/bin/bash
PROJECT_ROOT="/home/hcp-dev/hcp-project"
HCP_DIR="$PROJECT_ROOT/hcp"

cd "$HCP_DIR" || exit 1
bash stop_hcp.sh
sleep 2
bash start_hcp.sh
