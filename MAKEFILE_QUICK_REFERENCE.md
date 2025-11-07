# Makefile Quick Reference

## 📖 Overview

The Makefile now includes **100+ commands** organized into 13 categories, fully compatible with the latest codebase including Celery, Flower, pre-commit hooks, Black, isort, flake8, mypy, pylint, bandit, safety, detect-secrets, and all testing frameworks.

---

## 🚀 Quick Start Commands

```bash
# Complete setup for new developers
make setup

# Start development server
make dev

# Run all checks before commit
make quick-check

# Run full CI pipeline locally
make ci
```

---

## 📋 Command Categories

### 1. Setup & Installation (4 commands)

```bash
make install           # Install all dependencies
make install-dev       # Install dev dependencies
make install-hooks     # Install pre-commit hooks
make setup             # Complete setup (install + hooks + docker + migrations)
```

### 2. Development (3 commands)

```bash
make dev              # Start dev server with hot reload
make dev-docker       # Start docker services + dev server
make shell            # Open Python interactive shell
```

### 3. Celery & Background Tasks (5 commands)

```bash
make celery-worker         # Start Celery worker (4 concurrent workers)
make celery-beat           # Start Celery beat scheduler
make celery-worker-dev     # Celery worker with auto-reload
make flower                # Start Flower UI (http://localhost:5555)
make celery-purge          # Purge all tasks from queue (⚠️  dangerous)
```

### 4. Docker Operations (17 commands)

```bash
# Basic operations
make docker-up             # Start all services (PostgreSQL, Redis, Qdrant)
make docker-down           # Stop all services
make docker-restart        # Restart all services
make docker-build          # Build application Docker image
make docker-ps             # Check service status and health

# Logs
make docker-logs           # All service logs (follow mode)
make docker-logs-app       # Application logs only
make docker-logs-postgres  # PostgreSQL logs only
make docker-logs-redis     # Redis logs only
make docker-logs-qdrant    # Qdrant logs only

# Health & Maintenance
make docker-health         # Check health of all services
make docker-backup         # Backup all Docker volumes
make docker-clean          # Remove containers & images (preserve data)
make docker-clean-all      # Remove everything including data (⚠️  dangerous)
```

### 5. Database Operations (7 commands)

```bash
make db-migrate MESSAGE="description"  # Create new migration
make db-upgrade                        # Apply pending migrations
make db-downgrade                      # Rollback last migration
make db-reset                          # Reset database (⚠️  all data lost)
make db-shell                          # Open PostgreSQL shell
make db-dump                           # Create database dump
make db-restore FILE=backups/file.sql  # Restore from dump
```

### 6. Testing (10 commands)

```bash
# Run tests
make test              # All tests with coverage (unit + integration + e2e)
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-e2e          # End-to-end tests only

# Test modes
make test-watch        # Watch mode (re-run on changes)
make test-failed       # Re-run only failed tests
make test-verbose      # Verbose output with no capture
make test-markers      # Show available pytest markers

# Coverage
make coverage          # Generate and open HTML coverage report
make coverage-report   # Show coverage summary (no test run)
```

### 7. Code Quality & Linting (16 commands)

```bash
# Formatting
make format            # Format with Black + isort
make format-check      # Check formatting (no changes)

# Linting
make lint              # Run all linters (flake8 + mypy + pylint)
make lint-flake8       # Run flake8 only
make lint-mypy         # Run mypy only
make lint-pylint       # Run pylint only

# Security
make security          # All security checks (bandit + safety + secrets)
make security-bandit   # Run Bandit only
make security-safety   # Run Safety only
make security-secrets  # Scan for secrets only
make security-update-baseline  # Update secrets baseline

# Code Quality
make complexity        # Check code complexity (Radon)
make docstrings        # Check docstring coverage (interrogate)

# Pre-commit
make pre-commit-run    # Run all pre-commit hooks
make pre-commit-update # Update pre-commit hooks

# Combined checks
make check             # format + lint + security + test
make quality           # format-check + lint + complexity + docstrings
```

### 8. Cleaning (3 commands)

```bash
make clean         # Remove build artifacts and cache
make clean-all     # clean + docker-clean
make clean-pyc     # Remove Python bytecode files only
```

### 9. Production & Deployment (4 commands)

```bash
make build           # Build production Docker image
make deploy-staging  # Deploy to staging
make deploy-prod     # Deploy to production (with confirmation)
make run-prod        # Run production server (4 workers)
```

### 10. Monitoring & Observability (7 commands)

```bash
# UIs
make langfuse-ui     # Open Langfuse UI (http://localhost:3001)
make qdrant-ui       # Open Qdrant UI (http://localhost:6333/dashboard)
make flower-ui       # Open Flower UI (http://localhost:5555)

# Logs & Monitoring
make logs            # Show application logs
make redis-cli       # Open Redis CLI
make redis-monitor   # Monitor Redis commands in real-time
```

### 11. Documentation (3 commands)

```bash
make docs-serve      # Serve docs locally (http://localhost:8001)
make docs-build      # Build static documentation site
make docs-deploy     # Deploy to GitHub Pages
```

### 12. Utilities (10 commands)

