#!/bin/bash
# Start all CoLink services for local development

set -e

echo "Starting CoLink services..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if docker-compose services are running
echo -e "${BLUE}Checking infrastructure services...${NC}"
if ! docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo "Starting infrastructure services..."
    docker-compose -f docker-compose.dev.yml up -d
    echo "Waiting for services to be healthy..."
    sleep 10
fi

# Function to start a service in the background
start_service() {
    local service_name=$1
    local port=$2
    local service_dir="services/$service_name"

    if [ ! -d "$service_dir" ]; then
        echo -e "${BLUE}Skipping $service_name (not implemented yet)${NC}"
        return
    fi

    echo -e "${GREEN}Starting $service_name on port $port...${NC}"
    cd "$service_dir"

    # Check if requirements.txt has content
    if [ -s requirements.txt ]; then
        # Install dependencies if needed
        pip install -q -r requirements.txt
    fi

    # Start service
    if [ -f "app/main.py" ]; then
        uvicorn app.main:app --reload --port "$port" > "../../logs/$service_name.log" 2>&1 &
        echo $! > "../../logs/$service_name.pid"
    fi

    cd ../..
}

# Create logs directory
mkdir -p logs

# Start services
start_service "gateway" 8000
start_service "users" 8001
start_service "messaging" 8002
start_service "files" 8003
start_service "search" 8004
start_service "admin" 8005
start_service "channels" 8006
start_service "presence" 8007

echo -e "${GREEN}All services started!${NC}"
echo ""
echo "Service URLs:"
echo "  Gateway:   http://localhost:8000/docs"
echo "  Users:     http://localhost:8001/docs"
echo "  Messaging: http://localhost:8002/docs"
echo "  Files:     http://localhost:8003/docs"
echo "  Search:    http://localhost:8004/docs"
echo "  Admin:     http://localhost:8005/docs"
echo "  Channels:  http://localhost:8006/docs"
echo "  Presence:  http://localhost:8007/ws"
echo ""
echo "Infrastructure:"
echo "  Keycloak:   http://localhost:8080"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000"
echo ""
echo "To stop services, run: ./scripts/stop_services.sh"
