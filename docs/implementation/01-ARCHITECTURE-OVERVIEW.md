# MODULE 01: ARCHITECTURE OVERVIEW
[◀️ Back to Index](./00-INDEX.md) | [Next: Database Schema ▶️](./02-DATABASE-SCHEMA.md)

---

## 📋 TABLE OF CONTENTS
1. [Purpose & Scope](#purpose--scope)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Key Architectural Decisions](#key-architectural-decisions)
5. [Component Interaction](#component-interaction)

---

## EXECUTIVE SUMMARY

### Purpose
Build a production-grade, intelligent **comprehensive Shia Islamic chatbot** using RAG (Retrieval-Augmented Generation) technology with advanced features including multi-hop reasoning, specialized Islamic scholarship tools, comprehensive admin controls, and external API capabilities.

**IMPORTANT**: This chatbot is designed as a **general-purpose Islamic knowledge system**, covering ALL aspects of Shia Islam including but NOT limited to:
- **Aqidah** (Theology & Beliefs)
- **Fiqh** (Jurisprudence) & Ahkam (Rulings) - with Marja-specific guidance
- **Tafsir** (Quranic Interpretation & Commentary)
- **History** (Islamic & Shia History, Events, Figures)
- **Hadith** (Prophetic & Imams' Traditions)
- **Akhlaq** (Ethics & Morality)
- **Doubts Resolution** (Addressing Misconceptions & Questions)
- **Rejal** (Hadith Narrator Analysis)
- **Du'a & Supplications**
- **Biography** (Lives of Prophets, Imams, Scholars)
- **Contemporary Issues** (Modern-day Religious Guidance)

While Marja rulings and Fiqh are important components, they represent only ONE aspect of this comprehensive system.

### Key Characteristics
- **Primary Language**: Persian (Farsi) - with Arabic, English, and Urdu support
- **Backend Messages**: All standardized in English (frontend handles i18n/translation)
- **Architecture**: LangGraph-based multi-agent orchestration
- **Memory**: mem0 integration for intelligent, persistent memory
- **Guardrails**: NeMo Guardrails for LLM-based safety checks (no GPU required)
- **Vector DB**: Qdrant (with abstraction layer for future migration)
- **Chunking**: Chonkie library for intelligent, semantic text segmentation
- **ASR Support**: Automatic Speech Recognition for voice/audio file processing
- **Deployment**: Docker Compose with support for single-instance and multi-instance infrastructure
- **Multi-hop Intelligence**: Advanced reasoning for complex Islamic questions
- **External API**: Expose services to third-party companies

### Core Differentiators
1. **Comprehensive Islamic Knowledge** - Not limited to Fiqh/Ahkam, covers ALL religious domains
2. **Marja-Specific Rulings** - Direct integration with official Marja websites (NOT RAG-based for Ahkam)
3. **Rejal (narrator chain) validation and visualization**
4. **Professional hadith authentication and lookup**
5. **Multi-tier admin system with role-based permissions**
6. **Super-admin API key management dashboard** for third-party service control
7. **Comprehensive ticket support system**
8. **Dual leaderboards** (admin performance & user feedback quality)
9. **Chonkie-powered intelligent chunking** with admin approval workflow
10. **ASR (Speech-to-Text)** for voice/audio file support
11. **Cross-platform authentication** (Email/Google OAuth with account linking)
12. **Environment-aware multi-level logging** (dev/test/prod)
13. **HuggingFace-based backup system**
14. **External API for third-party integration**
15. **Test user environment with full separation**

---


## SYSTEM ARCHITECTURE OVERVIEW

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client Layer (UI)                                  │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │  Web UI      │  │  Mobile App  │  │ Admin Panel  │  │ External APIs │   │
│  │  (Persian)   │  │  (iOS/Android)  │  Dashboard   │  │  (3rd Party)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ SSE/WebSocket/REST
┌────────────────────────────────▼────────────────────────────────────────────┐
│                         FastAPI Gateway Layer                                │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ Rate Limiter │  │ Auth Middle  │  │ ENV Validator│  │ Secret Check  │   │
│  │ (Tier-based) │  │ (JWT/OAuth)  │  │ Pre-flight   │  │ Pre-flight    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ API Logging  │  │ Token Track  │  │ Request Val  │  │ Response Cache│   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                    LangGraph Orchestration Layer                             │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Query Processing Graph                              │ │
│  │                                                                        │ │
│  │  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐          │ │
│  │  │Input        │───▶│Intent        │───▶│Query Refinement│          │ │
│  │  │Guardrail    │    │Classification│    │with mem0       │          │ │
│  │  │(NeMo)       │    │(Multi-cat)   │    │                │          │ │
│  │  └─────────────┘    └──────────────┘    └────────┬───────┘          │ │
│  │                                                    │                  │ │
│  │                         ┌──────────────────────────▼────────────┐    │ │
│  │                         │    Smart Router (Cost-Aware)          │    │ │
│  │                         │    ├─ Greeting → Cheap LLM           │    │ │
│  │                         │    ├─ Simple QA → Mid-Tier LLM       │    │ │
│  │                         │    ├─ Complex → Top-Tier LLM         │    │ │
│  │                         │    └─ Multi-hop → Deep Search Flow   │    │ │
│  │                         └──────────────┬────────────────────────┘    │ │
│  └────────────────────────────────────────┼─────────────────────────────┘ │
│                                            │                                 │
│  ┌────────────────────────────────────────▼─────────────────────────────┐ │
│  │                    Execution Graphs (Parallel/Sequential)            │ │
│  │                                                                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │ │
│  │  │ Retrieval    │  │ Tool Calling │  │ Web Search   │             │ │
│  │  │ Graph        │  │ Graph        │  │ Graph        │             │ │
│  │  │ (2-stage)    │  │ (Parallel)   │  │ (Vertex AI)  │             │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │ │
│  │                                                                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │ │
│  │  │ Rejal        │  │ Multi-hop    │  │ mem0 Memory  │             │ │
│  │  │ Validation   │  │ Reasoning    │  │ Ops          │             │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │ │
│  └──────────────────────────────┬───────────────────────────────────────┘ │
│                                  │                                          │
│  ┌──────────────────────────────▼───────────────────────────────────────┐ │
│  │                  Response Generation & Post-Processing               │ │
│  │                                                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │ LLM          │  │ Citation     │  │ Output       │              │ │
│  │  │ Generation   │  │ Generation   │  │ Guardrail    │              │ │
│  │  │ (Streaming)  │  │              │  │ (NeMo)       │              │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │ │
│  │                                                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │ Hallucination│  │ Suggestion   │  │ Token        │              │ │
│  │  │ Detection    │  │ Generation   │  │ Tracking     │              │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                           Service Layer                                      │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ LLM Selector │  │ Embedder     │  │ Reranker     │  │ Tool Service  │   │
│  │ (Multi-tier) │  │ (Gemini/     │  │ (Cohere/     │  │ (Ahkam, Math, │   │
│  │              │  │  Cohere)     │  │  Vertex)     │  │  DateTime,etc)│   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ NeMo         │  │ mem0 Memory  │  │ Rejal        │  │ Ticket        │   │
│  │ Guardrails   │  │ Manager      │  │ Validator    │  │ System        │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                           Data Layer                                         │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ Qdrant       │  │ PostgreSQL   │  │ Redis        │  │ Langfuse      │   │
│  │ (Vectors)    │  │ (Relational) │  │ (Cache/Queue)│  │ (Observability│   │
│  │ Docker       │  │ 15+          │  │ Streams      │  │ Self-hosted)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │ HuggingFace  │  │ Docker Secrets│ │ Alembic      │                      │
│  │ (Backup)     │  │ Manager      │  │ (Migrations) │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

**1. LangGraph as Central Orchestrator**
- Enables complex multi-agent workflows
- Built-in state management and persistence
- Supports streaming and interrupts
- Node-level caching for performance
- Latest version: 0.6.5+ (Python)

**2. mem0 for Memory Management**
- Intelligent memory compression (up to 80% token reduction)
- Semantic understanding of context
- Cross-session persistence
- User-level fact tracking
- Integration: Native LangGraph support

**3. NeMo Guardrails (LLM-based)**
- No GPU requirements (uses LLM for checks)
- Input and output validation
- Dialog flow control
- Islamic content appropriateness checks
- Integration: RunnableRails with LangGraph

**4. Dynamic Vector DB Abstraction**
- Primary: Qdrant (latest features with binary quantization)
- Abstraction layer for future migration to Elasticsearch/others
- Hybrid search (dense + sparse vectors)
- Payload filtering capabilities

**5. Multi-Tier Infrastructure Support**
- **Option A**: Single infrastructure with logical separation (dev/test/prod in one DB)
- **Option B**: Separate infrastructures (separate DBs, Redis, etc.)
- Docker Compose orchestration for both
- Environment-specific configuration

---


## TECHNOLOGY STACK & VERSIONS

### Core Framework
```yaml
langchain: ">=0.3.0"  # V1.0 alpha available, migrating in October 2025
langgraph: ">=0.6.5"  # Latest with node caching, deferred nodes
langchain-openai: "latest"
langchain-anthropic: "latest"
langchain-google-vertexai: "latest"
langchain-google-genai: "latest"
langchain-cohere: "latest"
fastapi: ">=0.115.0"
uvicorn[standard]: ">=0.30.0"
python: "3.11+"
```

### LLM & AI Services
```yaml
# Multi-Provider Support (all integrated via LangChain)
llm_providers:
  - anthropic  # Claude models
  - openai  # GPT models
  - google_vertexai  # Gemini via Vertex AI
  - google_genai  # Gemini via Google AI
  - cohere  # Command models
  - openrouter  # Multi-model aggregator

# Model Tiers for Cost Optimization
tier_1_high_quality:
  - claude-sonnet-4-5
  - qwen-max-3

tier_2_balanced:
  - gpt-5-mini
  - gemini-2.5-flash
  - grok-4-fast

tier_3_fast_cheap:
  - gemini-flash-2.5-lite
  - gemini-flash-2.0
  
# Embeddings (Switchable)
embeddings:
  primary: "gemini-embedding-001"  # Google Vertex AI
  secondary: "embed-multilingual-v4.0"  # Cohere
  dimension_primary: 3072
  dimension_secondary: 1536

# Rerankers (2-stage retrieval)
rerankers:
  primary: "rerank-3.5"  # Cohere
  secondary: "Vertex AI Ranking API"  # Google

# Web Search
web_search: "Google Vertex AI Search"
```

### Memory & Guardrails
```yaml
mem0:
  package: "mem0ai>=0.1.0"
  features:
    - intelligent_compression
    - semantic_understanding
    - cross_session_memory
    - user_fact_tracking
  integration: "langgraph"
  
nemo_guardrails:
  package: "nemoguardrails>=0.10.0"
  repository: "https://github.com/NVIDIA-NeMo/Guardrails"
  docs: "https://docs.nvidia.com/nemo/guardrails/latest/"
  features:
    - input_rails
    - output_rails
    - dialog_rails
    - llm_based_validation  # No GPU required
  integration: "RunnableRails"
  colang_version: "2.0"
```

### Storage & Infrastructure
```yaml
qdrant:
  package: "qdrant-client>=1.11.0"
  deployment: "docker"
  image: "qdrant/qdrant:latest"
  features:
    - binary_quantization  # 40x performance boost
    - hybrid_search  # Dense + Sparse vectors
    - payload_filtering
    - horizontal_scaling

postgresql:
  version: "15+"
  extensions:
    - pgvector  # For potential hybrid storage
    - pg_trgm  # For text search
  connection_pooling: "SQLAlchemy + asyncpg"

redis:
  version: "7.2+"
  modules:
    - RedisJSON
    - RedisSearch
    - RedisTimeSeries
  features:
    - multi_level_caching
    - message_queues  # Redis Streams
    - rate_limiting

langfuse:
  deployment: "self-hosted or cloud" # should both support and be switchable
  repository: https://github.com/langfuse/langfuse
  docs: https://langfuse.com/guides/cookbook/integration_langgraph
  purpose: "observability and tracing"
  integration: "langraph"
```

### Chunking & Text Processing
```yaml
chonkie:
  package: "chonkie>=1.4.0"
  repository: "https://github.com/chonkie-inc/chonkie"
  docs: "https://docs.chonkie.ai"
  features:
    - semantic_chunking  # Context-aware chunking
    - token_chunking  # Token-based splitting
    - sentence_chunking  # Sentence-based splitting
    - multilingual_support  # 56+ languages including Persian & Arabic
    - custom_chunkers  # Extensible chunking strategies
  integration: "Direct API"
  use_cases:
    - automatic_document_chunking
    - admin_assisted_chunking  # With manual review UI
    - optimized_for_rag
```

### ASR (Automatic Speech Recognition)
```yaml
asr_providers:
  primary: "google_speech_to_text"  # Google Cloud Speech-to-Text
  secondary: "openai_whisper"  # Whisper API
  local_option: "whisper_local"  # Local Whisper model (optional)

supported_formats:
  - mp3
  - wav
  - m4a
  - ogg
  - flac
  - webm

supported_languages:
  - fa  # Persian/Farsi
  - ar  # Arabic
  - en  # English
  - ur  # Urdu

features:
  - automatic_language_detection
  - speaker_diarization  # Optional
  - punctuation_restoration
  - timestamps  # Word-level or phrase-level
```

### Development Tools
```yaml
dependency_management:
  tool: "poetry>=1.8.0"
  features:
    - script_automation
    - virtual_environment
    - lock_file_management

database_migrations:
  tool: "alembic>=1.13.0"
  features:
    - version_control
    - rollback_support
    - auto_generation

testing:
  - pytest>=8.0.0
  - pytest-asyncio>=0.23.0
  - pytest-cov>=4.0.0
  - factory-boy>=3.3.0
  - faker>=22.0.0

code_quality:
  - ruff>=0.5.0  # Linter + Formatter (replaces black, isort, flake8)
  - mypy>=1.11.0  # Type checking
  - pre-commit>=3.7.0

documentation:
  tool: "mkdocs-material>=9.5.0"
  features:
    - api_documentation
    - architecture_diagrams
    - admin_guides
```

### Container Orchestration
```yaml
docker:
  compose_version: "3.9"
  base_images:
    python: "python:3.11-slim"
    postgres: "postgres:15-alpine"
    redis: "redis:7.2-alpine"
    qdrant: "qdrant/qdrant:latest"

secrets_management:
  tool: "docker-secrets"  # Built-in Docker Compose secrets
  alternative: "doppler"  # Open-source secrets manager
  features:
    - environment_specific
    - rotation_support
    - audit_logging
```

---


---

## 🔗 Related Modules
- **Next:** [02-DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md) - Complete database structure
- **Implementation:** [20-IMPLEMENTATION-ROADMAP.md](./20-IMPLEMENTATION-ROADMAP.md) - Phased approach

---

[◀️ Back to Index](./00-INDEX.md) | [Next: Database Schema ▶️](./02-DATABASE-SCHEMA.md)
