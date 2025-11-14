#!/bin/bash
# Stop all CoLink services

set -e

echo "Stopping CoLink services..."

# Kill services by PID files
if [ -d "logs" ]; then
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid)
            if ps -p $pid > /dev/null 2>&1; then
                echo "Stopping $service_name (PID: $pid)..."
                kill $pid
            fi
            rm "$pidfile"
        fi
    done
fi

# Stop docker-compose services
echo "Stopping infrastructure services..."
docker-compose -f docker-compose.dev.yml down

echo "All services stopped!"
