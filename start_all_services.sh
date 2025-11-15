#!/bin/bash

export PATH="/Users/spartan/.local/bin:$PATH"
cd /Users/spartan/Documents/GitHub/Co-Link

# Create logs directory
mkdir -p logs

# Function to start a service
start_service() {
    local service=$1
    local port=$2
    echo "Starting $service on port $port..."
    cd services/$service
    uvicorn app.main:app --host 0.0.0.0 --port $port > ../../logs/$service.log 2>&1 &
    echo $! > ../../logs/$service.pid
    cd ../..
}

# Start all services
start_service "users" 8001
sleep 2
start_service "messaging" 8002
sleep 2
start_service "files" 8003
sleep 2
start_service "search" 8004
sleep 2
start_service "admin" 8005
sleep 2
start_service "channels" 8006
sleep 2
start_service "gateway" 8007
sleep 2
start_service "presence" 8008

echo "All services starting... Check logs directory for details"
echo "Services:"
echo "  Users:     http://localhost:8001/docs"
echo "  Messaging: http://localhost:8002/docs"
echo "  Files:     http://localhost:8003/docs"
echo "  Search:    http://localhost:8004/docs"
echo "  Admin:     http://localhost:8005/docs"
echo "  Channels:  http://localhost:8006/docs"
echo "  Gateway:   http://localhost:8007/docs"
echo "  Presence:  http://localhost:8008/docs"
