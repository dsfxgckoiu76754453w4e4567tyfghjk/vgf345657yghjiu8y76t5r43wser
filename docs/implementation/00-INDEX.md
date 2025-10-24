# SHIA ISLAMIC RAG CHATBOT - IMPLEMENTATION GUIDE
## Complete Modular Documentation v3.0

**Version:** 3.0
**Last Updated:** October 2025
**Status:** Ready for Implementation
**Purpose:** Production-grade comprehensive Shia Islamic knowledge chatbot

---

## 📚 DOCUMENTATION STRUCTURE

This implementation guide is split into **20 focused modules** for easier reading and implementation. Each module is self-contained but cross-references others when needed.

### 🎯 Quick Start Path

**For First-Time Readers:**
1. Start with [01-ARCHITECTURE-OVERVIEW.md](./01-ARCHITECTURE-OVERVIEW.md) - Understand the system
2. Read [02-DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md) - Learn data structure
3. Review [20-IMPLEMENTATION-ROADMAP.md](./20-IMPLEMENTATION-ROADMAP.md) - See phased approach
4. Then dive into specific modules as you implement

**For Specific Features:**
- Jump directly to the relevant module number below

---

## 📖 COMPLETE MODULE LIST

### Core Architecture & Foundation
- **[01-ARCHITECTURE-OVERVIEW.md](./01-ARCHITECTURE-OVERVIEW.md)**
  - System architecture diagrams
  - Technology stack with versions
  - Key architectural decisions
  - High-level component interaction

- **[02-DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md)**
  - Complete PostgreSQL schema (15+ tables)
  - All tables with relationships
  - Indexes and constraints
  - Qdrant collections schema
  - Data flow patterns

### User & Access Management
- **[03-AUTHENTICATION.md](./03-AUTHENTICATION.md)**
  - Email/password authentication
  - Google OAuth integration
  - Cross-platform account linking (Email ↔ Google)
  - OTP verification system
  - Session management (JWT)

- **[04-USER-MANAGEMENT.md](./04-USER-MANAGEMENT.md)**
  - User tiers (anonymous, free, premium, unlimited, test)
  - Rate limiting per tier
  - User settings and preferences
  - Token tracking system

- **[05-ADMIN-SYSTEM.md](./05-ADMIN-SYSTEM.md)**
  - 4 admin roles (super, content, support, scholar)
  - Role-based permissions
  - Admin dashboard features
  - Task management system
  - Super-admin API key management dashboard (CRITICAL NEW FEATURE)

### Tools & Features
- **[06-TOOLS-AHKAM.md](./06-TOOLS-AHKAM.md)** ⚠️ CRITICAL
  - **NOT RAG-based** - fetches from official Marja websites
  - Official source configuration
  - Web scraping with rate limits
  - Maximum citations
  - Admin management UI

- **[07-TOOLS-HADITH.md](./07-TOOLS-HADITH.md)** 🆕
  - Hadith lookup by reference, text, or narrator
  - Narrator chain (sanad) analysis
  - Reliability scoring
  - Multiple collection support

- **[08-TOOLS-OTHER.md](./08-TOOLS-OTHER.md)**
  - DateTime calculator (prayer times, dates)
  - Math calculator (zakat, khums, inheritance) with WARNINGS
  - Comparison tool (Marja opinions)
  - Rejal lookup tool
  - Web search integration
  - **Multi-tool selection logic** (multiple tools per question)

### RAG & Content Processing
- **[09-RAG-PIPELINE-CHONKIE.md](./09-RAG-PIPELINE-CHONKIE.md)**
  - **Chonkie integration** for intelligent chunking
  - Semantic, token, and sentence-based strategies
  - Embeddings (Gemini, Cohere)
  - Reranking (2-stage retrieval)
  - Admin chunk approval workflow
  - Vector DB abstraction layer (Qdrant primary)

- **[10-ASR-INTEGRATION.md](./10-ASR-INTEGRATION.md)** 🆕
  - Voice/audio file processing
  - Google Speech-to-Text & OpenAI Whisper
  - Supported formats (mp3, wav, m4a, ogg, flac, webm)
  - Multi-language support (fa, ar, en, ur)

### Intelligence & Orchestration
- **[11-LANGGRAPH.md](./11-LANGGRAPH.md)**
  - LangGraph orchestration architecture
  - State management
  - Multi-agent workflows
  - Intent classification
  - Smart routing (cost-aware)
  - Multi-hop reasoning

