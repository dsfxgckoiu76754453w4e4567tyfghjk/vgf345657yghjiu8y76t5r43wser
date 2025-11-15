# CLAUDE.md - AI Assistant Guide for WisQu Islamic Chatbot

**Last Updated**: 2025-01-13

---

## ⚠️ CRITICAL VPS WARNING

**EXTREMELY IMPORTANT**: This VPS hosts multiple production containers with real users in continuous operation. Be VERY careful about ALL Docker and system operations!

**NEVER run these commands:**
- `docker system prune -a` - Deletes ALL containers (including production!)
- `docker volume prune` - Deletes ALL volumes (data loss!)
- `docker stop $(docker ps -q)` - Stops ALL containers (breaks production!)
- `docker rm -f $(docker ps -aq)` - Removes ALL containers!
- Any command that affects containers outside this project's namespace

**ALWAYS use specific container names:**
- `docker logs shia-chatbot-dev-app` ✅
- `docker restart shia-chatbot-stage-app` ✅
- `docker compose -f docker-compose.app.dev.yml down` ✅

---

## 📋 Project Overview

**WisQu Islamic Chatbot** is a production-grade comprehensive Shia Islamic knowledge chatbot using RAG (Retrieval Augmented Generation) technology.

### Key Characteristics
- **Language**: Python 3.11
- **Framework**: FastAPI with async/await
- **Architecture**: Clean architecture with layered separation
- **Deployment**: Multi-environment Docker setup (LOCAL, DEV, STAGE, PROD)
- **AI Stack**: LangChain + LangGraph with multi-provider LLM support
- **Primary LLM**: OpenRouter (unified access to 100+ models)
- **Vector Database**: Qdrant for semantic search
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis with multiple DB isolation
- **Workflows**: Temporal for async task orchestration
- **Storage**: MinIO for object storage

---

## 🏗️ Architecture Overview

### Multi-Environment Isolation

All 4 environments run on the **SAME VPS** with complete isolation:

| Environment | Port | Database | Redis DB | Qdrant Prefix | MinIO Prefix | Temporal Queue |
|-------------|------|----------|----------|---------------|--------------|----------------|
| **LOCAL** (Dev) | 8003 | `shia_chatbot_local` | 0 | `local_` | `local-` | `wisqu-local-queue` |
| **DEV** (Team) | 8000 | `shia_chatbot_dev` | 1 | `dev_` | `dev-` | `wisqu-dev-queue` |
| **STAGE** | 8001 | `shia_chatbot_stage` | 2 | `stage_` | `stage-` | `wisqu-stage-queue` |
| **PROD** | 8002 | `shia_chatbot_prod` | 3 | `prod_` | `prod-` | `wisqu-prod-queue` |

**Auto-Configuration (Zero Manual Config):**

All environment-specific values are **automatically computed** from the `ENVIRONMENT` variable:
- Just set `ENVIRONMENT=local|dev|stage|prod`
- Database name, Redis DB, Temporal queue, Qdrant prefix, and MinIO prefix are auto-computed
- **No manual configuration needed** - eliminates human error

Example `.env` (simplified):
```bash
ENVIRONMENT=local  # Change this to switch environments

# Base values (environment auto-appended)
DATABASE_NAME=shia_chatbot  # → shia_chatbot_local
REDIS_HOST=localhost
REDIS_PORT=6379
# REDIS_DB auto-selected: 0 (local), 1 (dev), 2 (stage), 3 (prod)

TEMPORAL_TASK_QUEUE=wisqu-queue  # → wisqu-local-queue
# QDRANT_COLLECTION_PREFIX auto-computed: local_
# MINIO_BUCKET_PREFIX auto-computed: local-
```

### AI Architecture

**2-Stage Retrieval Pipeline** (20-40% quality improvement):
1. **Stage 1**: Vector search (Qdrant) retrieves top N candidates (e.g., 50)
2. **Stage 2**: Reranker (Cohere) refines to top K results (e.g., 10)

**Multi-Provider LLM Strategy**:
- **Primary**: OpenRouter (unified access to 100+ models)
- **Fallbacks**: Automatic routing if primary fails
- **Supported**: Claude (Anthropic), GPT (OpenAI), Gemini (Google), Cohere, and more

---

## 📁 Project Structure

