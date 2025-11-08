# Local Development & Testing Guide

## 🎯 Overview

This guide provides best practices for running, testing, and verifying the application **locally on your machine** before building Docker images or deploying. This workflow ensures you can:

- ✅ Run the application with hot reload
- ✅ Test all API endpoints via Swagger UI
- ✅ Run comprehensive tests
- ✅ Verify background tasks (Celery)
- ✅ Check database migrations
- ✅ Validate code quality
- ✅ Debug and iterate quickly

---

## 🏗️ Architecture: Hybrid Approach

**Best Practice:** Use Docker for infrastructure, run application natively.

```
┌─────────────────────────────────────────────────┐
│ LOCAL MACHINE                                   │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Native Python Environment (Poetry)       │  │
│  │                                          │  │
│  │  • FastAPI App (port 8000)              │  │
│  │  • Celery Worker                        │  │
│  │  • Hot Reload Enabled                   │  │
│  │  • Direct debugging                     │  │
│  └──────────────────────────────────────────┘  │
│                    ↓ connects to                │
│  ┌──────────────────────────────────────────┐  │
│  │ Docker Containers (Infrastructure)       │  │
│  │                                          │  │
│  │  • PostgreSQL (port 5433)               │  │
│  │  • Redis (port 6379)                    │  │
│  │  • Qdrant (port 6333)                   │  │
│  │  • Flower (port 5555)                   │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Why this approach?**
- ✅ Fast iteration with hot reload
- ✅ Easy debugging (attach debugger directly)
- ✅ No image rebuild for code changes
- ✅ Full IDE integration
- ✅ Consistent infrastructure (Docker services)

---

## 🚀 Complete Setup Workflow

### Step 1: Initial Setup (One-time)

```bash
# 1. Clone repository
git clone <repository-url>
cd shia-islamic-chatbot

# 2. Complete setup (installs deps, hooks, starts Docker, runs migrations)
make setup

# This runs:
# - poetry install --with dev
# - pre-commit install
# - docker compose up -d
# - alembic upgrade head
```

**What happens:**
- ✅ Poetry installs all dependencies
- ✅ Pre-commit hooks installed
- ✅ Docker containers started (PostgreSQL, Redis, Qdrant)
- ✅ Database migrations applied

---

### Step 2: Configure Environment

```bash
# Create .env file (if not exists)
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Essential variables for local development:**

```env
# Environment
ENVIRONMENT=dev
DEBUG=true

# Database (Docker PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/shia_chatbot

# Redis (Docker)
REDIS_URL=redis://localhost:6379/0

# Qdrant (Docker)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# API Keys (get from providers)
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
COHERE_API_KEY=your_key_here

# Langfuse (optional for local dev)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3001

# MinIO (if using)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Email (optional for local dev)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your-super-secret-key-for-development-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### Step 3: Verify Docker Services

```bash
# Check if all services are running
make docker-health

# Expected output:
# 🏥 Checking service health...
# Testing PostgreSQL connection:
# /var/run/postgresql:5432 - accepting connections
#
# Testing Redis connection:
# PONG
#
# Testing Qdrant connection:
# {"status":"ok"}
```

**If services are not running:**
```bash
# Start services
make docker-up

# View logs if there are issues
make docker-logs

# Restart services if needed
make docker-restart
```

---

## 🔬 Testing & Verification Workflow

### Complete Pre-Build Checklist

Before building the Docker image, follow this workflow:

```bash
# ============================================================================
# PHASE 1: CODE QUALITY & FORMATTING
# ============================================================================

# 1. Format code (auto-fix)
make format

# 2. Check formatting (verify)
make format-check

# 3. Run linters (flake8, mypy, pylint)
make lint

# 4. Check security (bandit, safety, detect-secrets)
make security

# 5. Check code complexity
make complexity

# 6. Check docstring coverage
make docstrings

# Quick alternative: Run all quality checks at once
make quality

# ============================================================================
# PHASE 2: TESTING
# ============================================================================

# 1. Run unit tests (fast)
make test-unit

# 2. Run integration tests (with Docker services)
make test-integration

# 3. Run all tests with coverage
make test

# 4. Check coverage report
make coverage

# Quick alternative: Before commit check
make quick-check

# ============================================================================
# PHASE 3: DATABASE MIGRATIONS
# ============================================================================

# 1. Check current migration status
poetry run alembic current

# 2. Create migration if needed
make db-migrate MESSAGE="your migration description"

# 3. Apply migrations
make db-upgrade

# 4. Verify database schema
make db-shell
# Run: \dt to list tables
# Run: \q to exit

# ============================================================================
# PHASE 4: RUN APPLICATION LOCALLY
# ============================================================================

# 1. Start FastAPI application
make dev

# App will start at: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
# Health endpoint: http://localhost:8000/health

# ============================================================================
# PHASE 5: MANUAL TESTING & VERIFICATION
# ============================================================================

# See "Manual Testing Workflow" section below

# ============================================================================
# PHASE 6: BACKGROUND TASKS (if using Celery)
# ============================================================================

