# Shia Islamic Chatbot

> Production-grade RAG-powered Islamic knowledge chatbot with multi-provider LLM support, semantic search, and comprehensive Islamic knowledge base.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-org/shia-islamic-chatbot)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Features

### Core Capabilities
- ✅ **Advanced RAG Pipeline** - Semantic search using Qdrant vector database with Chonkie chunking
- ✅ **Multi-Provider LLM Support** - OpenAI, Anthropic Claude, Google Gemini, Cohere via OpenRouter
- ✅ **Islamic Knowledge Base** - Hadith, Quranic verses, Fiqh rulings, and scholarly works
- ✅ **Automatic Speech Recognition** - Google Cloud Speech-to-Text and OpenAI Whisper
- ✅ **Multi-Environment Support** - Development, Staging, Production with environment isolation
- ✅ **Comprehensive Observability** - Langfuse integration for LLM tracing and analytics
- ✅ **Background Task Processing** - Celery with Redis for async operations
- ✅ **Real-time Monitoring** - Prometheus metrics and Grafana dashboards

### Advanced Features
- 🔐 **JWT Authentication** - Secure user management with role-based access control
- 📊 **Admin Dashboard** - User management, content moderation, system analytics
- 🎯 **Intent Detection** - Smart routing to appropriate tools and knowledge sources
- 🌍 **Multi-Language Support** - Arabic, English, and Persian
- 📈 **Analytics & Leaderboards** - User engagement tracking and gamification
- 🔄 **Environment Promotion** - Safe promotion of data between environments
- 📧 **Email Notifications** - Support tickets, moderation updates, account notifications

### Technical Highlights
- ⚡ **High Performance** - Async/await throughout, optimized database queries
- 🔒 **Security First** - Input validation, SQL injection prevention, secret scanning
- 🧪 **Comprehensive Testing** - 561+ test cases, 75% code coverage
- 📝 **API Documentation** - Interactive Swagger UI and ReDoc
- 🐳 **Containerized** - Docker Compose for easy deployment
- 🚀 **CI/CD Ready** - GitHub Actions with 40-50% faster execution

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Poetry** (Python dependency management)
- **PostgreSQL 15+** (via Docker)
- **Redis 7.2+** (via Docker)
- **Qdrant** (via Docker)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/shia-islamic-chatbot.git
cd shia-islamic-chatbot

# 2. Complete setup (installs deps, hooks, starts Docker, runs migrations)
make setup

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# 4. Start development server
make dev

# App runs at: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

**That's it!** Your chatbot is ready at http://localhost:8000

---

## 📖 Documentation

### For Users & Developers