```
.
├── src/app/                    # Main application code
│   ├── api/                    # API layer
│   │   └── v1/                 # API v1 endpoints
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── chat.py         # Chat endpoints
│   │       ├── conversations.py # Conversation management
│   │       ├── documents.py    # Document upload/management
│   │       ├── admin.py        # Admin endpoints
│   │       ├── health.py       # Health check endpoint
│   │       └── ...             # Other endpoints
│   ├── core/                   # Core application logic
│   │   ├── config.py           # Configuration management (Pydantic Settings)
│   │   ├── constants.py        # Application constants
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   ├── security.py         # Security utilities (JWT, passwords)
│   │   ├── logging.py          # Structured logging setup
│   │   ├── metrics.py          # Prometheus metrics
│   │   ├── langfuse_client.py  # LLM observability
│   │   └── temporal_client.py  # Temporal workflow client
│   ├── db/                     # Database layer
│   │   ├── base.py             # SQLAlchemy base and session
│   │   └── __init__.py
│   ├── middleware/             # FastAPI middleware
│   │   ├── security.py         # Security middleware
│   │   └── usage_tracking.py   # Usage tracking
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py             # User model
│   │   ├── conversation.py     # Conversation model
│   │   ├── document.py         # Document model
│   │   └── ...
│   ├── repositories/           # Data access layer (Repository pattern)
│   │   ├── user_repository.py
│   │   ├── conversation_repository.py
│   │   └── ...
│   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── auth.py
│   │   └── ...
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── chat_service.py     # Chat logic
│   │   ├── document_service.py # Document processing
│   │   ├── qdrant_service.py   # Vector database service
│   │   ├── openrouter_service.py # LLM service
│   │   ├── embeddings_service.py # Embedding generation
│   │   └── ...
│   ├── tools/                  # LangChain tools
│   │   ├── web_search.py       # Web search tool
│   │   ├── ahkam_tool.py       # Islamic rulings tool
│   │   └── ...
│   ├── workflows/              # Temporal workflows
│   │   └── ...
│   ├── utils/                  # Utility functions
│   │   └── ...
│   ├── templates/              # Email templates
│   │   └── ...
│   └── main.py                 # FastAPI application entry point
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   │   ├── test_auth_service.py
│   │   ├── test_chat_service.py
│   │   └── ...
│   └── integration/            # Integration tests (if any)
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic configuration
├── scripts/                    # Utility scripts
├── grafana/                    # Grafana dashboards
├── nginx/                      # Nginx configuration
├── docker-compose.base.yml     # Infrastructure services
├── docker-compose.app.dev.yml  # DEV environment
├── docker-compose.app.stage.yml # STAGE environment
├── docker-compose.app.prod.yml # PROD environment
├── Dockerfile                  # Application Docker image
├── Makefile                    # Development commands
├── pyproject.toml              # uv dependencies & tool configs
├── alembic.ini                 # Alembic configuration
├── .env.example                # Environment variables template
├── .pre-commit-config.yaml     # Pre-commit hooks
├── TECH_STACK.md               # Technology stack documentation
├── VPS_DEPLOYMENT.md           # Deployment guide
└── openapi.json                # API specification
```

---

## 🔧 Development Workflow

### Initial Setup

```bash
# 1. Install dependencies
make install-dev

# 2. Install pre-commit hooks
make install-hooks

# 3. Start infrastructure services (PostgreSQL, Redis, Qdrant, MinIO, etc.)
make docker-local

# 4. Set ENVIRONMENT variable (all other env-specific values auto-computed)
export ENVIRONMENT=local
# Note: DATABASE_NAME, REDIS_DB, TEMPORAL_TASK_QUEUE, QDRANT_COLLECTION_PREFIX,
#       and MINIO_BUCKET_PREFIX are automatically computed based on ENVIRONMENT

# 5. Run database migrations
uv run alembic upgrade head

# 6. Start development server
make dev
# or
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

### Environment Promotion Flow

```
LOCAL (you) → test locally
    ↓ (git push)
DEV (team) → frontend + QA test
    ↓ (git tag v1.0.0-rc1)
STAGE (beta) → internal team + beta users
    ↓ (git tag v1.0.0)
PROD (live) → all real users
```

### Development Commands (Makefile)

```bash
make help              # Show all available commands
make install          # Install dependencies
make install-dev      # Install dev dependencies
make install-hooks    # Install pre-commit hooks
make dev              # Start development server with hot reload
make test             # Run tests with coverage
make test-local       # Run tests locally (no Docker)
make lint             # Run all linters
make format           # Format code (black + isort)
make security         # Run security checks
make docker-local     # Start infrastructure services only
make db-migrate       # Create new migration
make db-upgrade       # Run migrations
make temporal-ui      # Open Temporal UI
make minio-ui         # Open MinIO console
```

---

## 📝 Code Conventions

### Code Style

- **Formatter**: Black (line length: 100)
- **Import Sorter**: isort (black profile)
- **Linter**: Ruff (fast Python linter)
- **Type Checker**: MyPy (strict mode)
- **Line Length**: 100 characters

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Import Order (isort)

1. Future imports
2. Standard library
3. Third-party packages
4. First-party (app)
5. Local folder

Example:
```python
from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

