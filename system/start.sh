#!/bin/bash
set -e

# Oonanji Vault - System Start Script (Docker)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting Oonanji Vault System..."

# Activate venv if present (optional, but requested by user flow)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Check for docker
if ! command -v docker &> /dev/null; then
    echo "Error: docker command not found."
    exit 1
fi

# Start Containers
docker compose up -d

echo "System Started."
