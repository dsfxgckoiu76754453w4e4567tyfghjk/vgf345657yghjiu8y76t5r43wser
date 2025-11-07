# Shia Islamic Chatbot - Implementation Guide

## 🎯 Project Status

**Current Phase:** Phase 1 - Foundation (Partially Complete)

### ✅ Completed

1. **Project Structure** ✓
   - Poetry dependency management configured
   - Docker Compose setup (PostgreSQL, Redis, Qdrant, Langfuse)
   - Directory structure created
   - Environment configuration ready

2. **Core Configuration** ✓
   - Settings management with Pydantic
   - Environment-based logging (dev/test/prod)
   - FastAPI application skeleton
   - CORS and security middleware

3. **Database Foundation** ✓
   - SQLAlchemy async setup
   - Alembic migrations configured
   - Core user models implemented:
     - `User` (email + OAuth authentication)
     - `OTPCode` (email verification)
     - `UserSession` (JWT sessions)
     - `LinkedAuthProvider` (cross-platform auth linking)
     - `UserSettings` (user preferences)

### 🚧 Next Steps

The implementation follows a **6-phase roadmap** (13-17 weeks total). See [docs/implementation/20-IMPLEMENTATION-ROADMAP.md](docs/implementation/20-IMPLEMENTATION-ROADMAP.md) for complete details.

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry 1.8.0+
- PostgreSQL 15+ (via Docker)

### 2. Initial Setup

```bash
# Clone the repository
cd /path/to/shia-islamic-chatbot

# Install dependencies with Poetry
poetry install

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start infrastructure services (PostgreSQL, Redis, Qdrant)
docker-compose up -d postgres redis qdrant

# Wait for services to be healthy (30 seconds)
sleep 30

# Create database and run migrations
poetry run alembic upgrade head

# Run the application
poetry run dev
```

The API will be available at `http://localhost:8000`