from .schemas import UserCreate
```

### Async Best Practices

- **Always use async/await** for I/O operations
- Use `asyncpg` for PostgreSQL (not psycopg2)
- Use `httpx` for HTTP requests (not requests)
- Use `aioredis` for Redis operations

### Type Hints

- **Required**: All function signatures must have type hints
- Use `typing` module for complex types
- MyPy checks are enabled in pre-commit hooks

Example:
```python
async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    """Get user by email address."""
    ...
```

### Docstrings

- **Required**: All public functions, classes, and methods
- **Style**: Google-style docstrings
- **Minimum**: 80% coverage (enforced by interrogate)

Example:
```python
def process_document(
    file_path: str,
    chunk_size: int = 512,
) -> list[str]:
    """
    Process a document and split into chunks.

    Args:
        file_path: Path to the document file.
        chunk_size: Size of each chunk in tokens.

    Returns:
        List of text chunks.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If chunk_size is invalid.
    """
    ...
```

### Error Handling

- Use custom exceptions (define in `app/core/exceptions.py`)
- Always log errors with structured logging
- Return proper HTTP status codes
- Include error details in development, hide in production

Example:
```python
from app.core.logging import get_logger
from app.core.exceptions import DocumentNotFoundError

logger = get_logger(__name__)

async def get_document(document_id: str) -> Document:
    try:
        document = await repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document {document_id} not found")
        return document
    except Exception as e:
        logger.error("get_document_failed", document_id=document_id, error=str(e))
        raise
```

### Logging

- Use **structlog** for structured JSON logging
- Include context in all log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Never log sensitive data (passwords, tokens, etc.)

Example:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Good
logger.info(
    "user_login_success",
    user_id=user.id,
    email=user.email,
    ip_address=request.client.host,
)

# Bad
logger.info(f"User {user.email} logged in")  # Unstructured
logger.info("login", password=password)  # Logs sensitive data!
```

---

## 🧪 Testing

### Testing Stack

- **Framework**: Pytest
- **Async Support**: pytest-asyncio
- **Coverage**: pytest-cov (minimum 80%)
- **Fixtures**: factory-boy + faker
- **Mocking**: pytest-mock

### Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests (fast, isolated)
│   ├── test_auth_service.py
│   ├── test_chat_service.py
│   └── ...
└── integration/          # Integration tests (slower, with DB/external services)
    └── ...
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
uv run pytest tests/unit/test_auth_service.py

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html
```

### Writing Tests

- **Naming**: `test_<function_name>_<scenario>`
- **AAA Pattern**: Arrange, Act, Assert
- **One assertion per test** (preferably)
- **Use fixtures** for common setup

Example:
```python
import pytest
from app.services.auth_service import AuthService

@pytest.mark.asyncio
async def test_authenticate_user_success(db_session, user_factory):
    """Test successful user authentication."""
    # Arrange
    user = await user_factory(email="test@example.com", password="password123")
    auth_service = AuthService(db_session)

    # Act
    result = await auth_service.authenticate(
        email="test@example.com",
        password="password123",
    )

    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.email == user.email
```

---

## 🚀 Deployment

### Deployment Files

- `docker-compose.base.yml`: Infrastructure services (PostgreSQL, Redis, Qdrant, MinIO, etc.)
- `docker-compose.app.dev.yml`: DEV environment
- `docker-compose.app.stage.yml`: STAGE environment
- `docker-compose.app.prod.yml`: PROD environment

### Deploy to Environment

```bash
# Start infrastructure (if not running)
docker compose -f docker-compose.base.yml up -d

# Deploy to DEV
docker compose -f docker-compose.base.yml -f docker-compose.app.dev.yml up -d --build

# Deploy to STAGE
docker compose -f docker-compose.base.yml -f docker-compose.app.stage.yml up -d --build

# Deploy to PROD
docker compose -f docker-compose.base.yml -f docker-compose.app.prod.yml up -d --build
```

### Database Migrations

```bash
# Create new migration (LOCAL)
export ENVIRONMENT=local  # Database name auto-computed as shia_chatbot_local
uv run alembic revision --autogenerate -m "add new table"