| Document | Description |
|----------|-------------|
| [**QUICK_START.md**](QUICK_START.md) | Get started in 3 steps |
| [**LOCAL_DEVELOPMENT_GUIDE.md**](LOCAL_DEVELOPMENT_GUIDE.md) | Complete development workflow |
| [**MAKEFILE_QUICK_REFERENCE.md**](MAKEFILE_QUICK_REFERENCE.md) | 100+ commands reference |
| [**API Documentation**](http://localhost:8000/docs) | Interactive Swagger UI (when running) |

### For DevOps & Operations

| Document | Description |
|----------|-------------|
| [**OPERATIONS.md**](OPERATIONS.md) | Deployment, promotion, configuration |
| [**CONTRIBUTING.md**](CONTRIBUTING.md) | Contributing guidelines |
| [**PRE_COMMIT_SETUP_GUIDE.md**](PRE_COMMIT_SETUP_GUIDE.md) | Code quality automation |
| [**CI_CD_OPTIMIZATION_SUMMARY.md**](CI_CD_OPTIMIZATION_SUMMARY.md) | CI/CD pipeline details |

### Architecture & Design

| Document | Description |
|----------|-------------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | System architecture overview |
| [**MULTI_ENVIRONMENT_ARCHITECTURE.md**](MULTI_ENVIRONMENT_ARCHITECTURE.md) | Environment isolation design |
| [**DATABASE_CONFIGURATION.md**](DATABASE_CONFIGURATION.md) | Database schema and configuration |

---

## 🎯 Usage

### Testing the API

```bash
# Start the application
make dev

# Open Swagger UI
open http://localhost:8000/docs

# Or test via curl
curl http://localhost:8000/health
```

### Example: Chat Completion

```python
import requests

# Register and login
response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
})

# Login to get token
response = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "user@example.com",
    "password": "SecurePassword123!"
})
token = response.json()["access_token"]

# Chat completion
response = requests.post(
    "http://localhost:8000/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "messages": [
            {"role": "user", "content": "What are the five pillars of Islam?"}
        ],
        "model": "gpt-4",
        "stream": False
    }
)

print(response.json())
```

### Example: Document Upload & RAG

```python
# Upload a document
response = requests.post(
    "http://localhost:8000/api/v1/documents/upload",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "title": "Hadith on Charity",
        "content": "The Prophet (PBUH) said: Charity does not decrease wealth...",
        "document_type": "hadith",
        "primary_category": "akhlaq",
        "language": "en"
    }
)

# Semantic search
response = requests.post(
    "http://localhost:8000/api/v1/documents/search",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "charity and wealth",
        "limit": 10
    }
)

print(response.json())
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                     │
│            (Web, Mobile, Desktop, API Clients)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌────────────┬──────────────┬──────────────┬────────────┐ │
│  │   Auth     │   Chat API   │ Documents API│  Admin API │ │
│  └────────────┴──────────────┴──────────────┴────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   PostgreSQL     │ │   Qdrant Vector  │ │   Redis Cache    │
│   (User Data,    │ │   Database       │ │   (Sessions,     │
│    Documents,    │ │   (Semantic      │ │    Queue)        │
│    Metadata)     │ │    Search)       │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Providers (via OpenRouter)           │
│     OpenAI  │  Anthropic  │  Google  │  Cohere  │  Others  │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend Framework:**
- FastAPI (async/await)
- Pydantic v2 (data validation)
- SQLAlchemy (async ORM)
- Alembic (migrations)

**AI & ML:**
- LangChain & LangGraph (orchestration)
- OpenRouter (multi-provider LLM access)
- Langfuse (observability)
- Chonkie (semantic chunking)

**Databases:**
- PostgreSQL 15 (primary database)
- Qdrant (vector database)
- Redis 7.2 (cache & queue)

**Background Tasks:**
- Celery (async task processing)
- Flower (monitoring)

**Deployment:**
- Docker & Docker Compose
- Gunicorn/Uvicorn
- Nginx (reverse proxy)

---

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# Test API endpoints (requires app running)
make test-local

# Check coverage
make coverage
```

**Test Coverage:** 561+ test cases, ~75% coverage

---

## 🔧 Development

### Daily Workflow

```bash
# Start infrastructure
make docker-up

# Start app with hot reload
make dev

# Start Celery worker (optional)
make celery-worker

# Test via Swagger UI
open http://localhost:8000/docs
```

### Before Committing

```bash
# Quick check (format + lint + unit tests)
make quick-check

# Full check (all quality checks)
make ci
```

### Before Building Docker Image

```bash
# Comprehensive verification
make verify-build

# If all checks pass
make build
```

### Available Commands

```bash
# See all 100+ available commands
make help
```

---

## 🚀 Deployment

### Local Development

```bash
make dev
```

### Docker Deployment

```bash
# Build image
make build

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-prod
```

### Production Deployment

See [**OPERATIONS.md**](OPERATIONS.md) for complete deployment procedures, environment promotion workflows, and configuration management.

---

## 🔒 Security

- ✅ JWT-based authentication
- ✅ Password hashing (bcrypt)
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ Secret scanning (detect-secrets)
- ✅ Security scanning (Bandit)
- ✅ Dependency vulnerability checks (Safety)
- ✅ Pre-commit hooks for code quality
- ✅ Rate limiting (SlowAPI)

---

## 📊 Monitoring & Observability

### Langfuse (LLM Observability)
```
http://localhost:3001
```

### Qdrant Dashboard (Vector Database)
```
http://localhost:6333/dashboard
```

### Flower (Celery Monitoring)
```
http://localhost:5555
```

### Prometheus & Grafana
See [**docs/MONITORING_GUIDE.md**](docs/MONITORING_GUIDE.md)

---

## 🤝 Contributing

We welcome contributions! Please see [**CONTRIBUTING.md**](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make ci`)
5. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- ✅ Black formatting (100 char line length)
- ✅ isort import sorting
- ✅ flake8 linting
- ✅ mypy type checking
- ✅ 80% docstring coverage
- ✅ Conventional commits

All enforced via pre-commit hooks.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** - For the excellent LLM orchestration framework
- **FastAPI** - For the modern, fast web framework
- **Qdrant** - For the powerful vector database
- **OpenRouter** - For unified LLM provider access
- **Langfuse** - For LLM observability
- **Chonkie** - For semantic text chunking

---

## 📞 Support

- **Documentation:** [See docs/ directory](docs/)
- **Issues:** [GitHub Issues](https://github.com/your-org/shia-islamic-chatbot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/shia-islamic-chatbot/discussions)

---

## 🗺️ Roadmap

- [ ] Voice input/output support
- [ ] Mobile applications (iOS, Android)
- [ ] Advanced Arabic NLP features
- [ ] Expanded knowledge base
- [ ] Real-time collaboration features
- [ ] GraphQL API
- [ ] Kubernetes deployment

See [**OPERATIONS.md**](OPERATIONS.md) for detailed roadmap.

---

**Made with ❤️ for the Shia Muslim community**

**Version:** 1.0.0
**Status:** Production Ready
**Last Updated:** November 2025