### 3. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API documentation (dev only)
open http://localhost:8000/docs
```

---

## 📚 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3) - **IN PROGRESS**

**Status:** 40% Complete

#### Completed Tasks
- [x] Project structure and Poetry setup
- [x] Docker Compose configuration
- [x] Environment configuration
- [x] Logging setup (structlog)
- [x] FastAPI application skeleton
- [x] Database connection (async SQLAlchemy)
- [x] Alembic migrations setup
- [x] Core user models (User, OTPCode, UserSession, etc.)

#### Remaining Tasks
- [ ] Complete remaining database models (see `docs/implementation/02-DATABASE-SCHEMA.md`):
  - [ ] Admin models (`SystemAdmin`, `AdminTask`)
  - [ ] Chat models (`Conversation`, `Message`, `MessageFeedback`)
  - [ ] Document models (`Document`, `DocumentChunk`, `DocumentEmbedding`)
  - [ ] Marja sources (`MarjaOfficialSource`, `AhkamFetchLog`)
  - [ ] Rejal models (`RejalPerson`, `HadithChain`)
  - [ ] Ticket models (`Ticket`, `TicketMessage`)
  - [ ] Leaderboard models
  - [ ] External API models (`ExternalAPIClient`, `APIUsageLog`)

- [ ] Authentication system:
  - [ ] JWT token generation/validation (`src/app/core/security.py`)
  - [ ] Password hashing (bcrypt/argon2)
  - [ ] OAuth Google integration
  - [ ] OTP generation and email sending
  - [ ] Account linking logic (email ↔ Google)

- [ ] API endpoints:
  - [ ] `/api/v1/auth/register` (email)
  - [ ] `/api/v1/auth/login` (email + Google OAuth)
  - [ ] `/api/v1/auth/verify-email` (OTP)
  - [ ] `/api/v1/auth/refresh-token`
  - [ ] `/api/v1/users/me`
  - [ ] `/api/v1/users/settings`

- [ ] Rate limiting implementation (slowapi)
- [ ] User tier management
- [ ] Basic tests

**Expected Duration:** 1-2 weeks remaining

---

### Phase 2: Core RAG Pipeline (Weeks 4-6)

**Modules:** [09-RAG-PIPELINE-CHONKIE.md](docs/implementation/09-RAG-PIPELINE-CHONKIE.md), [11-LANGGRAPH.md](docs/implementation/11-LANGGRAPH.md), [12-MEMORY-GUARDRAILS.md](docs/implementation/12-MEMORY-GUARDRAILS.md)

#### Key Tasks
1. **Qdrant Integration**
   - Create collections for embeddings
   - Binary quantization setup
   - Hybrid search configuration

2. **Chonkie Integration** (CRITICAL)
   - Install and configure Chonkie library
   - Implement semantic chunker
   - Admin chunk approval workflow

3. **Document Processing**
   - Upload endpoint
   - Text extraction (PDF, DOCX)
   - Chunking with Chonkie
   - Embedding generation (Gemini/Cohere)
   - Vector storage

4. **Retrieval System**
   - 2-stage retrieval (embedding + reranking)
   - Filters (document type, language, marja)
   - Result formatting

5. **LangGraph Orchestration**
   - State definition
   - Graph nodes (intent classification, retrieval, generation)
   - Streaming support

6. **mem0 & NeMo Guardrails**
   - Memory initialization
   - Guardrails setup (input/output validation)

**Expected Duration:** 2-3 weeks

---

### Phase 3: Specialized Tools (Weeks 7-10)

**Modules:** [06-TOOLS-AHKAM.md](docs/implementation/06-TOOLS-AHKAM.md), [07-TOOLS-HADITH.md](docs/implementation/07-TOOLS-HADITH.md), [08-TOOLS-OTHER.md](docs/implementation/08-TOOLS-OTHER.md)

#### Key Tasks

1. **Ahkam Tool** ⚠️ CRITICAL
   - **NOT RAG-based** - fetches from official Marja websites
   - Web scraping implementation (Beautiful Soup, rate limiting)
   - API integration (if available)
   - Caching (24-hour default)
   - Admin configuration UI
   - See [06-TOOLS-AHKAM.md](docs/implementation/06-TOOLS-AHKAM.md) for complete spec

2. **Hadith Lookup Tool** 🆕
   - Reference-based lookup
   - Text search
   - Narrator search (Rejal integration)
   - Chain (sanad) display

3. **Other Tools**
   - DateTime calculator (prayer times, Islamic dates)
   - Math calculator (zakat, khums, inheritance) **WITH WARNINGS**
   - Comparison tool (Marja opinions)
   - Rejal lookup

4. **Multi-Tool Orchestration**
   - Tool dependency analysis
   - Parallel/sequential execution
   - Result aggregation

**Expected Duration:** 3-4 weeks

---

### Phase 4: Admin Features (Weeks 11-12)

**Modules:** [05-ADMIN-SYSTEM.md](docs/implementation/05-ADMIN-SYSTEM.md), [15-TICKET-LEADERBOARD.md](docs/implementation/15-TICKET-LEADERBOARD.md)

#### Key Tasks
1. Super-admin API key management dashboard
2. Content admin chunk approval workflow
3. Support ticket system
4. Admin & user leaderboards
5. Role-based access control (4 roles)

**Expected Duration:** 2 weeks

---

### Phase 5: External API & Monitoring (Weeks 13-14)

**Modules:** [13-EXTERNAL-API.md](docs/implementation/13-EXTERNAL-API.md), [14-LOGGING-MONITORING.md](docs/implementation/14-LOGGING-MONITORING.md), [10-ASR-INTEGRATION.md](docs/implementation/10-ASR-INTEGRATION.md)

#### Key Tasks
1. Third-party API client system
2. API key generation and management
3. Super-admin controls (ban, suspend, rate limits)
4. Langfuse integration for LLM tracing
5. ASR support (Google Speech-to-Text + Whisper)

**Expected Duration:** 2 weeks

---

### Phase 6: Testing & Deployment (Weeks 15-17)

**Modules:** [17-DEPLOYMENT.md](docs/implementation/17-DEPLOYMENT.md), [18-TESTING.md](docs/implementation/18-TESTING.md), [19-SECURITY.md](docs/implementation/19-SECURITY.md)

#### Key Tasks
1. Comprehensive testing (>80% coverage)
2. Security hardening
3. Performance optimization
4. Production deployment configuration
5. Documentation

**Expected Duration:** 2-3 weeks

---

## 📂 Project Structure

```
shia-islamic-chatbot/
├── src/app/                    # Application source code
│   ├── api/                    # API endpoints (v1)
│   │   ├── v1/
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── users.py        # User management
│   │   │   ├── chat.py         # Chat endpoints
│   │   │   ├── admin.py        # Admin dashboard
│   │   │   └── tools.py        # Specialized tools
│   ├── core/                   # Core functionality
│   │   ├── config.py          # ✅ Settings management
│   │   ├── logging.py         # ✅ Environment-based logging
│   │   ├── security.py        # TODO: JWT, password hashing
│   │   └── dependencies.py    # TODO: FastAPI dependencies
│   ├── db/                    # Database
│   │   ├── base.py           # ✅ Database session
│   │   └── repositories/      # TODO: Data access layer
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py           # ✅ User, OTP, Session, LinkedAuth
│   │   ├── admin.py          # TODO: Admin models
│   │   ├── chat.py           # TODO: Conversation, Message
│   │   ├── document.py       # TODO: Document, Chunk, Embedding
│   │   ├── marja.py          # TODO: Marja sources, Ahkam logs
│   │   ├── rejal.py          # TODO: Rejal, Hadith chains
│   │   └── external_api.py   # TODO: API clients, usage logs
│   ├── schemas/               # Pydantic schemas
│   │   ├── auth.py           # TODO: Login, Register, Token
│   │   ├── user.py           # TODO: UserResponse, UserUpdate
│   │   └── chat.py           # TODO: MessageRequest, ChatResponse
│   ├── services/              # Business logic
│   │   ├── auth.py           # TODO: Authentication service
│   │   ├── user.py           # TODO: User management service
│   │   ├── rag.py            # TODO: RAG pipeline
│   │   ├── langraph.py       # TODO: LangGraph orchestration
│   │   └── tools/            # TODO: Specialized tools
│   │       ├── ahkam.py      # TODO: Ahkam (NOT RAG)
│   │       ├── hadith.py     # TODO: Hadith lookup
│   │       └── datetime.py   # TODO: Prayer times, dates
│   ├── tools/                 # LangChain tools
│   │   ├── ahkam_tool.py     # TODO: Ahkam LangChain tool
│   │   ├── hadith_tool.py    # TODO: Hadith LangChain tool
│   │   └── math_tool.py      # TODO: Math calculator
│   ├── utils/                 # Utilities
│   │   ├── email.py          # TODO: Email sending (OTP)
│   │   ├── chonkie.py        # TODO: Chonkie integration
│   │   └── cache.py          # TODO: Redis caching
│   └── main.py               # ✅ FastAPI application
├── tests/                     # Tests
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── alembic/                  # ✅ Database migrations
├── docs/implementation/      # ✅ Complete implementation docs
├── scripts/                  # Utility scripts
├── docker-compose.yml        # ✅ Infrastructure setup
├── Dockerfile               # ✅ Application container
├── pyproject.toml           # ✅ Dependencies
├── alembic.ini              # ✅ Alembic configuration
├── .env.example             # ✅ Environment template
└── README.md                # ✅ Project overview
```

---

## 🔑 Critical Implementation Notes

### 1. Ahkam Tool (CRITICAL ⚠️)

**DO NOT use RAG for Ahkam queries!**

The Ahkam tool must fetch directly from official Marja websites, not from the vector database. This ensures:
- Maximum authenticity
- Direct citations with URLs
- Real-time updates from official sources

See [docs/implementation/06-TOOLS-AHKAM.md](docs/implementation/06-TOOLS-AHKAM.md) for complete implementation.

### 2. Multi-Tool Selection

One question can trigger **multiple tools simultaneously**. For example:

> "What is Ayatollah Sistani's ruling on prayer times in London today?"

Should trigger:
1. **Ahkam tool** - for Sistani's ruling
2. **DateTime tool** - for London prayer times
3. **RAG retrieval** - for general prayer information

See [docs/implementation/08-TOOLS-OTHER.md](docs/implementation/08-TOOLS-OTHER.md).

### 3. Financial Calculation Warnings

**Zakat, khums, and inheritance calculations MUST include mandatory warnings:**

```python
warning = """
⚠️ IMPORTANT WARNING ⚠️

This calculation is provided for general guidance only and may contain errors.
YOU MUST double-check this calculation with:
1. Your Marja's official office
2. A qualified Islamic financial advisor
3. The latest fatwas from your Marja's website
"""
```

### 4. Chonkie Integration

Use **Chonkie library** for intelligent chunking, NOT traditional LangChain text splitters:

```python
from chonkie import SemanticChunker, TokenChunker

