# Developer Guide

> Complete guide for developers contributing to Shia Islamic Chatbot

**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Development Workflow](#development-workflow)
3. [Code Standards](#code-standards)
4. [Testing](#testing)
5. [Makefile Commands](#makefile-commands)
6. [Pre-commit Hooks](#pre-commit-hooks)
7. [Contributing](#contributing)

---

## 🚀 Quick Start

### Get Started in 3 Steps

```bash
# 1. Setup (one-time)
git clone <repository-url>
cd shia-islamic-chatbot
make setup

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
make dev
```

**That's it!** App runs at http://localhost:8000 (Swagger: http://localhost:8000/docs)

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry
- Git

---

## 🔄 Development Workflow

### Daily Development

```bash
# Start infrastructure (PostgreSQL, Redis, Qdrant)
make docker-up

# Terminal 1: Run app with hot reload
make dev

# Terminal 2 (optional): Start Celery worker
make celery-worker

# Terminal 3 (optional): Start Flower (Celery monitoring)
make flower
```

### Architecture: Hybrid Approach

**Best Practice:** Docker for infrastructure, native Python for app

```
┌─────────────────────────────────────┐
│ Native Python (Hot Reload)          │
│  • FastAPI (port 8000)              │
│  • Celery Worker                    │
│  • Easy debugging                   │
└──────────────┬──────────────────────┘
               ↓ connects to
┌─────────────────────────────────────┐
│ Docker Containers (Infrastructure)  │
│  • PostgreSQL (port 5433)           │
│  • Redis (port 6379)                │
│  • Qdrant (port 6333)               │
└─────────────────────────────────────┘
```

**Why this approach?**
- ✅ Fast iteration with hot reload
- ✅ Easy debugging (attach debugger)
- ✅ No image rebuild for code changes
- ✅ Full IDE integration

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write code** following our [code standards](#code-standards)

3. **Add tests** for new functionality

4. **Test via Swagger UI**
   - Open http://localhost:8000/docs
   - Test your endpoints interactively

5. **Before committing**
   ```bash
   make quick-check  # Fast verification
   # or
   make ci          # Full CI pipeline
   ```

6. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: Add amazing feature"
   git push origin feature/your-feature-name
   ```

---

## 📏 Code Standards

### Python Style

We use **Black** (100 char line length) and follow PEP 8.

#### Type Hints (Required)

```python
# ✅ Good
def process_document(content: str, user_id: int) -> Document:
    ...

async def get_user(user_id: int) -> Optional[User]:
    ...

# ❌ Bad
def process_document(content, user_id):
    ...
```

#### Docstrings (Google Style)

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts.

    Args:
        text1: First text to compare
        text2: Second text to compare

    Returns:
        Similarity score between 0 and 1

    Raises:
        ValueError: If either text is empty

    Example:
        >>> calculate_similarity("hello", "hi")
        0.85
    """
    ...
```

#### Import Organization (isort)

```python
# Standard library
import os
from typing import Optional, List

# Third-party
from fastapi import FastAPI, Depends
from sqlalchemy import select

# Local
from app.models import User
from app.services import AuthService
```

#### Naming Conventions

```python
# Classes: PascalCase
class DocumentService:
    pass

# Functions/variables: snake_case
def get_user_by_id(user_id: int):
    user_data = fetch_from_db(user_id)
    return user_data

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private: prefix with underscore
def _internal_helper():
    pass
```

### Error Handling

```python
# ✅ Good - Specific exceptions
try:
    user = await get_user(user_id)
except UserNotFoundError:
    raise HTTPException(status_code=404, detail="User not found")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error")

# ❌ Bad - Bare except
try:
    user = await get_user(user_id)
except:
    pass
```

---

## 🧪 Testing

### Test Structure

```python
# tests/unit/test_document_service.py
import pytest
from unittest.mock import AsyncMock, patch

class TestDocumentService:
    """Test suite for DocumentService."""

    @pytest.fixture
    def document_service(self):
        """Fixture providing DocumentService instance."""
        return DocumentService()

    @pytest.mark.asyncio
    async def test_create_document_success(self, document_service):
        """Test successful document creation."""
        # Arrange
        title = "Test Document"
        content = "Test content"

        # Act
        result = await document_service.create_document(
            title=title,
            content=content
        )

        # Assert
        assert result.title == title
        assert result.content == content
```

### Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# Specific test file
poetry run pytest tests/unit/test_document_service.py

# Specific test
poetry run pytest tests/unit/test_document_service.py::TestDocumentService::test_create_document_success

# Coverage report
make coverage
```

### Test Requirements

- ✅ Minimum 75% code coverage
- ✅ All new features must include tests
- ✅ All bug fixes must include regression tests
- ✅ Test both success and failure cases
- ✅ Test edge cases

### Test Best Practices

**✅ DO:**
- Use descriptive test names
- Test one thing per test
- Use fixtures for common setup
- Mock external dependencies
- Keep tests fast

**❌ DON'T:**
- Test implementation details
- Write flaky tests
- Depend on test execution order
- Leave commented-out code
- Skip tests without good reason

---

## 🛠️ Makefile Commands

### Setup & Installation

```bash
make setup              # Complete project setup
make install            # Install dependencies
make install-dev        # Install with dev tools
make install-hooks      # Install pre-commit hooks
```

### Development

```bash
make dev                # Start development server (hot reload)
make shell              # Open Python shell with app context
make celery-worker      # Start Celery worker
make celery-beat        # Start Celery beat scheduler
make flower             # Start Flower (Celery monitoring)
```

### Docker Operations

```bash
make docker-up          # Start dev infrastructure (PostgreSQL, Redis, Qdrant)
make docker-up-full     # Start full stack (all 10 services + monitoring)
make docker-down        # Stop all Docker services
make docker-health      # Check health of all services
make docker-logs        # View logs from all services
make docker-logs-app    # View app logs only
make docker-build       # Build Docker image
```

### Database Operations

```bash
make db-migrate MESSAGE="description"  # Create new migration
make db-upgrade         # Apply pending migrations
make db-downgrade       # Rollback last migration
make db-reset           # Reset database (downgrade all + upgrade all)
make db-shell           # Open PostgreSQL shell
make db-dump            # Create database backup
make db-restore FILE=backups/db_dump_*.sql  # Restore from backup
```

### Testing

```bash
make test               # Run all tests with coverage
make test-unit          # Run unit tests only
make test-integration   # Run integration tests only
make test-e2e           # Run end-to-end tests only
make test-watch         # Run tests in watch mode
make test-failed        # Re-run only failed tests
make coverage           # Generate and open coverage report
```

### Code Quality

```bash
make format             # Format code (Black + isort)
make format-check       # Check formatting without changes
make lint               # Run linters (flake8, mypy, pylint)
make type-check         # Run mypy type checking
make complexity         # Check code complexity (radon)
make docstring-check    # Check docstring coverage (interrogate)
```

### Security

```bash
make security           # Run security scans (Bandit + Safety)
make bandit             # Run Bandit security scanner
make safety             # Check dependency vulnerabilities
make detect-secrets     # Scan for secrets in code
```

### Pre-commit Hooks

```bash
make pre-commit-install  # Install pre-commit hooks
make pre-commit-run      # Run all hooks manually
make pre-commit-update   # Update hook versions
```

### Verification & CI

```bash
make quick-check        # Fast verification (format, lint, tests)
make ci                 # Full CI pipeline (all checks)
make verify-build       # Comprehensive pre-build verification
make test-local         # Test API endpoints locally
```

### Documentation

```bash
make docs-serve         # Serve documentation locally
make docs-build         # Build documentation
```

### Cleanup

```bash
make clean              # Remove build artifacts and caches
make docker-clean       # Remove Docker containers/images (keep volumes)
make docker-clean-all   # Remove everything including volumes (⚠️ deletes data)
```

### Help

```bash
make help               # Show all available commands
```

---

## 🎯 Pre-commit Hooks

### What Are Pre-commit Hooks?

Automated checks that run **before every commit** to ensure code quality.

### Installation

```bash
# Installed automatically by 'make setup'
# Or manually:
make install-hooks
```

### Hooks That Run

**Code Formatting:**
- ✅ Black (code formatting)
- ✅ isort (import sorting)
- ✅ Trailing whitespace removal
- ✅ End of file fixer

**Code Quality:**
- ✅ flake8 (linting)
- ✅ mypy (type checking)
- ✅ pylint (advanced linting)

**Security:**
- ✅ Bandit (security issues)
- ✅ detect-secrets (secret scanning)
- ✅ Safety (dependency vulnerabilities)

**Other:**
- ✅ YAML/TOML/JSON validation
- ✅ Large file prevention
- ✅ Commit message validation

### Usage

Hooks run automatically when you commit:

```bash
git commit -m "feat: Add feature"
# Hooks run automatically...
```

### Manual Execution

```bash
# Run all hooks manually
make pre-commit-run

# Run on specific files
poetry run pre-commit run --files src/app/models.py

# Skip hooks (emergency only!)
git commit --no-verify
```

### Updating Hooks

```bash
make pre-commit-update
```

---

## 🤝 Contributing

### Code of Conduct

- ✅ Be respectful and inclusive
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the project
- ❌ No harassment or discriminatory language
- ❌ No trolling or personal attacks

### Pull Request Process

#### 1. Before Creating PR

```bash
# Sync with upstream
git fetch upstream
git rebase upstream/main

# Run all checks
make ci

# Verify build
make verify-build
```

#### 2. PR Title

Use conventional commit format:

```
feat: Add document semantic search
fix: Resolve authentication timeout
docs: Update deployment guide
```

#### 3. PR Description

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing via Swagger UI

## Checklist
- [ ] Code follows project style
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
```

#### 4. Review Process

1. **Automated Checks** - CI/CD must pass
2. **Code Review** - At least one approval required
3. **Merge** - Squash and merge preferred

### Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting)
- `refactor` - Code restructuring
- `test` - Add/update tests
- `chore` - Maintenance tasks
- `perf` - Performance improvement
- `ci` - CI/CD changes

**Examples:**

```bash
feat: Add semantic search for documents

Implement semantic search using Qdrant vector database.
Supports filtering by category, language, and date.

Closes #123
```

```bash
fix: Prevent duplicate user registration

Add unique constraint on email field and handle
IntegrityError with appropriate error message.

Fixes #456
```

---

## 📝 Documentation Requirements

### When to Update Docs

- ✅ Adding new features
- ✅ Changing API endpoints
- ✅ Modifying configuration
- ✅ Adding environment variables
- ✅ Changing deployment process

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `DEVELOPER_GUIDE.md` | This file - complete dev guide |
| `OPERATIONS_GUIDE.md` | Deployment and operations |

### API Documentation

- Update docstrings in route handlers
- Use Pydantic models for schemas
- Swagger UI auto-generates from code

---

## ❓ Getting Help

- **General questions:** GitHub Discussions
- **Bug reports:** GitHub Issues
- **Feature requests:** GitHub Discussions

---

## 🎯 Quick Reference

### First Time Setup

```bash
git clone <repository-url>
cd shia-islamic-chatbot
make setup
cp .env.example .env
make dev
```

### Daily Workflow

```bash
make docker-up      # Start infrastructure
make dev            # Start app
# Code, test via Swagger UI
make quick-check    # Before committing
git commit          # Pre-commit hooks run automatically
```

### Before PR

```bash
make ci             # Full verification
make verify-build   # Comprehensive checks
```

---

**Version:** 1.0.0
**Last Updated:** November 2025
