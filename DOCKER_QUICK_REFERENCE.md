# Docker Quick Reference Guide

Quick command reference for different deployment scenarios.

## 🚀 Quick Commands

### Local Development (You - Fast Iteration)

```bash
# Start
make docker-local        # Infrastructure only
make dev                 # App with hot reload (Terminal 1)
make celery-worker-dev   # Celery worker (Terminal 2, optional)

# Stop
make docker-local-down

# Restart
make docker-local-restart
```

**What runs where:**
- 🐳 Docker: PostgreSQL, Redis, Qdrant, MinIO, Prometheus, Grafana, Nginx, Temporal
- 💻 Native: FastAPI (hot reload), Celery workers (hot reload)

**Benefits:**
- ⚡ Instant code changes (no Docker rebuild)
- 🐛 Full debugging with your IDE
- 🔄 Hot reload for Python changes

---

### Shared DEV Environment (Team Access)

```bash
# Start
make docker-dev

# View logs
make docker-logs-dev

# Restart
make docker-dev-restart

# Stop
make docker-dev-down
```

**Access:**
- App: http://localhost:8000
- Docs: http://localhost:8000/docs
- Flower: http://localhost:5555
- Qdrant: http://localhost:6333/dashboard
- Grafana: http://localhost:3000

---

### STAGE Environment (Beta Testing)

```bash
# Start
make docker-stage

# View logs
make docker-logs-stage

# Restart
make docker-stage-restart

# Stop
make docker-stage-down
```

**Access:**
- App: http://localhost:8001
- Flower: http://localhost:5556

---

### PROD Environment (⚠️ Shared VPS!)

```bash
# ⚠️ Check other containers first!
docker ps -a

# Start (requires confirmation)
make docker-prod

# View logs
make docker-logs-prod

# Stop (be careful!)
make docker-prod-down
```

**Access:**
- App: http://localhost:8002
- Flower: http://localhost:5557

**⚠️ SAFETY:**
- ✅ Use `docker-compose` commands (only affects shia-chatbot)
- ❌ Avoid `docker system prune` (affects ALL containers)
- ❌ Avoid `docker volume prune` (deletes ALL volumes)

---

## 📊 Monitoring & Health

```bash
# Check health of all services
make docker-health

# View logs
make docker-logs-dev        # DEV
make docker-logs-stage      # STAGE
make docker-logs-prod       # PROD

# Check container status
docker-compose ps

# Check resource usage
docker stats
```

---

## 🔧 Maintenance

```bash
# Backup volumes
make docker-backup

# Clean (keeps volumes)
make docker-clean

# Clean ALL (deletes data - requires confirmation)
make docker-clean-all
```

---

## 🐞 Celery Commands

### Local Development

```bash
# Single worker (all queues)
make celery-worker-dev

# With auto-reload
make celery-worker-dev-reload

# Beat scheduler
make celery-beat

# Inspect workers
make celery-inspect

# Monitor with Flower
make flower
```

### Production (Priority-Based)

```bash
# Separate workers per priority
make celery-worker-high      # User-facing tasks
make celery-worker-medium    # Background processing
make celery-worker-low       # Fire-and-forget

# All priority workers at once
make celery-worker-all-prod

# Beat scheduler
make celery-beat
```

---

## 📁 File Structure

```
.
├── Dockerfile                          # Main app image
├── docker-compose.base.yml             # Infrastructure (shared)
├── docker-compose.app.dev.yml          # DEV environment
├── docker-compose.app.stage.yml        # STAGE environment
├── docker-compose.app.prod.yml         # PROD environment (⚠️ VPS!)
├── docker-compose.redis-cluster.yml    # Optional: Redis cluster
├── docker-compose.db-replicas.yml      # Optional: DB replicas
└── DEPLOYMENT.md                       # Full guide
```

---

## 🔄 Typical Workflows

### Your Daily Development

