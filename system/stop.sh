#!/bin/bash
set -e

# Oonanji Vault - System Stop Script (Docker)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Stopping Oonanji Vault System..."

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Stop Containers
docker compose down

echo "System Stopped."
