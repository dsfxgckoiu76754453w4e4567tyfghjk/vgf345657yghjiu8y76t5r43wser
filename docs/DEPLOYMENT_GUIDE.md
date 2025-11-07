# 🚀 Deployment Guide - Queue Management System

## 📋 Overview

Complete guide for deploying the **Shia Islamic Chatbot** with production-grade queue management system using Celery, Redis, and multi-replica FastAPI deployment.

---

## ✅ Phase 1 & 2 COMPLETED

### What's Been Implemented:

**Phase 1: Core Queue Infrastructure** ✅
- Celery task queue with 3-tier priority system
- 12 task types (Chat, Images, ASR, Web Search, Emails, Cleanup, etc.)
- Job status API with progress tracking
- Auto-retry with exponential backoff
- Scheduled tasks (Celery Beat)

**Phase 2: Docker Deployment** ✅
- Multi-replica FastAPI (3 instances)
- Dedicated Celery workers (4 workers)
- NGINX load balancer
- SSL/TLS support
- Flower monitoring dashboard
- Deployment automation scripts

---

## 🏗️ Architecture

```
                    Internet
                        │
                        ▼
            ┌──────────────────────┐
            │   NGINX (Port 8100)  │
            │   Load Balancer      │
            │   + SSL (Port 8443)  │
            └──────────┬───────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼───┐   ┌────▼───┐   ┌────▼───┐
    │ App-1  │   │ App-2  │   │ App-3  │
    │ FastAPI│   │ FastAPI│   │ FastAPI│
    └────┬───┘   └────┬───┘   └────┬───┘
         │             │             │
         └─────────────┼─────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
    ┌────▼────┐               ┌──────▼──────┐
    │  Redis  │               │ PostgreSQL  │
    │ (Queue) │               │ (Results)   │
    └────┬────┘               └─────────────┘
         │
         │ Pull Tasks
         ▼
    ┌─────────────────────────────────┐
    │    Celery Workers (4)           │
    │  • High Priority (2× workers)   │
    │  • Medium Priority (1× worker)  │
    │  • Low Priority (1× worker)     │
    └─────────────────────────────────┘
```

---

## 🎯 Deployment Options

### Option 1: Local Development (Recommended First)

Perfect for testing before Docker deployment.

**Requirements:**
- Python 3.11+
- Poetry
- PostgreSQL (port 5433)
- Redis (port 6379)

**Steps:**

```bash
# 1. Install dependencies
poetry install

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings

# 3. Terminal 1 - FastAPI App
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Terminal 2 - Celery Worker
poetry run celery -A app.core.celery_app worker \
    --loglevel=info \
    --queues=high_priority,medium_priority,low_priority \
    --concurrency=4

# 5. Terminal 3 - Celery Beat (Optional)
poetry run celery -A app.core.celery_app beat --loglevel=info

# 6. Terminal 4 - Flower (Optional)
poetry run celery -A app.core.celery_app flower --port=5555
```

**Access:**
- API: http://localhost:8000/docs
- Flower: http://localhost:5555

---

### Option 2: Docker Compose Deployment (Production)

Full production deployment with load balancing.

**Requirements:**
- Docker & Docker Compose
- 16GB RAM minimum
- 4 CPU cores minimum
- Existing containers: postgres, redis, qdrant

**Steps:**

```bash
# 1. Ensure existing services are running
docker ps | grep shia-chatbot-postgres  # Should show running
docker ps | grep shia-chatbot-redis     # Should show running
docker ps | grep shia-chatbot-qdrant    # Should show running

# 2. Create environment file
cp .env.example .env.prod
# Edit .env.prod with production settings

# 3. Generate SSL certificates (or use Let's Encrypt)
# For development:
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"

# For production (Let's Encrypt):
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# 4. Start the system
./scripts/start-queue-system.sh prod

# 5. Monitor startup
docker-compose -f docker-compose.queue.yml logs -f

# 6. Verify health
curl http://localhost:8100/api/v1/health/
```

**Access:**
- API (HTTP): http://localhost:8100
- API (HTTPS): https://localhost:8443
- API Docs: http://localhost:8100/docs
- Flower: http://localhost:5556 (admin/changeme)
- Job Status: http://localhost:8100/api/v1/jobs/

---

## 🔧 Configuration

### Environment Variables

**Critical Settings (.env.prod):**