```bash
# Morning
make docker-local          # Start infrastructure
make dev                   # Start app

# During the day
# Edit code → Auto-reload → Test in browser
# Edit code → Auto-reload → Test in browser
# (Repeat as needed)

# Evening
Ctrl+C                     # Stop app
make docker-local-down     # Stop infrastructure
```

### Releasing to Team DEV

```bash
# 1. Test locally
make test
make lint

# 2. Commit & push
git add .
git commit -m "feat: your feature"
git push

# 3. Deploy to shared DEV
make docker-dev-restart
```

### Promoting to STAGE

```bash
# 1. Test DEV thoroughly
make test

# 2. Tag release
git tag v1.0.0-rc1
git push origin v1.0.0-rc1

# 3. Deploy to STAGE
make docker-stage-restart
```

### Deploying to PROD

```bash
# 1. Check other containers
docker ps -a

# 2. Test STAGE thoroughly
# (Manual testing, QA approval, etc.)

# 3. Tag production release
git tag v1.0.0
git push origin v1.0.0

# 4. Deploy (requires confirmation)
make docker-prod
```

---

## 🆘 Troubleshooting

### Can't connect to database

```bash
# Check health
make docker-health

# Check database
docker exec -it shia-chatbot-postgres psql -U postgres -l

# Restart
make docker-local-restart
```

### Port conflicts

```bash
# Find what's using port
lsof -i :5433  # Postgres
lsof -i :6379  # Redis
lsof -i :8000  # App

# Change port in .env
POSTGRES_PORT=5434

# Restart
make docker-local-restart
```

### Celery not processing

```bash
# Check workers
make celery-inspect

# View Flower dashboard
make flower  # http://localhost:5555

# Check logs (Docker)
docker logs shia-chatbot-dev-celery-worker

# Restart
make celery-worker-dev  # Local
# or
docker-compose -f docker-compose.app.dev.yml restart celery-worker  # Docker
```

### Container won't start

```bash
# Check logs
make docker-logs-dev

# Check status
docker-compose ps

# Restart specific service
docker-compose restart app

# Full restart
make docker-dev-restart
```

---

## ⚠️ Production VPS Safety

**This VPS hosts multiple production services with real users!**

### Safe Commands ✅

```bash
# Container-specific
docker stop shia-chatbot-prod-app
docker restart shia-chatbot-prod-celery-worker
docker logs shia-chatbot-prod-app

# docker-compose (only affects shia-chatbot)
docker-compose -f docker-compose.app.prod.yml down
docker-compose -f docker-compose.app.prod.yml restart app

# Makefile commands (safe)
make docker-prod
make docker-prod-down
make docker-prod-restart
```

### Dangerous Commands ❌

```bash
# These affect ALL containers on the VPS!
docker stop $(docker ps -q)      # Stops everything
docker rm $(docker ps -aq)       # Removes everything
docker system prune -a           # Deletes everything
docker volume prune              # Deletes all volumes
docker network prune             # Affects other services
```

### Before Any Production Action

1. ✅ Check running containers: `docker ps -a`
2. ✅ Check container names for conflicts
3. ✅ Check port bindings
4. ✅ Verify system resources
5. ✅ Read docker-compose.app.prod.yml warnings

---

## 📚 More Information

- **Full Deployment Guide**: `DEPLOYMENT.md`
- **Celery Guide**: `scripts/celery/README.md`
- **Architecture**: `docs/architecture.md`
- **API Documentation**: http://localhost:8000/docs
- **All Commands**: `make help`

---

## 🎯 Summary

| Mode | Command | Use Case | App Runs |
|------|---------|----------|----------|
| **Local Dev** | `make docker-local` + `make dev` | Your daily development | Native (hot reload) |
| **Shared DEV** | `make docker-dev` | Team collaboration | Docker |
| **STAGE** | `make docker-stage` | Beta testing | Docker |
| **PROD** | `make docker-prod` | Real users (⚠️ VPS!) | Docker |

**Key Principle**: Infrastructure always in Docker, app flexible based on workflow!
