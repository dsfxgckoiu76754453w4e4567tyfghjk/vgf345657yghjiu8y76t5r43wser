# Production Configuration Guide
**Complete Setup Guide for 100% Production Readiness**

This guide covers the remaining 5% configuration needed to achieve 100% production deployment confidence.

---

## Table of Contents
1. [Environment Variables Setup](#1-environment-variables-setup)
2. [Admin Authentication Middleware](#2-admin-authentication-middleware)
3. [Qdrant Vector Database Setup](#3-qdrant-vector-database-setup)
4. [External API Keys Configuration](#4-external-api-keys-configuration)
5. [Redis Setup for Rate Limiting](#5-redis-setup-for-rate-limiting)
6. [SMTP Email Configuration](#6-smtp-email-configuration)
7. [Production Deployment Checklist](#7-production-deployment-checklist)
8. [Monitoring & Health Checks](#8-monitoring--health-checks)

---

## 1. Environment Variables Setup

### Create Production `.env` File

Create `/root/WisQu-v2/vgf345657yghjiu8y76t5r43wser/.env.production`:

```bash
# ================================
# APPLICATION SETTINGS
# ================================
APP_NAME="Shia Islamic Chatbot"
ENVIRONMENT=production
DEBUG=false
API_VERSION=v1
LOG_LEVEL=info

# ================================
# DATABASE CONFIGURATION
# ================================
# PostgreSQL Database
DB_HOST=your-postgres-host.com
DB_PORT=5432
DB_USER=wisqu_user
DB_PASSWORD=your-secure-database-password-here
DB_NAME=wisqu_production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ================================
# SECURITY & JWT
# ================================
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Settings
CORS_ORIGINS=["https://your-frontend-domain.com","https://app.wisqu.com"]
CORS_ALLOW_CREDENTIALS=true

# ================================
# REDIS CONFIGURATION
# ================================
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password-here
REDIS_DB=0
REDIS_URL=redis://:your-redis-password-here@your-redis-host.com:6379/0

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# ================================
# QDRANT VECTOR DATABASE
# ================================
QDRANT_HOST=your-qdrant-host.com
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key-here
QDRANT_COLLECTION_NAME=wisqu_embeddings
QDRANT_VECTOR_SIZE=768
QDRANT_USE_SSL=true

# ================================
# EXTERNAL AI API KEYS
# ================================
# OpenAI (for ASR - Whisper)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_ASR_MODEL=whisper-1

# Google Gemini (for embeddings)
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=models/text-embedding-004

# Cohere (alternative embeddings)
COHERE_API_KEY=your-cohere-api-key-here
COHERE_MODEL=embed-multilingual-v3.0

# Default embedding provider: gemini, cohere, or openai
DEFAULT_EMBEDDING_PROVIDER=gemini

# ================================
# EMAIL / SMTP CONFIGURATION
# ================================
# Gmail Configuration (recommended for development)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@wisqu.com
SMTP_FROM_NAME="WisQu Support"
SMTP_USE_TLS=true

# Alternative: SendGrid
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USER=apikey
# SMTP_PASSWORD=your-sendgrid-api-key

# Alternative: Amazon SES
# SMTP_HOST=email-smtp.us-east-1.amazonaws.com
# SMTP_PORT=587
# SMTP_USER=your-ses-smtp-username
# SMTP_PASSWORD=your-ses-smtp-password

# ================================
# LANGFUSE (LLM Observability) - OPTIONAL
# ================================
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# ================================
# ADMIN SETTINGS
# ================================
# Super admin credentials (first admin user)
SUPER_ADMIN_EMAIL=admin@wisqu.com
SUPER_ADMIN_PASSWORD=change-this-secure-password-immediately

# Admin API Key for external tools
ADMIN_API_KEY_SECRET=your-admin-api-key-secret-here

# ================================
# FILE UPLOAD SETTINGS
# ================================
MAX_UPLOAD_SIZE_MB=25
ALLOWED_FILE_TYPES=["pdf","txt","docx","doc"]
UPLOAD_DIRECTORY=/var/wisqu/uploads

# ================================
# FEATURE FLAGS
# ================================
ENABLE_REGISTRATION=true
ENABLE_GOOGLE_OAUTH=false
ENABLE_ASR=true
ENABLE_DOCUMENT_UPLOAD=true
ENABLE_AHKAM_TOOL=true
ENABLE_HADITH_SEARCH=true
```

---

## 2. Admin Authentication Middleware

### Step 1: Create Admin Role Check Dependency

Create or verify `/root/WisQu-v2/vgf345657yghjiu8y76t5r43wser/src/app/core/dependencies.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user has admin privileges."""
    # Check if user has admin role (admin, moderator, or super_admin)
    admin_roles = ["admin", "moderator", "super_admin"]

    if not hasattr(current_user, 'role') or current_user.role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


async def get_super_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user has super admin privileges."""
    if not hasattr(current_user, 'role') or current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )

    return current_user
```

### Step 2: Add Role Field to User Model

Update `/root/WisQu-v2/vgf345657yghjiu8y76t5r43wser/src/app/models/user.py`:

```python
# Add to User model (around line 50)
role: Mapped[str] = mapped_column(
    String(20),
    default="user"
)  # user, moderator, admin, super_admin
```

### Step 3: Apply Admin Dependencies to Endpoints

Update admin endpoints in `/root/WisQu-v2/vgf345657yghjiu8y76t5r43wser/src/app/api/v1/admin.py`:

```python
from app.core.dependencies import get_current_admin_user, get_super_admin_user

# Example endpoint with admin auth
@router.get("/users")
async def list_users(
    current_admin: User = Depends(get_current_admin_user),  # ← Add this
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List all users (admin only)."""
    # ... implementation
```

### Step 4: Create Database Migration for Role Field

```bash
# Generate migration
cd /root/WisQu-v2/vgf345657yghjiu8y76t5r43wser
alembic revision --autogenerate -m "Add role field to users"

# Apply migration
alembic upgrade head
```

### Step 5: Create First Super Admin

```python
# Create script: scripts/create_super_admin.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User

settings = get_settings()

async def create_super_admin():
    engine = create_async_engine(settings.get_database_url())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if super admin exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == settings.super_admin_email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Super admin already exists: {settings.super_admin_email}")
            return

        # Create super admin
        admin = User(
            email=settings.super_admin_email,
            password_hash=hash_password(settings.super_admin_password),
            full_name="Super Administrator",
            role="super_admin",
            is_email_verified=True,
            is_active=True,
            account_type="unlimited"
        )

        session.add(admin)
        await session.commit()
        print(f"✅ Super admin created: {settings.super_admin_email}")

if __name__ == "__main__":
    asyncio.run(create_super_admin())
```

Run: `poetry run python scripts/create_super_admin.py`

---

## 3. Qdrant Vector Database Setup

### Option A: Qdrant Cloud (Recommended for Production)

1. **Sign up for Qdrant Cloud**
   - Visit: https://cloud.qdrant.io/
   - Create free account

2. **Create Cluster**
   - Choose region closest to your users
   - Select appropriate tier (starts free)
   - Note the cluster URL and API key

3. **Configure Environment**
   ```bash
   QDRANT_HOST=xyz-example.us-east.aws.cloud.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your-api-key-from-dashboard
   QDRANT_USE_SSL=true
   ```

### Option B: Self-Hosted Qdrant (Docker)

1. **Create docker-compose.yml**

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: wisqu-qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}
      - QDRANT__STORAGE__SNAPSHOT_PATH=/qdrant/snapshots
    restart: unless-stopped
    networks:
      - wisqu-network

networks:
  wisqu-network:
    driver: bridge
```

2. **Start Qdrant**
   ```bash
   docker-compose up -d qdrant
   ```

3. **Configure Environment**
   ```bash
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   QDRANT_API_KEY=your-generated-api-key
   QDRANT_USE_SSL=false  # true if using reverse proxy with SSL
   ```

### Step 3: Initialize Qdrant Collection

Create script: `scripts/init_qdrant.py`

```python
import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings

settings = get_settings()

async def initialize_qdrant():
    """Initialize Qdrant collection for embeddings."""
    client = AsyncQdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
        https=settings.qdrant_use_ssl
    )

    # Check if collection exists
    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if settings.qdrant_collection_name in collection_names:
        print(f"✅ Collection '{settings.qdrant_collection_name}' already exists")
        return

    # Create collection
    await client.create_collection(
        collection_name=settings.qdrant_collection_name,
        vectors_config=VectorParams(
            size=settings.qdrant_vector_size,  # 768 for Gemini
            distance=Distance.COSINE
        )
    )

    print(f"✅ Created collection: {settings.qdrant_collection_name}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(initialize_qdrant())
```

Run: `poetry run python scripts/init_qdrant.py`

---

## 4. External API Keys Configuration

### A. OpenAI API Key (for ASR - Whisper)

1. **Get API Key**
   - Visit: https://platform.openai.com/api-keys
   - Create new secret key
   - Copy and save immediately (shown only once)

2. **Configure**
   ```bash
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
   OPENAI_ASR_MODEL=whisper-1
   ```

3. **Test**
   ```bash
   curl https://api.openai.com/v1/models/whisper-1 \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### B. Google Gemini API Key (for Embeddings)

1. **Get API Key**
   - Visit: https://makersuite.google.com/app/apikey
   - Create API key
   - Enable "Generative Language API"

2. **Configure**
   ```bash
   GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   GEMINI_MODEL=models/text-embedding-004
   ```

3. **Test**
   ```python
   import google.generativeai as genai
   genai.configure(api_key="YOUR_API_KEY")

   result = genai.embed_content(
       model="models/text-embedding-004",
       content="Test embedding"
   )
   print(f"✅ Embedding dimension: {len(result['embedding'])}")
   ```

### C. Cohere API Key (Alternative Embeddings)

1. **Get API Key**
   - Visit: https://dashboard.cohere.com/api-keys
   - Create production key
   - Copy key

2. **Configure**
   ```bash
   COHERE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   COHERE_MODEL=embed-multilingual-v3.0
   ```

3. **Test**
   ```python
   import cohere
   co = cohere.Client("YOUR_API_KEY")

   response = co.embed(
       texts=["Test embedding"],
       model="embed-multilingual-v3.0"
   )
   print(f"✅ Embedding dimension: {len(response.embeddings[0])}")
   ```

### API Key Security Best Practices

1. **Never commit API keys to git**
   ```bash
   echo ".env*" >> .gitignore
   echo "!.env.example" >> .gitignore
   ```

2. **Use environment variables**
   - Production: Set via hosting platform (Railway, Render, AWS, etc.)
   - Development: Use `.env.local` (gitignored)

3. **Rotate keys regularly**
   - Set calendar reminder for quarterly rotation
   - Keep old key active for 24h during rotation

4. **Monitor usage**
   - Set up billing alerts
   - Track API call patterns
   - Watch for unusual spikes

---

## 5. Redis Setup for Rate Limiting

### Option A: Redis Cloud (Recommended)

1. **Sign up for Redis Cloud**
   - Visit: https://redis.com/try-free/
   - Create free 30MB database

2. **Get Connection Details**
   - Copy endpoint: `redis-xxxxx.redis.cloud:12345`
   - Copy password

3. **Configure**
   ```bash
   REDIS_HOST=redis-xxxxx.redis.cloud
   REDIS_PORT=12345
   REDIS_PASSWORD=your-redis-password
   REDIS_URL=redis://:your-redis-password@redis-xxxxx.redis.cloud:12345/0
   ```

### Option B: Self-Hosted Redis (Docker)

1. **Add to docker-compose.yml**

```yaml
  redis:
    image: redis:7-alpine
    container_name: wisqu-redis
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - ./redis_data:/data
    restart: unless-stopped
    networks:
      - wisqu-network
```

2. **Start Redis**
   ```bash
   docker-compose up -d redis
   ```

3. **Configure**
   ```bash
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your-secure-password
   REDIS_URL=redis://:your-secure-password@localhost:6379/0
   ```

### Test Redis Connection

```bash
# Install redis-cli
sudo apt-get install redis-tools  # Ubuntu/Debian
brew install redis  # macOS

# Test connection
redis-cli -h your-redis-host -p 6379 -a your-password ping
# Should return: PONG
```

### Configure Rate Limiting

Update `/root/WisQu-v2/vgf345657yghjiu8y76t5r43wser/src/app/core/config.py`:

```python
# Add to Settings class
rate_limit_enabled: bool = Field(default=True)
rate_limit_per_minute: int = Field(default=60)
```

---

## 6. SMTP Email Configuration

### Option A: Gmail (Development/Small Scale)

1. **Enable 2-Factor Authentication**
   - Go to: https://myaccount.google.com/security
   - Enable 2FA

2. **Create App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "WisQu App"
   - Copy 16-character password

3. **Configure**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
   SMTP_FROM_EMAIL=noreply@wisqu.com
   SMTP_FROM_NAME="WisQu Support"
   SMTP_USE_TLS=true
   ```

### Option B: SendGrid (Recommended for Production)

1. **Sign up for SendGrid**
   - Visit: https://signup.sendgrid.com/
   - Free tier: 100 emails/day

2. **Create API Key**
   - Settings → API Keys
   - Create API Key with "Full Access"
   - Copy key (shown only once)

3. **Configure**
   ```bash
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   SMTP_FROM_EMAIL=noreply@wisqu.com
   SMTP_FROM_NAME="WisQu Support"
   SMTP_USE_TLS=true
   ```

4. **Verify Sender**
   - Settings → Sender Authentication
   - Verify your sending email address
   - Or set up domain authentication (recommended)

### Option C: Amazon SES (High Volume)

1. **Set up SES**
   - AWS Console → Amazon SES
   - Verify email address or domain
   - Create SMTP credentials

2. **Configure**
   ```bash
   SMTP_HOST=email-smtp.us-east-1.amazonaws.com
   SMTP_PORT=587
   SMTP_USER=AKIAXXXXXXXXXXXXXXXXX
   SMTP_PASSWORD=your-ses-smtp-password
   SMTP_FROM_EMAIL=noreply@wisqu.com
   SMTP_FROM_NAME="WisQu Support"
   SMTP_USE_TLS=true
   ```

### Test Email Configuration

Create script: `scripts/test_email.py`

```python
import asyncio
from app.services.email_service import EmailService
from app.core.config import get_settings

settings = get_settings()

async def test_email():
    """Test email configuration."""
    email_service = EmailService()

    try:
        # Send test email
        await email_service.send_email(
            to_email="your-test-email@example.com",
            subject="WisQu Email Test",
            html_content="<h1>Email Configuration Successful!</h1><p>Your SMTP settings are working correctly.</p>",
            text_content="Email Configuration Successful! Your SMTP settings are working correctly."
        )
        print("✅ Test email sent successfully!")
    except Exception as e:
        print(f"❌ Email test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())
```

Run: `poetry run python scripts/test_email.py`

---

## 7. Production Deployment Checklist

### Pre-Deployment

- [ ] All environment variables set in `.env.production`
- [ ] Database migrations applied
- [ ] Super admin user created
- [ ] Qdrant collection initialized
- [ ] Redis connection tested
- [ ] Email sending tested
- [ ] All API keys validated
- [ ] SSL certificates installed
- [ ] Domain DNS configured

### Database

- [ ] PostgreSQL production database created
- [ ] Database user with appropriate permissions
- [ ] Connection pooling configured (pool_size=20)
- [ ] Backup strategy in place
- [ ] Run: `alembic upgrade head`

### External Services

- [ ] Qdrant: Collection created and accessible
- [ ] Redis: Instance running and accessible
- [ ] OpenAI: API key active and tested
- [ ] Google/Gemini: API key active and tested
- [ ] Cohere: API key active (if using)
- [ ] SMTP: Email sending tested

### Security

- [ ] JWT secret key generated (32+ characters)
- [ ] All passwords changed from defaults
- [ ] CORS origins restricted to production domains
- [ ] Rate limiting enabled
- [ ] HTTPS enforced
- [ ] Security headers configured

### Testing

- [ ] Run full test suite: `poetry run pytest tests/ -v`
- [ ] Coverage report generated: `poetry run pytest tests/ --cov=src/app`
- [ ] All critical tests passing (auth, documents, tools)
- [ ] Health checks working: `curl https://your-domain.com/health`

### Monitoring

- [ ] Logging configured (production level)
- [ ] Error tracking setup (Sentry, Rollbar, etc.)
- [ ] Health check monitoring
- [ ] API usage tracking
- [ ] Database performance monitoring
- [ ] Cost alerts for external APIs

---

## 8. Monitoring & Health Checks

### Setup Health Check Monitoring

1. **Use Uptime Monitor**
   - UptimeRobot: https://uptimerobot.com/ (free)
   - Pingdom: https://www.pingdom.com/
   - StatusCake: https://www.statuscake.com/

2. **Configure Endpoints to Monitor**
   ```
   https://your-domain.com/health
   https://your-domain.com/health?check_services=true
   ```

3. **Alert Configuration**
   - Email: your-admin-email@example.com
   - Slack webhook (optional)
   - PagerDuty (for critical systems)

### Application Monitoring

1. **Error Tracking with Sentry**

```bash
# Install
poetry add sentry-sdk

# Configure in main.py
import sentry_sdk

if settings.environment == "production":
    sentry_sdk.init(
        dsn="https://xxxxx@xxxxx.ingest.sentry.io/xxxxx",
        environment=settings.environment,
        traces_sample_rate=0.1,
    )
```

2. **Application Performance Monitoring (APM)**

```bash
# New Relic
poetry add newrelic

# Or DataDog
poetry add ddtrace
```

### Log Aggregation

**Option A: ELK Stack (Self-hosted)**
- Elasticsearch + Logstash + Kibana
- Collect and visualize logs

**Option B: Cloud Services**
- Datadog: https://www.datadoghq.com/
- New Relic: https://newrelic.com/
- Logtail: https://logtail.com/

---

## Quick Start Script

Create `scripts/setup_production.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 WisQu Production Setup Script"
echo "=================================="

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ .env.production not found!"
    echo "Please copy .env.example to .env.production and configure it"
    exit 1
fi

# Load environment
export $(cat .env.production | grep -v '^#' | xargs)

echo "✅ Environment loaded"

# Database migrations
echo "📊 Running database migrations..."
alembic upgrade head

# Create super admin
echo "👤 Creating super admin..."
poetry run python scripts/create_super_admin.py

# Initialize Qdrant
echo "🔍 Initializing Qdrant collection..."
poetry run python scripts/init_qdrant.py

# Test Redis
echo "🔴 Testing Redis connection..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping

# Test email
echo "📧 Testing email configuration..."
poetry run python scripts/test_email.py

# Run tests
echo "🧪 Running test suite..."
poetry run pytest tests/ -v --maxfail=5

echo ""
echo "✅ Production setup complete!"
echo "=================================="
echo "Next steps:"
echo "1. Review all configurations"
echo "2. Test all endpoints manually"
echo "3. Deploy to production server"
echo "4. Set up monitoring and alerts"
echo "5. Monitor logs for any issues"
```

Make executable: `chmod +x scripts/setup_production.sh`

Run: `./scripts/setup_production.sh`

---

## Support & Troubleshooting

### Common Issues

**Issue: "Could not connect to database"**
- Check DB credentials in .env
- Verify database server is running
- Test connection: `psql -h $DB_HOST -U $DB_USER -d $DB_NAME`

**Issue: "Qdrant connection failed"**
- Check QDRANT_HOST and QDRANT_PORT
- Verify API key if using Qdrant Cloud
- Test: `curl http://$QDRANT_HOST:$QDRANT_PORT/collections`

**Issue: "Redis connection refused"**
- Check REDIS_HOST and REDIS_PORT
- Verify Redis is running: `docker ps | grep redis`
- Test: `redis-cli -h $REDIS_HOST ping`

**Issue: "Email not sending"**
- Check SMTP credentials
- Verify 2FA and app password (Gmail)
- Test with: `poetry run python scripts/test_email.py`

**Issue: "Invalid API key" for external services**
- Regenerate key from provider dashboard
- Update .env.production
- Restart application

### Getting Help

- **Documentation:** See TEST_SUITE_REPORT.md
- **Issues:** Create issue in GitHub repository
- **Logs:** Check `logs/` directory for error details
- **Health Check:** `curl https://your-domain.com/health?check_services=true`

---

## Congratulations! 🎉

You now have a complete configuration guide for achieving **100% production readiness**.

Follow this guide step by step, and you'll have:
- ✅ Secure admin authentication
- ✅ Fully configured vector search
- ✅ All external API integrations
- ✅ Rate limiting with Redis
- ✅ Email notifications working
- ✅ Production monitoring in place

**Your application is ready for deployment with 100% confidence!**