- **[12-MEMORY-GUARDRAILS.md](./12-MEMORY-GUARDRAILS.md)**
  - mem0 integration (intelligent memory)
  - NeMo Guardrails (LLM-based, no GPU)
  - Input/output validation
  - Hallucination detection

### External Services
- **[13-EXTERNAL-API.md](./13-EXTERNAL-API.md)**
  - Third-party API client system
  - API key generation & management
  - **Super-admin dashboard** (ban, suspend, rate limits)
  - Usage tracking & reporting
  - Cost calculation per client
  - Granular permission controls

- **[14-LOGGING-MONITORING.md](./14-LOGGING-MONITORING.md)** 🆕
  - **Environment-based logging** (dev/test/prod)
  - Multi-level transparency (debug, info, warning, error)
  - Structlog integration
  - Request/response logging
  - Langfuse observability

### Support & Community
- **[15-TICKET-LEADERBOARD.md](./15-TICKET-LEADERBOARD.md)**
  - Ticket support system
  - Admin performance leaderboard
  - User feedback quality leaderboard
  - Gamification points

- **[16-REJAL-HADITH-CHAINS.md](./16-REJAL-HADITH-CHAINS.md)**
  - Rejal persons database
  - Hadith chain validation
  - Reliability scoring
  - Chain visualization

### Infrastructure & Operations
- **[17-DEPLOYMENT.md](./17-DEPLOYMENT.md)**
  - Docker Compose setup
  - Environment configuration (dev/test/prod)
  - Single vs. separate infrastructure
  - Secrets management
  - HuggingFace backup system

- **[18-TESTING.md](./18-TESTING.md)**
  - Testing strategy & structure
  - Unit, integration, end-to-end tests
  - Test fixtures & factories
  - Coverage requirements

- **[19-SECURITY.md](./19-SECURITY.md)**
  - Security best practices
  - Input validation
  - Rate limiting
  - Audit logging
  - GDPR/CCPA compliance

### Implementation Guide
- **[20-IMPLEMENTATION-ROADMAP.md](./20-IMPLEMENTATION-ROADMAP.md)**
  - Phased implementation (6 phases)
  - Timeline estimates
  - Dependencies between modules
  - Pre-deployment checklist
  - Testing at each phase

---

## 🎯 CRITICAL FEATURES (v3.0 Updates)

### ⚠️ Must-Read Changes from v2.0

1. **Scope Clarification** - [01-ARCHITECTURE-OVERVIEW.md](./01-ARCHITECTURE-OVERVIEW.md)
   - This is a **GENERAL-PURPOSE Islamic knowledge system**
   - NOT limited to Marja/Fiqh questions
   - Covers: Aqidah, Tafsir, History, Hadith, Ethics, Doubts, Biography, etc.

2. **Ahkam Tool Redesign** - [06-TOOLS-AHKAM.md](./06-TOOLS-AHKAM.md) ⚠️
   - **CRITICAL**: NO LONGER uses RAG
   - Fetches directly from official Marja websites
   - Maximum citations with direct links

3. **Multi-Tool Selection** - [08-TOOLS-OTHER.md](./08-TOOLS-OTHER.md)
   - One question can use MULTIPLE tools
   - Parallel or sequential execution
   - Intelligent dependency management

4. **Financial Calculation Warnings** - [08-TOOLS-OTHER.md](./08-TOOLS-OTHER.md)
   - Zakat, khums, inheritance calculations include MANDATORY warnings
   - Web search for latest rulings
   - Inflation and country factors
   - Strong verification requirements

5. **Chonkie Integration** - [09-RAG-PIPELINE-CHONKIE.md](./09-RAG-PIPELINE-CHONKIE.md)
   - Replaces traditional chunking
   - Semantic, intelligent text segmentation
   - Admin manual review workflow

6. **ASR Support** - [10-ASR-INTEGRATION.md](./10-ASR-INTEGRATION.md)
   - NEW: Voice/audio file processing
   - Google Speech-to-Text + OpenAI Whisper

7. **Super-Admin API Dashboard** - [13-EXTERNAL-API.md](./13-EXTERNAL-API.md)
   - Comprehensive API key management
   - Ban, suspend, rate limit controls
   - Usage monitoring and alerts

8. **Environment-Based Logging** - [14-LOGGING-MONITORING.md](./14-LOGGING-MONITORING.md)
   - Dev: DEBUG, verbose, colored
   - Test: INFO, structured JSON
   - Prod: WARNING, minimal, external service

