#!/bin/bash
set -e

echo "=========================================="
echo "  Path Fix & Environment Setup Tool"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo "This script will recreate the Python virtual environment to fix path issues."
echo ""

# Check if venv exists and remove it
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
    echo "Done."
fi

# Create new venv
echo "Creating new virtual environment..."
if command -v python3.9 &> /dev/null; then
    python3.9 -m venv venv
    echo "Created using python3.9"
elif command -v python3 &> /dev/null; then
    python3 -m venv venv
    echo "Created using python3"
else
    echo "Error: Python 3 not found."
    exit 1
fi

# Install requirements
echo "Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo ""
echo "=========================================="
echo "  ✓ Environment setup complete."
echo "=========================================="
echo ""
echo "You can now start the server with:"
echo "  ./start.sh"
echo ""
