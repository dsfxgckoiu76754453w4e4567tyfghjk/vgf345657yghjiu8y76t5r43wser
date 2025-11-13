# Deployment & Development Workflow Guide

This guide explains how to use the Docker infrastructure for different workflows: local development, team collaboration, staging, and production deployment.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Docker Infrastructure Overview](#docker-infrastructure-overview)
- [Deployment Modes](#deployment-modes)
- [Your Workflow (Developer)](#your-workflow-developer)
- [Team Workflow](#team-workflow)
- [Environment Promotion](#environment-promotion)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Local Development (Fast Iteration)

```bash
# 1. Start only infrastructure services
make docker-local

# 2. Run app locally with hot reload
make dev

# 3. Run Celery worker locally (optional)
make celery-worker-dev

# You now have:
# ✅ FastAPI running locally (hot reload)
# ✅ Connected to Docker services (Postgres, Redis, etc.)
# ✅ Fast iteration (no Docker rebuilds)
```

### Shared DEV Environment (Team Access)

```bash
# Deploy full DEV stack for team
make docker-dev

# Team accesses via: http://your-server:8000
```

---

## 🏗️ Docker Infrastructure Overview

### File Structure

```
.
├── Dockerfile                          # Main application image (multi-stage)
├── docker-compose.base.yml             # Infrastructure services (shared)
├── docker-compose.app.dev.yml          # DEV environment application
├── docker-compose.app.stage.yml        # STAGE environment application
├── docker-compose.app.prod.yml         # PROD environment application (⚠️ VPS!)
├── docker-compose.redis-cluster.yml    # Optional: Redis cluster scaling
└── docker-compose.db-replicas.yml      # Optional: PostgreSQL replicas
```

### Infrastructure Services (base.yml)

These run in **all modes** and are shared across environments:

| Service | Purpose | Port | Data Volume |
|---------|---------|------|-------------|
| **PostgreSQL** | Database | 5433 | `postgres_data` |
| **Redis** | Cache & Message Broker | 6379 | `redis_data` |
| **Qdrant** | Vector Database | 6333, 6334 | `qdrant_data` |
| **MinIO** | Object Storage | 9000, 9001 | `minio_data` |
| **Prometheus** | Metrics | 9090 | `prometheus_data` |
| **Grafana** | Dashboards | 3000 | `grafana_data` |
| **Nginx** | Reverse Proxy | 8100 | - |
| **Temporal** | Workflow Engine | 7233, 8233 | `temporal_data` |

### Application Services (app.*.yml)

Environment-specific application containers:

| Environment | Containers | External Port | Database | Redis DB |
|-------------|-----------|---------------|----------|----------|
| **DEV** | app, celery-worker, celery-beat, flower | 8000 | `shia_chatbot_dev` | 0 |
| **STAGE** | app, celery-worker, celery-beat, flower | 8001 | `shia_chatbot_stage` | 1 |
| **PROD** | app, celery-worker, celery-beat, flower | 8002 | `shia_chatbot_prod` | 2 |

### Environment Isolation

Each environment is **fully isolated**:

```yaml
DEV:
  Database: shia_chatbot_dev
  Redis DB: 0
  Qdrant Prefix: dev_
  MinIO Prefix: dev-
  Container Prefix: shia-chatbot-dev-*

STAGE:
  Database: shia_chatbot_stage
  Redis DB: 1
  Qdrant Prefix: stage_
  MinIO Prefix: stage-
  Container Prefix: shia-chatbot-stage-*

PROD:
  Database: shia_chatbot_prod
  Redis DB: 2
  Qdrant Prefix: prod_
  MinIO Prefix: prod-
  Container Prefix: shia-chatbot-prod-*
```

---

## 🎯 Deployment Modes

### Mode 1: Local Development (Infrastructure Only)

**When to use**: Your daily development workflow for rapid iteration

**What runs**:
- ✅ Docker: PostgreSQL, Redis, Qdrant, MinIO, etc. (infrastructure)
- ✅ Native: FastAPI app with hot reload
- ✅ Native: Celery worker (optional)

**Commands**:
```bash
# Start infrastructure
make docker-local

# Run app locally
make dev

# Run Celery locally (optional)
make celery-worker-dev

# Stop infrastructure
make docker-local-down
```

**Benefits**:
- ⚡ Fast iteration (no Docker rebuild)
- 🐛 Full debugging capability
- 🔄 Hot reload for code changes
- 💻 Use your IDE/editor directly

**Workflow**:
```bash
# 1. Start services once
make docker-local

# 2. Develop (repeat as needed)
make dev                    # Terminal 1: Run app
# Edit code → save → auto-reload → test

make celery-worker-dev      # Terminal 2: Run Celery (if needed)
# Edit tasks → restart worker → test

# 3. When done for the day
make docker-local-down
```

---

### Mode 2: Shared DEV Environment (Full Stack)

**When to use**: Deploy for frontend team, QA, and other developers

**What runs**:
- ✅ Docker: All infrastructure services
- ✅ Docker: FastAPI app container
- ✅ Docker: Celery workers (high/medium/low priority)
- ✅ Docker: Celery beat scheduler
- ✅ Docker: Flower monitoring

**Commands**:
```bash
# Start DEV environment
make docker-dev

# View logs
make docker-logs-dev

# Check health
make docker-health

# Stop DEV environment
make docker-dev-down

# Restart DEV environment
make docker-dev-restart
```

**Access**:
- **App**: http://localhost:8000 (or http://your-server:8000)
- **API Docs**: http://localhost:8000/docs
- **Flower**: http://localhost:5555
- **Qdrant**: http://localhost:6333/dashboard
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

**Environment Variables**:
- Uses `.env` file
- `ENVIRONMENT=dev`
- Debug mode enabled
- Verbose logging

---

### Mode 3: STAGE Environment (Pre-Release)

**When to use**: Beta testing with internal team and selected end users

**What runs**: Same as DEV but with production-like configuration

**Commands**:
```bash
# Start STAGE environment
make docker-stage

# View logs
make docker-logs-stage

# Stop STAGE environment
make docker-stage-down
```

**Access**:
- **App**: http://localhost:8001
- **Flower**: http://localhost:5556

**Environment Variables**:
- Uses `.env.stage` file (if exists) or `.env`
- `ENVIRONMENT=stage`
- Debug mode disabled
- Info-level logging
- Production-like resource limits

---

### Mode 4: PROD Environment (Live Production)

⚠️ **CRITICAL WARNING**: This VPS hosts other production containers with real users!

**When to use**: Serving actual end users

**What runs**: Same as STAGE but with full production optimizations

**Commands**:
```bash
# ⚠️ WARNING: Read docker-compose.app.prod.yml header first!
# Check existing containers
docker ps -a

# Start PROD environment (be careful!)
make docker-prod

# View logs
make docker-logs-prod

# Stop PROD environment
make docker-prod-down
```

**Access**:
- **App**: http://localhost:8002
- **Flower**: http://localhost:5557

**Environment Variables**:
- Uses `.env.prod` file
- `ENVIRONMENT=prod`
- Debug mode disabled
- Warning-level logging
- Maximum resource limits

**⚠️ SAFETY RULES**:

```bash
# ✅ SAFE - Container-specific commands
docker stop shia-chatbot-prod-app
docker rm shia-chatbot-prod-app
docker logs shia-chatbot-prod-app
docker-compose -f docker-compose.app.prod.yml down

# ❌ DANGEROUS - Will affect other production services!
docker system prune -a          # Deletes ALL containers!
docker volume prune             # Deletes ALL volumes!
docker network prune            # Affects other services!
docker stop $(docker ps -aq)    # Stops ALL containers!
```

---

## 👨‍💻 Your Workflow (Developer)

### Daily Development Routine

```bash
# Morning - Start infrastructure
make docker-local

# Develop iteratively
make dev  # Terminal 1: App with hot reload

# Edit code in your IDE
# Save → Auto-reload → Test in browser/Postman
# Repeat: Edit → Save → Test → Debug

# If working on background tasks
make celery-worker-dev  # Terminal 2: Celery with hot reload

# Evening - Stop infrastructure
make docker-local-down
```

### Testing Your Changes

```bash
# Run unit tests
make test-unit

# Run integration tests (requires docker-local running)
make test-integration

# Run all tests with coverage
make test

# Check code quality
make lint
make format
```

### Before Releasing to Team DEV

```bash
# 1. Ensure all tests pass
make test

# 2. Check code quality
make lint
make security

# 3. Commit your changes
git add .
git commit -m "feat: your feature description"

# 4. Push to trigger CI/CD or deploy manually
git push
```

---

## 👥 Team Workflow

### For Frontend Developers

```bash
# Connect to shared DEV environment
API_BASE_URL=http://dev-server:8000

# Access API documentation
http://dev-server:8000/docs

# Use Swagger UI for testing
# Or integrate with your frontend app
```

### For QA Team

```bash
# Test DEV environment
http://dev-server:8000/docs

# Monitor background tasks
http://dev-server:5555  # Flower dashboard

# Check system health
http://dev-server:8000/health

# View metrics
http://dev-server:3000  # Grafana dashboards
```

### For Other Backend Developers

**Option 1: Work on shared DEV**
```bash
# Deploy your changes to shared DEV
git push origin dev
# CI/CD deploys automatically
# Or manually: make docker-dev-restart
```

**Option 2: Run locally (like you)**
```bash
# Start infrastructure
make docker-local

# Run app locally
make dev

# Develop and test
```

---

## 🔄 Environment Promotion

### DEV → STAGE

```bash
# 1. Ensure DEV is stable
make test                        # All tests pass
make docker-health              # All services healthy

# 2. Tag release
git tag v1.0.0-rc1
git push origin v1.0.0-rc1

# 3. Deploy to STAGE
make docker-stage

# 4. Promote approved data (optional)
make docker-promote-dev-stage
```

### STAGE → PROD

```bash
# 1. STAGE tested and approved by team + beta users
make test                        # Final verification

# 2. Tag production release
git tag v1.0.0
git push origin v1.0.0

# 3. ⚠️ Deploy to PROD (check other containers first!)
docker ps -a                     # Verify no conflicts
make docker-prod                 # Deploy carefully

# 4. Promote approved data (optional)
make docker-promote-stage-prod
```

---

## 🐛 Troubleshooting

### Local Development Issues

**Problem**: Can't connect to database
```bash
# Check if infrastructure is running
make docker-health

# Check database connection
docker exec -it shia-chatbot-postgres psql -U postgres -d shia_chatbot

# Restart infrastructure
make docker-local-restart
```

**Problem**: Port conflicts
```bash
# Check what's using port 5433 (Postgres)
lsof -i :5433

# Change port in .env
POSTGRES_PORT=5434

# Restart
make docker-local-restart
```

**Problem**: Redis connection errors
```bash
# Check Redis
docker exec -it shia-chatbot-redis redis-cli ping

# Should return: PONG
```

### Shared DEV Issues

**Problem**: Container won't start
```bash
# Check logs
make docker-logs-dev

# Check container status
docker-compose -f docker-compose.base.yml -f docker-compose.app.dev.yml ps

# Restart specific service
docker-compose -f docker-compose.base.yml -f docker-compose.app.dev.yml restart app
```

**Problem**: Out of memory
```bash
# Check resource usage
docker stats

# Adjust resource limits in docker-compose.app.dev.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase if needed
```

### Celery Issues

**Problem**: Tasks not processing
```bash
# Check worker status (local)
make celery-inspect

# Check worker status (Docker)
docker logs shia-chatbot-dev-celery-worker

# Check Flower dashboard
http://localhost:5555

# Restart workers
make celery-worker-dev  # Local
# or
docker-compose -f docker-compose.app.dev.yml restart celery-worker  # Docker
```

**Problem**: Beat scheduler running multiple times
```bash
# Check beat processes
ps aux | grep celery.*beat

# Kill duplicate processes
pkill -f "celery.*beat"

# Ensure only ONE beat instance runs
make celery-beat
```

### Production Issues

**Problem**: Need to rollback
```bash
# Stop production
make docker-prod-down

# Deploy previous version
git checkout v1.0.0-prev
make docker-prod

# Or use specific image tag
docker-compose -f docker-compose.app.prod.yml pull
docker-compose -f docker-compose.app.prod.yml up -d
```

**Problem**: Other containers affected
```bash
# Check ALL containers
docker ps -a

# Check resource usage
docker stats

# Check network conflicts
docker network ls
docker network inspect chatbot-network
```

---

## 📚 Additional Resources

- **Architecture**: See `docs/architecture.md`
- **Celery**: See `scripts/celery/README.md`
- **API Documentation**: http://localhost:8000/docs
- **Makefile Commands**: Run `make help`

---

## 🤝 Summary

### For You (Daily Development)

```bash
make docker-local           # Start infrastructure once
make dev                    # Develop with hot reload
# Edit → Save → Test → Repeat
make docker-local-down      # Stop when done
```

### For Team (Shared Environment)

```bash
make docker-dev             # Deploy for team access
# Team uses: http://dev-server:8000
make docker-dev-restart     # Update with your changes
```

### For Release (Staging & Production)

```bash
make docker-stage           # Deploy to STAGE for testing
# Test with internal team + beta users
make docker-prod            # ⚠️ Deploy to PROD carefully
```

**Key Principle**: Infrastructure in Docker, App flexible (Docker or native) based on your workflow needs!