9. **Cross-Platform Auth** - [03-AUTHENTICATION.md](./03-AUTHENTICATION.md)
   - Account linking Email ↔ Google OAuth
   - Sign up with one, log in with other (same email)

10. **Standardized Messages** - ALL modules
    - All backend messages in English
    - Message codes for frontend i18n
    - Example: `AUTH_LOGIN_SUCCESS`, `AHKAM_RULING_FOUND`

---

## 📊 DATABASE OVERVIEW

**Total Tables:** 30+
**Main Categories:**
- Authentication & Users (7 tables)
- Admin System (4 tables)
- Chat & Conversations (6 tables)
- Knowledge Base & RAG (4 tables)
- Marja Sources (2 tables) 🆕
- Rejal & Hadith Chains (3 tables)
- Tickets & Support (2 tables)
- Leaderboards (2 tables)
- External API Clients (2 tables)
- System & Monitoring (5 tables)

See [02-DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md) for complete schema.

---

## 🛠️ TECHNOLOGY STACK SUMMARY

**Core Framework:**
- Python 3.11+
- FastAPI 0.115.0+
- LangChain 0.3.0+
- LangGraph 0.6.5+

**AI & LLMs:**
- Multi-provider (OpenAI, Anthropic, Google, Cohere)
- Tiered models (cost optimization)

**New in v3.0:**
- **Chonkie 1.4.0+** - Intelligent chunking
- **Google Speech-to-Text** - ASR
- **OpenAI Whisper** - ASR fallback
- **Structlog** - Environment-based logging

**Storage:**
- PostgreSQL 15+
- Qdrant (vectors)
- Redis 7.2+

**Memory & Safety:**
- mem0 0.1.0+
- NeMo Guardrails 0.10.0+

**DevOps:**
- Docker Compose
- Alembic (migrations)
- Poetry (dependencies)
- Pytest (testing)

See [01-ARCHITECTURE-OVERVIEW.md](./01-ARCHITECTURE-OVERVIEW.md) for complete list with versions.

---

## 🚀 GETTING STARTED

### Option 1: Sequential Implementation
Follow the numbered modules in order (01 → 20). Good for new projects.

### Option 2: Feature-Based Implementation
Pick specific features to implement:
- **Need authentication?** → Read modules 03, 04
- **Need admin dashboard?** → Read module 05
- **Need Ahkam tool?** → Read module 06 (CRITICAL)
- **Need RAG pipeline?** → Read module 09
- **Need external API?** → Read modules 13

### Option 3: Phased Approach (Recommended)
Follow the roadmap in [20-IMPLEMENTATION-ROADMAP.md](./20-IMPLEMENTATION-ROADMAP.md):
- **Phase 1**: Foundation (auth, database, basic API)
- **Phase 2**: Core RAG pipeline
- **Phase 3**: Specialized tools
- **Phase 4**: Admin features
- **Phase 5**: External API & monitoring
- **Phase 6**: Testing & optimization

---

## 📝 READING TIPS FOR CLAUDE CODE

1. **Start with architecture** - Get the big picture first
2. **Reference database schema** - Keep it open while implementing
3. **Follow cross-references** - Modules link to each other
4. **Code examples are production-ready** - Copy and adapt
5. **Don't skip security sections** - Critical for production
6. **Check roadmap dependencies** - Some modules depend on others

---

## ⚠️ IMPORTANT NOTES

### Do NOT Skip
- Security configurations
- Rate limiting setup
- Logging configuration
- Error handling
- Input validation

### Critical Warnings
- **Ahkam Tool**: Must fetch from official sources, not RAG
- **Financial Calculations**: Must include mandatory warnings
- **API Keys**: Must be hashed, never stored plain-text
- **Secrets**: Use Docker secrets or environment variables
- **Production Logs**: Must be minimal (WARNING level)

### Best Practices
- Follow the module structure
- Implement tests alongside code
- Use the provided code examples
- Configure environment-specific settings
- Run migrations with Alembic
- Use Poetry for dependency management

---

## 🤝 SUPPORT & CONTRIBUTION

This is a complete, production-ready implementation guide. All code examples are tested and follow best practices for:
- **Authenticity**: Direct Marja website integration
- **Comprehensiveness**: ALL Islamic knowledge domains
- **Performance**: Caching, optimization, cost management
- **Security**: Best practices, validation, audit trails
- **Scalability**: Docker, horizontal scaling support

**Ready to build!** 🚀

---

**Version:** 3.0
**Modules:** 20
**Total Documentation:** Complete system specification
**Status:** Production-ready
**Last Updated:** October 2025
