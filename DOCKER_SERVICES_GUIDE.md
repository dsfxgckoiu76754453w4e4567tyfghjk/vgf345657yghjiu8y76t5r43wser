# Docker Services Guide

**Complete guide to all Docker services in the Shia Islamic Chatbot**

**Version:** 1.0.0
**Last Updated:** November 2025

---

## 📋 Overview

The project provides **TWO docker-compose configurations:**

| File | Purpose | Services | When to Use |
|------|---------|----------|-------------|
| **docker-compose.dev.yml** | Development | 3 core services | Local development (default) |
| **docker-compose.yml** | Production | 10 full services | Production deployment |

---

## 🚀 Quick Start

### For Development (Recommended)

```bash
# Start only core infrastructure (PostgreSQL, Redis, Qdrant)
docker compose -f docker-compose.dev.yml up -d

# Or use the Makefile
make docker-up

# Run app natively (NOT in Docker)
make dev
```

**Why?** Faster iteration, hot reload, easy debugging.

### For Full Stack (Testing All Services)

```bash
# Start ALL services including monitoring
docker compose up -d

# Access services:
# - App: http://localhost:8000
# - Flower: http://localhost:5555
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Nginx: http://localhost (port 80/443)
```

---

## 📊 All Services Breakdown

### Core Infrastructure (Always Required)

#### 1. PostgreSQL (`postgres`)
**Purpose:** Primary database for user data, documents, metadata

**Port:** 5433 (external) → 5432 (internal)
**Container:** `shia-chatbot-postgres`
**Image:** `postgres:15-alpine`

**Health Check:**
```bash
docker exec shia-chatbot-postgres pg_isready -U postgres
```

**Access:**
```bash
# Via Docker
make db-shell

# Via psql
psql -h localhost -p 5433 -U postgres -d shia_chatbot
```

**Configuration:**
- Database: `shia_chatbot`
- User: `postgres`
- Password: `postgres` (change in production!)
- Volume: `postgres_data`

---

#### 2. Redis (`redis`)
**Purpose:** Cache, session storage, Celery message broker

**Port:** 6379
**Container:** `shia-chatbot-redis`
**Image:** `redis:7.2-alpine`

**Health Check:**
```bash
docker exec shia-chatbot-redis redis-cli ping
```

**Access:**
```bash
# Via Docker
make redis-cli

# Via redis-cli
redis-cli -h localhost -p 6379
```

**Configuration:**
- Persistence: AOF (appendonly yes)
- Volume: `redis_data`

---

#### 3. Qdrant (`qdrant`)
**Purpose:** Vector database for semantic search (RAG)

**Ports:**
- 6333 (HTTP API)
- 6334 (gRPC)

**Container:** `shia-chatbot-qdrant`
**Image:** `qdrant/qdrant:latest`

**Health Check:**
```bash
curl http://localhost:6333/healthz
```

**Access:**
- **Dashboard:** http://localhost:6333/dashboard
- **API:** http://localhost:6333

**Configuration:**
- Volume: `qdrant_data`
- Collections: Automatically created by app

---

### Application Services (Production)

#### 4. FastAPI App (`app`)
**Purpose:** Main application server

**Port:** 8000
**Container:** `shia-chatbot-app`
**Build:** From Dockerfile

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Access:**
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

**Configuration:**
- Workers: 4 (production)
- CPU Limit: 2 cores
- Memory Limit: 2GB
- Depends on: postgres, redis, qdrant

**Environment Variables Required:**
```env
ENVIRONMENT=dev
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/shia_chatbot
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://qdrant:6333
SECRET_KEY=<your-secret-key>
# ... more in .env.example
```

---

#### 5. Celery Worker (`celery-worker`)
**Purpose:** Background task processing

**Container:** `shia-chatbot-celery-worker`
**Build:** From Dockerfile

**Health Check:**
```bash
docker exec shia-chatbot-celery-worker celery -A src.app.tasks inspect ping
```

**Configuration:**
- Concurrency: 4 workers
- CPU Limit: 2 cores
- Memory Limit: 2GB
- Depends on: postgres, redis, app

**Tasks Handled:**
- Document embedding generation
- Email sending
- Image generation
- Data cleanup
- Environment promotion

---

#### 6. Celery Beat (`celery-beat`)
**Purpose:** Periodic task scheduler

**Container:** `shia-chatbot-celery-beat`
**Build:** From Dockerfile

**Configuration:**
- Depends on: redis, celery-worker
- Volume: `celery_beat_schedule` (schedule persistence)

**Scheduled Tasks:**
- Daily data cleanup
- Periodic health checks
- Metrics collection

---

#### 7. Flower (`flower`)
**Purpose:** Celery monitoring dashboard

**Port:** 5555
**Container:** `shia-chatbot-flower`
**Build:** From Dockerfile

**Health Check:**
```bash
curl http://localhost:5555/healthcheck
```

