# VPS Deployment Guide

All environments (dev, stage, prod) run on the **SAME VPS**.

## Quick Start

```bash
# Start infrastructure services (once)
docker compose -f docker-compose.base.yml up -d

# Deploy specific environment
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml up -d    # DEV
docker compose -f docker-compose.base.yml -f docker-compose.app.stage.yml up -d  # STAGE
docker compose -f docker-compose.base.yml -f docker-compose.app.prod.yml up -d   # PROD
```

## Environment Isolation

| Environment | Port | Database | Redis DB | Qdrant Prefix | MinIO Prefix |
|-------------|------|----------|----------|---------------|--------------|
| **DEV**     | 8000 | `shia_chatbot_dev` | 0 | `dev_` | `dev-` |
| **STAGE**   | 8001 | `shia_chatbot_stage` | 1 | `stage_` | `stage-` |
| **PROD**    | 8002 | `shia_chatbot_prod` | 2 | `prod_` | `prod-` |

## Infrastructure Services

Shared across all environments (docker-compose.base.yml):

- PostgreSQL (port 5433)
- Redis (port 6379)
- Qdrant (ports 6333, 6334)
- MinIO (ports 9000, 9001)
- Temporal (ports 7233, 8233)
- Prometheus (port 9090)
- Grafana (port 3000)
- Nginx (port 8100)

## Development Workflow

### On VPS (Your Daily Work)

```bash
# Pull latest changes
git pull origin main

# Update dependencies if needed
poetry install

# Run app directly (hot reload)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# Or restart deployed environment
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml restart app
```

### Deploying Updates

```bash
# 1. Commit and push
git add .
git commit -m "feat: your changes"
git push

# 2. On VPS, pull and restart
git pull
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml up -d --build
```

## Async Tasks

Temporal handles all background processing:
- Chat workflows
- File uploads
- Data processing

**Temporal UI**: http://localhost:8233

## Monitoring

- **App Health**: http://localhost:{port}/health
- **API Docs**: http://localhost:{port}/docs
- **Temporal UI**: http://localhost:8233
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## Common Commands

```bash
# Check status
docker compose ps

# View logs
docker logs shia-chatbot-dev-app -f

# Restart app
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml restart app

# Stop environment
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml down

# Database migrations
poetry run alembic upgrade head
```

## VPS Safety

⚠️ **This VPS hosts multiple production services!**

**Safe commands:**
```bash
docker compose down                      # Stops only your services
docker logs shia-chatbot-dev-app        # View specific container
docker restart shia-chatbot-dev-app     # Restart specific container
```

**Dangerous commands (NEVER use):**
```bash
docker system prune -a   # Deletes ALL containers!
docker volume prune      # Deletes ALL volumes!
docker stop $(docker ps -q)  # Stops ALL containers!
```

## Troubleshooting

### Can't connect to database
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs shia-chatbot-postgres

# Restart database
docker restart shia-chatbot-postgres
```

### Port already in use
```bash
# Find what's using the port
lsof -i :8000

# Kill the process or use a different port
```

### App won't start
```bash
# Check logs
docker logs shia-chatbot-dev-app

# Rebuild image
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml up -d --build --force-recreate
```

## File Structure

```
docker-compose.base.yml      # Infrastructure (shared)
docker-compose.app.dev.yml   # DEV environment
docker-compose.app.stage.yml # STAGE environment
docker-compose.app.prod.yml  # PROD environment
```

## Environment Promotion

```bash
# DEV → STAGE
docker compose -f docker-compose.base.yml -f docker-compose.app.stage.yml up -d --build

# STAGE → PROD (⚠️ be careful!)
docker compose -f docker-compose.base.yml -f docker-compose.app.prod.yml up -d --build
```

---

**That's it!** Simple, clean, minimal.

For more commands: `make help`