chunker = SemanticChunker(
    chunk_size=512,
    chunk_overlap=50,
    language="fa"  # Persian
)
```

### 5. Environment-Based Logging

- **Development**: DEBUG level, colored output
- **Test**: INFO level, JSON output
- **Production**: WARNING level, JSON output, external service

Configured in `src/app/core/logging.py`.

### 6. Cross-Platform Authentication

Users who sign up with email can log in with Google (and vice versa) if emails match:

```python
# Sign up: email@example.com (password)
# Can also log in: Google OAuth (email@example.com)
# → Same user account, linked in `linked_auth_providers` table
```

See [docs/implementation/03-AUTHENTICATION.md](docs/implementation/03-AUTHENTICATION.md).

---

## 🧪 Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/app --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_auth.py

# Run integration tests only
poetry run pytest tests/integration/
```

---

## 📖 Documentation

Complete implementation documentation is available in `docs/implementation/`:

- **[00-INDEX.md](docs/implementation/00-INDEX.md)** - Master index
- **[01-ARCHITECTURE-OVERVIEW.md](docs/implementation/01-ARCHITECTURE-OVERVIEW.md)** - System architecture
- **[02-DATABASE-SCHEMA.md](docs/implementation/02-DATABASE-SCHEMA.md)** - Complete database schema (30+ tables)
- **[06-TOOLS-AHKAM.md](docs/implementation/06-TOOLS-AHKAM.md)** - ⚠️ CRITICAL Ahkam tool (NOT RAG)
- **[20-IMPLEMENTATION-ROADMAP.md](docs/implementation/20-IMPLEMENTATION-ROADMAP.md)** - 6-phase roadmap

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Recreate database
docker-compose down
docker-compose up -d postgres
sleep 10
poetry run alembic upgrade head
```

### Alembic Migration Issues

```bash
# Reset migrations (CAUTION: Deletes all data)
docker-compose exec postgres psql -U postgres -c "DROP DATABASE shia_chatbot;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE shia_chatbot;"
poetry run alembic upgrade head
```

### Poetry Dependency Issues

```bash
# Clear cache and reinstall
poetry cache clear --all pypi
rm poetry.lock
poetry install
```

---

## 🤝 Contributing

When implementing new features:

1. **Read the relevant module** in `docs/implementation/`
2. **Follow the coding standards**:
   - Type hints everywhere
   - Docstrings for all functions
   - Environment-aware configurations
   - Comprehensive error handling
3. **Write tests** alongside code
4. **Update documentation** if needed
5. **Use standard message codes** (no hardcoded strings)

Example message code:
```python
# Bad
return {"message": "Login successful"}

# Good
return {"code": "AUTH_LOGIN_SUCCESS", "message": "Login successful"}
```

---

## 📞 Support

- **Documentation**: `docs/implementation/`
- **Issues**: GitHub Issues
- **Architecture Questions**: See `docs/implementation/01-ARCHITECTURE-OVERVIEW.md`

---

## ✅ Pre-Deployment Checklist

See complete checklist in [docs/implementation/20-IMPLEMENTATION-ROADMAP.md](docs/implementation/20-IMPLEMENTATION-ROADMAP.md#pre-deployment-checklist)

---

**Status**: Phase 1 (Foundation) - 40% Complete
**Next Milestone**: Complete authentication system and remaining database models
**Timeline**: 11-15 weeks remaining (depends on team size and experience)

Good luck with the implementation! 🚀