```env
# Environment
ENVIRONMENT=prod

# Database (use container names in Docker)
DATABASE_HOST=shia-chatbot-postgres
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=<strong-password>
DATABASE_NAME=shia_chatbot

# Redis (use container name)
REDIS_URL=redis://shia-chatbot-redis:6379/0

# Celery (auto-configured)
CELERY_BROKER_URL=redis://shia-chatbot-redis:6379/2

# Qdrant
QDRANT_URL=http://shia-chatbot-qdrant:6333

# MinIO
MINIO_ENDPOINT=shia-chatbot-minio:9000
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<secret-key>

# Security
JWT_SECRET_KEY=<random-64-char-string>

# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-<your-key>

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<app-password>

# Flower
FLOWER_USER=admin
FLOWER_PASSWORD=<strong-password>

# Langfuse
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-<key>
LANGFUSE_SECRET_KEY=sk-lf-<key>
```

---

## 📊 Resource Allocation

Optimized for **16GB RAM / 4 CPU cores**:

| Service | CPU | RAM | Instances |
|---------|-----|-----|-----------|
| NGINX | 0.25 | 256MB | 1 |
| FastAPI App | 0.75 × 3 = 2.25 | 1GB × 3 = 3GB | 3 |
| Celery High | 1.0 × 2 = 2.0 | 1.5GB × 2 = 3GB | 2 |
| Celery Medium | 0.5 | 1GB | 1 |
| Celery Low | 0.25 | 512MB | 1 |
| Celery Beat | 0.1 | 256MB | 1 |
| Flower | 0.25 | 512MB | 1 |
| MinIO | 0.5 | 1GB | 1 |
| **Total New** | **~6.1** | **~10.5GB** | **11** |

**Existing (Reused):**
- PostgreSQL: Already running
- Redis: Already running
- Qdrant: Already running

**Note:** If you have limited resources, reduce to 2 FastAPI replicas and 1 high-priority worker initially.

---

## 🔍 Monitoring

### Flower Dashboard

Access at: http://localhost:5556

**Login:**
- Username: `admin` (from FLOWER_USER)
- Password: Set in .env

**What You Can Monitor:**
- Active workers and their status
- Task success/failure rates
- Queue lengths (high/medium/low)
- Task execution times
- Worker resource usage
- Failed task details

### Logs

```bash
# All services
docker-compose -f docker-compose.queue.yml logs -f

# Specific service
docker-compose -f docker-compose.queue.yml logs -f app-1
docker-compose -f docker-compose.queue.yml logs -f celery-worker-high-1
docker-compose -f docker-compose.queue.yml logs -f nginx

# Follow logs
docker-compose -f docker-compose.queue.yml logs -f --tail=100

# Search logs
docker-compose -f docker-compose.queue.yml logs | grep ERROR
```

### Health Checks

```bash
# FastAPI health
curl http://localhost:8100/api/v1/health/

# Celery worker status
docker exec shia-chatbot-celery-high-1 celery -A app.core.celery_app inspect active

# Check specific worker
docker exec shia-chatbot-celery-high-1 celery -A app.core.celery_app status
```

---

## 🧪 Testing

### Test 1: Submit Chat Task

```bash
# Using curl
curl -X POST "http://localhost:8100/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "conversation_id": "<uuid>",
    "message": "What is Shia Islam?"
  }'

# Response includes job_id
{
  "job_id": "abc123-def456",
  "status": "PENDING"
}
```

### Test 2: Check Job Status

```bash
# Poll for result
curl "http://localhost:8100/api/v1/jobs/abc123-def456"

# Response shows progress
{
  "job_id": "abc123-def456",
  "status": "STARTED",
  "progress": 50,
  "status_message": "Processing chat message..."
}

# When complete
{
  "job_id": "abc123-def456",
  "status": "SUCCESS",
  "progress": 100,
  "result": {
    "response": "...",
    "tokens": 1234,
    "cost": 0.002
  }
}
```

### Test 3: Load Test

```bash
# Send 100 concurrent requests
for i in {1..100}; do
  curl -X POST "http://localhost:8100/api/v1/chat/" \
    -H "Content-Type: application/json" \
    -d '{"conversation_id":"<uuid>","message":"Test"}' &
done

# Monitor in Flower
# All tasks should be distributed across workers
```

---

## 🚨 Troubleshooting

### Problem: Services won't start

**Check:**
```bash
# Docker is running
docker ps

# Existing services are running
docker ps | grep shia-chatbot-postgres
docker ps | grep shia-chatbot-redis
docker ps | grep shia-chatbot-qdrant

# Network exists
docker network ls | grep chatbot-network

# Restart existing services if needed
docker restart shia-chatbot-postgres shia-chatbot-redis shia-chatbot-qdrant
```

