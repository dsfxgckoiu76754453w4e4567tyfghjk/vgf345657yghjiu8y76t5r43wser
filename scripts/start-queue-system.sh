#!/bin/bash
# ==========================================================================
# Start Shia Islamic Chatbot Queue System
# ==========================================================================
#
# This script safely starts the queue management system with:
# - Safety checks for existing containers
# - Network validation
# - Health monitoring
# - Graceful startup
#
# Usage:
#   ./scripts/start-queue-system.sh [environment]
#
# Examples:
#   ./scripts/start-queue-system.sh dev    # Start in dev mode
#   ./scripts/start-queue-system.sh prod   # Start in prod mode
#
# ==========================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0.31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-prod}"
COMPOSE_FILE="docker-compose.queue.yml"
ENV_FILE=".env.${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Shia Islamic Chatbot - Queue System${NC}"
echo -e "${GREEN}Starting in ${ENVIRONMENT} mode${NC}"
echo -e "${GREEN}========================================${NC}\n"

# ==========================================================================
# SAFETY CHECKS
# ==========================================================================

echo -e "${YELLOW}Running safety checks...${NC}"

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠${NC}  Environment file $ENV_FILE not found"
    echo -e "${YELLOW}⚠${NC}  Using default .env file"
    ENV_FILE=".env"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}ERROR: No .env file found${NC}"
        echo -e "${YELLOW}Create .env file from .env.example${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Environment file found: $ENV_FILE"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}ERROR: Compose file $COMPOSE_FILE not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Compose file found"

# Check if existing database container is running
if docker ps --format '{{.Names}}' | grep -q "shia-chatbot-postgres"; then
    echo -e "${GREEN}✓${NC} PostgreSQL container is already running (will be reused)"
else
    echo -e "${YELLOW}⚠${NC}  PostgreSQL container not running"
    echo -e "${YELLOW}⚠${NC}  Make sure to start it first with: docker-compose up -d postgres"
fi

# Check if existing Redis container is running
if docker ps --format '{{.Names}}' | grep -q "shia-chatbot-redis"; then
    echo -e "${GREEN}✓${NC} Redis container is already running (will be reused)"
else
    echo -e "${YELLOW}⚠${NC}  Redis container not running"
    echo -e "${YELLOW}⚠${NC}  Make sure to start it first with: docker-compose up -d redis"
fi

# Check if existing Qdrant container is running
if docker ps --format '{{.Names}}' | grep -q "shia-chatbot-qdrant"; then
    echo -e "${GREEN}✓${NC} Qdrant container is already running (will be reused)"
else
    echo -e "${YELLOW}⚠${NC}  Qdrant container not running"
    echo -e "${YELLOW}⚠${NC}  Make sure to start it first with: docker-compose up -d qdrant"
fi

# Warn about production containers
echo -e "\n${YELLOW}Checking for production containers (wisqu.ai)...${NC}"
PROD_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E '^(compose-|dev-)' || true)
if [ -n "$PROD_CONTAINERS" ]; then
    echo -e "${GREEN}✓${NC} Production containers detected and will NOT be affected:"
    echo "$PROD_CONTAINERS" | while read -r container; do
        echo -e "  - $container ${GREEN}(protected)${NC}"
    done
else
    echo -e "${GREEN}✓${NC} No production containers detected"
fi

# ==========================================================================
# PRE-DEPLOYMENT CHECKS
# ==========================================================================

echo -e "\n${YELLOW}Pre-deployment checks...${NC}"

# Check available system resources
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $7}')
CPU_CORES=$(nproc)

echo -e "${GREEN}✓${NC} System Resources:"
echo -e "  - Total Memory: ${TOTAL_MEM}GB"
echo -e "  - Available Memory: ${AVAILABLE_MEM}GB"
echo -e "  - CPU Cores: ${CPU_CORES}"

if [ "$AVAILABLE_MEM" -lt 4 ]; then
    echo -e "${YELLOW}⚠${NC}  Warning: Low available memory (${AVAILABLE_MEM}GB)"
    echo -e "${YELLOW}⚠${NC}  Recommended: At least 4GB free"
fi

# Create network if it doesn't exist
if docker network ls | grep -q "chatbot-network"; then
    echo -e "${GREEN}✓${NC} Network 'chatbot-network' exists"
else
    echo -e "${YELLOW}⚠${NC}  Creating network 'chatbot-network'..."
    docker network create chatbot-network
    echo -e "${GREEN}✓${NC} Network created"
fi

# Connect existing containers to network if needed
for container in shia-chatbot-postgres shia-chatbot-redis shia-chatbot-qdrant; do
    if docker ps --format '{{.Names}}' | grep -q "$container"; then
        if docker network inspect chatbot-network | grep -q "$container"; then
            echo -e "${GREEN}✓${NC} $container is already on chatbot-network"
        else
            echo -e "${YELLOW}⚠${NC}  Connecting $container to chatbot-network..."
            docker network connect chatbot-network "$container" 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Connected"
        fi
    fi
done

# ==========================================================================
# BUILD & START
# ==========================================================================

echo -e "\n${YELLOW}Building images...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache

echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# ==========================================================================
# HEALTH CHECKS
# ==========================================================================

echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "\n${YELLOW}Service Status:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Test FastAPI health endpoint
echo -e "\n${YELLOW}Testing FastAPI health endpoint...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8100/api/v1/health/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} FastAPI is healthy"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}⚠${NC}  Waiting for FastAPI... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}ERROR: FastAPI failed to start${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose -f $COMPOSE_FILE logs app-1${NC}"
    exit 1
fi

# ==========================================================================
# SUCCESS
# ==========================================================================

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Queue System Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Services:"
echo -e "  - ${GREEN}FastAPI (NGINX):${NC}   http://localhost:8100"
echo -e "  - ${GREEN}API Docs:${NC}          http://localhost:8100/docs"
echo -e "  - ${GREEN}Flower Dashboard:${NC}  http://localhost:5556 (admin/changeme)"
echo -e "  - ${GREEN}Job Status:${NC}        http://localhost:8100/api/v1/jobs/"

echo -e "\nUseful commands:"
echo -e "  - View logs:       ${YELLOW}docker-compose -f $COMPOSE_FILE logs -f${NC}"
echo -e "  - Check status:    ${YELLOW}docker-compose -f $COMPOSE_FILE ps${NC}"
echo -e "  - Stop services:   ${YELLOW}./scripts/stop-queue-system.sh${NC}"
echo -e "  - View workers:    ${YELLOW}docker-compose -f $COMPOSE_FILE logs -f celery-worker-high-1${NC}"

echo -e "\n${GREEN}Happy coding! 🚀${NC}\n"
