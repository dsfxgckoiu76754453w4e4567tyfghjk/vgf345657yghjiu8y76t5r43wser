# Contributing to Shia Islamic Chatbot

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to the project.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Documentation](#documentation)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Expected Behavior

- ✅ Be respectful and inclusive
- ✅ Use welcoming and inclusive language
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what is best for the community
- ✅ Show empathy towards others

### Unacceptable Behavior

- ❌ Harassment or discriminatory language
- ❌ Trolling or insulting comments
- ❌ Personal or political attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry
- Git
- Basic understanding of FastAPI, SQLAlchemy, and async Python

### Setup Development Environment

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/shia-islamic-chatbot.git
cd shia-islamic-chatbot

# 3. Add upstream remote
git remote add upstream https://github.com/original-org/shia-islamic-chatbot.git

# 4. Complete setup
make setup

# 5. Create a branch for your work
git checkout -b feature/your-feature-name
```

---

## 🔄 Development Workflow

### 1. Start Development Environment

```bash
# Start Docker services
make docker-up

# Start application
make dev

# In another terminal: Start Celery worker (if needed)
make celery-worker
```

### 2. Make Changes

- Write code following our [code standards](#code-standards)
- Add tests for new functionality
- Update documentation as needed
- Test your changes via Swagger UI (http://localhost:8000/docs)

### 3. Before Committing

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Or run everything at once
make quick-check
```

### 4. Commit Changes

```bash
# Stage your changes
git add .

# Commit with conventional commit message
git commit -m "feat: Add amazing feature"

# Pre-commit hooks will run automatically
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

---

## 📏 Code Standards

### Python Style

We use **Black** for code formatting with the following settings:

```python
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**Key principles:**
- ✅ Line length: 100 characters max
- ✅ Use type hints
- ✅ Write docstrings for all public functions/classes
- ✅ Follow PEP 8 guidelines
- ✅ Prefer async/await over callbacks
- ✅ Use Pydantic models for data validation

### Import Organization

We use **isort** with Black profile:

```python
# Standard library imports
import os
import sys
from typing import Optional, List

# Third-party imports
from fastapi import FastAPI, Depends
from sqlalchemy import select

# Local imports
from app.models import User
from app.services import AuthService
```

### Type Hints

**Always use type hints:**

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

### Docstrings

**Use Google-style docstrings:**

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

### Naming Conventions

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

_cache = {}
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

## 🧪 Testing Guidelines

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

### Test Coverage Requirements

- ✅ Minimum 75% code coverage
- ✅ All new features must include tests
- ✅ All bug fixes must include regression tests
- ✅ Test both success and failure cases
- ✅ Test edge cases

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# Specific test file
poetry run pytest tests/unit/test_document_service.py

# Specific test
poetry run pytest tests/unit/test_document_service.py::TestDocumentService::test_create_document_success

# With coverage
make coverage
```

### Test Best Practices

**✅ DO:**
- Use descriptive test names
- Test one thing per test
- Use fixtures for common setup
- Mock external dependencies
- Test error conditions
- Keep tests fast

**❌ DON'T:**
- Test implementation details
- Write flaky tests
- Depend on test execution order
- Leave commented-out code
- Skip tests without good reason

---

## 📝 Commit Guidelines

### Conventional Commits

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| **feat** | New feature | `feat: Add document upload endpoint` |
| **fix** | Bug fix | `fix: Resolve authentication timeout issue` |
| **docs** | Documentation | `docs: Update API documentation` |
| **style** | Code style (formatting) | `style: Format code with Black` |
| **refactor** | Code restructuring | `refactor: Simplify document processing logic` |
| **test** | Add/update tests | `test: Add tests for chat service` |
| **chore** | Maintenance tasks | `chore: Update dependencies` |
| **perf** | Performance improvement | `perf: Optimize database queries` |
| **ci** | CI/CD changes | `ci: Add GitHub Actions workflow` |

### Commit Message Examples

**✅ Good commits:**

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

```bash
docs: Add deployment guide

Create comprehensive deployment guide covering:
- Environment setup
- Docker deployment
- Database migrations
- Environment promotion

```

**❌ Bad commits:**

```bash
# Too vague
update stuff

# No type
added new feature

# Not descriptive
fix bug

# Multiple unrelated changes
feat: add search, fix login, update docs
```

### Pre-commit Hooks

Pre-commit hooks automatically run when you commit:

```bash
# Install hooks (done by make setup)
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files

# Skip hooks (emergency only!)
git commit --no-verify
```

**Hooks that run:**
- ✅ Black (formatting)
- ✅ isort (import sorting)
- ✅ flake8 (linting)
- ✅ mypy (type checking)
- ✅ Bandit (security)
- ✅ detect-secrets (secret scanning)
- ✅ Trailing whitespace
- ✅ End of file fixer
- ✅ Commit message validation

---

## 🔍 Pull Request Process

### Before Creating PR

```bash
# 1. Sync with upstream
git fetch upstream
git rebase upstream/main

# 2. Run all checks
make ci

# 3. Ensure all tests pass
make test

# 4. Verify build works
make verify-build
```

### PR Title

Use conventional commit format:

```
feat: Add document semantic search
fix: Resolve authentication timeout
docs: Update deployment guide
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing via Swagger UI

## Checklist
- [ ] My code follows the code style of this project
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] All new and existing tests pass
- [ ] I have updated the documentation accordingly
- [ ] I have added appropriate docstrings
- [ ] My changes generate no new warnings

## Screenshots (if applicable)
Add screenshots here

## Related Issues
Closes #123
Fixes #456
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline must pass
   - All tests must pass
   - Code coverage must not decrease
   - No security vulnerabilities

2. **Code Review**
   - At least one approval required
   - Address all review comments
   - Request re-review after changes

3. **Merge**
   - Squash and merge preferred
   - Delete branch after merge

---

## 📚 Documentation

### When to Update Documentation

- ✅ Adding new features
- ✅ Changing API endpoints
- ✅ Modifying configuration
- ✅ Adding environment variables
- ✅ Changing deployment process
- ✅ Adding dependencies

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start |
| `OPERATIONS.md` | Deployment, configuration, operations |
| `CONTRIBUTING.md` | This file - contributing guidelines |
| `LOCAL_DEVELOPMENT_GUIDE.md` | Local development workflow |
| `MAKEFILE_QUICK_REFERENCE.md` | Makefile commands reference |
| `docs/` | Detailed technical documentation |

### API Documentation

- Update docstrings in route handlers
- Use Pydantic models for request/response schemas
- Add examples in docstrings
- Swagger UI auto-generates from code

---

## 🎯 Areas for Contribution

### High Priority

- [ ] Additional test coverage
- [ ] Performance optimizations
- [ ] Documentation improvements
- [ ] Bug fixes

### Feature Requests

- [ ] GraphQL API
- [ ] Advanced Arabic NLP
- [ ] Voice input/output
- [ ] Mobile applications
- [ ] Real-time collaboration

### Good First Issues

Look for issues tagged with `good-first-issue` or `help-wanted`

---

## ❓ Questions?

- **General questions:** Open a [GitHub Discussion](https://github.com/your-org/shia-islamic-chatbot/discussions)
- **Bug reports:** Create an [Issue](https://github.com/your-org/shia-islamic-chatbot/issues)
- **Feature requests:** Open a [Discussion](https://github.com/your-org/shia-islamic-chatbot/discussions)

---

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!

---

**Version:** 1.0.0
**Last Updated:** November 2025