### Problem: Tasks stuck in PENDING

**Cause:** Celery workers not running or can't connect to Redis

**Fix:**
```bash
# Check worker logs
docker-compose -f docker-compose.queue.yml logs celery-worker-high-1

# Check Redis connection
docker exec shia-chatbot-redis redis-cli ping

# Restart workers
docker-compose -f docker-compose.queue.yml restart celery-worker-high-1
```

### Problem: High memory usage

**Cause:** Memory leaks or too many concurrent tasks

**Fix:**
```bash
# Restart workers (they auto-restart after 500 tasks)
docker-compose -f docker-compose.queue.yml restart celery-worker-high-1

# Reduce concurrency in docker-compose.queue.yml
# Change: --concurrency=8 to --concurrency=4
```

### Problem: SSL certificate errors

**Cause:** Missing or invalid SSL certificates

**Fix:**
```bash
# Generate self-signed cert for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem

# Or use HTTP only (comment out HTTPS server in nginx.conf)
```

---

## 🔄 Deployment Strategies

### Blue-Green Deployment (Recommended for STAGE→PROD)

```bash
# 1. Current production running on "green"
# 2. Deploy new version to "blue" environment
docker-compose -f docker-compose.queue.yml up -d --scale app-blue=3

# 3. Test blue environment
curl http://localhost:8101/api/v1/health/

# 4. Switch NGINX to blue
# Update nginx.conf upstream to point to blue

# 5. Reload NGINX
docker exec shia-chatbot-nginx nginx -s reload

# 6. Monitor for issues
# If problems: Switch back to green
# If good: Shut down green
```

### Rolling Deployment (For DEV→STAGE)

```bash
# 1. Update one replica at a time
docker-compose -f docker-compose.queue.yml up -d --no-deps app-1

# 2. Wait for health check
sleep 30

# 3. Update next replica
docker-compose -f docker-compose.queue.yml up -d --no-deps app-2

# 4. Repeat for all replicas
```

---

## 📈 Scaling

### Horizontal Scaling

**Add more FastAPI replicas:**
```bash
# In docker-compose.queue.yml, add app-4, app-5, etc.
# Then update nginx.conf upstream section

# Or use docker-compose scale (if supported)
docker-compose -f docker-compose.queue.yml up -d --scale app=5
```

**Add more Celery workers:**
```bash
# In docker-compose.queue.yml, add celery-worker-high-3, etc.
docker-compose -f docker-compose.queue.yml up -d celery-worker-high-3
```

### Vertical Scaling

**Increase worker concurrency:**
```yaml
# In docker-compose.queue.yml
command: >
  celery -A app.core.celery_app worker
  --concurrency=16  # Increased from 8
```

**Increase resource limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'   # Increased from 1.0
      memory: 3G     # Increased from 1.5G
```

---

## 🛑 Shutdown

```bash
# Graceful shutdown
./scripts/stop-queue-system.sh

# Shutdown with volume removal (⚠️ DATA LOSS)
./scripts/stop-queue-system.sh --remove-volumes

# Manual shutdown
docker-compose -f docker-compose.queue.yml stop
docker-compose -f docker-compose.queue.yml rm -f
```

---

## ✅ Production Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Set strong JWT_SECRET_KEY (64+ random characters)
- [ ] Configure real SSL certificates (Let's Encrypt)
- [ ] Set ENVIRONMENT=prod in .env
- [ ] Configure production SMTP settings
- [ ] Set up Langfuse for observability
- [ ] Configure CORS for production domains
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up monitoring alerts
- [ ] Test failover scenarios
- [ ] Document rollback procedures
- [ ] Set up SSL auto-renewal

---

## 📚 Additional Resources

- **Queue Management Guide**: `docs/QUEUE_MANAGEMENT.md`
- **API Documentation**: http://localhost:8100/docs
- **Flower Docs**: https://flower.readthedocs.io
- **Celery Docs**: https://docs.celeryq.dev
- **NGINX Docs**: https://nginx.org/en/docs/

---

## 🎉 You're All Set!

Your production-grade queue management system is now deployed with:
✅ Load balancing across 3 FastAPI replicas
✅ Priority-based task processing
✅ Auto-retry and error handling
✅ Real-time monitoring (Flower)
✅ SSL/TLS encryption
✅ Health checks and graceful shutdown
✅ Resource optimization
✅ Environment isolation

**Need help?** Check the troubleshooting section or view logs with:
```bash
docker-compose -f docker-compose.queue.yml logs -f
```
