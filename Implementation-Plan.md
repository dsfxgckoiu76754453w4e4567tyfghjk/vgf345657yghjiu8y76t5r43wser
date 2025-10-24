# SHIA ISLAMIC RAG CHATBOT - COMPLETE IMPLEMENTATION PLAN

## 📋 Overview

This comprehensive implementation plan has been created as a complete, production-ready blueprint for building a Shia Islamic RAG chatbot with advanced features. The plan incorporates ALL your specified requirements and is structured as a detailed prompt that can be given to an AI application builder.

## 📦 What's Included

The complete plan is divided into **THREE PARTS** for easier navigation:

### **Part 1: Core Architecture & Database**

**Contents:**
- Executive Summary
- System Architecture Overview (with detailed diagrams)
- Technology Stack & Latest Versions (verified with web search)
- Complete Database Schema (PostgreSQL)
  - All tables with your modifications applied
  - Token tracking system
  - Admin roles (4 types)
  - Ticket support
  - Leaderboards
  - Rejal validation
  - External API clients
  - And more...
- Qdrant Collections Schema
- LangGraph Implementation (partial)


# COMPREHENSIVE IMPLEMENTATION PLAN: Shia Islamic RAG Chatbot
## Production-Grade Architecture & Complete Development Blueprint

**Version:** 3.0 (UPDATED)
**Last Updated:** October 2025
**Target Implementation:** Q1-Q2 2026
**Primary Language:** Persian (Farsi)
**Status:** Ready for Implementation

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Technology Stack & Versions](#technology-stack--versions)
4. [Complete Database Schema](#complete-database-schema)
5. [LangGraph Implementation](#langgraph-implementation)
6. [Memory Management with mem0](#memory-management-with-mem0)
7. [Guardrails with NeMo](#guardrails-with-nemo)
8. [Authentication & User Management](#authentication--user-management)
9. [Multi-Tier User System](#multi-tier-user-system)
10. [Token Tracking System](#token-tracking-system)
11. [RAG Pipeline with Chonkie](#rag-pipeline-with-chonkie)
12. [Specialized Tools & Features](#specialized-tools--features)
13. [Admin Dashboard](#admin-dashboard)
14. [Super-Admin API Key Management](#super-admin-api-key-management)
15. [API for External Companies](#api-for-external-companies)
16. [Ticket Support System](#ticket-support-system)
17. [Leaderboard Systems](#leaderboard-systems)
18. [Rejal & Hadith Chain Validation](#rejal--hadith-chain-validation)
19. [ASR (Speech-to-Text) Integration](#asr-speech-to-text-integration)
20. [Logging System (Environment-Based)](#logging-system-environment-based)
21. [Backup & Recovery](#backup--recovery)
22. [Environment & Deployment](#environment--deployment)
23. [Testing Strategy](#testing-strategy)
24. [Security & Compliance](#security--compliance)
25. [Performance Optimization](#performance-optimization)
26. [Monitoring & Observability](#monitoring--observability)
27. [Cost Management](#cost-management)
28. [Implementation Roadmap](#implementation-roadmap)
29. [Pre-Deployment Checklist](#pre-deployment-checklist)

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

## COMPLETE DATABASE SCHEMA

### Architecture Philosophy

The database schema is designed with the following principles:

1. **Separation of Concerns**: Clear distinction between user data, content, analytics, and system operations
2. **Audit Trail**: Comprehensive logging of all actions for compliance and debugging
3. **Flexibility**: JSONB fields for extensibility without schema changes
4. **Performance**: Strategic indexing and partitioning where needed
5. **Hybrid Storage**: PostgreSQL for relational data, Qdrant for vectors, Redis for cache
6. **Token Tracking**: Detailed breakdown of token usage at every stage

### Database Schema (PostgreSQL 15+)

```sql
-- ================================================================
-- AUTHENTICATION & USER MANAGEMENT
-- ================================================================

-- Main users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Authentication fields (email/password OR Google OAuth)
    email VARCHAR(255) UNIQUE,  -- NOT NULL removed for truly anonymous users
    password_hash VARCHAR(255),  -- bcrypt/argon2 hashed password
    google_id VARCHAR(255) UNIQUE,  -- Google OAuth identifier
    
    -- Profile information
    full_name VARCHAR(255),
    profile_picture_url VARCHAR(500),  -- URL if from Google OAuth
    profile_picture_uploaded BOOLEAN DEFAULT FALSE,  -- TRUE if user uploaded custom image
    
    -- Religious preferences
    marja_preference VARCHAR(100),  -- User's selected Marja (e.g., 'Sistani', 'Khamenei')
    preferred_language VARCHAR(10) DEFAULT 'fa',  -- 'fa' (Persian), 'ar' (Arabic), 'en', 'ur'
    
    -- Account status
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    account_type VARCHAR(20) DEFAULT 'free',  -- 'anonymous', 'free', 'premium', 'unlimited', 'test'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT check_auth_method CHECK (
        (email IS NOT NULL AND password_hash IS NOT NULL) OR 
        (google_id IS NOT NULL) OR
        (account_type = 'anonymous' AND email IS NULL AND google_id IS NULL)
    )
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_account_type ON users(account_type);

-- OTP (One-Time Password) verification codes
CREATE TABLE otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,  -- 6-digit code
    purpose VARCHAR(50) NOT NULL,  -- 'email_verification', 'password_reset' ONLY
    
    -- Status tracking
    is_used BOOLEAN DEFAULT FALSE,
    attempts_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE,
    
    -- Link to user (nullable for new registrations)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    CONSTRAINT check_otp_purpose CHECK (purpose IN ('email_verification', 'password_reset'))
);

CREATE INDEX idx_otp_email_purpose ON otp_codes(email, purpose);
CREATE INDEX idx_otp_expires_at ON otp_codes(expires_at);

-- User sessions (for JWT or refresh tokens)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session identification
    session_token VARCHAR(500) UNIQUE NOT NULL,  -- JWT or random token
    refresh_token VARCHAR(500) UNIQUE,
    
    -- Session metadata
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,  -- {device_type, os, browser}
    
    -- Session lifecycle
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);

-- Account linking for cross-platform authentication (Email <-> Google OAuth)
-- Allows users who signed up with one method to log in with another using same email
CREATE TABLE linked_auth_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Provider details
    provider_type VARCHAR(50) NOT NULL,  -- 'email', 'google', 'apple', 'github', etc.
    provider_user_id VARCHAR(255),  -- Provider-specific user ID (e.g., Google ID)
    provider_email VARCHAR(255),  -- Email from provider

    -- Link status
    is_primary BOOLEAN DEFAULT FALSE,  -- The original sign-up method
    is_verified BOOLEAN DEFAULT FALSE,

    -- Metadata
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(user_id, provider_type)
);

CREATE INDEX idx_linked_providers_user_id ON linked_auth_providers(user_id);
CREATE INDEX idx_linked_providers_type ON linked_auth_providers(provider_type);
CREATE INDEX idx_linked_providers_email ON linked_auth_providers(provider_email);

-- User settings and preferences
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- UI preferences
    theme VARCHAR(20) DEFAULT 'light',  -- 'light', 'dark', 'auto'
    font_size VARCHAR(20) DEFAULT 'medium',  -- 'small', 'medium', 'large'
    
    -- Chat preferences
    default_chat_mode VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'fast', 'scholarly', 'deep_search', 'filtered'
    auto_play_quranic_audio BOOLEAN DEFAULT FALSE,
    
    -- Notification settings
    email_notifications_enabled BOOLEAN DEFAULT TRUE,
    push_notifications_enabled BOOLEAN DEFAULT FALSE,
    
    -- Privacy settings
    allow_data_for_training BOOLEAN DEFAULT TRUE,
    show_in_leaderboard BOOLEAN DEFAULT FALSE,
    
    -- Rate limiting tier (managed by system)
    rate_limit_tier VARCHAR(50) DEFAULT 'free',
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- ADMIN & SYSTEM USERS
-- ================================================================

CREATE TABLE system_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Admin role and permissions
    role VARCHAR(50) NOT NULL,  -- 'super_admin', 'content_admin', 'support_admin', 'scholar_reviewer'
    permissions JSONB NOT NULL DEFAULT '[]',  -- ['manage_users', 'manage_content', 'view_analytics', 'view_feedbacks', 'approve_chunks', 'answer_tickets', 'review_quality']
    
    -- Specific capabilities per role
    can_access_dashboard BOOLEAN DEFAULT TRUE,
    can_modify_content BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE,
    can_view_sensitive_data BOOLEAN DEFAULT FALSE,
    can_approve_chunking BOOLEAN DEFAULT FALSE,  -- For content quality control
    can_answer_tickets BOOLEAN DEFAULT FALSE,  -- For support team
    can_review_responses BOOLEAN DEFAULT FALSE,  -- For scholar reviewers
    
    -- Admin status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    assigned_by UUID REFERENCES system_admins(id),  -- Who granted admin access
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,  -- Reason for admin access
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_admin_role CHECK (role IN ('super_admin', 'content_admin', 'support_admin', 'scholar_reviewer'))
);

CREATE INDEX idx_admins_user_id ON system_admins(user_id);
CREATE INDEX idx_admins_role ON system_admins(role);

-- Admin task assignments and tracking
CREATE TABLE admin_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES system_admins(id) ON DELETE CASCADE,
    
    -- Task details
    task_type VARCHAR(50) NOT NULL,  -- 'chunk_review', 'ticket_response', 'content_upload', 'quality_review'
    task_description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'cancelled'
    
    -- Timestamps
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,
    
    -- Related entities
    related_document_id UUID,  -- If task is about a document
    related_ticket_id UUID,  -- If task is about a ticket
    related_chunk_id UUID,  -- If task is about chunk approval
    
    -- Performance tracking
    completion_time_minutes INTEGER,  -- Calculated on completion
    quality_score DECIMAL(3, 2)  -- 0.00 to 1.00, evaluated by super_admin
);

CREATE INDEX idx_admin_tasks_admin_id ON admin_tasks(admin_id);
CREATE INDEX idx_admin_tasks_status ON admin_tasks(status);
CREATE INDEX idx_admin_tasks_assigned_at ON admin_tasks(assigned_at);

-- ================================================================
-- CHAT MANAGEMENT
-- ================================================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- Nullable for truly anonymous chats
    
    -- Conversation metadata
    title VARCHAR(200),  -- Auto-generated, but user can edit
    is_title_auto_generated BOOLEAN DEFAULT TRUE,
    mode VARCHAR(50) DEFAULT 'standard',  -- 'standard', 'fast', 'scholarly', 'deep_search', 'filtered'
    
    -- Privacy settings
    is_anonymous BOOLEAN DEFAULT FALSE,  -- Anonymous chat for logged-in users
    is_truly_anonymous BOOLEAN DEFAULT FALSE,  -- Completely anonymous (no user_id)
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_anonymous_logic CHECK (
        (is_truly_anonymous = TRUE AND user_id IS NULL) OR
        (is_truly_anonymous = FALSE)
    )
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_mode ON conversations(mode);
CREATE INDEX idx_conversations_is_anonymous ON conversations(is_anonymous);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message identification
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    
    -- LLM processing details (only for assistant messages)
    llm_provider VARCHAR(50),  -- 'openai', 'anthropic', 'google', 'cohere', 'openrouter', NULL for user messages
    llm_model VARCHAR(100),    -- 'gpt-4', 'claude-3-sonnet', 'gemini-1.5-pro', NULL for user messages
    llm_purpose VARCHAR(50),  -- 'text_generation', 'classification', 'tool_selection', 'reranking', 'guardrail_check'
    
    -- Detailed Token tracking (CRITICAL FEATURE)
    -- Input token breakdown
    input_tokens_total INTEGER,
    input_tokens_user_prompt INTEGER,
    input_tokens_system_prompt INTEGER,
    input_tokens_rag_context INTEGER,
    input_tokens_web_search_results INTEGER,
    input_tokens_tool_outputs INTEGER,
    input_tokens_memory_context INTEGER,  -- mem0 injected context
    input_tokens_other INTEGER,
    
    -- Output tokens (only for assistant messages)
    output_tokens_generated INTEGER,
    output_tokens_citations INTEGER,
    output_tokens_suggestions INTEGER,
    
    -- Total tokens
    total_tokens_used INTEGER,
    estimated_cost_usd DECIMAL(10, 6),  -- Cost in USD
    
    -- Response quality metadata
    response_quality_score DECIMAL(3, 2),  -- 0.00 to 1.00 (from hallucination detection, etc.)
    has_citations BOOLEAN DEFAULT FALSE,
    citation_count INTEGER DEFAULT 0,
    
    -- Processing metadata (flexible, provider-specific)
    llm_metadata JSONB,  -- Different structure per provider: {finish_reason, temperature, etc.}
    processing_metadata JSONB,  -- {retrieval_time_ms, total_time_ms, cache_hit, etc.}
    
    -- Message status
    is_edited BOOLEAN DEFAULT FALSE,
    generation_stopped_by_user BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_llm_provider ON messages(llm_provider);
CREATE INDEX idx_messages_llm_purpose ON messages(llm_purpose);

-- Message edit history (simplified - no edit_reason, no edited_by)
CREATE TABLE message_edit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Edit details
    previous_content TEXT NOT NULL,
    new_content TEXT NOT NULL,
    
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_message_edits_message_id ON message_edit_history(message_id);

-- User feedback on messages
CREATE TABLE message_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Feedback type
    feedback_type VARCHAR(20) NOT NULL,  -- 'like', 'dislike', 'stop_generation'
    
    -- Detailed feedback (for dislikes)
    dislike_reason VARCHAR(50),  -- 'inaccurate', 'poor_citation', 'not_relevant', 'incomplete', 'inappropriate', 'other'
    feedback_text TEXT,  -- High character limit for detailed feedback (5000 chars)
    
    -- Context
    was_helpful BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_feedback_text_length CHECK (LENGTH(feedback_text) <= 5000)
);

CREATE INDEX idx_feedback_message_id ON message_feedback(message_id);
CREATE INDEX idx_feedback_type ON message_feedback(feedback_type);
CREATE INDEX idx_feedback_created_at ON message_feedback(created_at);

-- A/B testing responses (toggle-able feature)
CREATE TABLE ab_test_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Test enabled flag (system-wide control)
    is_enabled BOOLEAN DEFAULT FALSE,
    
    -- Two variants
    variant_a_content TEXT NOT NULL,
    variant_a_model VARCHAR(100) NOT NULL,
    variant_a_metadata JSONB,
    
    variant_b_content TEXT NOT NULL,
    variant_b_model VARCHAR(100) NOT NULL,
    variant_b_metadata JSONB,
    
    -- User selection
    user_selected_variant VARCHAR(1),  -- 'A', 'B', or NULL if no selection
    selection_time_seconds INTEGER,  -- How long user took to decide
    
    -- Test metadata
    test_purpose VARCHAR(100),  -- 'model_comparison', 'prompt_testing', etc.
    scheduled_during_off_peak BOOLEAN DEFAULT TRUE,  -- Recommendation to run during off-peak
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    selected_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ab_tests_message_id ON ab_test_responses(message_id);
CREATE INDEX idx_ab_tests_is_enabled ON ab_test_responses(is_enabled);

-- ================================================================
-- KNOWLEDGE BASE & RAG ARCHITECTURE
-- ================================================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Document identification
    title VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255),
    document_type VARCHAR(50) NOT NULL,  -- 'hadith', 'quran', 'tafsir', 'fiqh', 'book', 'article', 'fatwa', 'doubts_response', 'rejal', 'other'
    
    -- Source information
    source_reference VARCHAR(500),  -- Book name, hadith collection, article URL, etc.
    author VARCHAR(255),
    publisher VARCHAR(255),
    publication_date DATE,
    language VARCHAR(10) DEFAULT 'fa',  -- 'fa' (Persian), 'ar' (Arabic), 'en', 'ur'
    
    -- Religious context (NOT all documents need this)
    fiqh_category VARCHAR(100),  -- NULL if not Ahkam-related (e.g., 'prayer', 'fasting', 'zakat')
    
    -- Document classification
    primary_category VARCHAR(100) NOT NULL,  -- 'aqidah', 'fiqh', 'akhlaq', 'tafsir', 'history', 'doubts', 'rejal', 'general'
    secondary_categories JSONB DEFAULT '[]',  -- Multiple categories possible
    tags JSONB DEFAULT '[]',  -- Flexible tagging
    
    -- File type classification (for pre-processing optimization)
    file_type_category VARCHAR(50),  -- 'clean_text', 'ocr_required', 'asr_required', 'structured', 'other'
    requires_ocr BOOLEAN DEFAULT FALSE,  -- TRUE for PDFs, images that need OCR
    requires_asr BOOLEAN DEFAULT FALSE,  -- TRUE for Audios, Voices that need ASR
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed', 'awaiting_chunk_approval'
    chunk_count INTEGER DEFAULT 0,
    total_characters INTEGER,
    
    -- Chunking configuration
    chunking_mode VARCHAR(20) DEFAULT 'auto',  -- 'auto', 'manual'
    chunking_method VARCHAR(50),  -- 'semantic', 'fixed_size', 'paragraph', 'custom'
    chunk_size INTEGER DEFAULT 768,  -- Optimized for Persian/Arabic (larger than English)
    chunk_overlap INTEGER DEFAULT 150,  -- Optimized overlap for Persian/Arabic
    
    -- Quality and verification
    is_verified BOOLEAN DEFAULT FALSE,  -- Verified by scholar/admin
    verification_notes TEXT,
    quality_score DECIMAL(3, 2),  -- 0.00 to 1.00
    
    -- Chunking approval (NEW FEATURE)
    requires_chunk_approval BOOLEAN DEFAULT TRUE,  -- Can be turned off for automatic processing
    chunk_approval_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'needs_revision'
    chunk_approved_by UUID REFERENCES system_admins(id),
    chunk_approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    retrieval_count INTEGER DEFAULT 0,  -- How many times chunks were retrieved
    citation_count INTEGER DEFAULT 0,   -- How many times cited in responses
    
    -- Metadata (flexible field for additional info)
    additional_metadata JSONB DEFAULT '{}',
    
    -- Admin tracking
    uploaded_by UUID REFERENCES system_admins(id),
    verified_by UUID REFERENCES system_admins(id),
    
    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_category ON documents(primary_category);
CREATE INDEX idx_documents_language ON documents(language);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX idx_documents_chunk_approval_status ON documents(chunk_approval_status);
CREATE INDEX idx_documents_file_type_category ON documents(file_type_category);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Chunk content
    chunk_text TEXT NOT NULL,  -- Actual text content
    chunk_index INTEGER NOT NULL,  -- Position in document (0-based)
    
    -- Chunk metadata
    char_count INTEGER NOT NULL,
    word_count INTEGER,
    token_count_estimated INTEGER,  -- Estimated tokens (for cost calculation)
    
    -- Context preservation
    previous_chunk_id UUID REFERENCES document_chunks(id),  -- Link to previous chunk for context
    next_chunk_id UUID REFERENCES document_chunks(id),      -- Link to next chunk
    
    -- Chunking strategy info
    chunking_method VARCHAR(50),  -- 'semantic', 'fixed_size', 'paragraph', 'custom'
    overlap_with_previous INTEGER DEFAULT 0,  -- Characters of overlap
    
    -- Flexible metadata (for chunk-specific info)
    chunk_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_index ON document_chunks(chunk_index);

-- Dynamic vector DB abstraction (to support future migration from Qdrant)
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    -- Embedding identification
    embedding_model VARCHAR(100) NOT NULL,  -- 'gemini-text-embedding-004', 'cohere-embed-v3'
    embedding_model_version VARCHAR(50),
    vector_dimension INTEGER NOT NULL,
    
    -- Vector DB integration (DYNAMIC - not tied to Qdrant only)
    vector_db_type VARCHAR(50) NOT NULL DEFAULT 'qdrant',  -- 'qdrant', 'elasticsearch', 'milvus', etc.
    vector_db_collection_name VARCHAR(100) NOT NULL,
    vector_db_point_id UUID NOT NULL,  -- ID in the vector DB
    vector_db_metadata JSONB,  -- DB-specific metadata
    
    -- Embedding metadata
    embedding_generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding_cost_usd DECIMAL(10, 8),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,  -- FALSE if superseded by new embedding
    
    UNIQUE(chunk_id, embedding_model, vector_db_collection_name)
);

CREATE INDEX idx_embeddings_chunk_id ON document_embeddings(chunk_id);
CREATE INDEX idx_embeddings_model ON document_embeddings(embedding_model);
CREATE INDEX idx_embeddings_vector_db_point ON document_embeddings(vector_db_point_id);
CREATE INDEX idx_embeddings_vector_db_type ON document_embeddings(vector_db_type);

-- Citations (tracks which documents were used in which responses)
CREATE TABLE message_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    -- Citation details
    relevance_score DECIMAL(5, 4) NOT NULL,  -- 0.0000 to 1.0000 (from reranker)
    citation_text TEXT,  -- Excerpt shown to user
    citation_order INTEGER,  -- Order of citation in response (1, 2, 3...)
    
    -- CLARIFICATION: This field tracks whether the citation was actually shown to the user
    -- (Some retrieved chunks might not make it to the final response due to context limits)
    is_displayed BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_citations_message_id ON message_citations(message_id);
CREATE INDEX idx_citations_document_id ON message_citations(document_id);
CREATE INDEX idx_citations_chunk_id ON message_citations(chunk_id);

-- ================================================================
-- MARJA OFFICIAL WEBSITES & AHKAM SOURCES
-- ================================================================
-- CRITICAL: For Ahkam (religious rulings), we DO NOT use RAG retrieval.
-- Instead, we fetch directly from official Marja websites with maximum citations.
-- This table allows admins to configure and manage these official sources.

CREATE TABLE marja_official_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Marja identification
    marja_name VARCHAR(255) NOT NULL,  -- 'Sistani', 'Khamenei', 'Makarem Shirazi', etc.
    marja_name_arabic VARCHAR(255),
    marja_name_persian VARCHAR(255),
    marja_name_english VARCHAR(255),

    -- Official website information
    official_website_url VARCHAR(500) NOT NULL,
    website_language VARCHAR(10),  -- 'fa', 'ar', 'en', 'ur'
    website_type VARCHAR(50),  -- 'primary', 'secondary', 'mobile', 'api'

    -- API or Scraping configuration
    has_official_api BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(500),
    api_key_required BOOLEAN DEFAULT FALSE,
    api_documentation_url VARCHAR(500),

    -- Web scraping configuration (if no API available)
    scraping_enabled BOOLEAN DEFAULT TRUE,
    scraping_config JSONB,  -- {selectors, url_patterns, rate_limits, etc.}

    -- Fatwa/Ahkam specific URLs
    ahkam_section_url VARCHAR(500),  -- Direct link to Ahkam/Fatwa section
    search_url VARCHAR(500),  -- Search endpoint URL
    search_method VARCHAR(10) DEFAULT 'GET',  -- 'GET', 'POST'
    search_parameters JSONB,  -- {query_param: 'q', filters: {...}}

    -- Content structure
    response_format VARCHAR(50),  -- 'html', 'json', 'xml', 'text'
    content_selectors JSONB,  -- {title: '.fatwa-title', content: '.fatwa-body', ...}

    -- Reliability & Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,  -- Verified by scholar/admin
    last_verified_at TIMESTAMP WITH TIME ZONE,
    last_successful_fetch_at TIMESTAMP WITH TIME ZONE,

    -- Rate limiting (respect website policies)
    requests_per_minute INTEGER DEFAULT 10,
    requests_per_hour INTEGER DEFAULT 100,

    -- Caching policy
    cache_duration_hours INTEGER DEFAULT 24,  -- How long to cache responses

    -- Contact information
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),

    -- Metadata
    notes TEXT,
    additional_metadata JSONB DEFAULT '{}',

    -- Admin tracking
    added_by UUID REFERENCES system_admins(id),
    verified_by UUID REFERENCES system_admins(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_marja_sources_name ON marja_official_sources(marja_name);
CREATE INDEX idx_marja_sources_active ON marja_official_sources(is_active);
CREATE INDEX idx_marja_sources_language ON marja_official_sources(website_language);

-- Tracking Ahkam fetches from official sources
CREATE TABLE ahkam_fetch_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marja_source_id UUID NOT NULL REFERENCES marja_official_sources(id) ON DELETE CASCADE,

    -- Request details
    question_text TEXT NOT NULL,
    question_category VARCHAR(100),  -- 'prayer', 'fasting', 'zakat', etc.

    -- Response details
    fetch_status VARCHAR(50),  -- 'success', 'failed', 'no_result', 'rate_limited'
    response_found BOOLEAN DEFAULT FALSE,
    response_text TEXT,
    response_url VARCHAR(500),  -- Direct link to the ruling on official website

    -- Citation information
    citation_title VARCHAR(500),
    citation_reference VARCHAR(500),  -- Book/section reference if available

    -- Performance
    fetch_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,

    -- Quality
    confidence_score DECIMAL(3, 2),  -- How confident are we in this result

    -- Error handling
    error_message TEXT,

    -- Timestamps
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ahkam_fetch_source ON ahkam_fetch_log(marja_source_id);
CREATE INDEX idx_ahkam_fetch_status ON ahkam_fetch_log(fetch_status);
CREATE INDEX idx_ahkam_fetch_date ON ahkam_fetch_log(fetched_at);

-- ================================================================
-- REJAL & HADITH CHAIN VALIDATION (NEW FEATURE)
-- ================================================================

-- Rejal: Narrator/transmitter information for hadith authentication
CREATE TABLE rejal_persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Person identification
    name_arabic VARCHAR(255) NOT NULL,
    name_persian VARCHAR(255),
    name_english VARCHAR(255),
    kunyah VARCHAR(100),  -- Abu/Umm name
    laqab VARCHAR(100),  -- Descriptive title
    
    -- Biographical info
    birth_year INTEGER,
    death_year INTEGER,
    birth_place VARCHAR(255),
    lived_in JSONB DEFAULT '[]',  -- List of places lived
    
    -- Reliability rating (by Shia scholars)
    reliability_rating VARCHAR(50),  -- 'thiqah' (reliable), 'da`if' (weak), 'matruk' (abandoned), etc.
    reliability_score DECIMAL(3, 2),  -- 0.00 to 1.00 (calculated from multiple sources)
    reliability_sources JSONB DEFAULT '[]',  -- References to Rejal books
    
    -- Additional metadata
    teachers JSONB DEFAULT '[]',  -- List of teacher IDs
    students JSONB DEFAULT '[]',  -- List of student IDs
    biographical_notes TEXT,
    additional_metadata JSONB DEFAULT '{}',
    
    -- Admin tracking
    added_by UUID REFERENCES system_admins(id),
    verified_by UUID REFERENCES system_admins(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rejal_name_arabic ON rejal_persons(name_arabic);
CREATE INDEX idx_rejal_reliability_rating ON rejal_persons(reliability_rating);
CREATE INDEX idx_rejal_reliability_score ON rejal_persons(reliability_score);

-- Hadith narration chains (Sanad/Isnad)
CREATE TABLE hadith_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Related hadith text (stored in documents table)
    hadith_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    hadith_text TEXT NOT NULL,
    
    -- Chain metadata
    chain_type VARCHAR(50),  -- 'full_chain', 'broken_chain', 'suspended', 'mursal'
    source_book VARCHAR(255),  -- Original hadith collection
    hadith_number VARCHAR(50),  -- Number in the collection
    
    -- Chain quality assessment
    overall_reliability VARCHAR(50),  -- 'sahih', 'hasan', 'da`if', 'mawdu`'
    reliability_score DECIMAL(3, 2),  -- 0.00 to 1.00 (calculated from narrator chain)
    
    -- Visualization data (for graph display)
    chain_graph_data JSONB,  -- {nodes: [...], edges: [...]} for frontend visualization
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hadith_chains_document_id ON hadith_chains(hadith_document_id);
CREATE INDEX idx_hadith_chains_reliability ON hadith_chains(overall_reliability);
CREATE INDEX idx_hadith_chains_score ON hadith_chains(reliability_score);

-- Individual narrators in a specific chain
CREATE TABLE chain_narrators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id UUID NOT NULL REFERENCES hadith_chains(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES rejal_persons(id) ON DELETE CASCADE,
    
    -- Position in chain
    position INTEGER NOT NULL,  -- 1 = first narrator (closest to Prophet/Imam), higher = later
    
    -- Relationship to next narrator
    transmission_method VARCHAR(100),  -- 'heard from', 'was told by', 'on authority of'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(chain_id, position)
);

CREATE INDEX idx_chain_narrators_chain_id ON chain_narrators(chain_id);
CREATE INDEX idx_chain_narrators_person_id ON chain_narrators(person_id);
CREATE INDEX idx_chain_narrators_position ON chain_narrators(position);

-- ================================================================
-- TICKET SUPPORT SYSTEM (NEW FEATURE)
-- ================================================================

CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(50) UNIQUE NOT NULL,  -- User-facing ticket ID (e.g., "TICKET-2024-001234")
    
    -- User information
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL if ticket from anonymous user
    user_email VARCHAR(255),  -- In case anonymous user provides email
    user_name VARCHAR(255),
    
    -- Ticket details
    subject VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),  -- 'bug_report', 'feature_request', 'content_issue', 'technical_issue', 'general_inquiry'
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    
    -- Status
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'in_progress', 'waiting_user', 'resolved', 'closed'
    
    -- Assignment
    assigned_to UUID REFERENCES system_admins(id),  -- Support admin who will handle it
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Resolution
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES system_admins(id),
    
    -- Performance tracking
    first_response_time_minutes INTEGER,  -- Time from creation to first admin response
    resolution_time_minutes INTEGER,  -- Time from creation to resolution
    
    -- Related entities
    related_conversation_id UUID REFERENCES conversations(id),
    related_message_id UUID REFERENCES messages(id),
    related_document_id UUID REFERENCES documents(id),
    
    -- Attachments
    attachments JSONB DEFAULT '[]',  -- [{filename, url, size}]
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_assigned_to ON support_tickets(assigned_to);
CREATE INDEX idx_tickets_created_at ON support_tickets(created_at);
CREATE INDEX idx_tickets_ticket_number ON support_tickets(ticket_number);

-- Ticket messages/responses (conversation thread)
CREATE TABLE ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    
    -- Message details
    sender_type VARCHAR(20) NOT NULL,  -- 'user', 'admin', 'system'
    sender_id UUID,  -- user_id or admin_id
    message_text TEXT NOT NULL,
    
    -- Attachments
    attachments JSONB DEFAULT '[]',
    
    -- Internal notes (only visible to admins)
    is_internal_note BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX idx_ticket_messages_created_at ON ticket_messages(created_at);

-- ================================================================
-- LEADERBOARDS (NEW FEATURE)
-- ================================================================

-- Admin performance leaderboard
CREATE TABLE admin_leaderboard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES system_admins(id) ON DELETE CASCADE,
    
    -- Time period for this leaderboard entry
    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Performance metrics
    tasks_completed INTEGER DEFAULT 0,
    tasks_pending INTEGER DEFAULT 0,
    average_task_completion_time_minutes INTEGER,
    average_quality_score DECIMAL(3, 2),  -- From super_admin evaluations
    
    tickets_resolved INTEGER DEFAULT 0,
    average_ticket_response_time_minutes INTEGER,
    average_ticket_resolution_time_minutes INTEGER,
    
    documents_processed INTEGER DEFAULT 0,
    chunks_approved INTEGER DEFAULT 0,
    chunks_rejected INTEGER DEFAULT 0,
    
    responses_reviewed INTEGER DEFAULT 0,  -- For scholar reviewers
    
    -- Ranking
    rank INTEGER,
    points INTEGER DEFAULT 0,  -- Gamification points
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(admin_id, period_type, period_start)
);

CREATE INDEX idx_admin_leaderboard_admin_id ON admin_leaderboard(admin_id);
CREATE INDEX idx_admin_leaderboard_period ON admin_leaderboard(period_type, period_start);
CREATE INDEX idx_admin_leaderboard_rank ON admin_leaderboard(rank);

-- User feedback quality leaderboard
CREATE TABLE user_feedback_leaderboard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Time period
    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Feedback metrics
    total_feedbacks_given INTEGER DEFAULT 0,
    helpful_feedbacks INTEGER DEFAULT 0,  -- Marked as helpful by admins/LLM judge
    detailed_feedbacks INTEGER DEFAULT 0,  -- Feedbacks with text > 100 chars
    
    -- Quality assessment
    feedback_quality_score DECIMAL(3, 2),  -- 0.00 to 1.00 (evaluated by LLM as judge or admin)
    feedback_usefulness_score DECIMAL(3, 2),  -- How useful was the feedback for improvements
    
    -- Ranking
    rank INTEGER,
    points INTEGER DEFAULT 0,
    
    -- User opt-in
    show_in_public_leaderboard BOOLEAN DEFAULT FALSE,  -- Controlled by user in settings
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, period_type, period_start)
);

CREATE INDEX idx_user_feedback_leaderboard_user_id ON user_feedback_leaderboard(user_id);
CREATE INDEX idx_user_feedback_leaderboard_period ON user_feedback_leaderboard(period_type, period_start);
CREATE INDEX idx_user_feedback_leaderboard_rank ON user_feedback_leaderboard(rank);
CREATE INDEX idx_user_feedback_leaderboard_public ON user_feedback_leaderboard(show_in_public_leaderboard);

-- ================================================================
-- SYSTEM OPERATIONS & MONITORING
-- ================================================================

-- General API request tracking (ALL endpoints, not just LLM)
CREATE TABLE api_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request identification
    request_id VARCHAR(100) UNIQUE NOT NULL,  -- Unique per request for tracing
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    
    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    request_path TEXT,
    request_body_size INTEGER,  -- In bytes
    
    -- Response details
    status_code INTEGER,
    response_time_ms INTEGER,
    response_body_size INTEGER,  -- In bytes
    
    -- Resource usage (if applicable)
    total_tokens_used INTEGER DEFAULT 0,
    estimated_cost_usd DECIMAL(10, 6),
    
    -- Client information
    ip_address INET,
    user_agent TEXT,
    
    -- Environment
    environment VARCHAR(20),  -- 'dev', 'test', 'prod'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_requests_user_id ON api_requests(user_id);
CREATE INDEX idx_api_requests_created_at ON api_requests(created_at);
CREATE INDEX idx_api_requests_endpoint ON api_requests(endpoint);
CREATE INDEX idx_api_requests_environment ON api_requests(environment);

-- Rate limiting tracking
CREATE TABLE rate_limit_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Rate limit window
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    window_duration_minutes INTEGER NOT NULL,  -- 1440 for daily
    
    -- Usage within window
    request_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    
    -- Limit enforcement
    limit_exceeded BOOLEAN DEFAULT FALSE,
    limit_exceeded_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, window_start, window_duration_minutes)
);

CREATE INDEX idx_rate_limits_user_window ON rate_limit_tracking(user_id, window_start);

-- LLM API calls (detailed tracking with provider and purpose)
CREATE TABLE llm_api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,  -- Links to api_requests
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- LLM details
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'google', 'cohere', 'openrouter'
    model VARCHAR(100) NOT NULL,
    llm_purpose VARCHAR(50) NOT NULL,  -- 'text_generation', 'classification', 'tool_selection', 'reranking', 'guardrail_check', 'summarization'
    
    -- Token usage (detailed breakdown)
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    
    -- Token breakdown (if available from provider)
    cached_tokens INTEGER,  -- Tokens served from cache
    reasoning_tokens INTEGER,  -- For models with explicit reasoning
    
    -- Cost tracking
    cost_usd DECIMAL(10, 8) NOT NULL,
    
    -- Performance
    latency_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    cache_type VARCHAR(50),  -- 'response', 'prompt', NULL
    
    -- Request metadata
    temperature DECIMAL(3, 2),
    max_tokens INTEGER,
    top_p DECIMAL(3, 2),
    additional_params JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_calls_request_id ON llm_api_calls(request_id);
CREATE INDEX idx_llm_calls_provider ON llm_api_calls(provider);
CREATE INDEX idx_llm_calls_model ON llm_api_calls(model);
CREATE INDEX idx_llm_calls_purpose ON llm_api_calls(llm_purpose);
CREATE INDEX idx_llm_calls_created_at ON llm_api_calls(created_at);

-- Tool executions (unified table for all tools)
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,  -- Links to api_requests
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Tool identification
    tool_name VARCHAR(100) NOT NULL,  -- 'web_search', 'ahkam_lookup', 'datetime_calculator', 'math_calculator', 'comparison_tool', 'rejal_lookup'
    tool_category VARCHAR(50),  -- 'search', 'calculation', 'data_retrieval', 'analysis', 'validation'
    
    -- Tool execution
    input_parameters JSONB NOT NULL,
    output_result JSONB,
    execution_status VARCHAR(50),  -- 'success', 'failed', 'timeout', 'cached'
    
    -- Performance
    execution_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    
    -- For web search specific tracking (UPDATED: supports multiple queries)
    search_queries JSONB,  -- Array of queries if web_search generated multiple
    search_results_count INTEGER,  -- Total number of results returned
    
    -- Cost (if applicable)
    cost_usd DECIMAL(10, 6),
    
    -- Error handling
    error_message TEXT,
    error_traceback TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tool_executions_request_id ON tool_executions(request_id);
CREATE INDEX idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX idx_tool_executions_created_at ON tool_executions(created_at);
CREATE INDEX idx_tool_executions_was_cached ON tool_executions(was_cached);

-- Guardrail checks (NeMo Guardrails)
CREATE TABLE guardrail_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(100) NOT NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Check details
    check_type VARCHAR(50) NOT NULL,  -- 'input', 'output'
    validator_name VARCHAR(100) NOT NULL,  -- Name of the rail (e.g., 'ToxicLanguage', 'IslamicContentAppropriate')
    
    -- Result
    passed BOOLEAN NOT NULL,
    confidence_score DECIMAL(5, 4),
    
    -- Details
    check_details JSONB,  -- Specific findings from validator
    action_taken VARCHAR(50),  -- 'allow', 'block', 'flag', 'modify'
    
    -- Performance
    check_duration_ms INTEGER,
    was_cached BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_guardrail_checks_request_id ON guardrail_checks(request_id);
CREATE INDEX idx_guardrail_checks_passed ON guardrail_checks(passed);
CREATE INDEX idx_guardrail_checks_type ON guardrail_checks(check_type);

-- ================================================================
-- ADMIN DASHBOARD & DATA MANAGEMENT
-- ================================================================

CREATE TABLE data_feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Feed identification
    feed_name VARCHAR(255) NOT NULL,
    feed_type VARCHAR(50) NOT NULL,  -- 'rss', 'api', 'file_upload', 'manual', 'web_scrape_url'
    
    -- Source information
    source_reference VARCHAR(500),  -- URL for web scraping, file path, or description
    source_credentials JSONB,  -- Encrypted API keys, auth tokens (if needed)
    
    -- Web scraping (admins just provide URL, system handles scraping)
    scraping_config JSONB,  -- {selectors, depth, follow_links, etc.}
    
    -- Processing configuration
    processing_schedule VARCHAR(100),  -- Cron expression: '0 */6 * * *' or 'manual'
    auto_process BOOLEAN DEFAULT FALSE,
    require_approval BOOLEAN DEFAULT TRUE,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'paused', 'failed', 'disabled'
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50),  -- 'success', 'failed', 'partial'
    last_sync_message TEXT,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    total_documents_processed INTEGER DEFAULT 0,
    total_chunks_created INTEGER DEFAULT 0,
    total_sync_attempts INTEGER DEFAULT 0,
    successful_syncs INTEGER DEFAULT 0,
    failed_syncs INTEGER DEFAULT 0,
    
    -- Configuration
    feed_config JSONB DEFAULT '{}',  -- Feed-specific settings
    
    -- Admin tracking
    created_by UUID REFERENCES system_admins(id),
    updated_by UUID REFERENCES system_admins(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_feeds_type ON data_feeds(feed_type);
CREATE INDEX idx_data_feeds_status ON data_feeds(status);
CREATE INDEX idx_data_feeds_next_sync ON data_feeds(next_sync_at);

-- Data feed execution log
CREATE TABLE data_feed_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID NOT NULL REFERENCES data_feeds(id) ON DELETE CASCADE,
    
    -- Execution details
    execution_status VARCHAR(50) NOT NULL,  -- 'running', 'completed', 'failed'
    documents_processed INTEGER DEFAULT 0,
    documents_created INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Logs
    execution_log TEXT,
    error_message TEXT,
    
    triggered_by VARCHAR(50),  -- 'schedule', 'manual', 'api'
    triggered_by_admin UUID REFERENCES system_admins(id)
);

CREATE INDEX idx_feed_executions_feed_id ON data_feed_executions(feed_id);
CREATE INDEX idx_feed_executions_started_at ON data_feed_executions(started_at);

-- ================================================================
-- EXTERNAL API (FOR THIRD-PARTY COMPANIES)
-- ================================================================

CREATE TABLE external_api_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Client identification
    client_name VARCHAR(255) NOT NULL,
    client_company VARCHAR(255),
    client_email VARCHAR(255) NOT NULL,
    client_contact_person VARCHAR(255),
    client_phone VARCHAR(50),

    -- API credentials
    api_key VARCHAR(255) UNIQUE NOT NULL,  -- Hashed API key
    api_secret VARCHAR(255),  -- Hashed secret for additional security

    -- Access control & Status (SUPER-ADMIN MANAGEMENT)
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'suspended', 'banned', 'pending_approval', 'expired'
    is_active BOOLEAN DEFAULT TRUE,  -- Quick toggle
    allowed_endpoints JSONB DEFAULT '[]',  -- List of endpoints they can access
    blocked_endpoints JSONB DEFAULT '[]',  -- Explicitly blocked endpoints

    -- Rate limiting configuration (GRANULAR CONTROL)
    rate_limit_tier VARCHAR(50) DEFAULT 'basic',  -- 'basic', 'standard', 'premium', 'enterprise', 'custom'

    -- Custom rate limits (if tier = 'custom')
    custom_requests_per_minute INTEGER,
    custom_requests_per_hour INTEGER,
    custom_requests_per_day INTEGER,
    custom_requests_per_month INTEGER,
    custom_tokens_per_request INTEGER,
    custom_concurrent_requests INTEGER DEFAULT 5,

    -- Usage limits & tracking
    monthly_request_limit INTEGER,
    monthly_token_limit INTEGER,
    daily_request_limit INTEGER,
    daily_token_limit INTEGER,

    current_month_requests INTEGER DEFAULT 0,
    current_month_tokens INTEGER DEFAULT 0,
    current_day_requests INTEGER DEFAULT 0,
    current_day_tokens INTEGER DEFAULT 0,

    -- Cost tracking
    cost_per_token DECIMAL(10, 8),  -- Custom pricing
    current_month_cost_usd DECIMAL(10, 4) DEFAULT 0,
    total_cost_usd DECIMAL(12, 4) DEFAULT 0,

    -- IP & Security
    allowed_ips JSONB DEFAULT '[]',  -- Whitelist of allowed IP addresses
    blocked_ips JSONB DEFAULT '[]',  -- Blacklist of blocked IPs
    require_ip_whitelist BOOLEAN DEFAULT FALSE,

    -- Billing
    billing_email VARCHAR(255),
    plan_type VARCHAR(50),  -- 'free', 'pay_as_you_go', 'subscription', 'enterprise'
    payment_status VARCHAR(50) DEFAULT 'current',  -- 'current', 'overdue', 'suspended'

    -- Moderation & Control (SUPER-ADMIN ACTIONS)
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    banned_at TIMESTAMP WITH TIME ZONE,
    banned_by UUID REFERENCES system_admins(id),

    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason TEXT,
    suspension_start TIMESTAMP WITH TIME ZONE,
    suspension_end TIMESTAMP WITH TIME ZONE,  -- NULL for indefinite
    suspended_by UUID REFERENCES system_admins(id),

    -- Permissions & Features
    permissions JSONB DEFAULT '{}',  -- {allow_web_search: true, allow_tool_calls: false, ...}
    enabled_features JSONB DEFAULT '[]',  -- ['chat', 'embeddings', 'search']

    -- Alerts & Monitoring
    alert_on_high_usage BOOLEAN DEFAULT TRUE,
    alert_threshold_percentage INTEGER DEFAULT 80,  -- Alert at 80% of limit
    admin_notes TEXT,  -- Super-admin internal notes

    -- Audit trail
    created_by UUID REFERENCES system_admins(id),  -- Which admin created this client
    last_modified_by UUID REFERENCES system_admins(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_reset_at TIMESTAMP WITH TIME ZONE  -- Last time usage counters were reset
);

CREATE INDEX idx_external_clients_api_key ON external_api_clients(api_key);
CREATE INDEX idx_external_clients_is_active ON external_api_clients(is_active);
CREATE INDEX idx_external_clients_status ON external_api_clients(status);
CREATE INDEX idx_external_clients_is_banned ON external_api_clients(is_banned);
CREATE INDEX idx_external_clients_is_suspended ON external_api_clients(is_suspended);
CREATE INDEX idx_external_clients_company ON external_api_clients(client_company);

-- External API usage tracking
CREATE TABLE external_api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES external_api_clients(id) ON DELETE CASCADE,
    
    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    
    -- Response
    status_code INTEGER,
    response_time_ms INTEGER,
    
    -- Resource usage
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6),
    
    -- Client info
    ip_address INET,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_external_api_usage_client_id ON external_api_usage(client_id);
CREATE INDEX idx_external_api_usage_created_at ON external_api_usage(created_at);

-- ================================================================
-- AUDIT LOGS
-- ================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Actor (who did the action)
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL for system actions
    actor_type VARCHAR(50) DEFAULT 'user',  -- 'user', 'admin', 'system', 'api', 'external_client'
    actor_ip_address INET,
    
    -- Action details
    action VARCHAR(100) NOT NULL,  -- 'create', 'update', 'delete', 'login', 'logout', 'export', 'approve', etc.
    action_category VARCHAR(50),  -- 'auth', 'content', 'user_management', 'system', 'ticket', 'admin'
    
    -- Resource affected (polymorphic)
    resource_type VARCHAR(50) NOT NULL,  -- 'user', 'document', 'conversation', 'data_feed', 'admin', 'settings', 'ticket'
    resource_id UUID NOT NULL,  -- ID of the affected resource
    
    -- Change details
    previous_state JSONB,  -- State before action (for updates)
    new_state JSONB,       -- State after action
    changes JSONB,         -- Specific fields changed
    
    -- Context
    description TEXT,  -- Human-readable description
    metadata JSONB DEFAULT '{}',  -- Additional context
    
    -- Request tracking
    request_id VARCHAR(100),  -- Link to api_requests if applicable
    
    -- Environment
    environment VARCHAR(20),  -- 'dev', 'test', 'prod'
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action_category ON audit_logs(action_category);
CREATE INDEX idx_audit_logs_environment ON audit_logs(environment);

-- ================================================================
-- CACHE ANALYTICS (for performance optimization)
-- ================================================================

CREATE TABLE cache_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Cache identification
    cache_type VARCHAR(50) NOT NULL,  -- 'response', 'embedding', 'retrieval', 'tool', 'guardrail'
    cache_key_hash VARCHAR(64) NOT NULL,  -- SHA-256 of cache key (for privacy)
    
    -- Hit/Miss tracking
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    eviction_count INTEGER DEFAULT 0,
    
    -- Performance impact
    avg_latency_ms_on_miss INTEGER,
    avg_latency_ms_on_hit INTEGER,
    total_cost_saved_usd DECIMAL(10, 6) DEFAULT 0,
    
    -- Time tracking
    first_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Window for aggregation
    date_bucket DATE DEFAULT CURRENT_DATE,
    
    -- Environment
    environment VARCHAR(20),  -- 'dev', 'test', 'prod'
    
    UNIQUE(cache_type, cache_key_hash, date_bucket, environment)
);

CREATE INDEX idx_cache_analytics_type ON cache_analytics(cache_type);
CREATE INDEX idx_cache_analytics_date ON cache_analytics(date_bucket);
CREATE INDEX idx_cache_analytics_environment ON cache_analytics(environment);

-- ================================================================
-- BACKUP TRACKING (HuggingFace Integration)
-- ================================================================

CREATE TABLE backup_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Backup details
    backup_type VARCHAR(50) NOT NULL,  -- 'full', 'incremental', 'embeddings_only', 'documents_only'
    backup_destination VARCHAR(100) NOT NULL,  -- 'huggingface', 'local', 's3'
    
    -- HuggingFace specific
    hf_repository VARCHAR(255),  -- HuggingFace repo name (private)
    hf_commit_hash VARCHAR(100),
    
    -- Backup contents
    tables_backed_up JSONB,  -- List of table names
    total_rows INTEGER,
    total_size_mb DECIMAL(10, 2),
    
    -- Status
    status VARCHAR(50),  -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

CREATE INDEX idx_backup_logs_started_at ON backup_logs(started_at);
CREATE INDEX idx_backup_logs_status ON backup_logs(status);
CREATE INDEX idx_backup_logs_backup_type ON backup_logs(backup_type);
```

### Qdrant Collections (Vector DB Schema)

```python
# Collection configuration for dynamic vector DB abstraction
collections_config = {
    "shia_knowledge_gemini": {
        "vectors": {
            "size": 3072,
            "distance": "Cosine"
        },
        "quantization": {
            "binary": {
                "enabled": True,
                "always_ram": False  # Use for 40x performance boost
            }
        },
        "payload_schema": {
            "document_id": "keyword",
            "chunk_id": "keyword",
            "source_type": "keyword",  # hadith, quran, fiqh, tafsir, rejal, etc.
            "language": "keyword",  # fa, ar, en, ur
            "author": "text",
            "title": "text",
            "content": "text",  # Actual chunk text for re-ranking
            "metadata": "json"
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 200,
            "full_scan_threshold": 10000
        }
    },
    
    "shia_knowledge_cohere": {
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "quantization": {
            "binary": {
                "enabled": True,
                "always_ram": False
            }
        },
        "payload_schema": {
            # Same as above
        }
    },
    
    "conversation_memory_mem0": {
        "vectors": {
            "size": "MAKE IT FLEXIBLE TO CAN WORK WITH DIFFERENT EMBEDDINGS", 
            "distance": "Cosine"
        },
        "payload_schema": {
            "conversation_id": "keyword",
            "user_id": "keyword",
            "summary": "text",
            "key_points": "json",
            "facts": "json",  # mem0 extracted facts
            "timestamp": "integer"
        }
    },
    
    "rejal_persons_embeddings": {
        "vectors": {
            "size": "MAKE IT FLEXIBLE TO CAN WORK WITH DIFFERENT EMBEDDINGS",
            "distance": "Cosine"
        },
        "payload_schema": {
            "person_id": "keyword",
            "name_arabic": "text",
            "name_persian": "text",
            "biographical_notes": "text",
            "reliability_rating": "keyword",
            "reliability_score": "float"
        }
    }
}
```

---

## LANGGRAPH IMPLEMENTATION

### Main Orchestration Graph Architecture

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages

# State definition with mem0 integration
class ConversationState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], add_messages]
    user_id: str
    conversation_id: str
    mem0_user_id: str  # For mem0 memory tracking
    mode: str  # 'standard', 'fast', 'scholarly', 'deep_search', 'filtered'
    intent: str  # Classified intent
    query_refined: bool
    retrieval_context: List[dict]
    tool_results: List[dict]
    web_search_results: List[dict]
    citations: List[dict]
    hallucination_score: float
    token_tracking: dict  # Detailed token breakdown
    guardrail_passed: bool
    current_model_tier: int  # 1, 2, or 3
    environment: str  # 'dev', 'test', 'prod'
```

### Complete Graph Structure

```python
class ShiaRAGOrchestrator:
    """Main LangGraph orchestration for Shia Islamic chatbot"""
    
    def __init__(self):
        self.graph = StateGraph(ConversationState)
        self.setup_nodes()
        self.setup_edges()
        self.compile_graph()
    
    def setup_nodes(self):
        # Pre-processing nodes
        self.graph.add_node("env_validator", self.env_validator_node)
        self.graph.add_node("secret_checker", self.secret_checker_node)
        self.graph.add_node("input_guardrail", self.input_guardrail_node)
        self.graph.add_node("intent_classifier", self.intent_classifier_node)
        self.graph.add_node("mem0_retrieval", self.mem0_retrieval_node)
        self.graph.add_node("query_refiner", self.query_refiner_node)
        self.graph.add_node("smart_router", self.smart_router_node)
        
        # Execution nodes (different paths)
        self.graph.add_node("greeting_handler", self.greeting_handler_node)
        self.graph.add_node("simple_qa", self.simple_qa_node)
        self.graph.add_node("complex_rag", self.complex_rag_node)
        self.graph.add_node("multi_hop_reasoning", self.multi_hop_reasoning_node)
        self.graph.add_node("tool_calling", ToolNode(self.tools))
        self.graph.add_node("web_search", self.web_search_node)
        self.graph.add_node("rejal_validation", self.rejal_validation_node)
        
        # Post-processing nodes
        self.graph.add_node("llm_generation", self.llm_generation_node)
        self.graph.add_node("output_guardrail", self.output_guardrail_node)
        self.graph.add_node("citation_generator", self.citation_generator_node)
        self.graph.add_node("hallucination_detector", self.hallucination_detector_node)
        self.graph.add_node("suggestion_generator", self.suggestion_generator_node)
        self.graph.add_node("mem0_save", self.mem0_save_node)
        self.graph.add_node("token_tracker", self.token_tracker_node)
        self.graph.add_node("response_logger", self.response_logger_node)
    
    def setup_edges(self):
        # Sequential pre-processing
        self.graph.add_edge(START, "env_validator")
        self.graph.add_edge("env_validator", "secret_checker")
        self.graph.add_edge("secret_checker", "input_guardrail")
        self.graph.add_edge("input_guardrail", "intent_classifier")
        self.graph.add_edge("intent_classifier", "mem0_retrieval")
        self.graph.add_edge("mem0_retrieval", "query_refiner")
        self.graph.add_edge("query_refiner", "smart_router")
        
        # Conditional routing from smart_router
        self.graph.add_conditional_edges(
            "smart_router",
            self.route_by_intent,
            {
                "greeting": "greeting_handler",
                "simple_qa": "simple_qa",
                "complex": "complex_rag",
                "multi_hop": "multi_hop_reasoning",
                "tool_calling": "tool_calling",
                "web_search": "web_search",
                "rejal": "rejal_validation"
            }
        )
        
        # All execution paths converge to generation
        for node in ["greeting_handler", "simple_qa", "complex_rag", 
                     "multi_hop_reasoning", "tool_calling", "web_search", "rejal_validation"]:
            self.graph.add_edge(node, "llm_generation")
        
        # Sequential post-processing
        self.graph.add_edge("llm_generation", "output_guardrail")
        self.graph.add_edge("output_guardrail", "citation_generator")
        self.graph.add_edge("citation_generator", "hallucination_detector")
        self.graph.add_edge("hallucination_detector", "suggestion_generator")
        self.graph.add_edge("suggestion_generator", "mem0_save")
        self.graph.add_edge("mem0_save", "token_tracker")
        self.graph.add_edge("token_tracker", "response_logger")
        self.graph.add_edge("response_logger", END)
    
    def compile_graph(self):
        # Use PostgreSQL for checkpointing (state persistence)
        checkpointer = PostgresSaver.from_conn_string(
            os.getenv("DATABASE_URL")
        )
        
        self.compiled_graph = self.graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["llm_generation"],  # For stop generation feature
            interrupt_after=None
        )
```

### Key Node Implementations

#### 1. Intent Classification Node (Enriched Categories)

```python
def intent_classifier_node(self, state: ConversationState) -> ConversationState:
    """
    Classifies user intent with enriched categories for better routing.
    Uses cheap Tier 3 LLM for cost efficiency.
    """
    # Use mem0 context for better classification
    user_message = state["messages"][-1].content
    mem0_context = state.get("mem0_context", "")
    
    classification_prompt = f"""
You are an intent classifier for a Shia Islamic chatbot. Classify the user's intent into ONE of these categories:

GREETING: Simple greetings, hellos, how are you
SIMPLE_QA: Direct factual questions with clear answers
AHKAM_QUERY: Religious ruling questions (حکم شرعی)
COMPARISON: Comparing opinions, rulings, or interpretations
CALCULATION: Math, Zakat, Khums, prayer times, dates
COMPLEX_RESEARCH: Multi-faceted questions requiring deep analysis
MULTI_HOP: Questions requiring multiple reasoning steps
WEB_SEARCH: Current events, recent news, time-sensitive info
REJAL_QUERY: Questions about hadith narrators or chain authenticity
GENERAL_CHAT: Conversational, no specific information need
UNCLEAR: Cannot determine clear intent

User context (from memory): {mem0_context}
Current message: {user_message}

Respond with ONLY the category name.
"""
    
    # Use Tier 3 (cheap) LLM for classification
    llm = self.get_llm(tier=3)
    response = llm.invoke(classification_prompt)
    
    state["intent"] = response.content.strip().upper()
    state["token_tracking"]["classification"] = {
        "model": llm.model_name,
        "input_tokens": response.usage_metadata["input_tokens"],
        "output_tokens": response.usage_metadata["output_tokens"]
    }
    
    return state
```

#### 2. Smart Router Node (Cost-Aware)

```python
def smart_router_node(self, state: ConversationState) -> ConversationState:
    """
    Routes to appropriate execution path based on intent and cost optimization.
    """
    intent = state["intent"]
    mode = state["mode"]
    
    # Intent to execution path mapping
    routing_map = {
        "GREETING": ("greeting_handler", 3),  # Tier 3 LLM
        "SIMPLE_QA": ("simple_qa", 2),  # Tier 2 LLM
        "AHKAM_QUERY": ("complex_rag", 2),  # Tier 2 with specialized tools
        "COMPARISON": ("complex_rag", 2),
        "CALCULATION": ("tool_calling", 3),  # Tools + Tier 3 LLM
        "COMPLEX_RESEARCH": ("multi_hop_reasoning", 1),  # Tier 1 LLM
        "MULTI_HOP": ("multi_hop_reasoning", 1),
        "WEB_SEARCH": ("web_search", 2),
        "REJAL_QUERY": ("rejal_validation", 2),
        "GENERAL_CHAT": ("greeting_handler", 3),
        "UNCLEAR": ("simple_qa", 2)  # Default to simple QA with mid-tier
    }
    
    # Mode override (user preference)
    if mode == "fast":
        _, tier = routing_map.get(intent, ("simple_qa", 2))
        tier = 3  # Always use Tier 3 in fast mode
    elif mode == "scholarly":
        _, tier = routing_map.get(intent, ("simple_qa", 2))
        tier = 1  # Always use Tier 1 in scholarly mode
    
    execution_path, model_tier = routing_map.get(intent, ("simple_qa", 2))
    
    state["execution_path"] = execution_path
    state["current_model_tier"] = model_tier
    
    return state

def route_by_intent(self, state: ConversationState) -> str:
    """Routing function for conditional edges"""
    return state["execution_path"]
```

#### 3. Multi-Hop Reasoning Node (Complex Questions)

```python
async def multi_hop_reasoning_node(self, state: ConversationState) -> ConversationState:
    """
    Handles complex questions requiring multiple reasoning steps.
    Uses iterative retrieval and reasoning.
    """
    user_query = state["messages"][-1].content
    max_hops = 5
    
    # Initialize reasoning chain
    reasoning_steps = []
    accumulated_context = []
    
    for hop in range(max_hops):
        # Step 1: Decompose question or identify next sub-question
        if hop == 0:
            decomposition_prompt = f"""
You are analyzing a complex Islamic question. Break it down into sub-questions that need to be answered sequentially.

Main question: {user_query}

List the sub-questions in order:
"""
        else:
            decomposition_prompt = f"""
Based on what we've learned so far, what's the next sub-question we need to answer?

Main question: {user_query}
Previous findings: {reasoning_steps}

Next sub-question:
"""
        
        llm = self.get_llm(tier=1)  # Use best model for reasoning
        sub_question = llm.invoke(decomposition_prompt).content
        
        # Step 2: Retrieve relevant information for this sub-question
        retrieval_results = await self.retrieve_with_reranking(
            query=sub_question,
            top_k=10,
            filters=state.get("filters", {})
        )
        
        accumulated_context.extend(retrieval_results)
        
        # Step 3: Answer sub-question
        answer_prompt = f"""
Sub-question: {sub_question}
Relevant information: {retrieval_results}

Provide a concise answer:
"""
        
        sub_answer = llm.invoke(answer_prompt).content
        
        reasoning_steps.append({
            "hop": hop + 1,
            "sub_question": sub_question,
            "sub_answer": sub_answer,
            "sources": retrieval_results
        })
        
        # Step 4: Check if we have enough information
        completion_check = f"""
Main question: {user_query}
Reasoning so far: {reasoning_steps}

Can we now provide a complete answer to the main question? Answer YES or NO.
"""
        
        is_complete = llm.invoke(completion_check).content.strip().upper()
        
        if is_complete == "YES":
            break
    
    # Final synthesis
    synthesis_prompt = f"""
Synthesize a comprehensive answer to the main question using all the reasoning steps.

Main question: {user_query}
Reasoning steps: {reasoning_steps}

Provide a well-structured final answer:
"""
    
    final_answer = llm.invoke(synthesis_prompt).content
    
    state["retrieval_context"] = accumulated_context
    state["reasoning_steps"] = reasoning_steps
    state["messages"].append(AIMessage(content=final_answer))
    
    # Track tokens
    state["token_tracking"]["multi_hop"] = {
        "hops_used": len(reasoning_steps),
        "total_sub_questions": len(reasoning_steps),
        # Token details would be calculated from all LLM calls
    }
    
    return state
```

---

### **Part 2: Advanced Features & Tools**

**Contents:**
- **mem0 Memory Management** (complete integration with LangGraph)
- **NeMo Guardrails** (LLM-based, no GPU required)
  - Configuration files
  - Colang 2.0 flows
  - Custom validators for Islamic content
- **Specialized Tools:**
  - Ahkam (Religious Rulings) Tool
  - DateTime Calculator Tool
  - Math Calculator Tool (Zakat, Khums, Inheritance)
  - Comparison Tool
  - Rejal Lookup Tool
- **Multi-Level Caching Strategy** (6 levels)
  - Response, Embedding, Retrieval, Tool, Guardrail, Web Search caches
  - Cache optimization algorithms


---

# SHIA ISLAMIC RAG CHATBOT - IMPLEMENTATION PLAN (PART 2)

## Continuation from Part 1

---

## MEMORY MANAGEMENT WITH MEM0

### mem0 Integration Architecture

```python
from mem0 import Memory, MemoryClient
from langgraph.graph import StateGraph

# Configuration for mem0
mem0_config = {
    "llm": {
        "provider": "openai",  # Can use any provider
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "conversation_memory_mem0",
            "url": os.getenv("QDRANT_URL"),
            "api_key": os.getenv("QDRANT_API_KEY")
        }
    },
    "history_db_path": "postgresql://..."  # PostgreSQL for conversation history
}

# Initialize mem0
memory = Memory.from_config(mem0_config)
```

### Memory Operations in LangGraph Nodes

```python
class MemoryManager:
    """Manages mem0 operations within LangGraph workflow"""
    
    def __init__(self):
        self.memory = Memory.from_config(mem0_config)
    
    async def retrieve_memories(self, user_id: str, query: str) -> List[dict]:
        """
        Retrieve relevant memories for the current query.
        Called in query refinement stage.
        """
        memories = self.memory.search(
            query=query,
            user_id=user_id,
            limit=5  # Top 5 most relevant memories
        )
        
        return memories
    
    async def add_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str
    ):
        """
        Add a conversation turn to mem0.
        mem0 will automatically extract and update facts.
        """
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
        
        result = self.memory.add(
            messages,
            user_id=user_id,
            metadata={
                "conversation_turn": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return result
    
    async def get_user_profile(self, user_id: str) -> dict:
        """Get all memories for a user (for profile display)"""
        all_memories = self.memory.get_all(user_id=user_id)
        
        # Organize by category
        profile = {
            "preferences": [],
            "facts": [],
            "history": []
        }
        
        for memory in all_memories:
            category = memory.get("metadata", {}).get("category", "facts")
            profile[category].append(memory["memory"])
        
        return profile
    
    async def update_memory(self, memory_id: str, new_content: str):
        """Update a specific memory (when user corrects information)"""
        self.memory.update(
            memory_id=memory_id,
            data=new_content
        )
```

### Integration with Query Refinement

```python
async def mem0_retrieval_node(self, state: ConversationState) -> ConversationState:
    """
    Retrieve relevant memories before processing query.
    This enriches the query with user context.
    """
    user_id = state["mem0_user_id"]
    user_query = state["messages"][-1].content
    
    # Retrieve relevant memories
    memories = await self.memory_manager.retrieve_memories(
        user_id=user_id,
        query=user_query
    )
    
    # Format memories for context
    memory_context = "\n".join([
        f"- {mem['memory']}" for mem in memories
    ])
    
    state["mem0_context"] = memory_context
    state["mem0_memories"] = memories
    
    # Track tokens
    state["token_tracking"]["mem0_retrieval"] = {
        "memories_retrieved": len(memories),
        "context_tokens": estimate_tokens(memory_context)
    }
    
    return state

async def query_refiner_node(self, state: ConversationState) -> ConversationState:
    """
    Refine user query using mem0 context.
    Expands ambiguous queries with user's historical context.
    """
    user_query = state["messages"][-1].content
    mem0_context = state.get("mem0_context", "")
    conversation_history = state["messages"][:-1]  # Previous messages
    
    refinement_prompt = f"""
You are refining a user's query for a Shia Islamic chatbot.

User's historical preferences and facts:
{mem0_context}

Recent conversation:
{format_messages(conversation_history[-5:])}  # Last 5 messages

Current query: {user_query}

Refined query (expand ambiguities, add context, maintain Islamic terminology):
"""
    
    llm = self.get_llm(tier=3)  # Fast model for refinement
    refined_query = llm.invoke(refinement_prompt).content
    
    state["query_refined"] = True
    state["refined_query"] = refined_query
    state["token_tracking"]["query_refinement"] = {
        "model": llm.model_name,
        "input_tokens": estimate_tokens(refinement_prompt),
        "output_tokens": estimate_tokens(refined_query)
    }
    
    return state

async def mem0_save_node(self, state: ConversationState) -> ConversationState:
    """
    Save conversation turn to mem0 after response generation.
    mem0 will automatically extract facts and update user profile.
    """
    user_id = state["mem0_user_id"]
    
    # Get the last user message and assistant response
    user_message = state["messages"][-2].content  # Second to last
    assistant_message = state["messages"][-1].content  # Last
    
    await self.memory_manager.add_conversation_turn(
        user_id=user_id,
        user_message=user_message,
        assistant_message=assistant_message
    )
    
    state["token_tracking"]["mem0_save"] = {
        "memories_extracted": "auto"  # mem0 handles extraction
    }
    
    return state
```

### Memory Compression Benefits

```python
# mem0 automatically compresses conversation history
# Example: 10 turns of conversation (5000 tokens) → compressed to key facts (500 tokens)
# This reduces token usage by up to 80% while maintaining context

# Before mem0 (sending full history):
# Input tokens: 5000 (history) + 100 (query) + 1000 (system) = 6100 tokens

# With mem0 (sending compressed memories):
# Input tokens: 500 (compressed facts) + 100 (query) + 1000 (system) = 1600 tokens

# Savings: 74% reduction in input tokens!
```

---

## GUARDRAILS WITH NEMO

### NeMo Guardrails Configuration

```yaml
# config/guardrails/config.yml
instructions:
  - type: general
    content: |
      You are an assistant for a Shia Islamic chatbot.
      You must:
      1. Provide accurate Islamic information
      2. Respect all Islamic traditions and scholars
      3. Never provide harmful or inappropriate content
      4. Cite sources when making religious claims
      5. Be respectful of religious sensitivity

models:
  - type: main
    engine: custom  # We'll provide the LLM programmatically

rails:
  input:
    flows:
      - check toxic language
      - check islamic appropriateness
      - check pii
      - check injection attempts
  
  output:
    flows:
      - check harmful content
      - check religious accuracy
      - check citation presence
      - check bias
  
  dialog:
    single_call:
      enabled: True
```

### Colang 2.0 Flow Definitions

```colang
# config/guardrails/rails.co

# Input Rails
define flow check toxic language
  """Check for toxic or offensive language"""
  $result = execute check_toxicity
  
  if $result.is_toxic
    bot refuse toxic language
    stop

define flow check islamic appropriateness
  """Ensure query is appropriate for Islamic context"""
  $result = execute check_islamic_content_input
  
  if not $result.is_appropriate
    bot refuse inappropriate content
    stop

define flow check pii
  """Check for personal identifiable information"""
  $result = execute check_pii_detection
  
  if $result.contains_pii
    bot warn about pii
    # Continue but flag for logging

define flow check injection attempts
  """Check for prompt injection or jailbreak attempts"""
  $result = execute check_injection
  
  if $result.is_injection
    bot refuse injection
    stop

# Output Rails
define flow check harmful content
  """Ensure output doesn't contain harmful content"""
  $result = execute check_output_harm
  
  if $result.is_harmful
    bot provide safe alternative
    stop

define flow check religious accuracy
  """Verify religious content is accurate and properly cited"""
  $result = execute check_religious_accuracy
  
  if $result.accuracy_score < 0.7
    bot indicate uncertainty
    # Still proceed but with disclaimer

define flow check citation presence
  """Ensure claims have citations"""
  $result = execute check_citations
  
  if $result.missing_citations
    bot add citation reminder
    # Modify output to request citations

define flow check bias
  """Check for biased or one-sided religious opinions"""
  $result = execute check_bias_detection
  
  if $result.is_biased
    bot add balanced perspective
    # Modify output to include other views

# Bot responses
define bot refuse toxic language
  "من نمی‌توانم به درخواست‌هایی که حاوی زبان توهین‌آمیز هستند پاسخ دهم. لطفاً به شیوه‌ای محترمانه سؤال کنید."
  # Persian: "I cannot respond to requests containing offensive language. Please ask respectfully."

define bot refuse inappropriate content
  "این درخواست برای یک چت‌بات اسلامی مناسب نیست. چگونه می‌توانم در زمینه مسائل اسلامی به شما کمک کنم؟"
  # Persian: "This request is not appropriate for an Islamic chatbot. How can I help you with Islamic matters?"

define bot refuse injection
  "متوجه شدم که ممکن است سعی کنید رفتار سیستم را تغییر دهید. چگونه می‌توانم با سؤال واقعی شما کمک کنم؟"
  # Persian: "I noticed you might be trying to change the system's behavior. How can I help with your actual question?"

define bot indicate uncertainty
  "لطفاً توجه داشته باشید که من در مورد این موضوع کاملاً مطمئن نیستم. توصیه می‌کنم با یک عالم دینی مشورت کنید."
  # Persian: "Please note that I'm not completely certain about this matter. I recommend consulting with a religious scholar."
```

### Python Integration with LangGraph

```python
from nemoguardrails import RailsConfig, LLMRails
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
from langchain_core.runnables import RunnablePassthrough

class GuardrailsManager:
    """Manages NeMo Guardrails integration with LangGraph"""
    
    def __init__(self):
        # Load guardrails configuration
        self.config = RailsConfig.from_path("config/guardrails")
        
        # Create RunnableRails instance
        self.guardrails = RunnableRails(
            config=self.config,
            llm=self.get_guardrail_llm()  # LLM for guardrail checks
        )
    
    def get_guardrail_llm(self):
        """
        LLM for guardrail checks (no GPU required).
        Using cheap model for cost efficiency.
        """
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model="gpt-4o-mini",  # Fast and cheap
            temperature=0.0  # Deterministic for safety checks
        )
    
    async def check_input(self, user_message: str) -> dict:
        """
        Check user input against input rails.
        Returns: {passed: bool, action: str, message: str}
        """
        try:
            result = self.guardrails.invoke({
                "input": user_message,
                "check_type": "input"
            })
            
            return {
                "passed": result.get("allowed", True),
                "action": result.get("action", "allow"),
                "message": result.get("bot_message", ""),
                "details": result.get("details", {})
            }
        except Exception as e:
            # Log error but allow request to proceed
            logger.error(f"Input guardrail check failed: {e}")
            return {"passed": True, "action": "allow", "message": ""}
    
    async def check_output(self, assistant_response: str, context: str) -> dict:
        """
        Check assistant output against output rails.
        Returns: {passed: bool, modified_response: str, warnings: list}
        """
        try:
            result = self.guardrails.invoke({
                "input": context,  # Original query for context
                "output": assistant_response,
                "check_type": "output"
            })
            
            return {
                "passed": result.get("allowed", True),
                "modified_response": result.get("output", assistant_response),
                "warnings": result.get("warnings", []),
                "details": result.get("details", {})
            }
        except Exception as e:
            logger.error(f"Output guardrail check failed: {e}")
            return {
                "passed": True,
                "modified_response": assistant_response,
                "warnings": []
            }

# Integration with LangGraph nodes
async def input_guardrail_node(self, state: ConversationState) -> ConversationState:
    """Check user input with NeMo Guardrails"""
    user_message = state["messages"][-1].content
    
    start_time = time.time()
    check_result = await self.guardrails_manager.check_input(user_message)
    duration_ms = int((time.time() - start_time) * 1000)
    
    if not check_result["passed"]:
        # Block the request
        state["guardrail_passed"] = False
        state["messages"].append(
            AIMessage(content=check_result["message"])
        )
        # Add termination flag to skip remaining nodes
        state["terminate_early"] = True
    else:
        state["guardrail_passed"] = True
    
    # Log guardrail check
    await log_guardrail_check(
        request_id=state["request_id"],
        check_type="input",
        passed=check_result["passed"],
        duration_ms=duration_ms,
        details=check_result["details"]
    )
    
    # Track tokens
    state["token_tracking"]["input_guardrail"] = {
        "duration_ms": duration_ms,
        "passed": check_result["passed"]
    }
    
    return state

async def output_guardrail_node(self, state: ConversationState) -> ConversationState:
    """Check assistant output with NeMo Guardrails"""
    assistant_message = state["messages"][-1].content
    user_message = state["messages"][-2].content  # Original query
    
    start_time = time.time()
    check_result = await self.guardrails_manager.check_output(
        assistant_response=assistant_message,
        context=user_message
    )
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Update response if modified by guardrails
    if check_result["modified_response"] != assistant_message:
        state["messages"][-1] = AIMessage(
            content=check_result["modified_response"]
        )
        state["guardrail_modified_output"] = True
    
    state["guardrail_warnings"] = check_result["warnings"]
    
    # Log guardrail check
    await log_guardrail_check(
        request_id=state["request_id"],
        check_type="output",
        passed=check_result["passed"],
        duration_ms=duration_ms,
        details=check_result["details"]
    )
    
    # Track tokens
    state["token_tracking"]["output_guardrail"] = {
        "duration_ms": duration_ms,
        "modified": check_result["modified_response"] != assistant_message
    }
    
    return state
```

### Custom Validators for Islamic Content

```python
# config/guardrails/actions.py

from nemoguardrails.actions import action

@action(is_system_action=True)
async def check_islamic_content_input(context: dict):
    """
    Custom validator for Islamic content appropriateness.
    Uses LLM to check if query is appropriate for Islamic chatbot.
    """
    user_message = context.get("user_message", "")
    
    validation_prompt = f"""
You are checking if a user query is appropriate for a Shia Islamic chatbot.

Query: {user_message}

Check for:
1. Disrespectful language towards Islam, prophets, or imams
2. Attempts to debate theology in bad faith
3. Questions about non-Islamic religious practices (unless comparative)
4. Inappropriate or sexual content
5. Political extremism

Is this query appropriate? Respond with JSON:
{{"is_appropriate": true/false, "reason": "explanation"}}
"""
    
    llm = get_llm()  # Your LLM instance
    response = llm.invoke(validation_prompt)
    
    try:
        result = json.loads(response.content)
        return result
    except:
        # If parsing fails, allow request to proceed
        return {"is_appropriate": True, "reason": "Could not validate"}

@action(is_system_action=True)
async def check_religious_accuracy(context: dict):
    """
    Check if religious claims are accurate and properly cited.
    """
    assistant_response = context.get("bot_message", "")
    
    accuracy_prompt = f"""
You are checking the religious accuracy of a response from a Shia Islamic chatbot.

Response: {assistant_response}

Check:
1. Are religious claims accurate according to Shia Islam?
2. Are sources cited for factual claims?
3. Is the response balanced and fair?

Rate accuracy from 0.0 to 1.0 and respond with JSON:
{{"accuracy_score": 0.0-1.0, "missing_citations": true/false, "concerns": ["..."]}}
"""
    
    llm = get_llm()
    response = llm.invoke(accuracy_prompt)
    
    try:
        result = json.loads(response.content)
        return result
    except:
        return {"accuracy_score": 0.8, "missing_citations": False, "concerns": []}

@action(is_system_action=True)
async def check_citations(context: dict):
    """Check if response has proper citations"""
    assistant_response = context.get("bot_message", "")
    
    # Simple check: look for citation markers [1], [2], etc.
    import re
    citations = re.findall(r'\[\d+\]', assistant_response)
    
    return {
        "has_citations": len(citations) > 0,
        "citation_count": len(citations),
        "missing_citations": len(citations) == 0
    }
```

---

## SPECIALIZED TOOLS

### 1. Ahkam (Religious Rulings) Tool

```python
from langchain.tools import tool

@tool
def ahkam_lookup(
    question: str,
    user_marja: str = "Khamenei",
    category: str = None
) -> dict:
    """
    Look up religious ruling (حکم) for a specific question.
    
    Args:
        question: The ruling question in Persian, Arabic, or English
        user_marja: The Marja to consult (default: Khamenei)
        category: Fiqh category (e.g., 'prayer', 'fasting', 'zakat')
    
    Returns:
        {
            "ruling": str,
            "confidence": float,
            "sources": list,
            "variations": list  # Other Marja opinions if different
        }
    """
    # Step 1: Classify fiqh category if not provided
    if not category:
        category = classify_fiqh_category(question)
    
    # Step 2: Search documents filtered by Marja and category
    filters = {
        "document_type": "fatwa",
        "marja": user_marja,
        "fiqh_category": category
    }
    
    # Use RAG retrieval
    results = retrieve_with_filters(
        query=question,
        filters=filters,
        top_k=5
    )
    
    if not results:
        return {
            "ruling": "لا يوجد حكم واضح في المصادر المتاحة",  # No clear ruling in available sources
            "confidence": 0.0,
            "sources": [],
            "variations": []
        }
    
    # Step 3: Extract ruling from top results
    ruling_extraction_prompt = f"""
Based on the following fatwas from Marja {user_marja}, extract the religious ruling.

Question: {question}
Sources: {format_sources(results)}

Provide:
1. The ruling in Persian (حکم)
2. Confidence level (0.0 to 1.0)
3. Key points

Response in JSON format.
"""
    
    llm = get_llm(tier=2)
    ruling_response = llm.invoke(ruling_extraction_prompt)
    ruling_data = json.loads(ruling_response.content)
    
    # Step 4: Check for variations from other Maraji (if user wants comparison)
    variations = []
    if check_for_variations_needed():
        other_maraji = ["Khamenei", "Makarem Shirazi", "Wahid Khorasani"]
        for marja in other_maraji:
            if marja == user_marja:
                continue
            
            marja_results = retrieve_with_filters(
                query=question,
                filters={"marja": marja, "fiqh_category": category},
                top_k=2
            )
            
            if marja_results:
                variations.append({
                    "marja": marja,
                    "ruling": extract_ruling(marja_results),
                    "source": marja_results[0]["source"]
                })
    
    return {
        "ruling": ruling_data["ruling"],
        "confidence": ruling_data["confidence"],
        "sources": [r["source"] for r in results],
        "variations": variations
    }

def classify_fiqh_category(question: str) -> str:
    """Classify question into fiqh category using LLM"""
    categories = [
        "prayer", "fasting", "zakat", "khums", "hajj",
        "marriage", "divorce", "inheritance", "trade",
        "food", "clothing", "purification", "other"
    ]
    
    prompt = f"""
Classify this fiqh question into one category:
Categories: {categories}

Question: {question}

Category:
"""
    
    llm = get_llm(tier=3)  # Fast classification
    return llm.invoke(prompt).content.strip().lower()
```

### 2. DateTime Calculator Tool

```python
@tool
def datetime_calculator(
    query: str,
    location: dict = None
) -> dict:
    """
    Calculate Islamic dates, prayer times, and calendar conversions.
    
    Args:
        query: Natural language query about date/time
        location: {lat, lon, city} for prayer times
    
    Returns:
        {
            "result": str,
            "calculation_type": str,
            "details": dict
        }
    """
    # Parse query to determine calculation type
    calc_type = determine_calculation_type(query)
    
    if calc_type == "prayer_times":
        return calculate_prayer_times(location)
    
    elif calc_type == "hijri_conversion":
        return convert_to_hijri(query)
    
    elif calc_type == "ramadan_dates":
        return get_ramadan_dates(query)
    
    elif calc_type == "event_date":
        return get_islamic_event_date(query)
    
    else:
        return {"result": "Could not determine calculation type", "error": True}

def calculate_prayer_times(location: dict) -> dict:
    """Calculate prayer times for given location"""
    from praytimes import PrayTimes
    
    if not location:
        # Use default location (configured in settings)
        location = get_user_location()
    
    pt = PrayTimes('Jafari')  # Shia calculation method
    times = pt.getTimes(
        datetime.now().date(),
        location['coordinates'],
        location['timezone']
    )
    
    return {
        "result": format_prayer_times(times),
        "calculation_type": "prayer_times",
        "details": {
            "location": location,
            "method": "Jafari",
            "times": times
        }
    }

def convert_to_hijri(query: str) -> dict:
    """Convert Gregorian date to Hijri"""
    from hijri_converter import Gregorian, Hijri
    
    # Extract date from query
    date = extract_date(query)
    
    if not date:
        date = datetime.now().date()
    
    hijri = Hijri.fromisoformat(date.isoformat())
    
    return {
        "result": f"{hijri.datetuple()} هجری قمری",
        "calculation_type": "hijri_conversion",
        "details": {
            "gregorian": date.isoformat(),
            "hijri": str(hijri),
            "islamic_month": get_islamic_month_name(hijri.month)
        }
    }
```

### 3. Math Calculator Tool

```python
@tool
def math_calculator(
    calculation_type: str,
    parameters: dict
) -> dict:
    """
    Perform Islamic financial calculations.
    
    Args:
        calculation_type: 'zakat', 'khums', 'inheritance', 'general'
        parameters: Calculation-specific parameters
    
    Returns:
        {
            "result": float,
            "breakdown": dict,
            "ruling_notes": str
        }
    """
    if calculation_type == "zakat":
        return calculate_zakat(parameters)
    
    elif calculation_type == "khums":
        return calculate_khums(parameters)
    
    elif calculation_type == "inheritance":
        return calculate_inheritance(parameters)
    
    else:
        return calculate_general_math(parameters)

def calculate_zakat(params: dict) -> dict:
    """
    Calculate Zakat based on wealth type.
    
    Parameters:
        wealth_type: 'gold', 'silver', 'cash', 'livestock', 'trade_goods'
        amount: numeric value
        duration: months held
    """
    wealth_type = params["wealth_type"]
    amount = params["amount"]
    duration = params.get("duration", 12)
    
    # Nisab thresholds (update these from reliable sources)
    nisab = {
        "gold": 85,  # grams
        "silver": 595,  # grams
        "cash": 595 * get_current_silver_price(),  # equivalent to silver nisab
    }
    
    # Check if amount exceeds nisab
    if amount < nisab.get(wealth_type, 0):
        return {
            "result": 0.0,
            "zakat_applicable": False,
            "reason": "مقدار از نصاب کمتر است",  # Amount is below nisab
            "nisab_threshold": nisab[wealth_type]
        }
    
    # Check duration (must be held for one lunar year)
    if duration < 12:
        return {
            "result": 0.0,
            "zakat_applicable": False,
            "reason": "مدت زمان نگهداری کمتر از یک سال قمری است"
        }
    
    # Calculate zakat (2.5% for most wealth types)
    zakat_rate = 0.025
    zakat_amount = amount * zakat_rate
    
    return {
        "result": zakat_amount,
        "zakat_applicable": True,
        "breakdown": {
            "total_amount": amount,
            "zakat_rate": "2.5%",
            "zakat_amount": zakat_amount,
            "remaining": amount - zakat_amount
        },
        "ruling_notes": "زکات واجب است - Zakat is obligatory"
    }

def calculate_khums(params: dict) -> dict:
    """
    Calculate Khums (1/5 of surplus income).
    
    Parameters:
        annual_income: Total income for the year
        annual_expenses: Total necessary expenses
        exempt_items: List of Khums-exempt items
    """
    income = params["annual_income"]
    expenses = params["annual_expenses"]
    exempt = params.get("exempt_items", [])
    
    # Calculate surplus
    surplus = income - expenses
    
    # Subtract exempt items
    for item in exempt:
        surplus -= item["value"]
    
    if surplus <= 0:
        return {
            "result": 0.0,
            "khums_applicable": False,
            "reason": "هیچ مازاد درآمدی وجود ندارد",  # No surplus income
            "breakdown": {
                "income": income,
                "expenses": expenses,
                "surplus": 0
            }
        }
    
    # Calculate Khums (20%)
    khums_amount = surplus * 0.20
    
    # Split Khums (half for Sadat, half for Imam's portion)
    sadat_share = khums_amount * 0.5
    imam_share = khums_amount * 0.5
    
    return {
        "result": khums_amount,
        "khums_applicable": True,
        "breakdown": {
            "total_income": income,
            "total_expenses": expenses,
            "surplus": surplus,
            "khums_rate": "20%",
            "khums_amount": khums_amount,
            "sadat_share": sadat_share,
            "imam_share": imam_share
        },
        "ruling_notes": "خمس واجب است - Khums is obligatory"
    }
```

### 4. Comparison Tool

```python
@tool
def comparison_tool(
    comparison_type: str,
    entities: List[str],
    aspect: str = None
) -> dict:
    """
    Compare rulings, interpretations, or scholars' opinions.
    
    Args:
        comparison_type: 'maraji', 'interpretations', 'schools', 'historical'
        entities: List of items to compare (e.g., Marja names)
        aspect: Specific aspect to compare (e.g., 'prayer', 'fasting')
    
    Returns:
        {
            "comparison_table": dict,
            "similarities": list,
            "differences": list,
            "conclusion": str
        }
    """
    if comparison_type == "maraji":
        return compare_maraji_rulings(entities, aspect)
    
    elif comparison_type == "interpretations":
        return compare_tafsir_interpretations(entities, aspect)
    
    elif comparison_type == "schools":
        return compare_fiqh_schools(entities, aspect)
    
    else:
        return {"error": "Invalid comparison type"}

def compare_maraji_rulings(maraji: List[str], topic: str) -> dict:
    """Compare rulings from multiple Maraji on a topic"""
    
    comparison_data = {}
    
    for marja in maraji:
        # Retrieve rulings for this Marja
        rulings = retrieve_with_filters(
            query=topic,
            filters={"marja": marja, "document_type": "fatwa"},
            top_k=3
        )
        
        if rulings:
            comparison_data[marja] = {
                "ruling": extract_ruling(rulings),
                "source": rulings[0]["source"],
                "details": rulings[0]["content"]
            }
    
    # Analyze similarities and differences
    similarities = find_similarities(comparison_data)
    differences = find_differences(comparison_data)
    
    # Generate conclusion
    conclusion_prompt = f"""
Compare the rulings from these Maraji on {topic}:

{format_comparison_data(comparison_data)}

Provide:
1. Main points of agreement
2. Key differences
3. Possible reasons for differences
4. Practical guidance for followers

Response in Persian.
"""
    
    llm = get_llm(tier=2)
    conclusion = llm.invoke(conclusion_prompt).content
    
    return {
        "comparison_table": comparison_data,
        "similarities": similarities,
        "differences": differences,
        "conclusion": conclusion,
        "topic": topic
    }
```

### 5. Rejal Lookup Tool

```python
@tool
def rejal_lookup(
    narrator_name: str,
    context: str = None
) -> dict:
    """
    Look up information about a hadith narrator.
    
    Args:
        narrator_name: Name of the narrator (Arabic, Persian, or English)
        context: Optional context (hadith text, chain)
    
    Returns:
        {
            "person_info": dict,
            "reliability": dict,
            "biographical_notes": str,
            "related_chains": list
        }
    """
    # Search for narrator in rejal_persons table
    person = search_rejal_person(narrator_name)
    
    if not person:
        return {
            "found": False,
            "message": f"اطلاعاتی درباره '{narrator_name}' یافت نشد",
            "suggestions": suggest_similar_names(narrator_name)
        }
    
    # Get reliability information
    reliability_info = {
        "rating": person["reliability_rating"],
        "score": person["reliability_score"],
        "sources": person["reliability_sources"],
        "interpretation": interpret_reliability_rating(person["reliability_rating"])
    }
    
    # Get chains this person appears in
    related_chains = get_narrator_chains(person["id"])
    
    # Format biographical info
    bio = format_biography(person)
    
    return {
        "found": True,
        "person_info": {
            "name_arabic": person["name_arabic"],
            "name_persian": person["name_persian"],
            "name_english": person["name_english"],
            "kunyah": person["kunyah"],
            "birth_year": person["birth_year"],
            "death_year": person["death_year"],
            "lived_in": person["lived_in"]
        },
        "reliability": reliability_info,
        "biographical_notes": bio,
        "related_chains": related_chains,
        "teachers": person["teachers"],
        "students": person["students"]
    }

def interpret_reliability_rating(rating: str) -> str:
    """Interpret Rejal reliability rating"""
    interpretations = {
        "thiqah": "ثقه - قابل اعتماد / Reliable and trustworthy",
        "hasan": "حسن - خوب / Good, acceptable",
        "da`if": "ضعیف - ضعیف / Weak narrator",
        "matruk": "متروک - رها شده / Abandoned, not to be relied upon",
        "majhul": "مجهول - ناشناخته / Unknown",
        "muwaththaq": "موثق - معتبر / Authenticated and reliable"
    }
    
    return interpretations.get(rating, "تعریف نشده / Undefined")
```

---

## CACHING STRATEGY

### Multi-Level Caching Architecture

```python
from redis import Redis
from typing import Any, Optional
import hashlib
import json

class CacheManager:
    """Manages multi-level caching with Redis"""
    
    def __init__(self):
        self.redis = Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            db=0,
            decode_responses=True
        )
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate deterministic cache key"""
        key_data = f"{prefix}:{json.dumps(args)}:{json.dumps(kwargs, sort_keys=True)}"
        return f"{prefix}:{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"
    
    async def get_cached_response(
        self,
        query: str,
        mode: str,
        user_marja: str,
        environment: str
    ) -> Optional[str]:
        """
        Level 1: Response Cache
        Cache complete responses for identical queries
        """
        cache_key = self.generate_cache_key(
            "response",
            query=query,
            mode=mode,
            marja=user_marja,
            env=environment
        )
        
        cached = self.redis.get(cache_key)
        
        if cached:
            # Track cache hit
            await track_cache_hit("response", cache_key)
            return json.loads(cached)
        
        await track_cache_miss("response", cache_key)
        return None
    
    async def cache_response(
        self,
        query: str,
        mode: str,
        user_marja: str,
        environment: str,
        response: str,
        ttl: int = 86400  # 24 hours default
    ):
        """Cache a response"""
        cache_key = self.generate_cache_key(
            "response",
            query=query,
            mode=mode,
            marja=user_marja,
            env=environment
        )
        
        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(response)
        )
    
    async def get_cached_embedding(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """
        Level 2: Embedding Cache
        Cache embedding vectors
        """
        cache_key = self.generate_cache_key(
            "embedding",
            text=text,
            model=model
        )
        
        cached = self.redis.get(cache_key)
        
        if cached:
            await track_cache_hit("embedding", cache_key)
            return json.loads(cached)
        
        await track_cache_miss("embedding", cache_key)
        return None
    
    async def cache_embedding(
        self,
        text: str,
        model: str,
        embedding: List[float],
        ttl: int = 604800  # 7 days
    ):
        """Cache an embedding"""
        cache_key = self.generate_cache_key(
            "embedding",
            text=text,
            model=model
        )
        
        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(embedding)
        )
    
    async def get_cached_retrieval(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: dict
    ) -> Optional[List[dict]]:
        """
        Level 3: Retrieval Cache
        Cache retrieval results
        """
        cache_key = self.generate_cache_key(
            "retrieval",
            embedding_hash=hashlib.sha256(
                str(query_embedding).encode()
            ).hexdigest()[:16],
            top_k=top_k,
            filters=filters
        )
        
        cached = self.redis.get(cache_key)
        
        if cached:
            await track_cache_hit("retrieval", cache_key)
            return json.loads(cached)
        
        await track_cache_miss("retrieval", cache_key)
        return None
    
    async def cache_retrieval(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: dict,
        results: List[dict],
        ttl: int = 21600  # 6 hours
    ):
        """Cache retrieval results"""
        cache_key = self.generate_cache_key(
            "retrieval",
            embedding_hash=hashlib.sha256(
                str(query_embedding).encode()
            ).hexdigest()[:16],
            top_k=top_k,
            filters=filters
        )
        
        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(results)
        )
    
    async def get_cached_tool_result(
        self,
        tool_name: str,
        parameters: dict
    ) -> Optional[Any]:
        """
        Level 4: Tool Call Cache
        Cache tool execution results
        """
        cache_key = self.generate_cache_key(
            "tool",
            tool_name=tool_name,
            params=parameters
        )
        
        cached = self.redis.get(cache_key)
        
        if cached:
            await track_cache_hit("tool", cache_key)
            return json.loads(cached)
        
        await track_cache_miss("tool", cache_key)
        return None
    
    async def cache_tool_result(
        self,
        tool_name: str,
        parameters: dict,
        result: Any,
        ttl: int = None
    ):
        """Cache tool result with tool-specific TTL"""
        # Tool-specific TTL
        tool_ttls = {
            "datetime_calculator": 3600,  # 1 hour
            "math_calculator": 2592000,  # 30 days
            "ahkam_lookup": 86400,  # 24 hours
            "web_search": 3600,  # 1 hour
            "rejal_lookup": 604800  # 7 days
        }
        
        ttl = ttl or tool_ttls.get(tool_name, 3600)
        
        cache_key = self.generate_cache_key(
            "tool",
            tool_name=tool_name,
            params=parameters
        )
        
        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(result)
        )
    
    async def get_cached_guardrail_check(
        self,
        input_text: str,
        guardrail_type: str
    ) -> Optional[dict]:
        """
        Level 5: Guardrail Cache
        Cache guardrail check results
        """
        cache_key = self.generate_cache_key(
            "guardrail",
            text=input_text,
            type=guardrail_type
        )
        
        cached = self.redis.get(cache_key)
        
        if cached:
            await track_cache_hit("guardrail", cache_key)
            return json.loads(cached)
        
        await track_cache_miss("guardrail", cache_key)
        return None
    
    async def cache_guardrail_check(
        self,
        input_text: str,
        guardrail_type: str,
        result: dict,
        ttl: int = 3600  # 1 hour
    ):
        """Cache guardrail check result"""
        cache_key = self.generate_cache_key(
            "guardrail",
            text=input_text,
            type=guardrail_type
        )
        
        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(result)
        )
    
    async def get_cached_web_search(
        self,
        search_query: str
    ) -> Optional[List[dict]]:
        """
        Level 6: Web Search Cache
        Cache web search results
        """
        cache_key = self.generate_cache_key(
            "web_search",
            query=search_query
        )
        
        cached = self.redis.get(cache_key)
        
        if cached:
            await track_cache_hit("web_search", cache_key)
            return json.loads(cached)
        
        await track_cache_miss("web_search", cache_key)
        return None
    
    async def cache_web_search(
        self,
        search_query: str,
        results: List[dict],
        ttl: int = 3600  # 1 hour
    ):
        """Cache web search results"""
        cache_key = self.generate_cache_key(
            "web_search",
            query=search_query
        )
        
        self.redis.setex(
            cache_key,
            ttl,
            json.loads(results)
        )
        
        # Also store in PostgreSQL for analytics
        await store_web_search_in_db(search_query, results)
    
    async def invalidate_cache(
        self,
        cache_type: str = None,
        pattern: str = None
    ):
        """Invalidate cache entries"""
        if pattern:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        elif cache_type:
            keys = self.redis.keys(f"{cache_type}:*")
            if keys:
                self.redis.delete(*keys)
        else:
            # Invalidate all cache
            self.redis.flushdb()
```

### Cache Hit Rate Optimization

```python
# Target cache hit rates
CACHE_TARGETS = {
    "response": 0.70,  # 70% target
    "embedding": 0.85,  # 85% target
    "retrieval": 0.65,  # 65% target
    "tool": 0.50,  # 50% target
    "guardrail": 0.80,  # 80% target
    "web_search": 0.40  # 40% target
}

async def monitor_cache_performance():
    """Monitor cache hit rates and optimize TTLs"""
    for cache_type, target_rate in CACHE_TARGETS.items():
        # Get current hit rate from analytics
        current_rate = await get_cache_hit_rate(cache_type)
        
        if current_rate < target_rate:
            # Increase TTL to improve hit rate
            await adjust_cache_ttl(cache_type, increase=True)
        elif current_rate > target_rate + 0.1:
            # Decrease TTL to save memory
            await adjust_cache_ttl(cache_type, increase=False)
```

---




### **Part 3: Deployment & Operations**
**Contents:**
- **Admin Dashboard**
  - Document upload & management
  - Chunk approval workflow
  - Analytics dashboard
- **External API** (for third-party companies)
  - Client management
  - Rate limiting
  - Usage tracking
- **Ticket Support System**
  - Creation, assignment, resolution
  - Performance tracking
- **Leaderboard Systems**
  - Admin performance leaderboard
  - User feedback quality leaderboard
- **Rejal & Hadith Chain Validation**
  - Chain visualization
  - Reliability calculation
- **Backup & Recovery** (HuggingFace integration)
- **Environment & Deployment**
  - Docker Compose setup
  - Secrets management
  - Environment separation strategies
- **Testing Strategy**
- **Security & Compliance**
- **Pre-Deployment Checklist**
- **Implementation Roadmap** (36 weeks)
- **Cost Estimation**


---

# SHIA ISLAMIC RAG CHATBOT - IMPLEMENTATION PLAN (PART 3 - FINAL)

## Continuation from Parts 1 & 2

---

## ADMIN DASHBOARD

### Dashboard Architecture

```python
# FastAPI admin routes
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from typing import List, Optional

admin_router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

@admin_router.get("/dashboard/overview")
async def get_dashboard_overview(
    admin: Admin = Depends(verify_admin),
    time_range: str = "7d"  # 24h, 7d, 30d, 90d, all
):
    """
    Get high-level dashboard metrics.
    Permissions required: view_analytics
    """
    check_permission(admin, "view_analytics")
    
    metrics = {
        "users": {
            "total": await count_users(),
            "active_today": await count_active_users("24h"),
            "new_this_period": await count_new_users(time_range)
        },
        "conversations": {
            "total": await count_conversations(),
            "active": await count_active_conversations(),
            "avg_messages_per_conversation": await get_avg_messages()
        },
        "documents": {
            "total": await count_documents(),
            "pending_approval": await count_pending_chunks(),
            "processed_this_period": await count_processed_documents(time_range)
        },
        "performance": {
            "avg_response_time_ms": await get_avg_response_time(time_range),
            "cache_hit_rate": await get_cache_hit_rate(time_range),
            "error_rate": await get_error_rate(time_range)
        },
        "costs": {
            "total_cost_usd": await get_total_cost(time_range),
            "llm_cost": await get_llm_cost(time_range),
            "per_conversation": await get_cost_per_conversation(time_range)
        },
        "tickets": {
            "open": await count_tickets("open"),
            "in_progress": await count_tickets("in_progress"),
            "resolved_this_period": await count_resolved_tickets(time_range)
        }
    }
    
    return metrics
```

### Document Upload & Management

```python
@admin_router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    metadata: DocumentMetadata,
    admin: Admin = Depends(verify_admin)
):
    """
    Upload a new document for processing.
    Permissions required: manage_content
    """
    check_permission(admin, "manage_content")
    
    # Step 1: Validate file
    if not validate_file(file):
        raise HTTPException(400, "Invalid file type or size")
    
    # Step 2: Save file
    file_path = await save_upload(file)
    
    # Step 3: Detect file type category
    file_category = detect_file_category(file)
    requires_ocr = file_category == "ocr_required"
    
    # Step 4: Create document record
    document = await create_document(
        title=metadata.title,
        file_path=file_path,
        document_type=metadata.document_type,
        language=metadata.language or "fa",
        file_type_category=file_category,
        requires_ocr=requires_ocr,
        chunking_mode=metadata.chunking_mode or "auto",
        uploaded_by=admin.id
    )
    
    # Step 5: Queue for processing
    await queue_document_processing(document.id)
    
    # Step 6: Log action
    await log_audit(
        actor_id=admin.user_id,
        action="document_upload",
        resource_type="document",
        resource_id=document.id
    )
    
    return {
        "document_id": document.id,
        "status": "queued",
        "requires_ocr": requires_ocr,
        "estimated_processing_time": estimate_processing_time(file)
    }

def detect_file_category(file: UploadFile) -> str:
    """
    Detect file category for optimized processing.
    """
    extension = file.filename.split(".")[-1].lower()
    
    # Clean text files (no corruption when extracted)
    clean_text = ["txt", "md", "docx", "html"]
    
    # Requires OCR
    ocr_required = ["pdf", "jpg", "jpeg", "png", "tiff"]
    
    # Structured data
    structured = ["json", "xml", "csv"]
    
    if extension in clean_text:
        return "clean_text"
    elif extension in ocr_required:
        return "ocr_required"
    elif extension in structured:
        return "structured"
    else:
        return "other"
```

### Document Processing Pipeline

```python
from celery import Celery
from langchain.text_splitter import RecursiveCharacterTextSplitter

celery_app = Celery('shia_rag', broker=os.getenv('REDIS_URL'))

@celery_app.task
async def process_document(document_id: str):
    """
    Background task to process uploaded document.
    """
    document = await get_document(document_id)
    
    try:
        # Step 1: Update status
        await update_document_status(document_id, "processing")
        
        # Step 2: Extract text
        if document.requires_ocr:
            text = await extract_text_with_ocr(document.file_path)
        else:
            text = await extract_text_simple(document.file_path)
        
        # Step 3: Clean text
        text = clean_text(text, language=document.language)
        
        # Step 4: Chunking
        if document.chunking_mode == "auto":
            chunks = await chunk_text_auto(
                text=text,
                language=document.language,
                chunk_size=document.chunk_size,
                overlap=document.chunk_overlap
            )
        else:
            # Manual chunking - admin will review
            chunks = await chunk_text_manual(
                text=text,
                method=document.chunking_method
            )
        
        # Step 5: Create chunk records
        for idx, chunk in enumerate(chunks):
            await create_chunk(
                document_id=document_id,
                chunk_text=chunk["text"],
                chunk_index=idx,
                char_count=len(chunk["text"]),
                word_count=len(chunk["text"].split()),
                token_count_estimated=estimate_tokens(chunk["text"]),
                chunking_method=chunk["method"],
                overlap_with_previous=chunk.get("overlap", 0)
            )
        
        # Step 6: Generate embeddings
        await generate_embeddings_for_document(document_id)
        
        # Step 7: Update status
        if document.requires_chunk_approval:
            await update_document_status(document_id, "awaiting_chunk_approval")
            # Assign to content admin for review
            await assign_chunk_review_task(document_id)
        else:
            await update_document_status(document_id, "completed")
        
        # Step 8: Update document metadata
        await update_document(
            document_id,
            chunk_count=len(chunks),
            total_characters=len(text),
            processed_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        await update_document_status(document_id, "failed")
        raise

async def chunk_text_auto(
    text: str,
    language: str,
    chunk_size: int,
    overlap: int
) -> List[dict]:
    """
    Automatic chunking optimized for Persian/Arabic.
    """
    # Use semantic splitter for Persian/Arabic
    if language in ["fa", "ar"]:
        # Larger chunk size for Persian/Arabic (more efficient)
        effective_chunk_size = chunk_size  # 768 tokens
        effective_overlap = overlap  # 150 tokens
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=effective_chunk_size,
            chunk_overlap=effective_overlap,
            separators=["\n\n", "\n", ".", "؟", "!", "،", " ", ""],  # Persian/Arabic-specific
            length_function=estimate_tokens
        )
    else:
        # Standard splitter for English/Urdu
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=estimate_tokens
        )
    
    chunks = splitter.split_text(text)
    
    return [
        {
            "text": chunk,
            "method": "semantic",
            "overlap": effective_overlap if i > 0 else 0
        }
        for i, chunk in enumerate(chunks)
    ]
```

### Chunk Approval Workflow

```python
@admin_router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    admin: Admin = Depends(verify_admin)
):
    """
    Get chunks for review.
    Permissions required: approve_chunks
    """
    check_permission(admin, "approve_chunks")
    
    chunks = await get_chunks_for_document(document_id)
    document = await get_document(document_id)
    
    return {
        "document": document,
        "chunks": chunks,
        "total_chunks": len(chunks),
        "approval_status": document.chunk_approval_status
    }

@admin_router.post("/documents/{document_id}/chunks/approve")
async def approve_chunks(
    document_id: str,
    approval: ChunkApproval,
    admin: Admin = Depends(verify_admin)
):
    """
    Approve or request revision for chunks.
    Permissions required: approve_chunks
    """
    check_permission(admin, "approve_chunks")
    
    if approval.action == "approve":
        # Approve all chunks
        await update_document(
            document_id,
            chunk_approval_status="approved",
            chunk_approved_by=admin.id,
            chunk_approved_at=datetime.now(),
            processing_status="completed"
        )
        
        # Log action
        await log_audit(
            actor_id=admin.user_id,
            action="chunks_approved",
            resource_type="document",
            resource_id=document_id
        )
        
        return {"status": "approved"}
    
    elif approval.action == "reject":
        # Reject and request revision
        await update_document(
            document_id,
            chunk_approval_status="needs_revision",
            verification_notes=approval.notes
        )
        
        # Notify uploader
        await notify_admin(
            document.uploaded_by,
            f"Document '{document.title}' needs revision: {approval.notes}"
        )
        
        return {"status": "rejected"}
    
    elif approval.action == "modify":
        # Admin wants to manually modify chunks
        for modification in approval.modifications:
            await update_chunk(
                modification.chunk_id,
                chunk_text=modification.new_text
            )
        
        # Re-generate embeddings for modified chunks
        for mod in approval.modifications:
            await regenerate_embedding_for_chunk(mod.chunk_id)
        
        await update_document(
            document_id,
            chunk_approval_status="approved",
            chunk_approved_by=admin.id,
            chunk_approved_at=datetime.now()
        )
        
        return {"status": "modified_and_approved"}
```

---

## EXTERNAL API FOR THIRD-PARTY COMPANIES

### API Client Management

```python
@admin_router.post("/api-clients/create")
async def create_api_client(
    client_info: APIClientInfo,
    admin: Admin = Depends(verify_super_admin)
):
    """
    Create a new external API client.
    Permissions required: super_admin only
    """
    # Generate API key and secret
    api_key = generate_api_key()
    api_secret = generate_api_secret()
    
    # Hash for storage
    api_key_hash = hash_api_key(api_key)
    api_secret_hash = hash_api_secret(api_secret)
    
    # Create client record
    client = await create_external_client(
        client_name=client_info.client_name,
        client_company=client_info.company,
        client_email=client_info.email,
        api_key=api_key_hash,
        api_secret=api_secret_hash,
        rate_limit_tier=client_info.tier,
        allowed_endpoints=client_info.endpoints,
        monthly_request_limit=get_tier_limits(client_info.tier)["requests"],
        monthly_token_limit=get_tier_limits(client_info.tier)["tokens"]
    )
    
    # Log creation
    await log_audit(
        actor_id=admin.user_id,
        action="api_client_created",
        resource_type="external_client",
        resource_id=client.id
    )
    
    # Return unhashed credentials (ONLY THIS ONE TIME!)
    return {
        "client_id": client.id,
        "api_key": api_key,  # Show once, then it's hashed
        "api_secret": api_secret,  # Show once, then it's hashed
        "message": "IMPORTANT: Save these credentials. They will not be shown again!"
    }

def get_tier_limits(tier: str) -> dict:
    """Get rate limits for each tier"""
    tiers = {
        "basic": {
            "requests": 1000,
            "tokens": 100000,
            "cost_per_token": 0.00002
        },
        "standard": {
            "requests": 10000,
            "tokens": 1000000,
            "cost_per_token": 0.000015
        },
        "premium": {
            "requests": 100000,
            "tokens": 10000000,
            "cost_per_token": 0.00001
        },
        "enterprise": {
            "requests": None,  # Unlimited
            "tokens": None,  # Unlimited
            "cost_per_token": 0.000005
        }
    }
    
    return tiers.get(tier, tiers["basic"])
```

### External API Endpoints

```python
# Public API router (separate from admin)
public_api_router = APIRouter(prefix="/api/v1", tags=["public"])

async def verify_api_client(
    authorization: str = Header(...)
) -> ExternalClient:
    """Verify API client credentials"""
    try:
        # Parse "Bearer {api_key}" header
        api_key = authorization.split(" ")[1]
        
        # Hash and lookup
        api_key_hash = hash_api_key(api_key)
        client = await get_client_by_api_key(api_key_hash)
        
        if not client or not client.is_active:
            raise HTTPException(401, "Invalid or inactive API key")
        
        # Check if expired
        if client.expires_at and client.expires_at < datetime.now():
            raise HTTPException(401, "API key expired")
        
        # Check rate limits
        if not await check_external_rate_limits(client):
            raise HTTPException(429, "Rate limit exceeded")
        
        return client
        
    except Exception as e:
        raise HTTPException(401, "Authentication failed")

@public_api_router.post("/chat")
async def external_chat(
    request: ChatRequest,
    client: ExternalClient = Depends(verify_api_client)
):
    """
    External chat endpoint for third-party companies.
    """
    # Check if endpoint is allowed
    if "/chat" not in client.allowed_endpoints:
        raise HTTPException(403, "Access to this endpoint not granted")
    
    # Track usage
    start_time = time.time()
    
    try:
        # Process request through main chatbot
        response = await process_chat_request(
            query=request.query,
            mode=request.mode or "standard",
            user_id=f"external_{client.id}",  # Special user ID for external
            environment="prod"
        )
        
        # Calculate tokens and cost
        tokens_used = response["token_tracking"]["total_tokens"]
        cost = tokens_used * client.cost_per_token
        
        # Update client usage
        await update_client_usage(
            client_id=client.id,
            requests=1,
            tokens=tokens_used,
            cost=cost
        )
        
        # Log usage
        await log_external_api_usage(
            client_id=client.id,
            endpoint="/chat",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            tokens_used=tokens_used,
            cost_usd=cost
        )
        
        return {
            "response": response["answer"],
            "citations": response["citations"],
            "metadata": {
                "tokens_used": tokens_used,
                "cost_usd": cost,
                "model_used": response["model"]
            }
        }
        
    except Exception as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(500, "Internal server error")

@public_api_router.get("/usage")
async def get_usage_stats(
    client: ExternalClient = Depends(verify_api_client)
):
    """Get current month's usage statistics"""
    usage = await get_client_monthly_usage(client.id)
    
    return {
        "client_name": client.client_name,
        "current_month": {
            "requests": usage["requests"],
            "requests_limit": client.monthly_request_limit,
            "tokens": usage["tokens"],
            "tokens_limit": client.monthly_token_limit,
            "cost_usd": usage["cost"]
        },
        "rate_limit_tier": client.rate_limit_tier,
        "remaining_quota": {
            "requests": client.monthly_request_limit - usage["requests"] if client.monthly_request_limit else None,
            "tokens": client.monthly_token_limit - usage["tokens"] if client.monthly_token_limit else None
        }
    }
```

---

## TICKET SUPPORT SYSTEM

### Ticket Creation & Management

```python
@app.post("/tickets/create")
async def create_support_ticket(
    ticket: TicketCreate,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Create a support ticket.
    Available to both authenticated and anonymous users.
    """
    # Generate ticket number
    ticket_number = generate_ticket_number()
    
    # Create ticket
    new_ticket = await create_ticket(
        ticket_number=ticket_number,
        user_id=current_user.id if current_user else None,
        user_email=ticket.email,
        user_name=ticket.name or (current_user.full_name if current_user else "Anonymous"),
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=auto_classify_priority(ticket.description),
        related_conversation_id=ticket.conversation_id,
        related_message_id=ticket.message_id
    )
    
    # Auto-assign to support admin with least workload
    assigned_admin = await get_least_busy_support_admin()
    if assigned_admin:
        await assign_ticket(new_ticket.id, assigned_admin.id)
    
    # Send confirmation email
    await send_ticket_confirmation_email(
        email=ticket.email,
        ticket_number=ticket_number
    )
    
    # Log creation
    await log_audit(
        actor_id=current_user.id if current_user else None,
        action="ticket_created",
        resource_type="ticket",
        resource_id=new_ticket.id
    )
    
    return {
        "ticket_id": new_ticket.id,
        "ticket_number": ticket_number,
        "status": "open",
        "message": "تیکت شما ایجاد شد. به زودی پاسخ خواهید گرفت."  # Ticket created. You'll receive a response soon.
    }

@admin_router.get("/tickets")
async def get_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_me: bool = False,
    admin: Admin = Depends(verify_admin)
):
    """
    Get tickets for admin.
    Permissions required: answer_tickets
    """
    check_permission(admin, "answer_tickets")
    
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if assigned_to_me:
        filters["assigned_to"] = admin.id
    
    tickets = await get_tickets_with_filters(filters)
    
    return {
        "tickets": tickets,
        "total": len(tickets)
    }

@admin_router.post("/tickets/{ticket_id}/respond")
async def respond_to_ticket(
    ticket_id: str,
    response: TicketResponse,
    admin: Admin = Depends(verify_admin)
):
    """
    Respond to a ticket.
    Permissions required: answer_tickets
    """
    check_permission(admin, "answer_tickets")
    
    ticket = await get_ticket(ticket_id)
    
    # Add message to ticket thread
    message = await create_ticket_message(
        ticket_id=ticket_id,
        sender_type="admin",
        sender_id=admin.id,
        message_text=response.message,
        is_internal_note=response.is_internal
    )
    
    # Update ticket status
    if response.change_status:
        await update_ticket_status(ticket_id, response.new_status)
    
    # Track first response time (if this is first admin response)
    if not ticket.first_response_time_minutes:
        first_response_time = (datetime.now() - ticket.created_at).total_seconds() / 60
        await update_ticket(
            ticket_id,
            first_response_time_minutes=int(first_response_time)
        )
    
    # Send email notification to user (if not internal note)
    if not response.is_internal:
        await send_ticket_response_email(
            email=ticket.user_email,
            ticket_number=ticket.ticket_number,
            response=response.message
        )
    
    # Log action
    await log_audit(
        actor_id=admin.user_id,
        action="ticket_responded",
        resource_type="ticket",
        resource_id=ticket_id
    )
    
    return {"status": "success", "message_id": message.id}

@admin_router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution: TicketResolution,
    admin: Admin = Depends(verify_admin)
):
    """
    Mark ticket as resolved.
    Permissions required: answer_tickets
    """
    check_permission(admin, "answer_tickets")
    
    ticket = await get_ticket(ticket_id)
    
    # Calculate resolution time
    resolution_time = (datetime.now() - ticket.created_at).total_seconds() / 60
    
    # Update ticket
    await update_ticket(
        ticket_id,
        status="resolved",
        resolution_notes=resolution.notes,
        resolved_at=datetime.now(),
        resolved_by=admin.id,
        resolution_time_minutes=int(resolution_time)
    )
    
    # Update admin performance
    await update_admin_leaderboard(
        admin_id=admin.id,
        tickets_resolved=1,
        avg_resolution_time=resolution_time
    )
    
    # Send resolution email
    await send_ticket_resolution_email(
        email=ticket.user_email,
        ticket_number=ticket.ticket_number,
        resolution=resolution.notes
    )
    
    return {"status": "resolved"}
```

---

## LEADERBOARD SYSTEMS

### Admin Performance Leaderboard

```python
@admin_router.get("/leaderboard/admins")
async def get_admin_leaderboard(
    period: str = "monthly",  # daily, weekly, monthly, all_time
    admin: Admin = Depends(verify_super_admin)
):
    """
    Get admin performance leaderboard.
    Only super_admin can view.
    """
    period_start, period_end = get_period_range(period)
    
    leaderboard = await get_admin_leaderboard_data(
        period_type=period,
        period_start=period_start,
        period_end=period_end
    )
    
    # Sort by points
    leaderboard = sorted(leaderboard, key=lambda x: x["points"], reverse=True)
    
    # Assign ranks
    for idx, entry in enumerate(leaderboard, 1):
        entry["rank"] = idx
    
    return {
        "period": period,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "leaderboard": leaderboard
    }

@celery_app.task
async def calculate_admin_leaderboard_daily():
    """
    Daily task to calculate admin performance.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Get all active admins
    admins = await get_active_admins()
    
    for admin in admins:
        # Calculate metrics for yesterday
        metrics = await calculate_admin_metrics(
            admin_id=admin.id,
            start_date=yesterday,
            end_date=today
        )
        
        # Calculate points
        points = calculate_admin_points(metrics)
        
        # Update leaderboard
        await upsert_admin_leaderboard(
            admin_id=admin.id,
            period_type="daily",
            period_start=yesterday,
            period_end=today,
            **metrics,
            points=points
        )

def calculate_admin_points(metrics: dict) -> int:
    """
    Calculate gamification points for admin performance.
    """
    points = 0
    
    # Tasks completed
    points += metrics["tasks_completed"] * 10
    
    # Quality score
    if metrics["average_quality_score"]:
        points += int(metrics["average_quality_score"] * 50)
    
    # Ticket resolution
    points += metrics["tickets_resolved"] * 15
    
    # Fast response time (bonus)
    if metrics["average_ticket_response_time_minutes"] < 30:
        points += 20  # Bonus for fast response
    
    # Documents processed
    points += metrics["documents_processed"] * 5
    
    # Chunks approved
    points += metrics["chunks_approved"] * 3
    
    # Penalties for rejected chunks
    points -= metrics["chunks_rejected"] * 2
    
    return max(0, points)  # Ensure non-negative
```

### User Feedback Quality Leaderboard

```python
@app.get("/leaderboard/users")
async def get_user_leaderboard(
    period: str = "monthly",
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get user feedback quality leaderboard.
    Only shows users who opted in to public display.
    """
    period_start, period_end = get_period_range(period)
    
    # Get leaderboard (only public)
    leaderboard = await get_user_leaderboard_data(
        period_type=period,
        period_start=period_start,
        period_end=period_end,
        public_only=True
    )
    
    # Anonymize if user is not viewing their own position
    for entry in leaderboard:
        if not current_user or entry["user_id"] != current_user.id:
            entry["user_name"] = anonymize_name(entry["user_name"])
    
    return {
        "period": period,
        "leaderboard": leaderboard,
        "your_position": get_user_position(current_user.id, leaderboard) if current_user else None
    }

@celery_app.task
async def evaluate_user_feedback_quality():
    """
    Periodic task to evaluate quality of user feedback.
    Uses LLM as judge (sparingly to control costs).
    """
    # Get recent feedbacks that haven't been evaluated
    feedbacks = await get_unevaluated_feedbacks(limit=100)
    
    for feedback in feedbacks:
        # Skip empty feedbacks
        if not feedback.feedback_text:
            continue
        
        # Evaluate with LLM (cheap model)
        evaluation_prompt = f"""
You are evaluating the quality of user feedback for an AI chatbot.

Feedback: {feedback.feedback_text}

Rate the feedback on:
1. Specificity (0-1): How specific is the feedback?
2. Usefulness (0-1): How useful for improving the system?
3. Constructiveness (0-1): Is it constructive or just complaining?

Respond with JSON:
{{"specificity": 0.0-1.0, "usefulness": 0.0-1.0, "constructiveness": 0.0-1.0}}
"""
        
        llm = get_llm(tier=3)  # Cheap model
        evaluation = llm.invoke(evaluation_prompt)
        
        try:
            scores = json.loads(evaluation.content)
            overall_quality = (
                scores["specificity"] + 
                scores["usefulness"] + 
                scores["constructiveness"]
            ) / 3
            
            # Update feedback record
            await update_feedback_quality_score(
                feedback.id,
                quality_score=overall_quality
            )
            
        except Exception as e:
            logger.error(f"Failed to evaluate feedback: {e}")
```

---

## REJAL & HADITH CHAIN VALIDATION

### Hadith Chain Visualization

```python
@app.get("/hadith/{hadith_id}/chain")
async def get_hadith_chain_visualization(hadith_id: str):
    """
    Get hadith narration chain with visualization data.
    """
    # Get chain from database
    chain = await get_hadith_chain(hadith_id)
    
    if not chain:
        raise HTTPException(404, "Hadith chain not found")
    
    # Get narrators in order
    narrators = await get_chain_narrators(chain.id)
    
    # Build graph data for frontend visualization
    nodes = []
    edges = []
    
    for idx, narrator in enumerate(narrators):
        person = await get_rejal_person(narrator.person_id)
        
        # Add node
        nodes.append({
            "id": person.id,
            "label": person.name_arabic,
            "reliability": person.reliability_rating,
            "reliability_score": float(person.reliability_score),
            "birth_year": person.birth_year,
            "death_year": person.death_year,
            "position": narrator.position
        })
        
        # Add edge to next narrator
        if idx < len(narrators) - 1:
            next_narrator = narrators[idx + 1]
            edges.append({
                "from": person.id,
                "to": next_narrator.person_id,
                "label": narrator.transmission_method,
                "color": get_reliability_color(person.reliability_score)
            })
    
    return {
        "hadith_text": chain.hadith_text,
        "source_book": chain.source_book,
        "overall_reliability": chain.overall_reliability,
        "reliability_score": float(chain.reliability_score),
        "chain_type": chain.chain_type,
        "visualization": {
            "nodes": nodes,
            "edges": edges
        }
    }

def get_reliability_color(score: float) -> str:
    """Get color based on reliability score"""
    if score >= 0.8:
        return "#4CAF50"  # Green - Reliable
    elif score >= 0.6:
        return "#FFC107"  # Yellow - Acceptable
    elif score >= 0.4:
        return "#FF9800"  # Orange - Weak
    else:
        return "#F44336"  # Red - Very weak
```

### Chain Reliability Calculation

```python
async def calculate_chain_reliability(chain_id: str) -> float:
    """
    Calculate overall reliability of a hadith chain.
    Based on individual narrator reliability scores.
    """
    narrators = await get_chain_narrators(chain_id)
    
    if not narrators:
        return 0.0
    
    # Get reliability scores
    scores = []
    for narrator in narrators:
        person = await get_rejal_person(narrator.person_id)
        scores.append(person.reliability_score)
    
    # Chain is only as strong as its weakest link
    # But also consider average
    min_score = min(scores)
    avg_score = sum(scores) / len(scores)
    
    # Weighted: 70% weakest link, 30% average
    overall_score = (min_score * 0.7) + (avg_score * 0.3)
    
    return overall_score

async def classify_chain_overall_reliability(score: float) -> str:
    """Classify chain based on score"""
    if score >= 0.8:
        return "sahih"  # Authentic
    elif score >= 0.6:
        return "hasan"  # Good
    elif score >= 0.4:
        return "da`if"  # Weak
    else:
        return "mawdu`"  # Fabricated/Very weak
```

---

## BACKUP & RECOVERY (HUGGINGFACE)

### Automated Backup System

```python
from huggingface_hub import HfApi, create_repo

class HuggingFaceBackupManager:
    """Manages backups to private HuggingFace repository"""
    
    def __init__(self):
        self.api = HfApi(token=os.getenv("HF_TOKEN"))
        self.repo_id = os.getenv("HF_BACKUP_REPO")  # e.g., "org/shia-rag-backups"
        
        # Ensure repo exists (create if not)
        try:
            self.api.repo_info(repo_id=self.repo_id, repo_type="dataset")
        except:
            create_repo(
                repo_id=self.repo_id,
                repo_type="dataset",
                private=True
            )
    
    async def backup_embeddings(self):
        """Backup embeddings and vector DB"""
        backup_id = f"embeddings_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Export embeddings from Qdrant
        embeddings_data = await export_qdrant_collections()
        
        # Save to temp file
        temp_file = f"/tmp/{backup_id}.parquet"
        embeddings_data.to_parquet(temp_file)
        
        # Upload to HuggingFace
        self.api.upload_file(
            path_or_fileobj=temp_file,
            path_in_repo=f"embeddings/{backup_id}.parquet",
            repo_id=self.repo_id,
            repo_type="dataset"
        )
        
        # Log backup
        await log_backup(
            backup_type="embeddings_only",
            destination="huggingface",
            hf_repository=self.repo_id,
            status="completed",
            total_size_mb=os.path.getsize(temp_file) / (1024 * 1024)
        )
        
        # Cleanup
        os.remove(temp_file)
    
    async def backup_documents(self):
        """Backup document and chunk tables"""
        backup_id = f"documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Export documents from PostgreSQL
        documents = await export_documents_table()
        chunks = await export_chunks_table()
        
        # Save to parquet
        doc_file = f"/tmp/{backup_id}_documents.parquet"
        chunk_file = f"/tmp/{backup_id}_chunks.parquet"
        
        documents.to_parquet(doc_file)
        chunks.to_parquet(chunk_file)
        
        # Upload to HuggingFace
        self.api.upload_file(
            path_or_fileobj=doc_file,
            path_in_repo=f"documents/{backup_id}_documents.parquet",
            repo_id=self.repo_id,
            repo_type="dataset"
        )
        
        self.api.upload_file(
            path_or_fileobj=chunk_file,
            path_in_repo=f"documents/{backup_id}_chunks.parquet",
            repo_id=self.repo_id,
            repo_type="dataset"
        )
        
        # Cleanup
        os.remove(doc_file)
        os.remove(chunk_file)
    
    async def backup_full(self):
        """Full backup of all critical data"""
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        tables_to_backup = [
            "documents",
            "document_chunks",
            "document_embeddings",
            "rejal_persons",
            "hadith_chains",
            "chain_narrators",
            "users",  # Anonymized
            "conversations",  # Optional
            "support_tickets"
        ]
        
        for table in tables_to_backup:
            data = await export_table(table)
            
            # Anonymize sensitive data
            if table in ["users", "conversations"]:
                data = anonymize_data(data)
            
            # Save and upload
            file_path = f"/tmp/{backup_id}_{table}.parquet"
            data.to_parquet(file_path)
            
            self.api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=f"full_backups/{backup_id}/{table}.parquet",
                repo_id=self.repo_id,
                repo_type="dataset"
            )
            
            os.remove(file_path)

# Scheduled backup tasks
@celery_app.task
async def daily_backup_embeddings():
    """Daily backup of embeddings"""
    backup_manager = HuggingFaceBackupManager()
    await backup_manager.backup_embeddings()

@celery_app.task
async def weekly_backup_full():
    """Weekly full backup"""
    backup_manager = HuggingFaceBackupManager()
    await backup_manager.backup_full()
```

---

## ENVIRONMENT & DEPLOYMENT

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.9'

services:
  # FastAPI Application
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - QDRANT_URL=${QDRANT_URL}
      - ENVIRONMENT=${ENVIRONMENT:-dev}
    depends_on:
      - postgres
      - redis
      - qdrant
    volumes:
      - ./app:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - shia_rag_network
  
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=shia_rag
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - shia_rag_network
  
  # Redis Cache & Queue
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - shia_rag_network
  
  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    networks:
      - shia_rag_network
  
  # Celery Worker (Background Tasks)
  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - postgres
    volumes:
      - ./app:/app
    networks:
      - shia_rag_network
  
  # Celery Beat (Scheduled Tasks)
  celery_beat:
    build: .
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    volumes:
      - ./app:/app
    networks:
      - shia_rag_network
  
  # Langfuse (Observability) - Optional
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=${LANGFUSE_DATABASE_URL}
      - NEXTAUTH_SECRET=${LANGFUSE_SECRET}
      - NEXTAUTH_URL=http://localhost:3000
    depends_on:
      - postgres
    networks:
      - shia_rag_network
  
  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - shia_rag_network

volumes:
  postgres_data:
  redis_data:
  qdrant_data:

networks:
  shia_rag_network:
    driver: bridge
```

### Secrets Management (Docker Secrets)

```yaml
# docker-compose.prod.yml (extends docker-compose.yml)
version: '3.9'

services:
  app:
    secrets:
      - database_url
      - openai_api_key
      - anthropic_api_key
      - google_api_key
      - jwt_secret
    environment:
      - DATABASE_URL_FILE=/run/secrets/database_url
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key

secrets:
  database_url:
    external: true
  openai_api_key:
    external: true
  anthropic_api_key:
    external: true
  google_api_key:
    external: true
  jwt_secret:
    external: true
```

### Environment Separation (Two Strategies)

```python
# Strategy 1: Single Infrastructure with Logical Separation
class EnvironmentConfig:
    """Configuration for single-infrastructure setup"""
    
    @staticmethod
    def get_db_schema(environment: str) -> str:
        """Use different schemas for different environments"""
        return f"shia_rag_{environment}"  # dev, test, prod
    
    @staticmethod
    def get_redis_prefix(environment: str) -> str:
        """Use different key prefixes"""
        return f"{environment}:"
    
    @staticmethod
    def get_qdrant_collection_prefix(environment: str) -> str:
        """Use different collection names"""
        return f"{environment}_"

# Strategy 2: Separate Infrastructures
# docker-compose.dev.yml, docker-compose.test.yml, docker-compose.prod.yml
# Each with separate database instances, Redis, Qdrant
```

---

## TESTING STRATEGY

### Test Structure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

@pytest.fixture
def client():
    """Test client for API"""
    return TestClient(app)

@pytest.fixture
async def test_db():
    """Test database"""
    # Create test database
    await create_test_database()
    yield
    # Cleanup
    await drop_test_database()

@pytest.fixture
async def test_user(test_db):
    """Create test user"""
    user = await create_user(
        email="test@example.com",
        password="testpass123"
    )
    return user

@pytest.fixture
async def test_admin(test_db):
    """Create test admin"""
    user = await create_user(
        email="admin@example.com",
        password="adminpass123"
    )
    admin = await create_admin(
        user_id=user.id,
        role="super_admin",
        permissions=["*"]
    )
    return admin

# Unit Tests
# tests/test_llm_selection.py
def test_llm_tier_selection():
    """Test that correct LLM tier is selected based on intent"""
    assert select_llm_tier("GREETING") == 3
    assert select_llm_tier("SIMPLE_QA") == 2
    assert select_llm_tier("MULTI_HOP") == 1

# Integration Tests
# tests/test_rag_pipeline.py
@pytest.mark.asyncio
async def test_complete_rag_pipeline(test_db):
    """Test complete RAG pipeline"""
    # Create test document
    doc = await create_test_document()
    
    # Process document
    await process_document(doc.id)
    
    # Verify chunks created
    chunks = await get_chunks(doc.id)
    assert len(chunks) > 0
    
    # Verify embeddings created
    embeddings = await get_embeddings_for_document(doc.id)
    assert len(embeddings) > 0
    
    # Test retrieval
    results = await retrieve(
        query="test query",
        top_k=5
    )
    assert len(results) > 0

# End-to-End Tests
# tests/test_e2e_chat.py
@pytest.mark.asyncio
async def test_anonymous_user_chat(client):
    """Test anonymous user can chat"""
    response = client.post(
        "/api/chat",
        json={
            "query": "السلام علیکم",
            "mode": "standard"
        }
    )
    
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "citations" in response.json()
```

---

## SECURITY & COMPLIANCE

### Input Validation

```python
from pydantic import BaseModel, validator, EmailStr

class QueryRequest(BaseModel):
    query: str
    mode: str = "standard"
    conversation_id: Optional[str] = None
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) > 5000:
            raise ValueError("Query too long")
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    @validator('mode')
    def validate_mode(cls, v):
        allowed_modes = ["standard", "fast", "scholarly", "deep_search", "filtered"]
        if v not in allowed_modes:
            raise ValueError(f"Invalid mode. Allowed: {allowed_modes}")
        return v
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/chat")
@limiter.limit("10/minute")  # Anonymous users
async def chat_endpoint(
    request: Request,
    query: QueryRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # If authenticated, use user-specific limits
    if current_user:
        await check_user_rate_limit(current_user)
    
    # Process chat
    ...
```

---

## PRE-DEPLOYMENT CHECKLIST

### Automated Checks (Run before deployment)

```bash
#!/bin/bash
# scripts/pre_deploy_check.sh

echo "🔍 Starting pre-deployment checks..."

# 1. Environment validation
echo "Checking environment variables..."
python scripts/validate_env.py || exit 1

# 2. Secret validation
echo "Checking secrets..."
python scripts/validate_secrets.py || exit 1

# 3. Database migration check
echo "Checking database migrations..."
alembic check || exit 1

# 4. Run tests
echo "Running test suite..."
pytest tests/ --cov=app --cov-report=term || exit 1

# 5. Security scan
echo "Running security scan..."
safety check || exit 1

# 6. Linting
echo "Running linters..."
ruff check . || exit 1

# 7. Type checking
echo "Running type checker..."
mypy app/ || exit 1

# 8. Docker build test
echo "Testing Docker build..."
docker-compose -f docker-compose.test.yml build || exit 1

# 9. Integration test on test environment
echo "Running integration tests on test environment..."
pytest tests/integration/ --env=test || exit 1

echo "✅ All pre-deployment checks passed!"
```

### Manual Checklist

```markdown
## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage > 80%
- [ ] No linting errors
- [ ] Type checking passed
- [ ] Security vulnerabilities checked

### Database
- [ ] Migrations tested (forward and backward)
- [ ] Backup created
- [ ] Rollback plan documented

### Configuration
- [ ] Environment variables set
- [ ] Secrets rotated
- [ ] Feature flags configured

### Monitoring
- [ ] Alerts configured
- [ ] Dashboards created
- [ ] Logging verified

### Documentation
- [ ] API docs updated
- [ ] README updated
- [ ] CHANGELOG updated

### Communication
- [ ] Stakeholders notified
- [ ] Support team briefed
- [ ] Rollback plan communicated
```

---

## CONCLUSION

This comprehensive implementation plan provides a complete blueprint for building a production-grade Shia Islamic RAG chatbot. The system is designed to be:

1. **Scalable**: Handle growing user base
2. **Flexible**: Easy to modify and extend
3. **Cost-Effective**: Optimized for low operational costs
4. **Reliable**: High uptime and accuracy
5. **Secure**: Enterprise-grade security
6. **Observable**: Complete monitoring and tracing

**Ready for implementation!** 🚀

---


## 🎯 How to Use This Plan

### Implement this complete system following all specifications

## 📚 Key Technologies (Latest Versions)

All tools and versions have been verified as of October 2025:

- **LangGraph**: 0.6.5+ (with node caching, deferred nodes)
- **LangChain**: 0.3.0+ (v1.0 alpha available)
- **NeMo Guardrails**: 0.10.0+ (LLM-based, no GPU)
- **mem0**: 0.1.0+ (intelligent memory compression)
- **Qdrant**: Latest (with binary quantization for 40x speed)
- **PostgreSQL**: 15+
- **Redis**: 7.2+
- **FastAPI**: 0.115.0+
- **Python**: 3.11+

### CONSIDER BEFORE WRITE ANY SECTION WHICH RELATED TO A TOOL OR THECHNOLOGIE USE FROM YOUR THE `WEB SEARCH TOOL` TO BE SURE ABOUT THE YOUR WORDS ARE BE EXACTLY COMPATIBLE WITH LATEAST VERSION OF THE THOOSE TOOLS DOCUMENTATION.

## 🔐 Security Highlights

- NeMo Guardrails for input/output safety
- Docker secrets for credential management
- JWT authentication
- Rate limiting (multi-tier)
- Input validation with Pydantic
- Audit logging for all actions
- GDPR/CCPA compliant

## 🤝 Acknowledgments

This plan incorporates:
- Latest LangGraph features (node caching, deferred nodes)
- mem0 best practices for memory management
- NeMo Guardrails for safety
- Shia Islamic scholarship requirements
- Production deployment best practices
- Modern DevOps patterns