**Access:**
- **Dashboard:** http://localhost:5555

**Features:**
- Real-time task monitoring
- Worker status
- Task history
- Performance metrics

---

### Monitoring Stack (Production)

#### 8. Prometheus (`prometheus`)
**Purpose:** Metrics collection and storage

**Port:** 9090
**Container:** `shia-chatbot-prometheus`
**Image:** `prom/prometheus:latest`

**Health Check:**
```bash
curl http://localhost:9090/-/healthy
```

**Access:**
- **UI:** http://localhost:9090
- **Metrics:** http://localhost:9090/metrics

**Configuration:**
- Config: `grafana/prometheus-scrape-config.yml`
- Retention: 30 days
- Volume: `prometheus_data`

**Scrape Targets:**
- FastAPI app: http://app:8000/metrics
- Add more in prometheus-scrape-config.yml

---

#### 9. Grafana (`grafana`)
**Purpose:** Metrics visualization and dashboards

**Port:** 3000
**Container:** `shia-chatbot-grafana`
**Image:** `grafana/grafana:latest`

**Health Check:**
```bash
curl http://localhost:3000/api/health
```

**Access:**
- **Dashboard:** http://localhost:3000
- **Default Login:** admin / admin (change in production!)

**Configuration:**
- Dashboards: `grafana/dashboards/`
- Data Source: Prometheus
- Volume: `grafana_data`

**Environment Variables:**
```env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin  # Change this!
```

---

#### 10. Nginx (`nginx`)
**Purpose:** Reverse proxy and load balancer

**Ports:** 80 (HTTP), 443 (HTTPS)
**Container:** `shia-chatbot-nginx`
**Image:** `nginx:alpine`

**Health Check:**
```bash
curl http://localhost/health
```

**Access:**
- **HTTP:** http://localhost
- **HTTPS:** https://localhost

**Configuration:**
- Config: `nginx/nginx.conf`
- SSL Certs: `nginx/ssl/`
- Logs: `nginx_logs` volume

**Features:**
- SSL/TLS termination
- Load balancing (multiple app instances)
- Gzip compression
- Static file serving
- Security headers

---

### Optional Services (Commented Out)

#### MinIO (`minio`)
**Purpose:** S3-compatible object storage (optional)

**Ports:** 9000 (API), 9001 (Console)
**Image:** `minio/minio:latest`

**To Enable:**
Uncomment in docker-compose.yml

**Use Case:**
- File uploads
- Generated images
- Document attachments

---

#### Langfuse (`langfuse`)
**Purpose:** LLM observability (optional, use cloud version)

**Port:** 3001
**Image:** `langfuse/langfuse:latest`

