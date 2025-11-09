# Operations Guide

> Complete guide for deployment, configuration, and operations

**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Environment Architecture](#environment-architecture)
2. [Docker Services](#docker-services)
3. [Deployment](#deployment)
4. [Configuration](#configuration)
5. [Database Operations](#database-operations)
6. [Monitoring](#monitoring)
7. [Incident Response](#incident-response)
8. [Backup & Recovery](#backup--recovery)

---

## 🏗️ Environment Architecture

### Environment Specifications

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **Environment Variable** | `ENVIRONMENT=dev` | `ENVIRONMENT=stage` | `ENVIRONMENT=prod` |
| **Database Prefix** | `dev_` | `stage_` | `prod_` |
| **Debug Mode** | ✅ Enabled | ❌ Disabled | ❌ Disabled |
| **Log Level** | DEBUG | INFO | WARNING |
| **Workers** | 1 | 2 | 4+ |
| **Backups** | None | Daily | Hourly + Daily |
| **Monitoring** | Optional | Enabled | Full stack |
| **SSL** | Not required | Required | Required |

### Infrastructure Requirements

**Development:**
- Local machine
- Docker Desktop
- 8GB RAM minimum

**Staging:**
- 2 CPU cores, 4GB RAM
- PostgreSQL 15+
- Redis 7.2+
- SSL certificate

**Production:**
- 4+ CPU cores, 8GB+ RAM
- PostgreSQL 15+ (managed service recommended)
- Redis 7.2+ (managed service recommended)
- Load balancer
- CDN for static assets
- SSL certificate
- Monitoring stack

---

## 🐳 Docker Services

### New Optimized Architecture

**Composable Docker Setup** - Zero redundancy, complete isolation between environments

| File | Purpose | Services | When to Use |
|------|---------|----------|-------------|
| **docker-compose.base.yml** | All infrastructure | PostgreSQL, Redis, Qdrant, MinIO, Prometheus, Grafana, Nginx | Shared by all modes |
| **docker-compose.app.dev.yml** | DEV environment overlay | App, Celery, Flower (ENVIRONMENT=dev) | Internal team releases |
| **docker-compose.app.stage.yml** | STAGE environment overlay | App, Celery, Flower (ENVIRONMENT=stage) | Test users environment |
| **docker-compose.app.prod.yml** | PROD environment overlay | App, Celery, Flower (ENVIRONMENT=prod) | Production deployment |

### Two Modes of Operation

#### Mode 1: Local Development (No Image Build)

**Purpose:** Fast iteration, debugging, hot reload

```bash
# Start ALL infrastructure services in Docker
make docker-local

# Then run app natively
make dev           # FastAPI with hot reload
make celery-worker # Celery worker natively
```

**What runs in Docker:**
- PostgreSQL, Redis, Qdrant, MinIO
- Prometheus, Grafana, Nginx
- Everything EXCEPT the app

**What runs natively:**
- FastAPI app (hot reload, easy debugging)
- Celery worker (optional)

#### Mode 2: Environment Releases (Full Docker)

**Purpose:** Internal testing, staging, production

```bash
# DEV Environment (ENVIRONMENT=dev)
make docker-dev    # http://localhost:8000

# STAGE Environment (ENVIRONMENT=stage)
make docker-stage  # http://localhost:8001

# PROD Environment (ENVIRONMENT=prod)
make docker-prod   # http://localhost:8002
```

**What runs in Docker:**
- Everything: infrastructure + app + workers

### Environment Isolation

Each environment has **complete isolation:**

```
DEV:
  - Containers: shia-chatbot-dev-*
  - App Port: 8000
  - Flower Port: 5555
  - ENVIRONMENT=dev

STAGE:
  - Containers: shia-chatbot-stage-*
  - App Port: 8001
  - Flower Port: 5556
  - ENVIRONMENT=stage

PROD:
  - Containers: shia-chatbot-prod-*
  - App Port: 8002
  - Flower Port: 5557
  - ENVIRONMENT=prod
```

**Safe for VPS:** All environments can run simultaneously without conflicts

### Service Health Checks

```bash
make docker-health
```

| Service | Health Check Command | Endpoint |
|---------|---------------------|----------|
| PostgreSQL | `pg_isready -U postgres` | - |
| Redis | `redis-cli ping` | - |
| Qdrant | - | http://localhost:6333/healthz |
| FastAPI | - | http://localhost:8000/health |
| Celery | `celery inspect ping` | - |
| Flower | - | http://localhost:5555/healthcheck |
| Prometheus | - | http://localhost:9090/-/healthy |
| Grafana | - | http://localhost:3000/api/health |
| Nginx | - | http://localhost/health |

### Port Mapping

**Base Infrastructure Services (Shared):**

| Service | Internal | External | Protocol |
|---------|----------|----------|----------|
| PostgreSQL | 5432 | 5433 | TCP |
| Redis | 6379 | 6379 | TCP |
| Qdrant HTTP | 6333 | 6333 | HTTP |
| Qdrant gRPC | 6334 | 6334 | gRPC |
| MinIO API | 9000 | 9000 | HTTP |
| MinIO Console | 9001 | 9001 | HTTP |
| Prometheus | 9090 | 9090 | HTTP |
| Grafana | 3000 | 3000 | HTTP |
| Nginx | 80/443 | 8100/8443 | HTTP/HTTPS |

**Environment-Specific Services:**

| Service | DEV | STAGE | PROD | Protocol |
|---------|-----|-------|------|----------|
| FastAPI App | 8000 | 8001 | 8002 | HTTP |
| Flower | 5555 | 5556 | 5557 | HTTP |

**Note:** Different ports allow running multiple environments simultaneously

### Resource Limits

**Production configuration:**

```yaml
# FastAPI App
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G

# Celery Worker
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 512M
```

---

## 🚀 Deployment

### Pre-Deployment Checklist

```bash
# Run comprehensive verification
make verify-build

# Should show:
# ✅ ALL CHECKS PASSED - READY TO BUILD! ✅
```

**Checklist:**
- [ ] All tests pass (75%+ coverage)
- [ ] Code formatted (Black, isort)
- [ ] Linting passes (flake8, mypy, pylint)
- [ ] Security scans clean (Bandit, Safety)
- [ ] Pre-commit hooks configured
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Health checks working
- [ ] Swagger UI accessible

### Development Deployment

```bash
# 1. Start infrastructure
make docker-up

# 2. Run app natively
make dev

# 3. Test via Swagger UI
open http://localhost:8000/docs
```

### Staging Deployment

```bash
# 1. Build image
make build

# 2. Tag for staging
docker tag shia-chatbot:latest shia-chatbot:staging

# 3. Push to registry
docker push your-registry/shia-chatbot:staging

# 4. Deploy to staging server
ssh staging-server << 'EOF'
  docker pull your-registry/shia-chatbot:staging
  docker compose -f docker-compose.staging.yml up -d
  docker exec app alembic upgrade head
EOF

# 5. Smoke test
curl https://staging.yourapp.com/health
```

### Production Deployment (Blue-Green Strategy)

**Zero-downtime deployment:**

```bash
# 1. Deploy to green environment
ssh prod-server << 'EOF'
  docker pull your-registry/shia-chatbot:v1.0.0
  docker compose -f docker-compose.green.yml up -d
  docker exec app-green alembic upgrade head
EOF

# 2. Health check green environment
curl https://green.yourapp.com/health

# 3. Switch load balancer
ssh prod-server << 'EOF'
  sed -i 's/server app:8000/server app-green:8000/' /etc/nginx/conf.d/upstream.conf
  nginx -s reload
EOF

# 4. Monitor for 1 hour
# Watch metrics in Grafana

# 5. If stable, remove old blue environment
# If issues, rollback by switching nginx back to blue
```

### Rollback Procedure

```bash
# 1. Switch load balancer back to previous version
ssh prod-server << 'EOF'
  sed -i 's/server app-green:8000/server app-blue:8000/' /etc/nginx/conf.d/upstream.conf
  nginx -s reload
EOF

# 2. Rollback database migrations (if needed)
docker exec app alembic downgrade -1

# 3. Verify
curl https://yourapp.com/health
```

---

## ⚙️ Configuration

### Environment Variables

**Required variables:**

```env
# Environment
ENVIRONMENT=prod  # dev, stage, or prod

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333

# Security
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# API Keys
OPENROUTER_API_KEY=your-openrouter-api-key
```

**Optional variables:**

```env
# Langfuse (LLM Observability)
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

# ASR (Speech Recognition)
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# MinIO (Object Storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_URL=http://minio:9000

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-me-in-production

# Email (if using)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Secrets Management

**Development:**
- Store in `.env` file (gitignored)

**Staging/Production:**
- Use environment-specific secrets management:
  - AWS Secrets Manager
  - Azure Key Vault
  - HashiCorp Vault
  - Kubernetes Secrets

**Never commit secrets to git!**

---

## 🗄️ Database Operations

### Migrations

```bash
# Create new migration
make db-migrate MESSAGE="Add user preferences table"

# Apply migrations
make db-upgrade

# Rollback last migration
make db-downgrade

# Reset database (dev only)
make db-reset
```

### Production Migration Process

```bash
# 1. Test migration on staging
ssh staging-server << 'EOF'
  docker exec app alembic upgrade head
EOF

# 2. Backup production database
make db-dump

# 3. Apply migration to production
ssh prod-server << 'EOF'
  docker exec app alembic upgrade head
EOF

# 4. Verify
ssh prod-server << 'EOF'
  docker exec app alembic current
EOF

# 5. If issues, rollback
ssh prod-server << 'EOF'
  docker exec app alembic downgrade -1
EOF
```

### Database Backup

```bash
# Create backup
make db-dump

# Automated daily backup (add to cron)
0 2 * * * cd /path/to/app && make db-dump
```

### Database Restore

```bash
# Restore from backup
make db-restore FILE=backups/db_dump_20251109_120000.sql
```

---

## 📊 Monitoring

### Metrics Collection (Prometheus)

**Access:** http://localhost:9090

**Metrics available:**
- HTTP request count
- Request duration
- Response status codes
- Active requests
- Database query count
- Celery task metrics
- Custom business metrics

**Configuration:** `grafana/prometheus-scrape-config.yml`

```yaml
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

### Dashboards (Grafana)

**Access:** http://localhost:3000 (admin/admin)

**Pre-configured dashboards:**
- Application Overview
- Request Metrics
- Database Performance
- Celery Task Monitoring
- System Resources

### Celery Monitoring (Flower)

**Access:** http://localhost:5555

**Features:**
- Real-time task monitoring
- Worker status
- Task history
- Performance metrics

### Application Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Example metrics:**
```
# HTTP requests total
http_requests_total{method="GET",path="/api/v1/chat",status="200"} 1234

# Request duration
http_request_duration_seconds_sum{method="POST",path="/api/v1/chat"} 45.2

# Active requests
http_requests_active 12

# Database connections
db_connections_active 8
```

---

## 🚨 Incident Response

### Severity Levels

| Level | Response Time | Example |
|-------|--------------|---------|
| **SEV1 - Critical** | Immediate | App down, data loss |
| **SEV2 - High** | 1 hour | Feature broken, slow performance |
| **SEV3 - Medium** | 4 hours | Minor bug, non-critical issue |
| **SEV4 - Low** | 1 day | Enhancement request, cleanup |

### Common Issues & Solutions

#### App Container Won't Start

```bash
# Check logs
docker logs shia-chatbot-app

# Common causes:
# 1. Database not ready
docker exec shia-chatbot-postgres pg_isready

# 2. Missing environment variables
docker exec shia-chatbot-app env | grep -E "DATABASE|REDIS|SECRET"

# 3. Port conflict
lsof -i :8000
```

#### Celery Worker Not Processing Tasks

```bash
# Check worker health
docker exec shia-chatbot-celery-worker celery -A src.app.tasks inspect ping

# Check active workers
docker exec shia-chatbot-celery-worker celery -A src.app.tasks inspect active

# Check Flower dashboard
open http://localhost:5555

# Restart worker
docker compose restart celery-worker
```

#### High Memory Usage

```bash
# Check container resources
docker stats

# Check app metrics
curl http://localhost:8000/metrics | grep memory

# Scale workers
docker compose up -d --scale celery-worker=4

# Restart services
docker compose restart app celery-worker
```

#### Database Connection Issues

```bash
# Check PostgreSQL health
docker exec shia-chatbot-postgres pg_isready

# Check connections
docker exec shia-chatbot-postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Restart PostgreSQL
docker compose restart postgres

# Check connection pool settings in .env
# Adjust: SQLALCHEMY_POOL_SIZE, SQLALCHEMY_MAX_OVERFLOW
```

#### Prometheus Not Scraping Metrics

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check app metrics endpoint
curl http://localhost:8000/metrics

# Verify Prometheus config
docker exec shia-chatbot-prometheus cat /etc/prometheus/prometheus.yml

# Restart Prometheus
docker compose restart prometheus
```

---

## 💾 Backup & Recovery

### Backup Strategy

**Development:**
- No automated backups
- Manual backups before migrations

**Staging:**
- Daily automated backups
- 7-day retention

**Production:**
- Hourly incremental backups
- Daily full backups
- 30-day retention
- Off-site backup storage

### Automated Backup Setup

```bash
# Add to crontab
crontab -e

# Hourly backup (production)
0 * * * * cd /path/to/app && make db-dump

# Daily backup (staging)
0 2 * * * cd /path/to/app && make db-dump

# Weekly cleanup (remove backups older than 30 days)
0 3 * * 0 find /path/to/app/backups -name "*.sql" -mtime +30 -delete
```

### Recovery Procedure

```bash
# 1. Stop application
docker compose stop app celery-worker

# 2. Restore database
make db-restore FILE=backups/db_dump_20251109_120000.sql

# 3. Verify restoration
docker exec shia-chatbot-postgres psql -U postgres -d shia_chatbot -c "SELECT COUNT(*) FROM users;"

# 4. Start application
docker compose start app celery-worker

# 5. Health check
curl http://localhost:8000/health
```

### Disaster Recovery

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 1 hour

**Procedure:**

1. **Provision new infrastructure**
2. **Restore latest backup**
3. **Update DNS/load balancer**
4. **Verify all services**
5. **Monitor for issues**

---

## 🎯 Quick Reference

### Daily Operations

```bash
# Check service health
make docker-health

# View logs
docker compose logs -f app

# Restart service
docker compose restart app
```

### Deployment

```bash
# Build and deploy
make build
docker tag shia-chatbot:latest shia-chatbot:v1.0.0
docker push your-registry/shia-chatbot:v1.0.0
```

### Monitoring

```bash
# Check metrics
curl http://localhost:8000/metrics

# View Grafana
open http://localhost:3000

# View Flower
open http://localhost:5555
```

### Troubleshooting

```bash
# Check logs
docker logs shia-chatbot-app

# Check health
make docker-health

# Restart everything
docker compose restart
```

---

**Version:** 1.0.0
**Last Updated:** November 2025