# Run migrations (LOCAL)
uv run alembic upgrade head

# Run migrations (DEV - deployed)
docker exec shia-chatbot-dev-app alembic upgrade head

# Run migrations (STAGE)
docker exec shia-chatbot-stage-app alembic upgrade head

# Run migrations (PROD)
docker exec shia-chatbot-prod-app alembic upgrade head
```

---

## 🔑 Key Technologies

### Core Framework
- **FastAPI**: Modern async web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation (v2.x)

### AI & LLM
- **OpenRouter**: Primary LLM provider (100+ models)
- **LangChain**: LLM orchestration framework
- **LangGraph**: Multi-agent workflows
- **Langfuse**: LLM observability & tracing

### AI Components
- **Cohere Rerank**: 2-stage retrieval reranking
- **Gemini Embeddings**: Text-to-vector (3072 dimensions)
- **mem0ai**: Conversation memory
- **NeMo Guardrails**: Content safety & filtering
- **Chonkie**: Semantic text chunking

### Database & Storage
- **PostgreSQL**: Primary database
- **SQLAlchemy**: ORM (async)
- **Alembic**: Database migrations
- **Redis**: Caching & sessions
- **Qdrant**: Vector database
- **MinIO**: Object storage

### Workflow & Tasks
- **Temporal**: Async workflow orchestration (replaces Celery)

### Observability
- **Structlog**: Structured JSON logging
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Langfuse**: LLM-specific tracing

### Development Tools
- **uv**: Blazing-fast dependency management
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **isort**: Import sorter
- **MyPy**: Static type checker
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks
- **Bandit**: Security scanner
- **detect-secrets**: Secret detection

---

## 📚 Important Files

### Configuration
- `.env.example`: Environment variables template (311 lines, comprehensive)
- `pyproject.toml`: uv dependencies + tool configurations
- `alembic.ini`: Database migration configuration
- `.pre-commit-config.yaml`: Pre-commit hooks configuration

### Documentation
- `TECH_STACK.md`: Complete technology stack overview
- `VPS_DEPLOYMENT.md`: Deployment guide (257 lines)
- `openapi.json`: Auto-generated OpenAPI 3.1.0 specification
- `Makefile`: Development commands reference (500+ lines)

### Application Entry Point
- `src/app/main.py`: FastAPI application initialization

### Core Configuration
- `src/app/core/config.py`: Pydantic Settings configuration
- `src/app/core/constants.py`: Application constants
- `src/app/core/logging.py`: Structured logging setup

---

## 💡 Tips for AI Assistants

### When Making Changes

1. **Always read existing code first** before making changes
2. **Follow existing patterns** - this codebase has established conventions
3. **Run pre-commit hooks** - they will auto-format and check your code
4. **Update tests** - all changes should have corresponding tests
5. **Check type hints** - MyPy will fail if types are incorrect
6. **Use structured logging** - never use print statements
7. **Handle errors properly** - use custom exceptions and log errors

### When Adding New Features

1. **Check `TECH_STACK.md`** for approved technologies
2. **Use existing services** - don't reinvent the wheel
3. **Follow layered architecture**:
   - API layer (`api/v1/`) → handles HTTP
   - Service layer (`services/`) → business logic
   - Repository layer (`repositories/`) → data access
   - Model layer (`models/`) → ORM models
   - Schema layer (`schemas/`) → Pydantic validation
4. **Add to appropriate layer** - don't mix concerns
5. **Create migrations** if database changes are needed
6. **Update OpenAPI spec** - FastAPI auto-generates it

### When Fixing Bugs

1. **Write a failing test first** (TDD)
2. **Fix the bug**
3. **Ensure test passes**
4. **Add logging** if error handling improved
5. **Check related code** - similar bugs might exist elsewhere

### When Refactoring

1. **Ensure tests pass before starting**
2. **Make small, incremental changes**
3. **Run tests after each change**
4. **Don't change behavior** - only structure
5. **Update documentation** if public APIs change

### Common Gotchas

1. **Environment variables**: Always check `.env.example` for available vars
2. **Database isolation**: Each environment has its own database
3. **Redis DB numbers**: Different for each environment (0,1,2,3)
4. **Qdrant collections**: Prefixed by environment (dev_, stage_, prod_, local_)
5. **MinIO buckets**: Prefixed by environment
6. **Temporal queues**: Different queue per environment
7. **Docker containers**: NEVER use destructive commands (see VPS warning)
8. **Port conflicts**: Each environment uses different ports
9. **Async/await**: Always use async for I/O operations
10. **Type hints**: Required for all function signatures

### Code Quality Checklist

Before committing, ensure:
- [ ] Code follows Black formatting (100 char line length)
- [ ] Imports sorted with isort
- [ ] Type hints added for all functions
- [ ] Docstrings added (Google style)
- [ ] Tests written and passing
- [ ] No linting errors (Ruff)
- [ ] No type errors (MyPy)
- [ ] No security issues (Bandit)
- [ ] No secrets committed (detect-secrets)
- [ ] Structured logging used (not print)
- [ ] Error handling implemented
- [ ] Pre-commit hooks pass

### Pre-commit Hooks

The following checks run automatically on commit:
- File checks (large files, merge conflicts, etc.)
- Python syntax validation
- JSON/YAML/TOML validation
- Code formatting (Black, isort)
- Linting (Ruff, Flake8)
- Type checking (MyPy)
- Security scanning (Bandit, detect-secrets)
- Docstring checks
- Trailing whitespace removal
- End-of-file fixer

### Useful Commands Reference

```bash
# Development
make dev                          # Start dev server
make shell                        # Open Python shell

