#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/backend"
source ../freshbus_analytics/bin/activate
while true; do
    echo "Starting Freshbus Backend Server..."
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
    echo ""
    echo "[WARNING] Server stopped. Restarting in 5 seconds..."
    sleep 5
done
