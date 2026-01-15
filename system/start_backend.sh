#!/bin/bash

# Start backend server
echo "Starting backend server..."
source venv/bin/activate
export LC_ALL=C.utf8
setsid nohup python backend.py > logs/backend.log 2>&1 &