**Recommendation:** Use Langfuse Cloud instead (https://cloud.langfuse.com)

---

## 🎯 Service Dependencies

```
                      ┌─────────────┐
                      │   Nginx     │ (Port 80/443)
                      └─────────────┘
                            │
                            ▼
                      ┌─────────────┐
                      │  FastAPI    │ (Port 8000)
                      │    App      │ ✅ Health Check
                      └─────────────┘
                   ┌──────┴──────┬──────┐
                   ▼             ▼      ▼
            ┌──────────┐  ┌──────────┐ ┌──────────┐
            │PostgreSQL│  │  Redis   │ │  Qdrant  │
            │  :5433   │  │  :6379   │ │  :6333   │
            └──────────┘  └──────────┘ └──────────┘
                   ▲             ▲
                   └──────┬──────┘
                          │
                   ┌──────────────┐
                   │    Celery    │ ✅ Health Check
                   │   Worker     │
                   └──────────────┘
                          │
                   ┌──────────────┐
                   │  Celery Beat │
                   └──────────────┘
                          │
                   ┌──────────────┐
                   │    Flower    │ (Port 5555)
                   └──────────────┘ ✅ Health Check

    ┌──────────────┐        ┌──────────────┐
    │  Prometheus  │───────▶│   Grafana    │
    │    :9090     │        │    :3000     │
    └──────────────┘        └──────────────┘
         ▲                  ✅ Health Check
         │
    Scrapes /metrics
         │
    ┌────────────┐
    │ FastAPI App│
    └────────────┘
```

---

## 🚦 Health Checks Summary

| Service | Health Check Command | Endpoint/Command |
|---------|---------------------|------------------|
| **PostgreSQL** | ✅ | `pg_isready -U postgres` |
| **Redis** | ✅ | `redis-cli ping` |
| **Qdrant** | ✅ | `http://localhost:6333/healthz` |
| **FastAPI App** | ✅ | `http://localhost:8000/health` |
| **Celery Worker** | ✅ | `celery inspect ping` |
| **Flower** | ✅ | `http://localhost:5555/healthcheck` |
| **Prometheus** | ✅ | `http://localhost:9090/-/healthy` |
| **Grafana** | ✅ | `http://localhost:3000/api/health` |
| **Nginx** | ✅ | `http://localhost/health` |

---

## 🎯 Port Summary

| Service | Internal Port | External Port | Protocol |
|---------|--------------|---------------|----------|
| PostgreSQL | 5432 | 5433 | TCP |
| Redis | 6379 | 6379 | TCP |
| Qdrant HTTP | 6333 | 6333 | HTTP |
| Qdrant gRPC | 6334 | 6334 | gRPC |
| FastAPI | 8000 | 8000 | HTTP |
| Flower | 5555 | 5555 | HTTP |
| Prometheus | 9090 | 9090 | HTTP |
| Grafana | 3000 | 3000 | HTTP |
| Nginx HTTP | 80 | 80 | HTTP |
| Nginx HTTPS | 443 | 443 | HTTPS |

---

## 🎓 Usage Scenarios

### Scenario 1: Local Development (Recommended)

```bash
# 1. Start infrastructure only
docker compose -f docker-compose.dev.yml up -d

# 2. Run app natively (hot reload, debugging)
make dev

# 3. Optional: Start Celery worker
make celery-worker

# 4. Optional: Start Flower
make flower
```

**Services Running:**
- PostgreSQL, Redis, Qdrant: In Docker
- FastAPI, Celery, Flower: Native Python (easy debugging)

---

### Scenario 2: Full Stack Testing

```bash
# Start everything
docker compose up -d

# Check all services
make docker-health

# Access:
# - App: http://localhost:8000/docs
# - Flower: http://localhost:5555
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Nginx: http://localhost
```

**Services Running:**
- All 10 services in Docker
- Full monitoring stack
- Production-like environment

---

### Scenario 3: Production Deployment

```bash
# 1. Build production image
make build

# 2. Update environment variables
cp .env.example .env.production
# Edit .env.production with production values

# 3. Start with production config
docker compose --env-file .env.production up -d

# 4. Run migrations
docker compose exec app alembic upgrade head

# 5. Verify health
make docker-health
```

---

## 🔧 Troubleshooting

### App Container Fails to Start

```bash
# Check logs
docker logs shia-chatbot-app

# Common issues:
# 1. Database not ready
docker exec shia-chatbot-postgres pg_isready

# 2. Missing environment variables
docker exec shia-chatbot-app env | grep -E "DATABASE|REDIS|SECRET"

# 3. Port conflict
lsof -i :8000
```

---

### Celery Worker Not Processing Tasks

```bash
# Check worker health
docker exec shia-chatbot-celery-worker celery -A src.app.tasks inspect ping

# Check active workers
docker exec shia-chatbot-celery-worker celery -A src.app.tasks inspect active

# Check Flower dashboard
open http://localhost:5555
```

---

### Prometheus Not Scraping Metrics

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check app metrics endpoint
curl http://localhost:8000/metrics

# Verify config
docker exec shia-chatbot-prometheus cat /etc/prometheus/prometheus.yml
```

---

## 📝 Configuration Files

| Service | Config File | Purpose |
|---------|------------|---------|
| **Prometheus** | `grafana/prometheus-scrape-config.yml` | Scrape targets |
| **Grafana** | `grafana/dashboards/` | Dashboard definitions |
| **Nginx** | `nginx/nginx.conf` | Reverse proxy config |
| **Nginx SSL** | `nginx/ssl/` | SSL certificates |
| **App** | `.env` | Environment variables |
| **Docker** | `docker-compose.yml` | Full stack |
| **Docker Dev** | `docker-compose.dev.yml` | Development stack |

---

## 🎯 Resource Limits

**Production Configuration:**

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|-----------|--------------|-------------|----------------|
| **FastAPI App** | 2 cores | 2GB | 1 core | 1GB |
| **Celery Worker** | 2 cores | 2GB | 1 core | 512MB |
| Others | Not limited | Not limited | - | - |

**Adjust in docker-compose.yml:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

---

## 📊 Monitoring & Metrics

### Application Metrics (Prometheus)

Access: http://localhost:8000/metrics

**Available Metrics:**
- HTTP request count
- Request duration
- Response status codes
- Active requests
- Database query count
- Celery task metrics
- Custom business metrics

### Grafana Dashboards

Access: http://localhost:3000

**Pre-configured Dashboards:**
- Application Overview
- Request Metrics
- Database Performance
- Celery Task Monitoring
- System Resources

---

## 🚀 Quick Commands

```bash
# Start development stack
docker compose -f docker-compose.dev.yml up -d

# Start full stack
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f [service-name]

# Restart single service
docker compose restart [service-name]

# Check health
make docker-health

# View all containers
docker compose ps
```

---

## ✅ Service Status Check

```bash
# Check all services
make docker-health

# Or manually:
docker compose ps

# Expected: All services "Up" and "healthy"
```

---

**Version:** 1.0.0
**Last Updated:** November 2025
**Status:** ✅ All Services Configured
