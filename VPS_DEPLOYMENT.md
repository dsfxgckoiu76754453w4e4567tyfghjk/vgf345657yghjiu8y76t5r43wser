# VPS Deployment Guide

All environments run on the **SAME VPS** with complete isolation.

## 4 Environments

1. **LOCAL** - Your personal development (not deployed, just you working)
2. **DEV** - Deployed for frontend team + QA testing
3. **STAGE** - Pre-release testing with beta users
4. **PROD** - Production for real users

## Environment Isolation (Complete)

| Environment | Port | Database | Redis DB | Qdrant | MinIO | Temporal Queue |
|-------------|------|----------|----------|--------|-------|----------------|
| **LOCAL** (You) | 8003 | `shia_chatbot_local` | 3 | `local_` | `local-` | `wisqu-local-queue` |
| **DEV** (Team) | 8000 | `shia_chatbot_dev` | 0 | `dev_` | `dev-` | `wisqu-dev-queue` |
| **STAGE** | 8001 | `shia_chatbot_stage` | 1 | `stage_` | `stage-` | `wisqu-stage-queue` |
| **PROD** | 8002 | `shia_chatbot_prod` | 2 | `prod_` | `prod-` | `wisqu-prod-queue` |

✅ **Complete isolation** - Each environment has its own database, Redis DB, collections, buckets, and workflows.

## Quick Start

### Your Personal Development (LOCAL)

```bash
# 1. Start infrastructure (once)
docker compose -f docker-compose.base.yml up -d

# 2. Set environment variables for LOCAL
export DATABASE_NAME=shia_chatbot_local
export REDIS_DB=3
export QDRANT_COLLECTION_PREFIX=local_
export MINIO_BUCKET_PREFIX=local-
export TEMPORAL_TASK_QUEUE=wisqu-local-queue

# 3. Run migrations for LOCAL database
poetry run alembic upgrade head

# 4. Run app with hot reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

### Deploy for Team (DEV/STAGE/PROD)

```bash
# Start infrastructure (if not running)
docker compose -f docker-compose.base.yml up -d

# Deploy specific environment
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml up -d    # DEV
docker compose -f docker-compose.base.yml -f docker-compose.app.stage.yml up -d  # STAGE
docker compose -f docker-compose.base.yml -f docker-compose.app.prod.yml up -d   # PROD
```

## Infrastructure Services

Shared across all 4 environments (docker-compose.base.yml):

- PostgreSQL (port 5433) - Contains 4 databases
- Redis (port 6379) - DB 0,1,2,3 for isolation
- Qdrant (ports 6333, 6334) - Collection prefixes for isolation
- MinIO (ports 9000, 9001) - Bucket prefixes for isolation
- Temporal (ports 7233, 8233) - Task queues for isolation
- Prometheus (port 9090)
- Grafana (port 3000)
- Nginx (port 8100)

## Your Development Workflow (LOCAL → DEV → STAGE → PROD)

### 1. Work Locally (LOCAL environment)

```bash
# Pull latest
git pull

# Work on features (uses shia_chatbot_local database)
export DATABASE_NAME=shia_chatbot_local REDIS_DB=3
poetry run uvicorn app.main:app --reload --port 8003

# Test your changes
curl http://localhost:8003/health
```

### 2. Deploy to Team DEV

```bash
# Commit and push
git add .
git commit -m "feat: your feature"
git push

# Restart DEV environment (frontend/QA will use this)
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml up -d --build
```

### 3. Promote to STAGE

```bash
# Tag release
git tag v1.0.0-rc1
git push --tags

# Deploy to STAGE (beta testers)
docker compose -f docker-compose.base.yml -f docker-compose.app.stage.yml up -d --build
```

### 4. Deploy to PROD

```bash
# After STAGE testing passes
git tag v1.0.0
git push --tags

# Deploy to PROD (real users)
docker compose -f docker-compose.base.yml -f docker-compose.app.prod.yml up -d --build
```

## Database Management

### Run Migrations

```bash
# LOCAL (your work)
export DATABASE_NAME=shia_chatbot_local
poetry run alembic upgrade head

# DEV (deployed)
docker exec shia-chatbot-dev-app alembic upgrade head

# STAGE (deployed)
docker exec shia-chatbot-stage-app alembic upgrade head

# PROD (deployed)
docker exec shia-chatbot-prod-app alembic upgrade head
```

### Create New Migration

```bash
# Work on LOCAL first
export DATABASE_NAME=shia_chatbot_local
poetry run alembic revision --autogenerate -m "add new table"
poetry run alembic upgrade head

# Test it, then deploy to team
```

## Async Tasks (Temporal)

All environments use Temporal with isolated task queues:

- **Temporal UI**: http://localhost:8233
- View workflows per environment using queue filters
- Monitor execution, retries, errors

## Monitoring

- **Your LOCAL**: http://localhost:8003/health
- **DEV (Team)**: http://localhost:8000/health + /docs
- **STAGE**: http://localhost:8001/health + /docs
- **PROD**: http://localhost:8002/health + /docs
- **Temporal**: http://localhost:8233
- **Grafana**: http://localhost:3000 (admin/admin)

## Common Commands

```bash
# Check running containers
docker compose ps

# View logs
docker logs shia-chatbot-dev-app -f        # DEV
docker logs shia-chatbot-stage-app -f      # STAGE
docker logs shia-chatbot-prod-app -f       # PROD

# Restart environment
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml restart app

# Stop environment
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml down
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
# Check PostgreSQL
docker ps | grep postgres

# Check if your database exists
docker exec -it shia-chatbot-postgres psql -U postgres -l

# Should see: shia_chatbot_local, shia_chatbot_dev, shia_chatbot_stage, shia_chatbot_prod
```

### Port conflict

```bash
# Check what's using port
lsof -i :8003   # LOCAL
lsof -i :8000   # DEV
lsof -i :8001   # STAGE
lsof -i :8002   # PROD
```

### Database migrations out of sync

```bash
# Check current version
poetry run alembic current

# View migration history
poetry run alembic history

# Upgrade to latest
poetry run alembic upgrade head
```

## Promotion Strategy

```
LOCAL (you) → test locally
    ↓
DEV (team) → frontend + QA test
    ↓
STAGE (beta) → internal team + beta users test
    ↓
PROD (live) → all real users
```

---

**That's it!** 4 completely isolated environments on same VPS.

For more: `make help`
