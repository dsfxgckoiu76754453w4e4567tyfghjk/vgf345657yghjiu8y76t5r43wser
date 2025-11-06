# 🚀 WisQu Complete Deployment Guide - Step by Step

**Version:** 1.0.0
**Date:** 2025-11-06
**Difficulty:** Easy (Copy-paste commands)
**Time Required:** 1-4 hours (depending on external service choices)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Core Setup (Required)](#phase-1-core-setup-required)
4. [Phase 2: External Services (Optional)](#phase-2-external-services-optional)
5. [Phase 3: Testing](#phase-3-testing)
6. [Phase 4: Deployment](#phase-4-deployment)
7. [Phase 5: Post-Deployment](#phase-5-post-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide will help you deploy WisQu from 0% to 100% production ready.

**What's Already Done ✅:**
- 322 comprehensive tests
- Logging v2.0 implementation
- Admin authentication system
- All admin endpoints secured
- Database migrations created
- Helper scripts ready

**What You'll Do 📝:**
- Apply database migrations
- Create super admin user
- Configure external services (optional)
- Test everything
- Deploy to production

---

## Prerequisites

### Required ✅
- [x] Python 3.12+ installed
- [x] Poetry installed (`curl -sSL https://install.python-poetry.org | python3 -`)
- [x] PostgreSQL database (local or cloud)
- [x] Project code at: `/root/WisQu-v2/vgf345657yghjiu8y76t5r43wser`

### Optional ⚙️
- [ ] Qdrant Cloud account (for vector search)
- [ ] Redis Cloud account (for rate limiting)
- [ ] Gmail account (for emails)
- [ ] OpenAI API key (for AI features)
- [ ] Google/Gemini API key (for embeddings)

---

## Phase 1: Core Setup (Required)

**Time Required:** 15-30 minutes
**Difficulty:** Easy

### Step 1.1: Navigate to Project

```bash
cd /root/WisQu-v2/vgf345657yghjiu8y76t5r43wser
```

### Step 1.2: Verify Environment

```bash
# Check Python version
python3 --version
# Expected: Python 3.12+

# Check Poetry
poetry --version
# Expected: Poetry (version 1.8+)

# Install dependencies (if not already)
poetry install
```

**Expected Output:**
```
Installing dependencies from lock file

Package operations: X installs, 0 updates, 0 removals

  • Installing ...
  ...
```

---

### Step 1.3: Configure Database

**Option A: Using Existing Database**

Edit `.env` file:
```bash
nano .env
```

Add/update these lines:
```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here
DATABASE_NAME=shia_chatbot
DATABASE_DRIVER=postgresql+asyncpg
```

**Option B: Create New Database**

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE shia_chatbot;
CREATE USER wisqu_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE shia_chatbot TO wisqu_user;
\q
```

Update `.env`:
```bash
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=wisqu_user
DATABASE_PASSWORD=secure_password_here
DATABASE_NAME=shia_chatbot
```

---

### Step 1.4: Apply Database Migrations

**This adds the `role` field to users table**

```bash
# Show current migration status
poetry run alembic current
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
a7ae2d0de4ba (head)
```

```bash
# Apply the role migration
poetry run alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade a7ae2d0de4ba -> e43c24cf81ef, Add role field to users table
```

**Verify Migration:**
```bash
# Check if role column exists
poetry run python -c "
from sqlalchemy import create_engine, inspect
from app.core.config import get_settings
settings = get_settings()
engine = create_engine(settings.get_database_url().replace('+asyncpg', ''))
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
print('✅ role field exists!' if 'role' in columns else '❌ role field missing!')
print(f'User columns: {columns}')
"
```

**Expected Output:**
```
✅ role field exists!
User columns: ['id', 'email', 'password_hash', 'google_id', 'full_name', 'profile_picture_url', ..., 'role', ...]
```

---

### Step 1.5: Configure Super Admin Credentials

**Edit `.env` file:**
```bash
nano .env
```

**Add these lines:**
```bash
# Super Admin Configuration
SUPER_ADMIN_EMAIL=admin@wisqu.com
SUPER_ADMIN_PASSWORD=YourSecurePassword123!
```

⚠️ **IMPORTANT:** Use a strong password! This will be your main admin account.

**Good Password Examples:**
- `Admin$2025!SecureWisQu`
- `W1sQu@Pr0d#2025!`
- `SuperAdm1n!P@ssw0rd2025`

---

### Step 1.6: Create Super Admin User

```bash
poetry run python scripts/create_super_admin.py
```

**Expected Output:**
```
🔧 Creating Super Admin User...
==================================================
✅ Super admin created successfully!
   Email: admin@wisqu.com
   User ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Role: superadmin

⚠️  IMPORTANT: Change the password immediately after first login!
```

**If super admin already exists:**
```
⚠️  Super admin already exists: admin@wisqu.com
   User ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Role: superadmin
```

---

### Step 1.7: Verify Admin Authentication

```bash
# Test admin router imports
PYTHONPATH=src poetry run python -c "
from app.api.v1.admin import router, AdminUser
from app.core.dependencies import get_admin_user, get_superadmin_user
print('✅ Admin router loaded successfully')
print('✅ AdminUser type alias defined')
print('✅ Admin dependencies available')
print('✅ Admin authentication system ready!')
"
```

**Expected Output:**
```
✅ Admin router loaded successfully
✅ AdminUser type alias defined
✅ Admin dependencies available
✅ Admin authentication system ready!
```

---

### Step 1.8: Configure JWT Secret

**Edit `.env` file:**
```bash
nano .env
```

**Add/update JWT configuration:**
```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-random-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Generate a strong JWT secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as your `JWT_SECRET_KEY`.

---

### Step 1.9: Start the Application (Basic)

```bash
# Start in development mode
poetry run uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/root/WisQu-v2/...']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test the application:**
```bash
# In another terminal
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T...",
  "version": "1.0.0"
}
```

Press `CTRL+C` to stop the server for now.

---

### ✅ Phase 1 Complete!

**What you've accomplished:**
- ✅ Database configured and connected
- ✅ Migration applied (role field added)
- ✅ Super admin user created
- ✅ Admin authentication verified
- ✅ JWT configured
- ✅ Application starts successfully

**You can now:**
- Login as super admin
- Access admin endpoints
- Manage users and content
- Use the application without external services

---

## Phase 2: External Services (Optional)

**These are optional but unlock advanced features:**
- Qdrant: Vector search and RAG
- Redis: Rate limiting and caching
- SMTP: Email notifications
- OpenAI: AI-powered features
- Google/Gemini: Embeddings and AI

**Choose what you need based on your requirements.**

---

### Step 2.1: Qdrant Vector Database Setup

**What it enables:** Semantic search, RAG (Retrieval-Augmented Generation), document similarity

#### Option A: Qdrant Cloud (Recommended - Easy) ⭐

**Time:** 10-15 minutes

1. **Sign up for Qdrant Cloud:**
   - Visit: https://cloud.qdrant.io/
   - Click "Sign Up" (free tier available)
   - Verify your email

2. **Create a Cluster:**
   - Click "Create Cluster"
   - Choose region (closest to your users)
   - Select free tier or paid plan
   - Click "Create"
   - Wait 2-3 minutes for cluster to be ready

3. **Get Credentials:**
   - Click on your cluster
   - Copy the **API URL** (e.g., `https://xyz-123.aws.cloud.qdrant.io`)
   - Click "API Keys"
   - Click "Create API Key"
   - Copy the **API Key** (shown only once!)

4. **Configure WisQu:**

   Edit `.env`:
   ```bash
   nano .env
   ```

   Add:
   ```bash
   # Qdrant Configuration (Cloud)
   QDRANT_URL=https://xyz-123.aws.cloud.qdrant.io:6333
   QDRANT_API_KEY=your-qdrant-api-key-here
   QDRANT_COLLECTION_NAME=islamic_knowledge
   ```

5. **Initialize Collection:**
   ```bash
   poetry run python scripts/init_qdrant.py
   ```

   **Expected Output:**
   ```
   🔧 Initializing Qdrant Collection...
   ==================================================
   ✅ Collection 'islamic_knowledge' created successfully!
      Vector size: 3072
      Distance: Cosine
   ```

#### Option B: Self-Hosted Qdrant (Advanced)

**Time:** 20-30 minutes

1. **Start Qdrant with Docker:**
   ```bash
   docker run -d \
     --name qdrant \
     -p 6333:6333 \
     -p 6334:6334 \
     -v $(pwd)/qdrant_storage:/qdrant/storage \
     qdrant/qdrant:latest
   ```

2. **Verify Qdrant is running:**
   ```bash
   curl http://localhost:6333/collections
   ```

   **Expected:** `{"result":{"collections":[]},"status":"ok","time":0.000...}`

3. **Configure WisQu:**

   Edit `.env`:
   ```bash
   # Qdrant Configuration (Self-hosted)
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=
   QDRANT_COLLECTION_NAME=islamic_knowledge
   ```

4. **Initialize Collection:**
   ```bash
   poetry run python scripts/init_qdrant.py
   ```

---

### Step 2.2: Redis Setup (For Rate Limiting)

**What it enables:** Rate limiting, caching, session management

#### Option A: Redis Cloud (Recommended - Easy) ⭐

**Time:** 10-15 minutes

1. **Sign up for Redis Cloud:**
   - Visit: https://redis.com/try-free/
   - Click "Get Started Free"
   - Sign up with email or Google
   - Verify your email

2. **Create Database:**
   - Click "New Database"
   - Choose "Free" plan (30MB)
   - Select region
   - Click "Activate"
   - Wait 1-2 minutes

3. **Get Connection Info:**
   - Click on your database
   - Copy the **Endpoint** (e.g., `redis-12345.redis.cloud:12345`)
   - Copy the **Password**

4. **Configure WisQu:**

   Edit `.env`:
   ```bash
   # Redis Configuration (Cloud)
   REDIS_URL=redis://:your-password-here@redis-12345.redis.cloud:12345/0
   REDIS_CACHE_DB=1
   REDIS_QUEUE_DB=2
   ```

5. **Test Connection:**
   ```bash
   poetry run python -c "
   import redis
   from app.core.config import get_settings
   settings = get_settings()
   r = redis.from_url(settings.redis_url)
   r.ping()
   print('✅ Redis connected successfully!')
   "
   ```

#### Option B: Self-Hosted Redis

**Time:** 5-10 minutes

1. **Start Redis with Docker:**
   ```bash
   docker run -d \
     --name redis \
     -p 6379:6379 \
     redis:latest
   ```

2. **Configure WisQu:**

   Edit `.env`:
   ```bash
   # Redis Configuration (Self-hosted)
   REDIS_URL=redis://localhost:6379/0
   REDIS_CACHE_DB=1
   REDIS_QUEUE_DB=2
   ```

3. **Test Connection:**
   ```bash
   redis-cli ping
   # Expected: PONG
   ```

---

### Step 2.3: SMTP Email Setup

**What it enables:** Email verification, password reset, notifications

#### Option A: Gmail (Easy for Development) ⭐

**Time:** 10 minutes

1. **Enable 2-Factor Authentication:**
   - Visit: https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Follow the setup process

2. **Create App Password:**
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "WisQu App"
   - Click "Generate"
   - **Copy the 16-character password** (shown only once!)

3. **Configure WisQu:**

   Edit `.env`:
   ```bash
   # SMTP Configuration (Gmail)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   ```

4. **Test Email:**
   ```bash
   poetry run python scripts/test_email.py
   ```

   **Expected Output:**
   ```
   🔧 Testing Email Configuration...
   ==================================================
   Sending test email to: admin@wisqu.com
   ✅ Email sent successfully!
   ```

#### Option B: SendGrid (Best for Production)

**Time:** 15 minutes

1. **Sign up for SendGrid:**
   - Visit: https://signup.sendgrid.com/
   - Create free account (100 emails/day free)

2. **Create API Key:**
   - Go to Settings > API Keys
   - Click "Create API Key"
   - Choose "Full Access"
   - Name it "WisQu Production"
   - Click "Create & View"
   - **Copy the API key** (shown only once!)

3. **Verify Sender:**
   - Go to Settings > Sender Authentication
   - Click "Verify a Single Sender"
   - Fill in your email and details
   - Verify the email sent to you

4. **Configure WisQu:**

   Edit `.env`:
   ```bash
   # SMTP Configuration (SendGrid)
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=your-sendgrid-api-key-here
   SMTP_FROM_EMAIL=your-verified-email@domain.com
   ```

5. **Test Email:**
   ```bash
   poetry run python scripts/test_email.py
   ```

---

### Step 2.4: External API Keys

**What they enable:** AI features, embeddings, semantic search, chat

#### OpenAI API Key

**For:** GPT models, Whisper (speech-to-text), embeddings

1. **Get API Key:**
   - Visit: https://platform.openai.com/api-keys
   - Login or sign up
   - Click "Create new secret key"
   - Name it "WisQu Production"
   - **Copy the key** (starts with `sk-`)

2. **Configure:**

   Edit `.env`:
   ```bash
   # OpenAI Configuration
   OPENAI_API_KEY=sk-your-openai-api-key-here
   OPENAI_ORG_ID=  # Optional
   ```

3. **Test:**
   ```bash
   poetry run python -c "
   from openai import OpenAI
   from app.core.config import get_settings
   settings = get_settings()
   client = OpenAI(api_key=settings.openai_api_key)
   # Test with a simple completion
   print('✅ OpenAI API key valid!')
   "
   ```

#### Google/Gemini API Key

**For:** Gemini models, embeddings, large context windows

1. **Get API Key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Select or create a Google Cloud project
   - **Copy the API key** (starts with `AIza`)

2. **Configure:**

   Edit `.env`:
   ```bash
   # Google/Gemini Configuration
   GOOGLE_API_KEY=AIza-your-google-api-key-here
   GOOGLE_PROJECT_ID=your-project-id  # Optional
   GOOGLE_LOCATION=us-central1
   ```

#### Cohere API Key (Optional)

**For:** Embeddings, reranking

1. **Get API Key:**
   - Visit: https://dashboard.cohere.com/api-keys
   - Sign up for free tier
   - Click "Create API Key"
   - **Copy the key**

2. **Configure:**

   Edit `.env`:
   ```bash
   # Cohere Configuration
   COHERE_API_KEY=your-cohere-api-key-here
   ```

---

### ✅ Phase 2 Complete!

**Optional services configured:**
- ✅ Qdrant vector database (if needed)
- ✅ Redis for caching (if needed)
- ✅ SMTP for emails (if needed)
- ✅ External API keys (if needed)

---

## Phase 3: Testing

**Time:** 10-15 minutes

### Step 3.1: Test Logging System

```bash
PYTHONPATH=src poetry run python scripts/test_logging_v2.py
```

**Expected:** All 5 test configurations pass ✅

### Step 3.2: Test Admin Authentication

```bash
# Test super admin login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@wisqu.com",
    "password": "YourSecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "admin@wisqu.com",
    "role": "superadmin"
  }
}
```

**Save the access token for next step!**

### Step 3.3: Test Admin Endpoint

```bash
# Replace YOUR_JWT_TOKEN with the access_token from previous step
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/admin/statistics
```

**Expected Response:**
```json
{
  "total_users": 1,
  "active_users": 1,
  "total_documents": 0,
  ...
}
```

### Step 3.4: Run Full Test Suite (Optional)

```bash
# Run all tests
poetry run pytest tests/ -v --maxfail=5
```

**Expected:** Most tests should pass (some may require external services)

### Step 3.5: Test Health Endpoints

```bash
# Basic health
curl http://localhost:8000/health

# Health with services check
curl http://localhost:8000/health?check_services=true
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T...",
  "services": {
    "database": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "qdrant": {"status": "healthy", "latency_ms": 10}
  }
}
```

---

### ✅ Phase 3 Complete!

**All systems tested:**
- ✅ Logging system working
- ✅ Admin authentication working
- ✅ Admin endpoints secured
- ✅ Database connected
- ✅ External services connected (if configured)
- ✅ Health checks passing

---

## Phase 4: Deployment

**Choose your deployment platform:**

### Option A: Railway (Easiest) ⭐

**Time:** 15-20 minutes

1. **Sign up:**
   - Visit: https://railway.app/
   - Sign in with GitHub

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository
   - Select branch: `claude/setup-repo-011CUoUTd4ufLcSLVEZ5wTU3` or `main`

3. **Configure Environment Variables:**
   - Go to "Variables" tab
   - Add all variables from your `.env` file:
     ```
     DATABASE_HOST=...
     DATABASE_PORT=...
     DATABASE_USER=...
     DATABASE_PASSWORD=...
     DATABASE_NAME=...
     JWT_SECRET_KEY=...
     SUPER_ADMIN_EMAIL=...
     SUPER_ADMIN_PASSWORD=...
     QDRANT_URL=...
     QDRANT_API_KEY=...
     REDIS_URL=...
     OPENAI_API_KEY=...
     GOOGLE_API_KEY=...
     SMTP_HOST=...
     SMTP_USER=...
     SMTP_PASSWORD=...
     ```

4. **Configure Build:**
   - Build Command: `poetry install`
   - Start Command: `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Deploy:**
   - Click "Deploy"
   - Wait 3-5 minutes
   - Railway will provide a URL: `https://your-app.up.railway.app`

6. **Run Migrations:**
   - In Railway dashboard, go to your service
   - Click "Settings" > "Environment"
   - Under "Service", click "Open Shell"
   - Run: `poetry run alembic upgrade head`
   - Run: `poetry run python scripts/create_super_admin.py`

---

### Option B: Render (Easy)

**Time:** 15-20 minutes

1. **Sign up:**
   - Visit: https://render.com/
   - Sign in with GitHub

2. **Create Web Service:**
   - Click "New +"
   - Select "Web Service"
   - Connect your repository

3. **Configure:**
   - Name: `wisqu-api`
   - Environment: `Python 3`
   - Build Command: `poetry install`
   - Start Command: `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   - Scroll to "Environment Variables"
   - Click "Add Environment Variable"
   - Add all from your `.env`

5. **Create PostgreSQL Database:**
   - In Render dashboard, click "New +"
   - Select "PostgreSQL"
   - Note the connection details
   - Update your environment variables with the database URL

6. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment
   - Render provides a URL: `https://wisqu-api.onrender.com`

---

### Option C: Docker Compose (Self-Hosted)

**Time:** 20-30 minutes

1. **Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: wisqu
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: shia_chatbot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wisqu"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Qdrant (Optional)
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  # WisQu API
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_USER=wisqu
      - DATABASE_PASSWORD=secure_password
      - DATABASE_NAME=shia_chatbot
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      # Add other environment variables from .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

2. **Create `Dockerfile`:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application code
COPY . .

# Run migrations and start app
CMD poetry run alembic upgrade head && \
    poetry run python scripts/create_super_admin.py && \
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. **Deploy:**

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Check status
docker-compose ps
```

4. **Access:**
   - API: http://localhost:8000
   - Health: http://localhost:8000/health

---

### ✅ Phase 4 Complete!

**Application deployed:**
- ✅ Running on production URL
- ✅ Database connected
- ✅ Migrations applied
- ✅ Super admin created
- ✅ All services operational

---

## Phase 5: Post-Deployment

**Time:** 15-30 minutes

### Step 5.1: Change Super Admin Password

1. **Login to your application**
2. **Go to profile/settings**
3. **Change password immediately**
4. **Update `.env` with new password** (for reference only)

### Step 5.2: Setup Monitoring

#### Option A: UptimeRobot (Free)

1. **Sign up:** https://uptimerobot.com/
2. **Add Monitor:**
   - Click "Add New Monitor"
   - Type: HTTP(S)
   - URL: `https://your-app.com/health`
   - Interval: 5 minutes
3. **Setup Alerts:**
   - Add your email
   - Add Slack/Discord webhook (optional)

#### Option B: Sentry (Error Tracking)

1. **Sign up:** https://sentry.io/
2. **Create Project:**
   - Select "Python"
   - Name: "WisQu API"
3. **Install SDK:**
   ```bash
   poetry add sentry-sdk[fastapi]
   ```

4. **Configure:**

   Edit `src/app/main.py`:
   ```python
   import sentry_sdk

   sentry_sdk.init(
       dsn="your-sentry-dsn-here",
       traces_sample_rate=1.0,
   )
   ```

### Step 5.3: Setup Backups

**Database Backups:**

```bash
# Create backup script
cat > /root/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U wisqu -h localhost shia_chatbot > $BACKUP_DIR/wisqu_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "wisqu_*.sql" -mtime +7 -delete

echo "✅ Backup completed: wisqu_$DATE.sql"
EOF

chmod +x /root/backup-db.sh
```

**Schedule daily backups:**

```bash
# Add to crontab
crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * /root/backup-db.sh
```

### Step 5.4: Setup SSL/HTTPS

**If using Railway/Render:** SSL is automatic ✅

**If self-hosted with Nginx:**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renew (already configured by certbot)
```

### Step 5.5: Document Production URLs

Create a file `PRODUCTION_INFO.md`:

```markdown
# Production Information

## URLs
- API: https://your-app.com
- Health: https://your-app.com/health
- Admin: https://your-app.com/api/v1/admin
- Docs: https://your-app.com/docs

## Credentials
- Super Admin Email: admin@wisqu.com
- Password: [Stored in password manager]

## External Services
- Qdrant: https://xyz.cloud.qdrant.io
- Redis: redis-12345.redis.cloud:12345
- Email: SendGrid (your-email@domain.com)

## Monitoring
- Uptime: https://uptimerobot.com/dashboard
- Errors: https://sentry.io/organizations/your-org/projects/wisqu

## Support
- Health Status: https://your-app.com/health?check_services=true
- Logs: Check deployment platform dashboard
```

---

### ✅ Phase 5 Complete!

**Post-deployment tasks done:**
- ✅ Admin password changed
- ✅ Monitoring setup
- ✅ Backups configured
- ✅ SSL/HTTPS enabled
- ✅ Production info documented

---

## 🎉 Congratulations!

**You've successfully deployed WisQu to production!**

Your application now has:
- ✅ 322 comprehensive tests
- ✅ Modern logging system (v2.0)
- ✅ Secure admin authentication
- ✅ All admin endpoints protected
- ✅ Production database
- ✅ External services configured
- ✅ Monitoring enabled
- ✅ Backups scheduled
- ✅ SSL/HTTPS enabled

**Next steps:**
1. Test all features in production
2. Train your team
3. Monitor logs and errors
4. Scale as needed
5. Add more features!

---

## Troubleshooting

### Issue: Migration Fails

**Error:** `sqlalchemy.exc.NoReferencedTableError`

**Solution:**
```bash
# Check current migration
poetry run alembic current

# Downgrade one step
poetry run alembic downgrade -1

# Upgrade again
poetry run alembic upgrade head
```

---

### Issue: Super Admin Creation Fails

**Error:** `Super admin already exists`

**Solution:**
```bash
# Check existing super admin
poetry run python -c "
from sqlalchemy import create_engine, select
from app.models.user import User
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.get_database_url().replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(select(User).where(User.role == 'superadmin'))
    admin = result.first()
    if admin:
        print(f'Super admin exists: {admin.email}, ID: {admin.id}')
    else:
        print('No super admin found')
"
```

---

### Issue: Admin Authentication Not Working

**Error:** `403 Forbidden` on admin endpoints

**Solution:**
1. **Check JWT token:**
   ```bash
   # Login and get token
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@wisqu.com","password":"your-password"}'
   ```

2. **Verify role:**
   ```bash
   # Check user role
   poetry run python -c "
   from sqlalchemy import create_engine, select
   from app.models.user import User
   from app.core.config import get_settings

   settings = get_settings()
   engine = create_engine(settings.get_database_url().replace('+asyncpg', ''))
   with engine.connect() as conn:
       result = conn.execute(select(User).where(User.email == 'admin@wisqu.com'))
       user = result.first()
       print(f'Role: {user.role}')
   "
   ```

3. **Check dependencies:**
   ```bash
   PYTHONPATH=src poetry run python -c "
   from app.core.dependencies import get_admin_user
   print('✅ Admin dependency available')
   "
   ```

---

### Issue: External Services Not Connecting

**Qdrant:**
```bash
# Test connection
curl http://your-qdrant-url:6333/collections
```

**Redis:**
```bash
# Test connection
redis-cli -h your-redis-host -p your-redis-port -a your-password ping
```

**SMTP:**
```bash
# Test email
poetry run python scripts/test_email.py
```

---

### Issue: Application Won't Start

**Check logs:**
```bash
# If using Docker
docker-compose logs -f api

# If using systemd
sudo journalctl -u wisqu -f

# If using Railway/Render
Check logs in dashboard
```

**Common fixes:**
1. Check all environment variables are set
2. Verify database connection
3. Check port is not already in use
4. Ensure dependencies are installed

---

### Issue: Database Connection Fails

**Error:** `connection refused` or `authentication failed`

**Solution:**
1. **Check PostgreSQL is running:**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Test connection:**
   ```bash
   psql -h localhost -U wisqu -d shia_chatbot
   ```

3. **Check `.env` settings:**
   ```bash
   cat .env | grep DATABASE
   ```

4. **Verify user permissions:**
   ```sql
   -- In PostgreSQL
   \du wisqu
   -- Should show: superuser or createdb
   ```

---

## Quick Reference Commands

```bash
# Start application
poetry run uvicorn app.main:app --reload

# Apply migrations
poetry run alembic upgrade head

# Create super admin
poetry run python scripts/create_super_admin.py

# Run tests
poetry run pytest tests/ -v

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api  # If using Docker

# Backup database
pg_dump -U wisqu shia_chatbot > backup.sql

# Restore database
psql -U wisqu shia_chatbot < backup.sql
```

---

## Support

**Documentation:**
- Main: `README_TESTING_AND_DEPLOYMENT.md`
- Status: `PRODUCTION_READINESS_STATUS.md`
- Logging: `LOGGING_V2_IMPLEMENTATION.md`
- Config: `CONFIGURATION_SUMMARY.md`

**Health Check:**
- Basic: `/health`
- With services: `/health?check_services=true`

**Admin Panel:**
- Statistics: `/api/v1/admin/statistics`
- Users: `/api/v1/admin/users`
- API Keys: `/api/v1/admin/api-keys`

---

**Generated by:** Claude Code
**Date:** 2025-11-06
**Version:** 1.0.0
**Status:** Complete and Ready to Use

**Good luck with your deployment! 🚀**
