# ADR-001: Initial Architecture Setup

**Status**: Accepted
**Date**: 2025-01-13
**Impact**: Critical

---

## Problem
Need to establish the foundational technology stack and architecture patterns for a production-grade Islamic knowledge chatbot with RAG capabilities.

---

## Decision
Adopt a modern Python microservice architecture with:
- **Framework**: FastAPI (async, high performance, auto-docs)
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **Vector DB**: Qdrant for semantic search
- **Cache**: Redis for sessions and caching
- **Storage**: MinIO (S3-compatible) for files and media
- **Architecture**: Clean layered architecture (API → Service → Repository → Model)

---

## Why
- **FastAPI**: Type-safe, async, automatic API docs, production-ready
- **PostgreSQL**: Reliable, ACID compliant, great JSON support
- **Qdrant**: Pure vector DB with metadata filtering, self-hosted
- **Redis**: Industry standard for caching, battle-tested
- **MinIO**: S3-compatible, self-hosted, no vendor lock-in
- **Clean Architecture**: Testability, maintainability, clear separation of concerns

---

## Alternatives Rejected
- **Django**: Heavier framework, less async support
- **Pinecone/Weaviate**: Vendor lock-in, hosted-only options
- **MongoDB**: Less ACID guarantees, SQL better for relational data
- **AWS S3**: Vendor lock-in, higher costs, development complexity

---

## Impact

**Changed Components:**
- Project structure established
- Docker compose infrastructure
- Base dependencies in pyproject.toml

**Breaking Changes:** No (initial setup)

**Migration Required:** No

---

## Notes
- Multi-environment isolation (dev, stage, prod) built from day one
- 4-tier architecture: API → Service → Repository → Model
- See TECH_STACK.md for complete technology list
