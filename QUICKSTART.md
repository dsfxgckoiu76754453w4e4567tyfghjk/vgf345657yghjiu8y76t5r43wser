# Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry 1.8.0+

## Installation (5 minutes)

```bash
# 1. Install dependencies
make install
# OR: poetry install

# 2. Copy environment file
cp .env.example .env

# 3. Start infrastructure services
make docker-up
# OR: docker-compose up -d

# 4. Wait for services to start (30 seconds)
sleep 30

# 5. Run database migrations
make db-upgrade
# OR: poetry run alembic upgrade head

# 6. Start the application
make dev
# OR: poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Quick Setup (All-in-One)**:
```bash
make setup  # Installs dependencies, starts Docker, and runs migrations
make dev    # Start development server
```

## Verify

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## Useful Commands

```bash
# View all available make commands
make help

# Run tests
make test

# Format and lint code
make format
make lint

# Database operations
make db-migrate MESSAGE="add new table"
make db-downgrade

# Docker operations
make docker-down    # Stop services
make docker-restart # Restart services
make docker-logs    # View logs

# Clean up
make clean          # Remove cache files
make clean-all      # Remove cache + Docker resources
```

## Next Steps

1. Read [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for complete details
2. Review [docs/implementation/](docs/implementation/) for architecture and modules
3. Start implementing Phase 1 remaining tasks

## Project Status

**Phase 1 (Foundation)**: 40% Complete

### ✅ Completed
- Project structure
- Docker setup
- Core configuration
- Database models (users, auth, sessions)
- Alembic migrations
- FastAPI skeleton

### 🚧 Next Tasks
- Authentication system (JWT, OAuth, OTP)
- Remaining database models (30+ tables)
- API endpoints
- Rate limiting

**Timeline**: 11-15 weeks remaining

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed roadmap.

---

## 🔧 Development Notes

### Important: Dependency Lock File Tracking

**Current Setup (Development Phase):**
- `poetry.lock` is currently **tracked in git** to ensure exact dependency versions across development machines
- This helps maintain consistency during active development and troubleshooting

**⚠️ TODO Before Production:**
```bash
# Uncomment this line in .gitignore before production deployment:
# poetry.lock
```

**Why this change is temporary:**
1. **Development Phase**: Tracking `poetry.lock` ensures all developers use identical package versions
2. **Production Phase**: Libraries should manage their own dependencies, allowing users to get compatible versions
3. **Best Practice**: Applications track `poetry.lock`, libraries don't

**Checklist for Production:**
- [ ] Uncomment `poetry.lock` in `.gitignore`
- [ ] Remove `poetry.lock` from git: `git rm --cached poetry.lock`
- [ ] Commit the change: `git commit -m "Remove poetry.lock tracking for production"`
- [ ] Update this note in QUICKSTART.md

---

## 📋 Development Roadmap

See the complete implementation plan in [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) and phase-specific guides:
- [PHASE2_GUIDE.md](PHASE2_GUIDE.md) - Authentication & Authorization
- [PHASE3_GUIDE.md](PHASE3_GUIDE.md) - Core RAG System
- [PHASE4_GUIDE.md](PHASE4_GUIDE.md) - Advanced Features
- [PHASE5_GUIDE.md](PHASE5_GUIDE.md) - Production Deployment
- [PHASE6_GUIDE.md](PHASE6_GUIDE.md) - Monitoring & Optimization
