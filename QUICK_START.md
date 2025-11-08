# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup (One-time)

```bash
# Clone and setup
git clone <repository-url>
cd shia-islamic-chatbot
make setup
```

This will:
- ✅ Install all dependencies
- ✅ Install pre-commit hooks
- ✅ Start Docker services (PostgreSQL, Redis, Qdrant)
- ✅ Run database migrations

### Step 2: Configure Environment

```bash
# Create .env from example
cp .env.example .env

# Edit with your API keys
nano .env
```

**Minimum required:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/shia_chatbot
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
SECRET_KEY=<generate-with-command-below>

# Generate secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Run & Test

```bash
# Terminal 1: Start app
make dev

# App runs at: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

**Test via Swagger UI:**
1. Open http://localhost:8000/docs
2. Try "GET /health" endpoint
3. Test other endpoints

---

## 📋 Daily Development Workflow

```bash
# Morning: Start everything
make docker-up              # Start infrastructure
make dev                    # Start app (Terminal 1)
make celery-worker          # Start background tasks (Terminal 2, optional)

# Develop & test
# - Code with hot reload
# - Test via Swagger: http://localhost:8000/docs
# - Check logs in terminal

# Before commit
make quick-check            # format + lint + tests

# Evening: Stop (or leave running)
# Ctrl+C to stop dev server
make docker-down            # Stop infrastructure (optional)
```

---

## 🧪 Testing Your Changes

### Option 1: Automated Endpoint Testing

```bash
# Terminal 1: App must be running (make dev)

# Terminal 2: Run automated tests
make test-local
```

**Tests 8 critical endpoints:**
- Health check
- Swagger UI access
- User registration
- User login
- Authentication
- Chat endpoint (if available)
- Document upload (if available)
- Qdrant status

### Option 2: Manual Testing via Swagger

```bash
# 1. Start app
make dev

# 2. Open Swagger UI
open http://localhost:8000/docs

# 3. Test endpoints interactively
# - Click endpoint → "Try it out" → Fill data → "Execute"
# - For authenticated endpoints: Click "Authorize" → Enter token
```

### Option 3: Run Full Test Suite

```bash
# All tests
make test

# Just unit tests (fast)
make test-unit

# Just integration tests
make test-integration

# View coverage
make coverage
```

---

## 🔍 Before Building Docker Image

**Best Practice: Always verify before building!**

```bash
# Comprehensive verification (recommended)
make verify-build
```

**This checks 20+ items:**
- ✅ Code formatting (Black, isort)
- ✅ Linting (flake8, mypy, pylint)
- ✅ Security (bandit, safety, detect-secrets)
- ✅ Tests (unit, integration, coverage)
- ✅ Database migrations
- ✅ Application health
- ✅ Swagger UI accessibility
- ✅ Docker services running

**If all checks pass:**
```bash
make build
```

---

## 🎯 Quick Commands Reference

### Development

| Command | Description |
|---------|-------------|
| `make dev` | Start development server (hot reload) |
| `make docker-up` | Start PostgreSQL, Redis, Qdrant |
| `make docker-health` | Check service health |
| `make celery-worker` | Start background task worker |
| `make flower` | Start Celery monitoring UI |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run all tests with coverage |
| `make test-unit` | Run unit tests only (fast) |
| `make test-local` | Test API endpoints locally |
| `make verify-build` | Comprehensive pre-build check |

### Code Quality

| Command | Description |
|---------|-------------|
| `make format` | Auto-format code (Black + isort) |
| `make lint` | Run all linters |
| `make security` | Run security checks |
| `make quick-check` | Fast check before commit |
| `make ci` | Full CI pipeline locally |

### Database

| Command | Description |
|---------|-------------|
| `make db-shell` | Open PostgreSQL shell |
| `make db-migrate MESSAGE="..."` | Create migration |
| `make db-upgrade` | Apply migrations |
| `make db-dump` | Backup database |

### Build & Deploy

| Command | Description |
|---------|-------------|
| `make verify-build` | Verify before building (recommended) |
| `make build` | Build Docker image |
| `make deploy-staging` | Deploy to staging |

---

## 🌐 Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| **FastAPI App** | http://localhost:8000 | Main application |
| **Swagger UI** | http://localhost:8000/docs | Interactive API docs |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Health Check** | http://localhost:8000/health | Application health |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector database UI |
| **Flower** | http://localhost:5555 | Celery monitoring (when running) |

**Database ports:**
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`
- Qdrant: `localhost:6333`

---

## 🐛 Common Issues

### "Application not starting"

```bash
# Check Docker services
make docker-health

# Restart services
make docker-restart

# Check .env configuration
cat .env
```

### "Tests failing"

```bash
# Make sure services are running
make docker-up

# Reinstall dependencies
poetry install --with dev

# Run verbose tests
make test-verbose
```

### "Port already in use"

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### "Module not found"

```bash
# Verify virtual environment
poetry env info

# Reinstall
poetry install --with dev
```

---

## 📚 Complete Documentation

- **Full Guide:** `LOCAL_DEVELOPMENT_GUIDE.md`
- **Makefile Commands:** `MAKEFILE_QUICK_REFERENCE.md`
- **Pre-commit Hooks:** `PRE_COMMIT_SETUP_GUIDE.md`
- **CI/CD Pipeline:** `.github/workflows/OPTIMIZATION_GUIDE.md`

---

## 🎓 Best Practices

✅ **DO:**
- Use `make verify-build` before building Docker images
- Test via Swagger UI before committing
- Run `make quick-check` before committing
- Keep .env file secure (never commit)
- Use Docker for infrastructure (PostgreSQL, Redis, Qdrant)
- Run app natively for development (hot reload, debugging)

❌ **DON'T:**
- Build Docker image for every code change
- Skip tests before building
- Commit .env or secrets
- Run app in Docker during development
- Deploy without testing first

---

## 🆘 Need Help?

1. **Check health:** `make docker-health`
2. **View logs:** `make docker-logs`
3. **Read full guide:** `LOCAL_DEVELOPMENT_GUIDE.md`
4. **Run verification:** `make verify-build`

---

**Happy Coding! 🚀**