# Testing
make test                         # Run all tests
uv run pytest -k test_name    # Run specific test
uv run pytest --lf            # Run last failed tests

# Code Quality
make lint                         # Run all linters
make format                       # Format code
make security                     # Security checks

# Database
make db-migrate                   # Create migration
make db-upgrade                   # Run migrations
uv run alembic current        # Check current version
uv run alembic history        # View migration history

# Docker
make docker-local                 # Start infrastructure only
docker compose ps                 # Check running containers
docker logs shia-chatbot-dev-app -f  # View logs
docker exec -it shia-chatbot-dev-app bash  # Shell into container

# Monitoring
make temporal-ui                  # Open Temporal UI (port 8233)
make minio-ui                     # Open MinIO console (port 9001)
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Qdrant Dashboard: http://localhost:6333/dashboard
```

### Architecture Patterns

1. **Dependency Injection**: Use FastAPI's `Depends()`
2. **Repository Pattern**: Data access logic in `repositories/`
3. **Service Pattern**: Business logic in `services/`
4. **DTO Pattern**: Pydantic schemas for data transfer
5. **Factory Pattern**: Test fixtures with factory-boy
6. **Strategy Pattern**: Multiple LLM providers
7. **Observer Pattern**: Event-driven with Temporal workflows

### Performance Considerations

1. **Use async/await** for all I/O operations
2. **Connection pooling**: Already configured for PostgreSQL, Redis
3. **Caching**: Redis for frequently accessed data
4. **Batch operations**: Use bulk insert/update when possible
5. **Pagination**: Always paginate large result sets
6. **Indexing**: Add database indexes for frequently queried fields
7. **Vector search**: Use metadata filters to reduce search space

### Security Best Practices

1. **Never log secrets** (passwords, API keys, tokens)
2. **Use environment variables** for sensitive configuration
3. **Validate all inputs** with Pydantic schemas
4. **Sanitize user content** before storing/displaying
5. **Use JWT tokens** for authentication (already implemented)
6. **Rate limiting**: Already configured (SlowAPI)
7. **CORS**: Properly configured in settings
8. **SQL injection**: Use SQLAlchemy ORM (never raw SQL)
9. **Pre-commit hooks**: Run security scans automatically

---

## 🔄 Recent Changes (from git history)

- **2025-01-13**: Refactored to use OpenRouter as primary LLM and web search provider
- **2025-01-13**: Removed Tavily integration (replaced with OpenRouter search)
- **2025-01-13**: Added auto-generated OpenAPI 3.1.0 specification
- **2025-01-13**: Converted Apidog collection to Postman Collection v2.1 format
- **2025-01-13**: Initial project setup and architecture

---

## 📖 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **LangChain Docs**: https://python.langchain.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **OpenRouter Docs**: https://openrouter.ai/docs
- **Temporal Docs**: https://docs.temporal.io/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **uv Docs**: https://github.com/astral-sh/uv

---

**Questions or Issues?**
- Check `TECH_STACK.md` for technology details
- Check `VPS_DEPLOYMENT.md` for deployment procedures
- Run `make help` for available commands
- Check `.env.example` for configuration options

**Remember**: This is a production system with real users. Always test thoroughly in LOCAL → DEV → STAGE before deploying to PROD!
