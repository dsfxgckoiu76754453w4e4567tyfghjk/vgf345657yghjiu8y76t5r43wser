#!/bin/bash
# ==========================================================================
# Stop Shia Islamic Chatbot Queue System
# ==========================================================================
#
# Gracefully stops the queue management system
#
# Usage:
#   ./scripts/stop-queue-system.sh [--remove-volumes]
#
# Options:
#   --remove-volumes    Also remove volumes (data will be lost!)
#
# ==========================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.queue.yml"
REMOVE_VOLUMES=false

# Parse arguments
if [ "$1" == "--remove-volumes" ]; then
    REMOVE_VOLUMES=true
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Stopping Queue System${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Check if services are running
RUNNING_SERVICES=$(docker-compose -f "$COMPOSE_FILE" ps -q | wc -l)
if [ "$RUNNING_SERVICES" -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC}  No queue services are running"
    exit 0
fi

echo -e "${YELLOW}Stopping services gracefully...${NC}"

# Stop services (this sends SIGTERM for graceful shutdown)
docker-compose -f "$COMPOSE_FILE" stop

echo -e "${GREEN}✓${NC} Services stopped"

# Remove containers
echo -e "${YELLOW}Removing containers...${NC}"
docker-compose -f "$COMPOSE_FILE" rm -f

echo -e "${GREEN}✓${NC} Containers removed"

# Remove volumes if requested
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}⚠${NC}  Removing volumes (DATA WILL BE LOST)..."
    read -p "Are you sure? (yes/NO): " -r
    if [[ $REPLY =~ ^yes$ ]]; then
        docker-compose -f "$COMPOSE_FILE" down -v
        echo -e "${GREEN}✓${NC} Volumes removed"
    else
        echo -e "${YELLOW}⚠${NC}  Volume removal cancelled"
    fi
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Queue System Stopped${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Your production containers are ${GREEN}SAFE${NC} and still running:"
docker ps --format '{{.Names}}' | grep -E '^(compose-|dev-)' || echo -e "${YELLOW}No production containers found${NC}"

echo -e "\nTo start again: ${YELLOW}./scripts/start-queue-system.sh${NC}\n"
