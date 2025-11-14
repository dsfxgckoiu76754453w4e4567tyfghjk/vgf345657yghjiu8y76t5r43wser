# Dependency Mapping & Legacy Code Reference

**Purpose**: Comprehensive map of all dependencies, service relationships, and legacy code patterns to streamline future migrations and refactoring.

**Generated**: 2025-01-14
**Last Updated**: 2025-01-14
**Maintainer**: Keep this updated when adding/removing services or changing architecture

---

## Table of Contents
1. [Current Architecture Stack](#current-architecture-stack)
2. [Service Dependency Map](#service-dependency-map)
3. [Configuration Dependencies](#configuration-dependencies)
4. [External API Dependencies](#external-api-dependencies)
5. [Legacy Code Inventory](#legacy-code-inventory)
6. [Migration Checklist Template](#migration-checklist-template)

---

## Current Architecture Stack

### **Core Framework**
- **FastAPI** 0.109.0+ - Async web framework
- **Python** 3.11+ - Runtime
- **uv** - Package manager (replaced Poetry)
- **PostgreSQL** 16+ - Primary database
- **Redis** 7+ - Caching & sessions
- **Temporal** - Workflow orchestration (replaced Celery)

### **AI/LLM Stack**
- **OpenRouter** (Primary) - Unified LLM API
  - Access to 100+ models (Claude, GPT, Gemini, etc.)
- **LangChain** - LLM orchestration
- **LangGraph** - Multi-agent workflows
- **Langfuse** - LLM observability

### **AI Components**
| Component | Purpose | Config Key |
|-----------|---------|------------|
| **Embeddings** | Text-to-vector | `EMBEDDING_PROVIDER` (gemini) |
| **Reranker** | 2-stage retrieval | `RERANKER_PROVIDER` (cohere) |
| **ASR** | Speech-to-text | `ASR_PROVIDER` (google/whisper/gemini) |
| **Web Search** | Online search | `WEB_SEARCH_PROVIDER` (openrouter) |
| **Image Gen** | AI images | `IMAGE_GENERATION_ENABLED` |
| **Guardrails** | Content safety | `GUARDRAILS_ENABLED` |
| **mem0** | Conversation memory | `MEM0_ENABLED` |
| **Chonkie** | Semantic chunking | `CHUNKING_STRATEGY` |

### **Storage & Databases**
- **Qdrant** - Vector database for embeddings
- **MinIO** - S3-compatible object storage
- **PostgreSQL** - Relational data (4 isolated databases)
- **Redis** - Cache (4 isolated DBs: 0,1,2,3)

### **Observability**
- **Langfuse** - LLM tracing
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Structlog** - Structured JSON logging

---

## Service Dependency Map

### **Service Layer (35 services)**

```
Core Services (Always Active):
├── auth.py                    → PostgreSQL, Redis, JWT
├── admin_service.py           → PostgreSQL, Redis
├── datetime_service.py        → (Pure utility, no deps)
└── rate_limiter_service.py    → Redis

LLM/AI Services:
├── openrouter_service.py      → OpenRouter API, Langfuse
├── embeddings_service.py      → Google Gemini API
├── reranker_service.py        → Cohere API
├── langgraph_service.py       → OpenRouter, DocumentService, IntentDetector
├── intent_detector.py         → OpenRouter API
├── enhanced_chat_service.py   → LangGraph, Qdrant, Temporal
├── web_search_service.py      → OpenRouter API (with web plugin)
├── image_generation_service.py → OpenRouter API
├── langfuse_service.py        → Langfuse API
└── prompt_manager.py          → PostgreSQL

ASR & Media:
├── asr_service.py             → Google Speech / Whisper / Gemini
└── tool_orchestration_service.py → Multiple tools

Document & RAG:
├── document_service.py        → PostgreSQL, Qdrant, MinIO
├── qdrant_service.py          → Qdrant API
├── chonkie_service.py         → (Chunking utility)
└── dataset_service.py         → PostgreSQL, MinIO

Storage:
├── minio_storage_service.py   → MinIO API
└── response_cache_service.py  → Redis

Communication:
├── email_service.py           → Mailgun API / SMTP
└── google_oauth.py            → Google OAuth API

Islamic Knowledge Tools:
├── ahkam_service.py           → External Ahkam API
├── hadith_service.py          → (Planned)
└── math_service.py            → (Date conversions)

Business Logic:
├── subscription_service.py    → PostgreSQL, Stripe
├── support_service.py         → PostgreSQL, Email
├── promotion_service.py       → PostgreSQL
├── presets_service.py         → PostgreSQL
├── leaderboard_service.py     → PostgreSQL, Redis
├── evaluation_service.py      → PostgreSQL
└── external_api_client_service.py → PostgreSQL
```

### **Critical Service Dependencies**

#### **Chat Flow (Main User Journey)**
```
User Request
    ↓
chat.py (API)
    ↓
enhanced_chat_service.py
    ├→ langgraph_service.py
    │   ├→ intent_detector.py → OpenRouter
    │   ├→ document_service.py → Qdrant + PostgreSQL
    │   └→ openrouter_service.py → OpenRouter API
    ├→ response_cache_service.py → Redis
    ├→ langfuse_service.py → Langfuse (observability)
    └→ Temporal (async workflows)
```

#### **Document Upload & RAG**
```
documents.py (API)
    ↓
document_service.py
    ├→ minio_storage_service.py → MinIO (file storage)
    ├→ embeddings_service.py → Gemini (vector generation)
    ├→ chonkie_service.py (chunking)
    ├→ qdrant_service.py → Qdrant (vector storage)
    └→ PostgreSQL (metadata)
```

#### **ASR (Speech-to-Text)**
```
asr.py (API)
    ↓
asr_service.py
    ├→ Google Speech-to-Text (default)
    ├→ OpenAI Whisper (alternative)
    └→ Gemini Audio (alternative)
```

---

## Configuration Dependencies

### **Environment-Specific Settings**

| Environment | Port | DB | Redis | Qdrant Prefix | MinIO Prefix | Temporal Queue |
|-------------|------|-----|-------|---------------|--------------|----------------|
| **LOCAL** | 8003 | `shia_chatbot_local` | 0 | `local_` | `local-` | `wisqu-local-queue` |
| **DEV** | 8000 | `shia_chatbot_dev` | 1 | `dev_` | `dev-` | `wisqu-dev-queue` |
| **STAGE** | 8001 | `shia_chatbot_stage` | 2 | `stage_` | `stage-` | `wisqu-stage-queue` |
| **PROD** | 8002 | `shia_chatbot_prod` | 3 | `prod_` | `prod-` | `wisqu-prod-queue` |

### **Critical Configuration Fields**

#### **LLM Configuration**
```python
# Primary (Recommended)
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=sk-or-v1-...

# Alternatives
LLM_PROVIDER=openai  # Direct OpenAI
LLM_PROVIDER=google  # Direct Google Gemini
```

#### **ASR Configuration**
```python
ASR_PROVIDER=google              # google | whisper | gemini
GOOGLE_API_KEY=...               # Shared with embeddings
GEMINI_ASR_MODEL=gemini-2.0-flash-exp  # Separate from LLM model
```

#### **Email Configuration**
```python
EMAIL_PROVIDER=mailgun           # mailgun | smtp
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=...
```

#### **Web Search Configuration**
```python
WEB_SEARCH_PROVIDER=openrouter   # openrouter | serper
WEB_SEARCH_MODEL=openai/gpt-4o-mini-search-preview
```

### **Shared API Keys**
- `GOOGLE_API_KEY` - Used by:
  - Embeddings (gemini-embedding-001)
  - ASR (Google Speech-to-Text)
  - Gemini ASR (when `ASR_PROVIDER=gemini`)

- `OPENROUTER_API_KEY` - Used by:
  - LLM chat (primary)
  - Intent detection
  - Web search (with plugin)
  - Image generation
  - Tool orchestration

---

## External API Dependencies

### **Primary APIs (Production Critical)**

| API | Purpose | Fallback | Rate Limits |
|-----|---------|----------|-------------|
| **OpenRouter** | LLM (primary) | OpenAI direct | Per model varies |
| **Cohere** | Reranking | None (critical) | 1000/month free |
| **Google Gemini** | Embeddings | OpenRouter embeddings | Variable |
| **Mailgun** | Email/OTP | SMTP fallback | 5000/month free |
| **Temporal Cloud** | Workflows | Self-hosted option | Varies by plan |
| **Langfuse Cloud** | Observability | Self-hosted option | 50K events/month free |

### **Optional APIs**

| API | Purpose | Required | Alternative |
|-----|---------|----------|-------------|
| **Google Speech** | ASR | No | Whisper, Gemini |
| **OpenAI Whisper** | ASR | No | Google, Gemini |
| **Serper** | Web search | No | OpenRouter search |
| **Stripe** | Payments | Yes (if subscriptions enabled) | - |

### **Self-Hosted Services (No External API)**

- PostgreSQL
- Redis
- Qdrant
- MinIO
- Prometheus
- Grafana

---

## Legacy Code Inventory

### **📊 Current Status (2025-01-14)**

| Pattern | Count | Priority | Status |
|---------|-------|----------|--------|
| **Celery references** | 36 | 🟡 Low | Documentation only |
| **Poetry references** | 104 | 🔴 High | CI/CD + pre-commit |
| **pip install** | 14 | 🟡 Medium | Docs + external files |
| **Tavily references** | 2 | 🟢 Low | Documentation only |
| **Anthropic direct** | 0 | ✅ Clean | Removed |
| **Old Redis DB** | 1 | 🟢 Low | Documentation |

### **Detailed Breakdown**

#### **1. Celery References (36) - Documentation Only**

**Type**: Historical references in ADRs and documentation

**Files**:
- `docs/adr/003-temporal-workflow-engine.md` - ADR documenting migration
- `CLAUDE.md` - Mentions Temporal replaces Celery
- `TECH_STACK.md` - Architecture notes
- `grafana/README.md` - Old Grafana dashboard docs
- `src/app/workflows/chat_workflow.py:10` - Comment "Benefits over Celery"

**Action Needed**:
- ✅ Keep ADRs (historical record)
- 🔧 Update Grafana README to remove Celery dashboard references
- 🔧 Review comments in workflow files

**Priority**: 🟡 Low - No active code, only documentation

---

#### **2. Poetry References (104) - Active in CI/CD**

**Type**: Package manager (replaced by uv)

**Files**:
- `.github/workflows/ci-cd.yml` - 50+ references
- `.pre-commit-config.yaml` - Poetry hooks
- `docs/adr/004-uv-package-manager.md` - Migration ADR
- Various documentation

**Action Needed**:
- 🔴 **HIGH PRIORITY**: Migrate CI/CD workflow to uv
- 🔴 **HIGH PRIORITY**: Update pre-commit hooks
- ⚠️ Remove `poetry.lock` from .gitignore exclusions
- Update all installation docs

**Priority**: 🔴 High - Active in CI/CD pipeline

**Migration Template**:
```yaml
# OLD (Poetry)
- name: Install Poetry
  run: pip install poetry==${{ env.POETRY_VERSION }}
- run: poetry install --no-interaction

# NEW (uv)
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh
- run: uv sync
```

---

#### **3. pip install References (14) - Mixed**

**Type**: Package installation commands

**Files**:
- `docs/adr/004-uv-package-manager.md` - Examples
- `Dockerfile` - Some pip usage
- `.github/workflows/*.yml` - CI/CD
- `openrouter-full-doc.txt` - External docs
- `src/app/utils/audio_utils.py` - Installation hint

**Action Needed**:
- 🟡 Update Dockerfile to use uv
- 🟡 Update audio_utils.py error messages
- ✅ Keep ADR examples (historical)
- ✅ External docs (openrouter) - ignore

**Priority**: 🟡 Medium - Some active usage

---

#### **4. Tavily References (2) - Documentation Only**

**Type**: Old web search provider (replaced by OpenRouter)

**Files**:
- `CLAUDE.md` - ADR reference
- `docs/adr/002-openrouter-llm-provider.md` - Migration note

**Action Needed**:
- ✅ Keep as historical record

**Priority**: 🟢 Low - Documentation only

---

#### **5. Old Redis DB References (1)**

**Type**: Wrong Redis DB mapping (LOCAL=3 instead of 0)

**Files**:
- Check: `CLAUDE.md`, `VPS_DEPLOYMENT.md` already fixed

**Action Needed**:
- ✅ Already fixed in previous commits

**Priority**: ✅ Complete

---

### **Files That Should NEVER Have Legacy Code**

These files are actively executed and must be kept clean:

```
src/app/**/*.py          - All Python source code
src/app/core/config.py   - Configuration (CRITICAL)
src/app/core/metrics.py  - Metrics (already migrated to Temporal)
.env.example             - Environment template (already cleaned)
docker-compose*.yml      - Docker configs
Dockerfile               - Container build
pyproject.toml          - Dependencies (uv format)
```

### **Files That CAN Have Legacy Code**

Historical documentation is valuable:

```
docs/adr/*.md           - Architecture Decision Records (keep all history)
CLAUDE.md               - Developer guide (may reference migrations)
TECH_STACK.md           - Tech stack evolution
*.backup.yml            - Backup files (clearly marked)
```

---

## Migration Checklist Template

When migrating technologies, use this checklist:

### **Phase 1: Code Changes**
- [ ] Update `src/app/core/config.py` - Add/remove config fields
- [ ] Update `.env.example` - Add/remove environment variables
- [ ] Update `pyproject.toml` - Add/remove dependencies
- [ ] Update services in `src/app/services/` - Replace API calls
- [ ] Update tests in `tests/` - Replace test fixtures
- [ ] Update `src/app/core/metrics.py` - Replace metrics

### **Phase 2: Infrastructure**
- [ ] Update `docker-compose*.yml` - Add/remove services
- [ ] Update `Dockerfile` - Change build process
- [ ] Update Makefile - Change commands
- [ ] Update nginx configs if needed

### **Phase 3: CI/CD**
- [ ] Update `.github/workflows/ci-cd.yml` - Change CI commands
- [ ] Update `.pre-commit-config.yaml` - Change hooks
- [ ] Update `scripts/verify-before-build.sh` - Change checks

### **Phase 4: Documentation**
- [ ] Create ADR in `docs/adr/` - Document decision
- [ ] Update `TECH_STACK.md` - Update stack list
- [ ] Update `CLAUDE.md` - Update developer guide
- [ ] Update `VPS_DEPLOYMENT.md` - Update deployment steps
- [ ] Update `README.md` - Update main readme
- [ ] Update this `DEPENDENCY_MAPPING.md` - Update mappings

### **Phase 5: Cleanup**
- [ ] Remove old dependencies from `pyproject.toml`
- [ ] Remove old environment variables from `.env.example`
- [ ] Remove old Docker services
- [ ] Remove old scripts
- [ ] Update `.gitignore` if needed
- [ ] Mark old CI workflows as `.backup.yml`

### **Phase 6: Verification**
- [ ] Run `uv run alembic check` - Database migrations
- [ ] Run `uv run pytest` - All tests pass
- [ ] Run `make lint` - Code quality
- [ ] Run `make security` - Security checks
- [ ] Test in LOCAL environment
- [ ] Deploy to DEV environment
- [ ] Test in DEV with frontend
- [ ] Deploy to STAGE for beta testing
- [ ] Deploy to PROD

---

## Quick Reference Commands

### **Find Legacy Patterns**

```bash
# Find Celery references
grep -r "celery\|Celery" --include="*.py" src/

# Find Poetry references
grep -r "poetry" --include="*.py" --include="*.yml" --include="*.yaml" .

# Find pip install
grep -r "pip install" --include="*.py" --include="*.md" .

# Find old Redis DB references
grep -r "REDIS.*3\|redis://.*:6379/3" --include="*.py" --include="*.md" .
```

### **Check Service Dependencies**

```bash
# Find what imports a service
grep -r "from app.services.X import\|import app.services.X" src/

# Find all external API calls
grep -r "requests.get\|httpx" --include="*.py" src/app/services/

# Find all async functions
grep -r "async def" --include="*.py" src/app/services/
```

### **Configuration Audit**

```bash
# Find all getattr(settings, ...)
grep -r "getattr(settings" --include="*.py" src/

# Find all settings. references
grep -r "settings\." --include="*.py" src/ | grep -v "def settings"

# Check environment variables
grep "^[A-Z_]*=" .env.example | wc -l
```

---

## Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Update legacy code inventory | After each migration | Dev Team |
| Review service dependencies | Quarterly | Tech Lead |
| Audit external APIs | Quarterly | DevOps |
| Update this document | After major changes | Dev Team |
| Check for deprecated deps | Monthly | DevOps |

---

## Notes

- **Do not delete ADRs** - They are historical records
- **Mark legacy clearly** - Use comments like `# LEGACY: Remove after migration to X`
- **Test in all 4 environments** - LOCAL → DEV → STAGE → PROD
- **Update this doc** - Keep it current for future migrations

---

**Last Review**: 2025-01-14
**Next Review Due**: 2025-04-14 (Quarterly)

---

## Internal Module Dependencies

### **Most Imported Core Modules**

Ranking shows criticality - changes to top modules affect many files:

| Rank | Module | Imported By | Purpose |
|------|--------|-------------|---------|
| 1 | `app.core.logging` | 65 files | Structured logging |
| 2 | `app.core.config` | 39 files | Settings & configuration |
| 3 | `app.db.base` | 31 files | Database session |
| 4 | `app.models.user` | 16 files | User model |
| 5 | `app.core.dependencies` | 11 files | FastAPI dependencies |
| 6 | `app.models.chat` | 8 files | Chat/message model |
| 7 | `app.core.langfuse_client` | 6 files | LLM observability |
| 8 | `app.models.mixins` | 5 files | Model base classes |
| 9 | `app.services.qdrant_service` | 4 files | Vector search |
| 10 | `app.models.subscription` | 4 files | Subscription model |

### **Critical Internal Dependency Chains**

```
API Endpoint
    ↓
app.core.dependencies (get_db, get_current_user)
    ├→ app.db.base (Database session)
    ├→ app.core.config (settings)
    ├→ app.models.user (User model)
    └→ app.services.auth (Authentication)

Service Layer
    ↓
app.core.logging (get_logger)
app.core.config (get_settings)
    ↓
app.models.* (Database models)
app.schemas.* (Pydantic validation)
    ↓
app.repositories.* (Data access)
    ↓
app.db.base (Database session)
```

### **Module Import Graph (Top-Level)**

```
src/app/
├── main.py
│   ├→ core.logging
│   ├→ core.config
│   ├→ core.dependencies
│   ├→ core.metrics
│   ├→ api.v1 (all routers)
│   └→ middleware.*
│
├── core/
│   ├── config.py (⚠️ CRITICAL - 39 imports)
│   │   └→ No internal dependencies (base module)
│   ├── logging.py (⚠️ CRITICAL - 65 imports)
│   │   └→ config.py only
│   ├── dependencies.py (⚠️ CRITICAL - 11 imports)
│   │   ├→ config.py
│   │   ├→ db.base
│   │   └→ models.user
│   ├── security.py
│   │   └→ config.py
│   └── metrics.py
│       └→ config.py
│
├── api/v1/
│   ├── All endpoints depend on:
│   │   ├→ core.logging
│   │   ├→ core.dependencies
│   │   ├→ schemas.* (matching endpoint)
│   │   └→ services.* (matching endpoint)
│
├── services/ (35 services)
│   ├→ core.logging (ALL services)
│   ├→ core.config (38 services)
│   └→ Varies by service
│
├── models/ (11 models)
│   ├→ db.base (ALL models)
│   ├→ models.mixins (most models)
│   └→ sqlalchemy.*
│
├── schemas/ (Pydantic)
│   └→ pydantic only (no internal deps)
│
└── repositories/
    ├→ models.* (corresponding model)
    ├→ db.base
    └→ sqlalchemy.*
```

---

## Complete Environment Variable Mapping

**Total ENV Variables**: 129 unique variables
**Files Using ENVs**: 40 Python files

### **Top 20 Most Used ENV Variables**

| Rank | Variable | Used By | Description |
|------|----------|---------|-------------|
| 1 | `ENVIRONMENT` | 12 files | Current env (local/dev/stage/prod) |
| 2 | `LANGFUSE_ENABLED` | 9 files | LLM observability toggle |
| 3 | `OPENROUTER_API_KEY` | 6 files | Primary LLM API key |
| 4 | `APP_VERSION` | 5 files | Application version |
| 5 | `DATABASE_URL` | 5 files | Database connection |
| 6 | `OPENROUTER_APP_URL` | 5 files | App URL for OpenRouter |
| 7 | `OPENROUTER_APP_NAME` | 5 files | App name for OpenRouter |
| 8 | `DEBUG` | 4 files | Debug mode toggle |
| 9 | `IS_PRODUCTION` | 4 files | Production environment check |
| 10 | `OPENROUTER_BASE_URL` | 3 files | OpenRouter API base |
| 11 | `REDIS_URL` | 3 files | Redis connection |
| 12 | `LLM_MODEL` | 3 files | Default LLM model |
| 13 | `TEMPORAL_ENABLED` | 2 files | Temporal workflows toggle |
| 14 | `APP_NAME` | 2 files | Application name |
| 15 | `MINIO_ENABLED` | 2 files | MinIO storage toggle |

### **ENV Variables by Category**

#### **1. Core Application (8 variables)**
- `ENVIRONMENT` → 12 files
- `APP_NAME` → 2 files
- `APP_VERSION` → 5 files
- `DEBUG` → 4 files
- `API_HOST` → main.py
- `API_PORT` → main.py
- `IS_PRODUCTION` → 4 files
- `IS_STAGE` → 1 file

#### **2. Database (10 variables)**
- `DATABASE_URL` → 5 files
- `DATABASE_HOST` → core/startup.py
- `DATABASE_PORT` → core/startup.py
- `DATABASE_NAME` → 2 files
- `DATABASE_POOL_SIZE` → 2 files
- `DATABASE_MAX_OVERFLOW` → db/base.py
- `DATABASE_READ_REPLICA_ENABLED` → db/base.py
- `DATABASE_READ_REPLICA_HOST` → db/base.py
- `DATABASE_READ_REPLICA_PORT` → db/base.py
- `DATABASE_DRIVER` → db/base.py

#### **3. Redis (3 variables)**
- `REDIS_URL` → 3 files
- `REDIS_DB` → services/response_cache_service.py
- `REDIS_PASSWORD` → (if set)

#### **4. OpenRouter / LLM (15 variables)**
- `OPENROUTER_API_KEY` → 6 files
  - services/openrouter_service.py
  - services/enhanced_chat_service.py
  - services/intent_detector.py
  - services/langgraph_service.py
  - services/web_search_service.py
  - services/image_generation_service.py
- `OPENROUTER_BASE_URL` → 3 files
- `OPENROUTER_APP_NAME` → 5 files
- `OPENROUTER_APP_URL` → 5 files
- `LLM_PROVIDER` → services/langgraph_service.py
- `LLM_MODEL` → 3 files
- `LLM_TEMPERATURE` → services/openrouter_service.py
- `LLM_MAX_TOKENS` → services/openrouter_service.py
- `CACHE_CONTROL_STRATEGY` → services/openrouter_service.py
- `CACHE_MIN_TOKENS` → services/openrouter_service.py
- `PROMPT_CACHING_ENABLED` → services/openrouter_service.py
- `MODEL_ROUTING_ENABLED` → services/openrouter_service.py
- `DEFAULT_FALLBACK_MODELS` → 2 files
- `ENABLE_AUTO_ROUTER` → services/openrouter_service.py
- `TRACK_USER_IDS` → services/openrouter_service.py

#### **5. Embeddings (3 variables)**
- `EMBEDDING_PROVIDER` → services/embeddings_service.py
- `EMBEDDING_MODEL` → services/embeddings_service.py
- `EMBEDDING_DIMENSION` → 2 files

#### **6. Reranker (3 variables)**
- `RERANKER_ENABLED` → services/reranker_service.py
- `RERANKER_PROVIDER` → services/reranker_service.py
- `RERANKER_MODEL` → services/reranker_service.py

#### **7. ASR (Speech-to-Text) (6 variables)**
- `ASR_ENABLED` → api/v1/health.py
- `ASR_PROVIDER` → services/asr_service.py
- `ASR_LANGUAGE` → api/v1/health.py
- `GOOGLE_API_KEY` → services/asr_service.py, embeddings_service.py
- `GEMINI_ASR_MODEL` → services/asr_service.py
- `OPENAI_API_KEY` → services/asr_service.py

#### **8. Web Search (5 variables)**
- `WEB_SEARCH_ENABLED` → services/web_search_service.py
- `WEB_SEARCH_PROVIDER` → services/web_search_service.py
- `WEB_SEARCH_MODEL` → services/web_search_service.py
- `WEB_SEARCH_TEMPERATURE` → services/web_search_service.py
- `SERPER_API_KEY` → services/web_search_service.py

#### **9. MinIO / Storage (10 variables)**
- `MINIO_ENABLED` → 2 files
- `MINIO_ENDPOINT` → 2 files
- `MINIO_ACCESS_KEY` → services/minio_storage_service.py
- `MINIO_SECRET_KEY` → services/minio_storage_service.py
- `MINIO_BUCKET_PREFIX` → services/minio_storage_service.py
- `MINIO_BUCKET_IMAGES` → 2 files
- `MINIO_BUCKET_DOCUMENTS` → services/minio_storage_service.py
- `MINIO_BUCKET_AUDIO_RESOURCES` → services/minio_storage_service.py
- `MINIO_BUCKET_AUDIO_USER` → services/minio_storage_service.py
- `MINIO_SECURE` → services/minio_storage_service.py

#### **10. Qdrant (Vector DB) (5 variables)**
- `QDRANT_URL` → services/qdrant_service.py
- `QDRANT_API_KEY` → services/qdrant_service.py
- `QDRANT_COLLECTION_NAME` → services/qdrant_service.py
- `QDRANT_COLLECTION_PREFIX` → services/qdrant_service.py
- `QDRANT_TIMEOUT` → services/qdrant_service.py

#### **11. Temporal (Workflows) (5 variables)**
- `TEMPORAL_ENABLED` → 2 files
- `TEMPORAL_HOST` → workflows/chat_workflow.py, core/temporal_client.py
- `TEMPORAL_NAMESPACE` → core/temporal_client.py
- `TEMPORAL_TASK_QUEUE` → workflows/chat_workflow.py
- `TEMPORAL_TLS_ENABLED` → core/temporal_client.py

#### **12. Langfuse (Observability) (4 variables)**
- `LANGFUSE_ENABLED` → 9 files (most critical observability flag)
- `LANGFUSE_PUBLIC_KEY` → services/langfuse_service.py
- `LANGFUSE_SECRET_KEY` → services/langfuse_service.py
- `LANGFUSE_HOST` → services/langfuse_service.py

#### **13. Email (Mailgun/SMTP) (8 variables)**
- `EMAIL_PROVIDER` → services/email_service.py
- `MAILGUN_API_KEY` → services/email_service.py
- `MAILGUN_DOMAIN` → services/email_service.py
- `MAILGUN_FROM_EMAIL` → services/email_service.py
- `MAILGUN_FROM_NAME` → services/email_service.py
- `SMTP_HOST` → services/email_service.py
- `SMTP_PORT` → services/email_service.py
- `SMTP_USER` → services/email_service.py

#### **14. Chunking (Chonkie) (3 variables)**
- `CHUNKING_STRATEGY` → services/chonkie_service.py
- `CHUNK_SIZE` → services/chonkie_service.py
- `CHUNK_OVERLAP` → services/chonkie_service.py

#### **15. Ahkam Tool (3 variables)**
- `AHKAM_CACHE_TTL_HOURS` → services/ahkam_service.py
- `AHKAM_FETCH_TIMEOUT_SECONDS` → services/ahkam_service.py
- `AHKAM_MAX_RETRIES` → services/ahkam_service.py

#### **16. CORS (2 variables)**
- `CORS_ORIGINS` → main.py
- `CORS_ALLOW_CREDENTIALS` → main.py

#### **17. Image Generation (3 variables)**
- `IMAGE_GENERATION_ENABLED` → services/image_generation_service.py
- `IMAGE_GENERATION_MODELS` → services/image_generation_service.py
- `IMAGE_STORAGE_TYPE` → services/image_generation_service.py

#### **18. Guardrails (3 variables)**
- `GUARDRAILS_ENABLED` → services/enhanced_chat_service.py
- `GUARDRAILS_LLM_PROVIDER` → (tbd)
- `GUARDRAILS_LLM_MODEL` → (tbd)

#### **19. mem0 (Memory) (2 variables)**
- `MEM0_ENABLED` → services/enhanced_chat_service.py
- `MEM0_COMPRESSION_ENABLED` → (tbd)

### **Environment Variable Impact Matrix**

| Variable | Files Affected | Impact if Changed | Breaking Change |
|----------|----------------|-------------------|----------------|
| `OPENROUTER_API_KEY` | 6 | 🔴 All LLM features break | Yes |
| `DATABASE_URL` | 5 | 🔴 Complete app failure | Yes |
| `LANGFUSE_ENABLED` | 9 | 🟡 Observability lost | No |
| `ENVIRONMENT` | 12 | 🔴 Config mismatch | Yes |
| `REDIS_URL` | 3 | 🔴 Cache/session failure | Yes |
| `MINIO_ENABLED` | 2 | 🟡 File storage disabled | No |
| `TEMPORAL_ENABLED` | 2 | 🟡 Async workflows disabled | No |
| `ASR_ENABLED` | 1 | 🟢 Voice input disabled | No |

---

## Class and Schema Dependencies

### **Database Models (11 models)**

Located in: `src/app/models/`

```python
# Core Models
User (models/user.py)
    ├→ TimestampMixin, SoftDeleteMixin
    └→ Relationships:
        ├→ OneToMany: Chat, Subscription, Document, SupportTicket
        └→ Depends on: None

Chat (models/chat.py)
    ├→ TimestampMixin
    └→ Relationships:
        ├→ ManyToOne: User
        ├→ OneToMany: Message
        └→ Depends on: User

Message (models/chat.py)
    ├→ TimestampMixin
    └→ Relationships:
        ├→ ManyToOne: Chat
        └→ Depends on: Chat, User (indirect)

Document (models/document.py)
    ├→ TimestampMixin, SoftDeleteMixin
    └→ Relationships:
        ├→ ManyToOne: User
        ├→ OneToMany: DocumentChunk
        └→ Depends on: User

DocumentChunk (models/document.py)
    ├→ TimestampMixin
    └→ Relationships:
        ├→ ManyToOne: Document
        └→ Depends on: Document, User (indirect)

Subscription (models/subscription.py)
    ├→ TimestampMixin
    └→ Relationships:
        ├→ ManyToOne: User
        └→ Depends on: User

SupportTicket (models/support_ticket.py)
    ├→ TimestampMixin, SoftDeleteMixin
    └→ Relationships:
        ├→ ManyToOne: User
        └→ Depends on: User

Marja (models/marja.py)
    ├→ TimestampMixin
    └→ Standalone model (no user relationship)

Storage (models/storage.py)
    ├→ TimestampMixin
    └→ Tracks file storage usage

Admin (models/admin.py)
    ├→ TimestampMixin
    └→ Admin user model (separate from User)

Environment (models/environment.py)
    ├→ TimestampMixin
    └→ Tracks environment deployments
```

### **Model Mixins (Shared Base Classes)**

Located in: `src/app/models/mixins.py`

```python
TimestampMixin
    ├→ Adds: created_at, updated_at
    └→ Used by: ALL models (11 models)

SoftDeleteMixin
    ├→ Adds: deleted_at, is_deleted
    └→ Used by: User, Document, SupportTicket

UUIDMixin
    ├→ Adds: UUID primary key
    └→ Used by: (if applicable)
```

### **Pydantic Schemas**

Located in: `src/app/schemas/`

```
schemas/
├── user.py
│   ├→ UserBase, UserCreate, UserUpdate, UserResponse
│   └→ No internal dependencies (pure Pydantic)
├── chat.py
│   ├→ MessageCreate, ChatCreate, ChatResponse
│   └→ May reference: user schemas
├── auth.py
│   ├→ LoginRequest, TokenResponse, RegisterRequest
│   └→ References: user schemas
├── document.py
│   ├→ DocumentUpload, DocumentResponse
│   └→ References: user schemas
└── ... (20+ schema files)
```

**Schema Naming Convention**:
- `*Base` - Shared fields
- `*Create` - For POST requests
- `*Update` - For PATCH requests
- `*Response` - For API responses
- `*InDB` - Database representation (rare)

---

## Tool Dependencies

### **LangChain Tools**

Located in: `src/app/tools/`

```
tools/
├── __init__.py        - Tool registry
├── web_search.py      - Web search tool
│   └→ Depends on: web_search_service.py
├── ahkam_tool.py      - Islamic rulings
│   └→ Depends on: ahkam_service.py
└── ... (more tools as needed)
```

### **Utility Modules**

Located in: `src/app/utils/`

```
utils/
├── audio_utils.py     - Audio processing
├── datetime_utils.py  - Date/time conversion
├── text_utils.py      - Text processing
└── validators.py      - Custom validators
```

---

## API Endpoint Dependencies

### **All API Endpoints**

Located in: `src/app/api/v1/`

Every endpoint follows this pattern:

```python
# Example: chat.py
from app.core.dependencies import get_db, get_current_user
from app.core.logging import get_logger
from app.schemas.chat import ChatCreate, ChatResponse
from app.services.enhanced_chat_service import EnhancedChatService

@router.post("/chat")
async def create_chat(
    request: ChatCreate,              # Schema dependency
    db: AsyncSession = Depends(get_db),  # DB dependency
    user: User = Depends(get_current_user),  # Auth dependency
):
    service = EnhancedChatService(db)  # Service dependency
    return await service.process_chat(...)
```

**Standard Dependency Pattern**:
1. `app.core.dependencies` - get_db, get_current_user, etc.
2. `app.core.logging` - get_logger
3. `app.schemas.*` - Request/response validation
4. `app.services.*` - Business logic
5. `app.models.*` - (indirect via service)

### **Endpoint Groups**

| File | Endpoints | Key Dependencies |
|------|-----------|------------------|
| `auth.py` | Login, Register, OAuth | auth, google_oauth services |
| `chat.py` | Chat CRUD, Messages | enhanced_chat_service |
| `documents.py` | Upload, Search | document_service, qdrant_service |
| `asr.py` | Transcribe, Translate | asr_service |
| `images.py` | Generate images | image_generation_service |
| `health.py` | Health check | core/health.py |
| `admin.py` | Admin operations | admin_service |
| `subscriptions.py` | Subscription CRUD | subscription_service |
| `support.py` | Support tickets | support_service |
| `tools.py` | Tool management | tool_orchestration_service |
| `websocket.py` | Real-time chat | WebSocket, enhanced_chat_service |

---

## Database Schema Relationships

### **Entity Relationship Diagram (Simplified)**

```
┌─────────────┐
│    User     │
│  (Primary)  │
└──────┬──────┘
       │
       ├──── OneToMany ───┬─── Chat
       │                  ├─── Subscription
       │                  ├─── Document
       │                  └─── SupportTicket
       │
┌──────┴──────────┐
│      Chat       │
└──────┬──────────┘
       │
       └──── OneToMany ──── Message

┌─────────────────┐
│    Document     │
└──────┬──────────┘
       │
       └──── OneToMany ──── DocumentChunk
                             (Stores: embedding_vector, qdrant_id)

Standalone:
- Marja (Islamic scholars)
- Admin (Admin users)
- Storage (File tracking)
- Environment (Deployment tracking)
```

### **Foreign Key Constraints**

```sql
-- Critical constraints
Chat.user_id → User.id (ON DELETE CASCADE)
Message.chat_id → Chat.id (ON DELETE CASCADE)
Document.user_id → User.id (ON DELETE CASCADE)
DocumentChunk.document_id → Document.id (ON DELETE CASCADE)
Subscription.user_id → User.id (ON DELETE CASCADE)
SupportTicket.user_id → User.id (ON DELETE SET NULL)
```

---

## Custom Middleware

Located in: `src/app/middleware/`

```
middleware/
├── security.py
│   ├→ RateLimitMiddleware
│   ├→ SecurityHeadersMiddleware
│   └→ Depends on: Redis, rate_limiter_service
│
└── usage_tracking.py
    ├→ UsageTrackingMiddleware
    └→ Depends on: Database, core/metrics
```

**Middleware Execution Order** (in `main.py`):
1. CORSMiddleware
2. SecurityHeadersMiddleware
3. RateLimitMiddleware
4. UsageTrackingMiddleware
5. PrometheusMiddleware (metrics)

---

## Repository Pattern

Located in: `src/app/repositories/`

```
repositories/
├── user_repository.py
│   └→ CRUD operations for User model
├── chat_repository.py
│   └→ CRUD operations for Chat/Message models
├── document_repository.py
│   └→ CRUD operations for Document/Chunk models
└── ... (11 repositories total)
```

**Pattern**:
```python
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        # Data access logic
    
    async def create(self, user_data: dict) -> User:
        # Creation logic
```

---

## Workflow Dependencies (Temporal)

Located in: `src/app/workflows/`

```
workflows/
└── chat_workflow.py
    ├→ Temporal client
    ├→ Database (async session)
    ├→ Services: enhanced_chat_service
    └→ Activities: process_message, generate_response, etc.
```

**Workflow Activities**:
- `process_user_message` - Main chat processing
- `generate_llm_response` - LLM generation
- `update_conversation_memory` - mem0 update
- `log_to_langfuse` - Observability

---

## Configuration Method Dependencies

### **How Services Get Configuration**

```python
# Pattern 1: Import settings directly
from app.core.config import get_settings
settings = get_settings()

# Pattern 2: getattr with default
from app.core.config import get_settings
settings = get_settings()
api_key = getattr(settings, "openrouter_api_key", None)

# Pattern 3: Direct attribute access
settings.openrouter_api_key  # May raise AttributeError
```

### **Configuration Access Patterns**

| Service | Pattern | Reason |
|---------|---------|--------|
| **Core services** | Direct import | Always required |
| **Optional services** | getattr with default | May be disabled |
| **Dynamic services** | Runtime checks | Feature flags |

---

## Cross-Cutting Concerns

### **1. Logging**

**Every file uses**:
```python
from app.core.logging import get_logger
logger = get_logger(__name__)
```

**Impact**: Changing logging structure affects ALL 103 Python files

### **2. Database Sessions**

**Pattern**:
```python
from app.core.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def endpoint(db: AsyncSession = Depends(get_db)):
    # Use db
```

**Files affected**: All API endpoints (18 files) + Services (35 files)

### **3. Authentication**

**Pattern**:
```python
from app.core.dependencies import get_current_user
from app.models.user import User

async def endpoint(user: User = Depends(get_current_user)):
    # User is authenticated
```

**Files affected**: All protected endpoints (~15 files)

---

## Critical Path Analysis

### **User Request → Response Flow**

```
1. Nginx (port 8100) → FastAPI (port 8000-8003)
2. CORS Middleware
3. Security Middleware
4. Rate Limit Middleware
5. Usage Tracking Middleware
6. FastAPI Router (api/v1/*.py)
7. FastAPI Dependencies (get_db, get_current_user)
8. Pydantic Schema Validation
9. Service Layer (services/*.py)
10. Repository Layer (repositories/*.py)
11. Database (PostgreSQL)
12. External APIs (OpenRouter, Qdrant, etc.)
13. Response Serialization (Pydantic)
14. Prometheus Metrics
15. Return to client
```

**Single Points of Failure**:
1. `app.core.config` - Settings initialization
2. `app.db.base` - Database connection
3. `app.core.logging` - Logging system
4. OpenRouter API - Primary LLM
5. PostgreSQL - Primary database
6. Redis - Cache/sessions

---

## Dependency Update Strategy

### **When Updating a Core Module**

If you change:
- `app.core.config` → Affects 39 files
- `app.core.logging` → Affects 65 files
- `app.db.base` → Affects 31 files
- `app.models.user` → Affects 16 files

**Testing Strategy**:
1. Run unit tests for the module
2. Run integration tests for dependent services
3. Run E2E tests for affected API endpoints
4. Check all 4 environments (LOCAL → DEV → STAGE → PROD)

### **When Adding a New ENV Variable**

1. Add to `src/app/core/config.py`
2. Add to `.env.example`
3. Update this `DEPENDENCY_MAPPING.md`
4. Document in affected service docstrings
5. Add validation if critical
6. Add to health check if applicable

### **When Adding a New Service**

1. Create in `src/app/services/`
2. Add dependencies clearly in docstring
3. Update this `DEPENDENCY_MAPPING.md`
4. Add to service dependency graph
5. Create corresponding repository if DB access needed
6. Create corresponding schema if API exposed
7. Add metrics if critical path
8. Add health check if external API

---

## Debugging Dependency Issues

### **Find What Uses a Module**

```bash
# Find all imports of a module
grep -r "from app.services.X import\|import app.services.X" src/

# Find all references to a class
grep -r "ClassName" src/

# Find all ENV variable usage
grep -r "VARIABLE_NAME" src/
```

### **Find What a Module Uses**

```bash
# See all imports in a file
head -50 src/app/services/service_name.py | grep "^import\|^from"

# See all env variables used
grep -E "getattr\(settings|settings\." src/app/services/service_name.py
```

### **Circular Dependency Detection**

```bash
# Use Python's built-in tool
python3 -m pydeps src/app --max-bacon 2 --show-deps
```

---

**Last Updated**: 2025-01-14
**Total Dependencies Mapped**:
- External APIs: 8
- Services: 35
- Models: 11
- Schemas: 20+
- ENV Variables: 129
- Internal Modules: 60+

