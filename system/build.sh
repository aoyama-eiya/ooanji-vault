#!/bin/bash
export NEXT_TELEMETRY_DISABLED=1
echo "Building frontend..."
npm run build
echo "Build complete."