# In a new terminal:
make celery-worker

# In another terminal (optional):
make flower

# Flower UI: http://localhost:5555

# ============================================================================
# PHASE 7: FULL CI PIPELINE (before building)
# ============================================================================

# Run complete CI pipeline locally
make ci

# Or quick CI check
make ci-quick

# ============================================================================
# PHASE 8: BUILD DOCKER IMAGE (only when everything passes)
# ============================================================================

# Build production image
make build
```

---

## 🧪 Manual Testing Workflow

### Step 1: Start Application

```bash
# Terminal 1: Start FastAPI app
make dev

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

### Step 2: Access Swagger UI

**Open browser:** http://localhost:8000/docs

**Swagger UI provides:**
- ✅ Interactive API documentation
- ✅ Try out endpoints directly
- ✅ See request/response schemas
- ✅ Authentication testing
- ✅ Real-time validation

### Step 3: Test Core Endpoints

#### 1. Health Check

**Endpoint:** `GET /health`

```bash
# Using curl
curl http://localhost:8000/health | jq

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-11-07T12:00:00Z",
  "version": "1.0.0"
}

# With service checks
curl "http://localhost:8000/health?check_services=true" | jq
```

#### 2. Authentication

**Endpoint:** `POST /api/v1/auth/register`

```bash
# Via Swagger UI:
# 1. Click "POST /api/v1/auth/register"
# 2. Click "Try it out"
# 3. Fill in the request body:
{
  "email": "test@example.com",
  "password": "TestPassword123!",
  "full_name": "Test User"
}
# 4. Click "Execute"

# Via curl:
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'
```

**Then login:**

```bash
# Via Swagger UI:
# 1. Click "POST /api/v1/auth/login"
# 2. Use the test credentials

# Via curl:
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123!"

# Copy the access_token from response
```

**Authorize in Swagger:**
1. Click "Authorize" button (top right)
2. Paste token in format: `Bearer <your_token>`
3. Click "Authorize"
4. Now you can test authenticated endpoints

#### 3. Chat Endpoint

**Endpoint:** `POST /api/v1/chat/completions`

```bash
# Via Swagger UI (after authorization):
{
  "messages": [
    {
      "role": "user",
      "content": "What is the first pillar of Islam?"
    }
  ],
  "model": "gpt-4",
  "stream": false
}
```

#### 4. Document Upload & RAG

**Endpoint:** `POST /api/v1/documents/upload`

```bash
# Via Swagger UI:
{
  "title": "Test Hadith",
  "content": "This is a test hadith content for RAG testing.",
  "document_type": "hadith",
  "primary_category": "aqidah",
  "language": "en"
}
```

**Then search:**

**Endpoint:** `POST /api/v1/documents/search`

```bash
{
  "query": "aqidah",
  "limit": 10
}
```

### Step 4: Test Background Tasks (Celery)

**Terminal 2: Start Celery worker**

```bash
make celery-worker
```

**Terminal 3: Start Flower (monitoring)**

```bash
make flower
```

**Open Flower UI:** http://localhost:5555

**Test background tasks:**
1. Trigger a task via API (e.g., document embedding generation)
2. Watch task progress in Flower UI
3. Check task results

### Step 5: Database Verification

```bash
# Open PostgreSQL shell
make db-shell

# Check tables
\dt

# Query users
SELECT id, email, full_name, created_at FROM users;

# Query documents
SELECT id, title, document_type, created_at FROM documents;

# Exit
\q
```

### Step 6: Redis Verification

```bash
# Open Redis CLI
make redis-cli

# Check keys
KEYS *

# Check cached data
GET some_cache_key

# Monitor commands (in real-time)
# Exit CLI first (Ctrl+C), then:
make redis-monitor
```

### Step 7: Qdrant Verification

**Open Qdrant UI:** http://localhost:6333/dashboard

**Or via curl:**

```bash
# Check collections
curl http://localhost:6333/collections | jq

# Check collection info
curl http://localhost:6333/collections/dev_documents | jq
```

---

## 🐛 Debugging Tips

### Enable Debug Mode

**In .env:**
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

**Restart app:**
```bash
# Stop app (Ctrl+C)
make dev
```

### Use Python Debugger

**Add breakpoint in code:**
```python
import pdb; pdb.set_trace()
```

**Or use VS Code debugger:**

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### View Logs in Real-time

**Application logs:**
```bash
# Already shown in terminal running 'make dev'
```

**Docker service logs:**
```bash
# All services
make docker-logs

# Specific service
make docker-logs-postgres
make docker-logs-redis
make docker-logs-qdrant
```

### Test Watch Mode

**For rapid iteration:**
```bash
# Re-run tests on file changes
make test-watch

# Or specific tests
poetry run ptw tests/unit/test_chat_service.py -- -v
```

---

## 📋 Pre-Build Checklist

Use this checklist before building Docker image:

