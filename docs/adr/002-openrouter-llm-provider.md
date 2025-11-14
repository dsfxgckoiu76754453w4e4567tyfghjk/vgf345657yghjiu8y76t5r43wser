# ADR-002: OpenRouter as Primary LLM Provider

**Status**: Accepted
**Date**: 2025-01-13
**Impact**: High

---

## Problem
Need a flexible, cost-effective way to access multiple LLM providers (OpenAI, Anthropic, Google, etc.) without managing individual API integrations and avoiding vendor lock-in.

---

## Decision
Use OpenRouter as the primary LLM provider with unified API access to 100+ models from multiple providers.

**Configuration:**
- Primary provider: OpenRouter
- Fallback routing enabled
- Model: `anthropic/claude-3.5-sonnet` (default)
- Web search: Integrated via OpenRouter plugin

---

## Why
- **Unified API**: Single integration for 100+ models (OpenAI, Anthropic, Google, etc.)
- **Cost Optimization**: Automatic routing to cheapest/fastest models
- **No Vendor Lock-in**: Easy to switch models without code changes
- **Built-in Features**: Prompt caching, web search, structured outputs
- **Usage Tracking**: Centralized billing and usage analytics
- **Fallback Support**: Auto-fallback if primary model is down
- **Developer Experience**: Standard OpenAI-compatible API

---

## Alternatives Rejected
- **Direct Provider APIs**: Multiple integrations, higher complexity, vendor lock-in
- **LiteLLM**: Similar but less mature, smaller model selection
- **LangChain Hub**: Focused on chains, not provider abstraction
- **Build Custom Proxy**: High maintenance, reinventing the wheel

---

## Impact

**Changed Components:**
- `src/app/services/openrouter_service.py` - Primary LLM service
- `src/app/services/langgraph_service.py` - Uses OpenRouter
- `src/app/core/config.py` - OpenRouter configuration
- `.env.example` - OpenRouter API key and settings

**Dependencies Added:**
- `openai` library (OpenRouter uses OpenAI-compatible API)
- LangChain OpenAI integration

**Removed:**
- Tavily web search (replaced by OpenRouter web search)

**Breaking Changes:** No (backward compatible config)

**Migration Required:** No (optional)

---

## Notes
- **Prompt Caching**: 50-90% cost savings on repeated context
- **Web Search Models**: Perplexity Sonar for real-time search
- **Model Routing**: Can use `openrouter/auto` for automatic model selection
- **Monitoring**: Usage tracked via OpenRouter dashboard
- **Fallback Models**: Configure in `DEFAULT_FALLBACK_MODELS` env var
- **Sign Up**: https://openrouter.ai (free tier available)
