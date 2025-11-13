# Tech Stack

**WisQu Islamic Chatbot** — Production RAG system with multi-provider AI support

---

## Infrastructure

| Technology | Type | Purpose |
|------------|------|---------|
| **Docker** | Container Platform | Service orchestration & isolation |
| **PostgreSQL** | Database | User data, documents, metadata |
| **Redis** | Cache/Queue | Response caching, session storage |
| **Qdrant** | Vector Database | Semantic search & embeddings |
| **MinIO** | Object Storage | File uploads, backups |

---

## Backend

| Technology | Type | Purpose |
|------------|------|---------|
| **FastAPI** | Web Framework | REST API endpoints |
| **Uvicorn** | ASGI Server | Async request handling |
| **Pydantic** | Library | Data validation & settings |
| **SQLAlchemy** | ORM | Database operations |
| **Alembic** | Migration Tool | Schema versioning |
| **AsyncPG** | Driver | PostgreSQL async driver |

---

## AI & LLM

| Technology | Type | Purpose |
|------------|------|---------|
| **OpenRouter** | API | **Primary LLM provider** - Unified access (100+ models) |
| **Claude** (Anthropic) | API | LLM via OpenRouter |
| **Gemini** (Google) | API | Embeddings & LLM via OpenRouter |
| **GPT** (OpenAI) | API | LLM via OpenRouter |
| **Cohere** | API | Embeddings & reranking |
| **LangChain** | SDK | LLM orchestration framework |
| **LangGraph** | SDK | Multi-agent workflows |
| **Langfuse** | Platform | LLM observability & tracing |

---

## AI Components

| Technology | Type | Purpose |
|------------|------|---------|
| **Cohere Rerank** | API | 2-stage retrieval (20-40% quality boost) |
| **Gemini Embeddings** | API | Text-to-vector (3072 dimensions) |
| **mem0ai** | SDK | Conversation memory |
| **NeMo Guardrails** | Library | Content safety & filtering |
| **Chonkie** | Library | Semantic text chunking |

---

## Authentication

| Technology | Type | Purpose |
|------------|------|---------|
| **Google OAuth** | API | Social login |
| **JWT** (python-jose) | Library | Token authentication |
| **Passlib + bcrypt** | Library | Password hashing |
| **OTP Email** | Feature | Email verification |

---

## Email

| Technology | Type | Purpose |
|------------|------|---------|
| **Mailgun** | API | Production email delivery |
| **SMTP** | Protocol | Email fallback |

---

## Search

| Technology | Type | Purpose |
|------------|------|---------|
| **OpenRouter** | API | **Primary web search** - Perplexity Sonar + search-enabled LLMs |
| **Serper** | API | Google Search API (alternative) |

---

## Workflow & Tasks

| Technology | Type | Purpose |
|------------|------|---------|
| **Temporal** | SDK | Async workflow orchestration |

---

## Observability

| Technology | Type | Purpose |
|------------|------|---------|
| **Structlog** | Library | Structured JSON logging |
| **Prometheus** | Platform | Metrics collection |
| **Langfuse** | Platform | LLM-specific observability |

---

## HTTP & Web

| Technology | Type | Purpose |
|------------|------|---------|
| **HTTPX** | Library | Async HTTP client |
| **AIOHTTP** | Library | Alternative async HTTP |
| **Beautiful Soup** | Library | HTML parsing |

---

## Development

| Technology | Type | Purpose |
|------------|------|---------|
| **Poetry** | Tool | Dependency management |
| **Ruff** | Linter | Fast Python linting |
| **Black** | Formatter | Code formatting |
| **MyPy** | Type Checker | Static type checking |
| **Pytest** | Framework | Testing |
| **Pre-commit** | Tool | Git hooks |
| **Bandit** | Security | Security scanning |

---

## Key Architecture Decisions

**Multi-Provider AI**: OpenRouter provides unified access to 100+ models with automatic fallbacks

**2-Stage Retrieval**: Vector search (Qdrant) → Reranking (Cohere) = 20-40% quality improvement

**Task-Type Embeddings**: Separate optimizations for document indexing vs query search (LangChain best practice)

**Unified Accounts**: Same email = ONE user across Google OAuth and email/password

**Temporal Workflows**: Replace Celery with modern workflow orchestration for complex async tasks

**Multi-Environment**: LOCAL → DEV → STAGE → PROD with complete isolation

---

**Last Updated**: 2025-01-13