```bash
# ☐ 1. All code formatted
make format-check

# ☐ 2. All linters pass
make lint

# ☐ 3. All security checks pass
make security

# ☐ 4. All tests pass
make test

# ☐ 5. Code coverage >= 75%
make coverage

# ☐ 6. Database migrations applied
poetry run alembic current

# ☐ 7. Application starts without errors
make dev  # Then Ctrl+C

# ☐ 8. Health endpoint responds
curl http://localhost:8000/health

# ☐ 9. Swagger UI loads
# Open http://localhost:8000/docs

# ☐ 10. Core endpoints tested
# Register, Login, Chat, Document Upload tested via Swagger

# ☐ 11. Background tasks work (if using Celery)
# Celery worker running, tasks complete in Flower

# ☐ 12. Database has expected data
make db-shell  # Check tables

# ☐ 13. Full CI pipeline passes
make ci

# ☐ 14. Pre-commit hooks pass
make pre-commit-run

# ☐ 15. Documentation updated
# README, API docs, CHANGELOG updated

# ============================================================================
# ALL CHECKS PASSED? NOW BUILD!
# ============================================================================

# Build Docker image
make build

# Or deploy to staging
make deploy-staging
```

---

## 🎯 Quick Commands Reference

### Daily Development

```bash
# Morning startup
make docker-up         # Start infrastructure
make dev               # Start app
make celery-worker     # Start background tasks (if needed)

# Evening shutdown
# Ctrl+C to stop dev server
# Ctrl+C to stop celery worker
make docker-down       # Stop infrastructure (or leave running)
```

### Before Commit

```bash
make quick-check       # Fast: format + flake8 + unit tests
```

### Before Push

```bash
make ci                # Full: format-check + lint + security + test
```

### Before Build

```bash
# Complete verification
make ci                # Full CI pipeline
make test              # All tests
make coverage          # Check coverage

# Manual testing
make dev               # Test via Swagger
# Open http://localhost:8000/docs
# Test all critical endpoints

# Database check
make db-shell          # Verify schema and data

# All good? Build!
make build
```

---

## 🔧 Common Issues & Solutions

### Issue: "Database connection failed"

**Solution:**
```bash
# Check PostgreSQL is running
make docker-health

# Restart PostgreSQL
docker restart shia-chatbot-postgres

# Check .env DATABASE_URL
# Should be: postgresql+asyncpg://postgres:postgres@localhost:5433/shia_chatbot
```

### Issue: "Redis connection failed"

**Solution:**
```bash
# Check Redis is running
docker exec shia-chatbot-redis redis-cli ping

# Restart Redis
docker restart shia-chatbot-redis
```

### Issue: "Module not found"

**Solution:**
```bash
# Reinstall dependencies
poetry install --with dev

# Verify virtual environment
poetry env info
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
poetry run uvicorn src.app.main:app --port 8001
```

### Issue: "Migration conflicts"

**Solution:**
```bash
# Check migration history
poetry run alembic history

# Downgrade to base
make db-reset

# Or specific version
poetry run alembic downgrade <revision>
```

---

## 📊 Performance Testing

### Load Testing with Locust (optional)

```bash
# Install locust
poetry add --group dev locust

# Create locustfile.py
# Run load tests
locust -f tests/locustfile.py --host=http://localhost:8000
```

### API Response Time Testing

```bash
# Using curl with timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# curl-format.txt:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_total:  %{time_total}\n
```

---

## 🚀 Deployment Workflow

### After Local Testing Passes

```bash
# 1. Ensure working tree is clean
git status

# 2. Run full CI
make ci

# 3. Build Docker image
make build

# 4. Tag image for deployment
docker tag shia-chatbot:latest shia-chatbot:v1.0.0

# 5. Deploy to staging
make deploy-staging

# 6. Test on staging
curl https://staging.yourapp.com/health

# 7. Deploy to production (with confirmation)
make deploy-prod
```

---

## 📚 Additional Resources

- **Makefile Commands:** See `MAKEFILE_QUICK_REFERENCE.md`
- **Pre-commit Hooks:** See `PRE_COMMIT_SETUP_GUIDE.md`
- **CI/CD Pipeline:** See `.github/workflows/OPTIMIZATION_GUIDE.md`
- **FastAPI Docs:** http://localhost:8000/docs (when running)
- **Qdrant Dashboard:** http://localhost:6333/dashboard
- **Flower UI:** http://localhost:5555 (when running)

---

## 🎓 Best Practices Summary

✅ **DO:**
- Use Docker for infrastructure (PostgreSQL, Redis, Qdrant)
- Run app natively for development (hot reload, debugging)
- Test locally before building Docker image
- Run full CI pipeline before pushing
- Use Swagger UI for API testing
- Keep .env secrets secure (never commit)
- Run migrations before starting app
- Monitor background tasks with Flower
- Check code coverage regularly

❌ **DON'T:**
- Build Docker image for every code change
- Run app in Docker during development (slow iteration)
- Skip tests before building
- Commit secrets to version control
- Deploy without testing on staging
- Ignore security warnings
- Skip database migrations

---

**Last Updated:** 2025-11-07
**For:** Shia Islamic Chatbot v1.0.0
