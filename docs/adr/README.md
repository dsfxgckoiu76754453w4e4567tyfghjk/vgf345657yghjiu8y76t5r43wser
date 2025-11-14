# Architecture Decision Records (ADR)

Track important architectural decisions in this project.

## Quick Start

1. Copy `TEMPLATE.md`
2. Name it: `XXX-short-title.md` (e.g., `003-temporal-migration.md`)
3. Fill in sections
4. Commit with PR

## Naming Convention
```
XXX-short-descriptive-title.md
001-initial-framework.md
002-database-choice.md
003-temporal-migration.md
```

## Status Values
- **Accepted**: Active decision
- **Deprecated**: No longer valid
- **Superseded**: Replaced by ADR-XXX

## Keep It Simple
- Be concise (< 1 page)
- Focus on "what" and "why", not "how"
- Update when decisions change
- Link related ADRs

## Index
| # | Title | Status | Date |
|---|-------|--------|------|
| [001](001-initial-architecture.md) | Initial Architecture Setup | Accepted | 2025-01-13 |
| [002](002-openrouter-llm-provider.md) | OpenRouter as Primary LLM Provider | Accepted | 2025-01-13 |
| [003](003-temporal-workflow-engine.md) | Temporal Replaces Celery | Accepted | 2025-01-14 |
| [004](004-uv-package-manager.md) | Migrate to uv Package Manager | Accepted | 2025-01-14 |
| [005](005-gemini-asr-integration.md) | Gemini Audio for ASR Transcription | Accepted | 2025-01-14 |
