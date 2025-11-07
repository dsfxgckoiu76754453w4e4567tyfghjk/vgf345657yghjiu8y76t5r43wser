# Operations Guide

> Comprehensive guide for deploying, managing, and operating the Shia Islamic Chatbot in production environments.

**Version:** 1.0.0
**Last Updated:** November 2025
**Audience:** DevOps Engineers, Platform Engineers, SREs

---

## 📋 Table of Contents

1. [Environment Architecture](#environment-architecture)
2. [Deployment Procedures](#deployment-procedures)
3. [Environment Promotion](#environment-promotion)
4. [Configuration Management](#configuration-management)
5. [Database Operations](#database-operations)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Backup & Recovery](#backup--recovery)
8. [Scaling & Performance](#scaling--performance)
9. [Security Operations](#security-operations)
10. [Incident Response](#incident-response)
11. [Runbooks](#runbooks)

---

## 🏗️ Environment Architecture

### Environment Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                         PRODUCTION                          │
│  • prod_ prefixed resources                                 │
│  • High availability, auto-scaling                          │
│  • Real users, real data                                    │
│  • Strict change control                                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ Promotion (manual, reviewed)
                              │
┌─────────────────────────────────────────────────────────────┐
│                          STAGING                            │
│  • stage_ prefixed resources                                │
│  • Production-like environment                              │
│  • Pre-production testing                                   │
│  • QA validation                                            │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ Promotion (automated)
                              │
┌─────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT                          │
│  • dev_ prefixed resources                                  │
│  • Feature development                                      │
│  • Rapid iteration                                          │
│  • Developer testing                                        │
└─────────────────────────────────────────────────────────────┘
```

### Environment Specifications

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **Environment Variable** | `ENVIRONMENT=dev` | `ENVIRONMENT=stage` | `ENVIRONMENT=prod` |
| **Database Prefix** | `dev_` | `stage_` | `prod_` |
| **Qdrant Collections** | `dev_documents` | `stage_documents` | `prod_documents` |
| **MinIO Buckets** | `dev-*` | `stage-*` | `prod-*` |
| **Debug Mode** | ✅ Enabled | ❌ Disabled | ❌ Disabled |
| **Log Level** | DEBUG | INFO | WARNING |
| **Rate Limits** | Permissive | Standard | Strict |
| **Backups** | None | Daily | Hourly + Daily |
| **Monitoring** | Basic | Full | Full + Alerts |

---

## 🚀 Deployment Procedures

### Prerequisites Checklist

Before any deployment, ensure:

```bash
# 1. All tests pass
make ci

# 2. Code quality checks pass
make verify-build

# 3. Security scans pass
make security

# 4. Database migrations are ready
poetry run alembic check

# 5. Configuration is validated
# Check .env files for each environment

# 6. Stakeholders notified
# Especially for production deployments
```

### Development Deployment

**Audience:** Developers
**Frequency:** Continuous (on every commit to develop branch)
**Approval:** None required

```bash
# 1. Ensure on develop branch
git checkout develop
git pull origin develop

# 2. Run verification
make verify-build

# 3. Start local environment
make docker-up
make dev

# 4. Verify health
curl http://localhost:8000/health

# 5. Test via Swagger
open http://localhost:8000/docs
```

**CI/CD:** Auto-deploys on push to `develop` branch (if configured)

### Staging Deployment

**Audience:** QA Team, Product Managers
**Frequency:** Daily or on-demand
**Approval:** Tech Lead approval required

```bash
# ============================================================================
# STAGING DEPLOYMENT PROCEDURE
# ============================================================================

# 1. Create release branch
git checkout -b release/v1.0.0

# 2. Update version in pyproject.toml
poetry version 1.0.0

# 3. Run full verification
make ci
make verify-build

# 4. Build Docker image
make build

# 5. Tag image for staging
docker tag shia-chatbot:latest shia-chatbot:v1.0.0-staging

# 6. Push to container registry
docker push shia-chatbot:v1.0.0-staging

# 7. Deploy to staging server
ssh staging-server << 'EOF'
  cd /app/shia-chatbot

  # Pull latest image
  docker pull shia-chatbot:v1.0.0-staging

  # Stop current container
  docker-compose down

  # Backup database
  docker exec postgres pg_dump -U postgres shia_chatbot > backup_$(date +%Y%m%d_%H%M%S).sql

  # Update docker-compose.yml to use new image
  sed -i 's/image: .*/image: shia-chatbot:v1.0.0-staging/' docker-compose.yml

  # Run database migrations
  docker-compose run --rm app alembic upgrade head

  # Start services
  docker-compose up -d

  # Health check
  sleep 10
  curl http://localhost:8000/health
EOF

# 8. Verify deployment
curl https://staging.yourapp.com/health

# 9. Run smoke tests
./scripts/test-locally.sh

# 10. Notify QA team
# Send notification via Slack/Email
```

**Rollback Procedure:**

```bash
ssh staging-server << 'EOF'
  cd /app/shia-chatbot

  # Revert to previous image
  docker-compose down
  docker-compose pull shia-chatbot:v1.0.0-previous
  sed -i 's/image: .*/image: shia-chatbot:v1.0.0-previous/' docker-compose.yml
  docker-compose up -d
EOF
```

### Production Deployment

**Audience:** End Users
**Frequency:** Weekly or on critical fixes
**Approval:** Product Manager + Tech Lead + DevOps approval required

**Deployment Window:** Off-peak hours (e.g., 2 AM - 4 AM UTC)

```bash
# ============================================================================
# PRODUCTION DEPLOYMENT PROCEDURE (Blue-Green Strategy)
# ============================================================================

# Prerequisites:
# 1. Code merged to main branch
# 2. Staging deployment verified (minimum 24 hours)
# 3. All stakeholders approved
# 4. Maintenance window scheduled
# 5. Rollback plan prepared

# ============================================================================
# PHASE 1: PRE-DEPLOYMENT
# ============================================================================

# 1. Create production tag
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# 2. Build production image
make build
docker tag shia-chatbot:latest shia-chatbot:v1.0.0

# 3. Push to container registry
docker push shia-chatbot:v1.0.0

# 4. Verify image
docker pull shia-chatbot:v1.0.0
docker run --rm shia-chatbot:v1.0.0 python --version

# ============================================================================
# PHASE 2: BACKUP
# ============================================================================

# 5. Backup production database
ssh prod-server << 'EOF'
  # Full database backup
  docker exec prod-postgres pg_dump -U postgres shia_chatbot > \
    /backups/prod_backup_$(date +%Y%m%d_%H%M%S).sql

  # Backup Qdrant data
  docker run --rm -v prod_qdrant_data:/data -v /backups:/backup ubuntu \
    tar czf /backup/qdrant_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

  # Backup MinIO data (if applicable)
  # mc mirror prod-minio /backups/minio_$(date +%Y%m%d_%H%M%S)/
EOF

# 6. Verify backups
ssh prod-server "ls -lh /backups/ | tail -5"

# ============================================================================
# PHASE 3: DEPLOYMENT (Blue-Green)
# ============================================================================

# 7. Deploy to green environment (while blue is live)
ssh prod-server << 'EOF'
  cd /app/shia-chatbot

  # Pull new image
  docker pull shia-chatbot:v1.0.0

  # Update green environment config
  cp docker-compose.yml docker-compose.green.yml
  sed -i 's/container_name: app/container_name: app-green/' docker-compose.green.yml
  sed -i 's/8000:8000/8001:8000/' docker-compose.green.yml
  sed -i 's/image: .*/image: shia-chatbot:v1.0.0/' docker-compose.green.yml

  # Start green environment
  docker-compose -f docker-compose.green.yml up -d

  # Wait for startup
  sleep 30

  # Run migrations on green
  docker exec app-green alembic upgrade head
EOF

# 8. Health check green environment
ssh prod-server "curl http://localhost:8001/health"

# 9. Run smoke tests on green
ssh prod-server << 'EOF'
  # Test critical endpoints
  curl -f http://localhost:8001/health || exit 1
  curl -f http://localhost:8001/docs || exit 1

  # Test authentication
  # ... additional smoke tests ...
EOF

# ============================================================================
# PHASE 4: TRAFFIC SWITCH
# ============================================================================

# 10. Switch load balancer to green (assuming Nginx)
ssh prod-server << 'EOF'
  # Update Nginx upstream
  sed -i 's/server app:8000/server app-green:8000/' /etc/nginx/conf.d/upstream.conf

  # Test Nginx config
  nginx -t

  # Reload Nginx (zero downtime)
  nginx -s reload
EOF

# 11. Monitor green environment
# Check logs, metrics, error rates for 15 minutes

# 12. Verify production is working
curl https://yourapp.com/health

# ============================================================================
# PHASE 5: CLEANUP
# ============================================================================

# 13. Stop blue environment (old version)
ssh prod-server "docker-compose -f docker-compose.blue.yml down"

# 14. Keep blue environment for 24 hours (for quick rollback)
# Then remove after confirming stability

# ============================================================================
# PHASE 6: POST-DEPLOYMENT
# ============================================================================

# 15. Update monitoring dashboards
# Verify all metrics are reporting correctly

# 16. Notify stakeholders
echo "Production deployment v1.0.0 completed successfully" | mail -s "Deployment Success" team@example.com

# 17. Document deployment
# Update deployment log, release notes
```

**Quick Rollback (within 24 hours):**

```bash
ssh prod-server << 'EOF'
  # Switch Nginx back to blue
  sed -i 's/server app-green:8000/server app:8000/' /etc/nginx/conf.d/upstream.conf
  nginx -t && nginx -s reload

  # Restart blue if stopped
  docker-compose -f docker-compose.blue.yml up -d
EOF
```

**Database Rollback (if migrations were run):**

```bash
ssh prod-server << 'EOF'
  # Rollback migrations
  docker exec app alembic downgrade -1

  # Or restore from backup
  docker exec -i prod-postgres psql -U postgres shia_chatbot < \
    /backups/prod_backup_YYYYMMDD_HHMMSS.sql
EOF
```

---

## 🔄 Environment Promotion

### Data Promotion Workflow

**Use Case:** Promote validated content/configuration from staging to production

```bash
# ============================================================================
# DOCUMENT PROMOTION (Staging → Production)
# ============================================================================

# 1. Export approved documents from staging
ssh staging-server << 'EOF'
  docker exec stage-postgres psql -U postgres shia_chatbot << SQL
    COPY (
      SELECT * FROM documents
      WHERE moderation_status = 'approved'
      AND created_at > '2025-11-01'
    ) TO '/tmp/approved_documents.csv' CSV HEADER;
SQL

  # Export document chunks
  docker exec stage-postgres psql -U postgres shia_chatbot << SQL
    COPY (
      SELECT dc.* FROM document_chunks dc
      INNER JOIN documents d ON dc.document_id = d.id
      WHERE d.moderation_status = 'approved'
      AND d.created_at > '2025-11-01'
    ) TO '/tmp/approved_chunks.csv' CSV HEADER;
SQL

  # Download files
  scp stage-server:/tmp/approved_*.csv ./staging_data/
EOF

# 2. Promote Qdrant vectors
ssh staging-server << 'EOF'
  # Export Qdrant collection snapshot
  curl -X POST "http://localhost:6333/collections/stage_documents/snapshots" \
    -H "Content-Type: application/json"

  # Download snapshot
  SNAPSHOT=$(curl -s http://localhost:6333/collections/stage_documents/snapshots | jq -r '.[0].name')
  curl "http://localhost:6333/collections/stage_documents/snapshots/$SNAPSHOT" \
    -o /tmp/qdrant_snapshot.snapshot
EOF

# 3. Import to production (during maintenance window)
ssh prod-server << 'EOF'
  # Import documents
  docker exec -i prod-postgres psql -U postgres shia_chatbot << SQL
    \copy documents FROM '/tmp/approved_documents.csv' CSV HEADER;
    \copy document_chunks FROM '/tmp/approved_chunks.csv' CSV HEADER;
SQL

  # Import Qdrant snapshot
  curl -X POST "http://localhost:6333/collections/prod_documents/snapshots/upload" \
    -F "snapshot=@/tmp/qdrant_snapshot.snapshot"

  # Restore snapshot
  curl -X PUT "http://localhost:6333/collections/prod_documents/snapshots/$SNAPSHOT/recover"
EOF

# 4. Verify promotion
ssh prod-server << 'EOF'
  # Check document count
  docker exec prod-postgres psql -U postgres shia_chatbot -c \
    "SELECT COUNT(*) FROM documents WHERE created_at > '2025-11-01';"

  # Check Qdrant vectors
  curl "http://localhost:6333/collections/prod_documents"
EOF
```

### Configuration Promotion

```bash
# ============================================================================
# CONFIGURATION PROMOTION
# ============================================================================

# 1. Export staging configuration (sanitized)
ssh staging-server << 'EOF'
  # Export database configuration (without secrets)
  docker exec stage-postgres pg_dump -U postgres --schema-only shia_chatbot > \
    /tmp/schema_export.sql

  # Export application settings (sanitized)
  grep -v "SECRET\|PASSWORD\|KEY" .env > /tmp/staging_config.env
EOF

# 2. Review and adapt for production
scp staging-server:/tmp/staging_config.env ./
# Manually review and update for production

# 3. Apply to production
scp ./production_config.env prod-server:/app/.env
ssh prod-server "docker-compose restart app"
```

---

## ⚙️ Configuration Management

### Environment Variables

**Critical Variables (Required):**

```bash
# Application
ENVIRONMENT=prod  # dev, stage, prod
DEBUG=false       # MUST be false in production
SECRET_KEY=<64-char-random-string>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# Qdrant
QDRANT_URL=http://host:6333
QDRANT_API_KEY=<secure-key>

# LLM Providers
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
GOOGLE_API_KEY=<key>
COHERE_API_KEY=<key>

# OpenRouter
OPENROUTER_API_KEY=<key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Langfuse
LANGFUSE_PUBLIC_KEY=<key>
LANGFUSE_SECRET_KEY=<key>
LANGFUSE_HOST=https://langfuse.example.com

# MinIO (optional)
MINIO_ENDPOINT=minio.example.com:9000
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<key>
MINIO_USE_SSL=true

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<app-password>
SMTP_FROM_EMAIL=noreply@example.com

# Security
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=WARNING  # DEBUG, INFO, WARNING, ERROR, CRITICAL
STRUCTLOG_DEV_MODE=false
```

**Generating Secure Keys:**

```bash
# SECRET_KEY (for JWT tokens)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Database password
openssl rand -base64 32

# API keys
# Use provider's dashboard to generate
```

### Configuration Files

**docker-compose.yml (Production):**

```yaml
version: '3.8'

services:
  app:
    image: shia-chatbot:${VERSION:-latest}
    container_name: shia-chatbot-app
    restart: unless-stopped
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - qdrant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    container_name: shia-chatbot-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7.2-alpine
    container_name: shia-chatbot-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "AUTH", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: shia-chatbot-qdrant
    restart: unless-stopped
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    healthcheck:
      test: ["CMD-SHELL", "timeout 1 bash -c '</dev/tcp/127.0.0.1/6333'"]
      interval: 10s
      timeout: 5s
      retries: 5

  celery-worker:
    image: shia-chatbot:${VERSION:-latest}
    container_name: shia-chatbot-celery
    restart: unless-stopped
    env_file: .env
    command: celery -A src.app.tasks worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - postgres

  flower:
    image: shia-chatbot:${VERSION:-latest}
    container_name: shia-chatbot-flower
    restart: unless-stopped
    env_file: .env
    command: celery -A src.app.tasks flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

---

## 🗄️ Database Operations

### Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Add new feature"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Check current version
poetry run alembic current

# View migration history
poetry run alembic history

# Rollback to specific version
poetry run alembic downgrade <revision>
```

### Database Backup

**Daily Automated Backup:**

```bash
#!/bin/bash
# /opt/scripts/backup-database.sh

BACKUP_DIR=/backups/postgres
RETENTION_DAYS=30

# Create backup
docker exec shia-chatbot-postgres pg_dump -U postgres shia_chatbot | \
  gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Cleanup old backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz \
  s3://your-bucket/postgres-backups/
```

**Cron Job:**

```bash
# /etc/cron.d/backup-database
0 2 * * * root /opt/scripts/backup-database.sh >> /var/log/backup.log 2>&1
```

### Database Restore

```bash
# Restore from backup
gunzip < /backups/postgres/backup_20251107_020000.sql.gz | \
  docker exec -i shia-chatbot-postgres psql -U postgres shia_chatbot

# Or from S3
aws s3 cp s3://your-bucket/postgres-backups/backup_20251107_020000.sql.gz - | \
  gunzip | docker exec -i shia-chatbot-postgres psql -U postgres shia_chatbot
```

---

## 📊 Monitoring & Alerts

### Health Check Endpoints

```bash
# Application health
curl https://yourapp.com/health

# With service checks
curl https://yourapp.com/health?check_services=true

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-07T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  }
}
```

### Monitoring Stack

**Prometheus Metrics:**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'shia-chatbot'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

**Alert Rules:**

```yaml
# alerts.yml
groups:
  - name: shia-chatbot
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{container="shia-chatbot-app"} > 2e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
```

---

## 🔐 Security Operations

### SSL/TLS Certificate Management

**Using Let's Encrypt:**

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d yourapp.com -d www.yourapp.com

# Auto-renewal (cron)
0 3 * * * certbot renew --quiet
```

### Secret Rotation

```bash
# Rotate JWT secret
NEW_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# Update in production
ssh prod-server << EOF
  sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" /app/.env
  docker-compose restart app
EOF

# Update all active tokens (force re-login)
# This happens automatically as old tokens expire
```

### Security Scanning

```bash
# Run security scans before deployment
make security

# Scan Docker image
docker scan shia-chatbot:v1.0.0

# Check for vulnerabilities
poetry run safety check
```

---

## 🚨 Incident Response

### Incident Response Plan

**Severity Levels:**

| Level | Response Time | Impact | Example |
|-------|---------------|--------|---------|
| **P0 - Critical** | < 15 min | Complete outage | Database down, app crashed |
| **P1 - High** | < 1 hour | Major degradation | High error rate, slow responses |
| **P2 - Medium** | < 4 hours | Partial degradation | Minor feature broken |
| **P3 - Low** | < 24 hours | Minor impact | Non-critical bug |

**Incident Response Steps:**

1. **Detection & Alert**
   - Automated monitoring alerts
   - User reports
   - Health check failures

2. **Triage & Assessment**
   - Check severity level
   - Identify affected services
   - Estimate impact

3. **Communication**
   - Notify stakeholders
   - Update status page
   - Start incident channel

4. **Mitigation**
   - Execute runbooks
   - Apply hotfixes
   - Rollback if necessary

5. **Resolution**
   - Verify fix
   - Monitor for recurrence
   - Update documentation

6. **Post-Mortem**
   - Root cause analysis
   - Action items
   - Process improvements

---

## 📖 Runbooks

### Runbook: Application Not Starting

**Symptoms:** App container exits immediately or crashes on startup

**Diagnosis:**

```bash
# Check container logs
docker logs shia-chatbot-app --tail 100

# Check container status
docker ps -a | grep shia-chatbot-app

# Check resource usage
docker stats shia-chatbot-app
```

**Common Causes & Solutions:**

1. **Database connection failed**
   ```bash
   # Check database is running
   docker ps | grep postgres

   # Test connection
   docker exec shia-chatbot-postgres pg_isready

   # Check DATABASE_URL in .env
   grep DATABASE_URL .env
   ```

2. **Missing environment variables**
   ```bash
   # Verify .env file
   docker exec shia-chatbot-app env | grep -E "SECRET|DATABASE|REDIS"
   ```

3. **Port already in use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000

   # Kill process or change port
   ```

### Runbook: High Memory Usage

**Symptoms:** OOM kills, slow performance, swap usage

**Diagnosis:**

```bash
# Check memory usage
docker stats shia-chatbot-app

# Check container limits
docker inspect shia-chatbot-app | grep -i memory

# Application metrics
curl http://localhost:8000/metrics | grep memory
```

**Solutions:**

```bash
# Restart application (temporary fix)
docker restart shia-chatbot-app

# Increase memory limit (permanent)
# In docker-compose.yml:
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

# Apply changes
docker-compose up -d
```

### Runbook: Database Connection Pool Exhausted

**Symptoms:** "Connection pool exhausted" errors in logs

**Diagnosis:**

```bash
# Check active connections
docker exec shia-chatbot-postgres psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='shia_chatbot';"

# Check max connections
docker exec shia-chatbot-postgres psql -U postgres -c \
  "SHOW max_connections;"
```

**Solutions:**

```bash
# Increase pool size in application
# In .env:
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Increase PostgreSQL max_connections
# In postgresql.conf:
max_connections = 200

# Restart services
docker-compose restart postgres app
```

---

## 📈 Scaling & Performance

### Horizontal Scaling

**Load Balancer (Nginx):**

```nginx
upstream shia_chatbot_backend {
    least_conn;
    server app1:8000 max_fails=3 fail_timeout=30s;
    server app2:8000 max_fails=3 fail_timeout=30s;
    server app3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name yourapp.com;

    location / {
        proxy_pass http://shia_chatbot_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Connection pooling
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Performance Tuning

**PostgreSQL:**

```bash
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

**Redis:**

```bash
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

**Uvicorn Workers:**

```bash
# Increase worker count based on CPU cores
# Formula: (2 * CPU cores) + 1
uvicorn src.app.main:app --workers 9 --host 0.0.0.0 --port 8000
```

---

## 📞 Support Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| **On-Call Engineer** | oncall@example.com | Immediate incidents (P0, P1) |
| **DevOps Lead** | devops-lead@example.com | Deployment approvals |
| **Tech Lead** | tech-lead@example.com | Architecture decisions |
| **Product Manager** | pm@example.com | Feature releases |

---

## 📝 Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-07 | 1.0.0 | Initial release | DevOps Team |

---

**Document Version:** 1.0.0
**Last Review:** 2025-11-07
**Next Review:** 2025-12-07