```bash
# Environment
make env-example     # Create .env.example from .env

# Dependencies
make requirements     # Export requirements.txt
make requirements-dev # Export requirements-dev.txt (with dev)
make update          # Update all dependencies
make update-pre-commit  # Update pre-commit hooks

# Version management
make version              # Show current version
make version-bump-patch   # 1.0.0 -> 1.0.1
make version-bump-minor   # 1.0.0 -> 1.1.0
make version-bump-major   # 1.0.0 -> 2.0.0
```

### 13. CI/CD Simulation (2 commands)

```bash
make ci           # Full CI pipeline (format-check + lint + security + test)
make ci-quick     # Quick CI (format-check + flake8 + unit tests)
```

### 14. Development Workflows (4 commands)

```bash
make dev-setup     # Alias for setup
make dev-reset     # Complete reset (⚠️  deletes all data)
make quick-check   # format + flake8 + unit tests (before commit)
make full-check    # All checks (before push)
```

---

## 🎯 Common Workflows

### First Time Setup

```bash
# Clone repository
git clone <repository-url>
cd shia-islamic-chatbot

# Complete setup (installs deps, hooks, starts docker, runs migrations)
make setup

# Start development
make dev
```

### Daily Development

```bash
# Start Docker services
make docker-up

# Start dev server
make dev

# In another terminal: Start Celery worker
make celery-worker

# In another terminal: Start Flower for monitoring
make flower
```

### Before Committing

```bash
# Quick check (fast)
make quick-check

# Or full check (slower but comprehensive)
make full-check
```

### Before Pushing

```bash
# Run full CI pipeline locally
make ci
```

### Running Tests

```bash
# Run all tests
make test

# Run only unit tests (faster)
make test-unit

# Run tests in watch mode (during development)
make test-watch

# Re-run only failed tests
make test-failed
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Check security
make security

# Check code complexity
make complexity

# Check docstring coverage
make docstrings

# Run all quality checks
make quality
```

### Database Operations

```bash
# Create migration
make db-migrate MESSAGE="add user table"

# Apply migrations
make db-upgrade

# Access database shell
make db-shell

# Backup database
make db-dump

# Restore database
make db-restore FILE=backups/db_dump_20231107_120000.sql
```

### Monitoring

```bash
# Check Docker service health
make docker-health

# View logs
make docker-logs

# Open monitoring UIs
make qdrant-ui
make langfuse-ui
make flower-ui

# Monitor Redis
make redis-monitor
```

### Cleanup

```bash
# Clean Python artifacts
make clean

# Clean everything including Docker
make clean-all

# Nuclear option: reset everything (⚠️  deletes all data)
make dev-reset
```

---

## 🔧 Key Changes from Old Makefile

### Replaced Tools

| Old | New |
|-----|-----|
| `ruff format` | `black` + `isort` |
| `ruff check` | `flake8` + `mypy` + `pylint` |
| Security (placeholder) | `bandit` + `safety` + `detect-secrets` |

### New Directories

- `SRC_DIR=src/app` - Source code directory
- `TEST_DIR=tests` - Test directory

### Fixed Commands

- ✅ `dev`: Uses correct module path `src/app.main:app`
- ✅ `test-unit`: Uses `tests/unit/` directory
- ✅ `test-integration`: Uses `tests/integration/` directory
- ✅ `docker-up`: Shows service ports
- ✅ `docker-health`: Proper health checks for all services
- ✅ `security`: Actually runs security tools (was placeholder)

---

## 📊 Service Ports

| Service | Port | UI URL |
|---------|------|--------|
| PostgreSQL | 5433 | N/A |
| Redis | 6379 | N/A |
| Qdrant | 6333 | http://localhost:6333/dashboard |
| Application | 8000 | http://localhost:8000 |
| Langfuse | 3001 | http://localhost:3001 |
| Flower | 5555 | http://localhost:5555 |
| Docs | 8001 | http://localhost:8001 |

---

## ⚠️ Dangerous Commands (Use with Caution)

These commands will **delete data**:

- `make docker-clean-all` - Deletes all Docker volumes
- `make db-reset` - Drops and recreates database
- `make dev-reset` - Complete environment reset
- `make celery-purge` - Deletes all queued tasks

All dangerous commands require confirmation before execution.

---

## 🆘 Troubleshooting

### Docker services not starting

```bash
# Check service health
make docker-health

# View logs
make docker-logs

# Restart services
make docker-restart
```

### Tests failing

```bash
# Run verbose tests to see details
make test-verbose

# Re-run only failed tests
make test-failed
```

### Formatting issues

```bash
# Auto-fix formatting
make format

# Check what would change
make format-check
```

### Pre-commit hooks failing

```bash
# Run hooks manually
make pre-commit-run

# Update hooks
make pre-commit-update
```

---

## 📚 Additional Resources

- **Full Makefile**: See all commands with `make help`
- **Pre-commit Guide**: See `PRE_COMMIT_SETUP_GUIDE.md`
- **Quick Reference**: See `.pre-commit-quick-ref.md`
- **CI/CD Guide**: See `.github/workflows/OPTIMIZATION_GUIDE.md`

---

**Last Updated:** 2025-11-07
**Total Commands:** 100+
**Categories:** 13
