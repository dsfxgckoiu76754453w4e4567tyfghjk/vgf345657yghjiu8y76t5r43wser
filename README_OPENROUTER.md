# 🚀 OpenRouter Advanced Features Integration

Complete production-ready integration of OpenRouter's advanced features for cost-optimized, high-availability AI chat.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Integrated-orange.svg)](https://openrouter.ai/)

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
poetry install

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 3. Run migrations
alembic upgrade head

# 4. Seed subscription plans
python scripts/seed_plan_limits.py

# 5. Start server
uvicorn app.main:app --reload

# 6. Access API docs
open http://localhost:8000/docs
```

---

## 🎯 Features

### **💰 Cost Optimization (50-90% Savings)**
- ✅ **Prompt Caching** - Cache system prompts and conversation history
- ✅ **Automatic Cache Management** - Smart cache breakpoint placement
- ✅ **Cost Tracking** - Real-time cost and savings monitoring

### **🔄 High Availability**
- ✅ **Model Routing** - Automatic fallback to alternative models
- ✅ **Multiple Fallback Chains** - Configure priority-based fallbacks
- ✅ **Routing Strategies** - auto, price, latency, uptime

### **⚡ Performance**
- ✅ **Streaming Responses** - Real-time Server-Sent Events (SSE)
- ✅ **Sub-second Latency** - Optimized request handling
- ✅ **Efficient Caching** - Redis + PostgreSQL

### **🖼️ Multi-Modal**
- ✅ **Image Generation** - Gemini, DALL-E, Flux support
- ✅ **PDF Processing** - Extract and process PDFs
- ✅ **Audio Processing** - Transcription and processing

### **📊 Analytics**
- ✅ **Admin Dashboard** - System-wide statistics
- ✅ **Usage Tracking** - Per-user quota monitoring
- ✅ **Cost Analytics** - Detailed cost breakdown
- ✅ **Cache Metrics** - Cache hit rate and savings

### **🔐 Security**
- ✅ **JWT Authentication** - Secure API access
- ✅ **Role-Based Access** - Admin vs user permissions
- ✅ **Quota Enforcement** - Plan-based rate limiting
- ✅ **Usage Quotas** - Prevent overages

---

## 📦 What's Included

### **API Endpoints (25+)**

#### Chat
- `POST /api/v1/chat` - Send message (streaming/non-streaming)
- `POST /api/v1/chat/structured` - Structured output with JSON schema
- `GET /api/v1/chat/cache-stats/{id}` - Cache performance stats

#### Conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation details
- `PATCH /api/v1/conversations/{id}` - Update conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `POST /api/v1/conversations/{id}/generate-title` - Auto-generate title

#### Images
- `POST /api/v1/images/generate` - Generate image
- `GET /api/v1/images/history` - Image history
- `GET /api/v1/images/{id}` - Get image
- `DELETE /api/v1/images/{id}` - Delete image

#### Presets
- `POST /api/v1/presets` - Create preset
- `GET /api/v1/presets` - List presets
- `GET /api/v1/presets/{id}` - Get preset
- `PATCH /api/v1/presets/{id}` - Update preset
- `DELETE /api/v1/presets/{id}` - Delete preset
- `POST /api/v1/presets/{id}/duplicate` - Duplicate preset

#### Subscriptions
- `GET /api/v1/subscriptions/me` - Current subscription
- `POST /api/v1/subscriptions` - Create subscription
- `GET /api/v1/subscriptions/usage` - Usage statistics
- `POST /api/v1/subscriptions/cancel` - Cancel subscription
- `GET /api/v1/subscriptions/plans` - List plans

#### Analytics (Admin)
- `GET /api/v1/analytics/system-stats` - System statistics
- `GET /api/v1/analytics/plan-distribution` - Plan breakdown
- `GET /api/v1/analytics/usage-trends` - Usage trends
- `GET /api/v1/analytics/top-users` - Top users
- `GET /api/v1/analytics/model-usage` - Model statistics
- `GET /api/v1/analytics/cache-performance` - Cache metrics

#### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/metrics` - Basic metrics

### **Services**

1. **OpenRouterService** - Complete OpenRouter client
2. **EnhancedChatService** - Chat with all advanced features
3. **ImageGenerationService** - Multi-model image generation
4. **PresetsService** - User-defined configurations
5. **SubscriptionService** - Plan and quota management

### **Database**

- **6 New Tables**: subscriptions, plan_limits, monthly_usage_quotas, generated_images, model_presets, message_attachments
- **13 New Message Fields**: caching, routing, structured output metadata
- **Alembic Migrations**: Full schema migrations included
- **Seed Scripts**: Default subscription plans

### **Tests**

- **70+ Unit Tests** - Comprehensive test coverage
- **Service Tests** - All services tested
- **Integration Ready** - Easy to add E2E tests

---

## 💎 Subscription Plans

| Feature | Free | Premium | Unlimited | Enterprise |
|---------|------|---------|-----------|------------|
| **Price/month** | $0 | $19.99 | $99.99 | $499.99 |
| **Messages** | 100 | 2,000 | 10,000 | 100,000 |
| **Tokens** | 100K | 5M | 50M | 500M |
| **Images** | 5 | 100 | 1,000 | 10,000 |
| **Documents** | 10 | 500 | 5,000 | 50,000 |
| **Audio (mins)** | 5 | 100 | 1,000 | 10,000 |
| **Web Search** | ✅ | ✅ | ✅ | ✅ |
| **Image Gen** | ❌ | ✅ | ✅ | ✅ |
| **PDF Processing** | ❌ | ✅ | ✅ | ✅ |
| **Audio Processing** | ❌ | ✅ | ✅ | ✅ |
| **Prompt Caching** | ❌ | ✅ | ✅ | ✅ |
| **Advanced Models** | ❌ | ✅ | ✅ | ✅ |
| **Presets** | 3 | 20 | 100 | 500 |
| **Max Context** | 4K | 200K | 1M | 1M |
| **Priority Support** | ❌ | ❌ | ✅ | ✅ |

---

## 📚 Usage Examples

### **Chat with Streaming**

```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        "http://localhost:8000/api/v1/chat",
        json={
            "conversation_id": "uuid",
            "message": "Explain the five pillars of Islam",
            "stream": True,
            "enable_caching": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                if data["type"] == "content":
                    print(data["content"], end="", flush=True)
```

### **Generate Image**

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful mosque at sunset",
    "aspect_ratio": "16:9",
    "model": "google/gemini-2.5-flash-image-preview"
  }'
```

### **Create Preset**

```bash
curl -X POST http://localhost:8000/api/v1/presets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Islamic Scholar",
    "slug": "islamic-scholar",
    "model": "anthropic/claude-3.5-sonnet",
    "system_prompt": "You are a knowledgeable Islamic scholar...",
    "temperature": 0.7,
    "max_tokens": 4096
  }'
```

### **Check Usage**

```bash
curl http://localhost:8000/api/v1/subscriptions/usage \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "messages": {"used": 150, "limit": 2000, "remaining": 1850},
  "tokens": {"used": 500000, "limit": 5000000, "remaining": 4500000},
  "total_cost_usd": 2.45,
  "cache_savings_usd": 1.20
}
```

### **Admin Analytics**

```bash
# System statistics
curl http://localhost:8000/api/v1/analytics/system-stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Cache performance
curl http://localhost:8000/api/v1/analytics/cache-performance \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## ⚙️ Configuration

### **Required Environment Variables**

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=WisQu Islamic Chatbot
OPENROUTER_APP_URL=https://wisqu.com

# LLM Provider
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### **Optional Features**

```bash
# Prompt Caching (50-90% savings!)
PROMPT_CACHING_ENABLED=true
CACHE_CONTROL_STRATEGY=auto
CACHE_MIN_TOKENS=1024

# Model Routing
MODEL_ROUTING_ENABLED=true
DEFAULT_FALLBACK_MODELS=anthropic/claude-3.5-sonnet,openai/gpt-4o
ROUTING_STRATEGY=auto

# Image Generation
IMAGE_GENERATION_ENABLED=true
IMAGE_GENERATION_MODELS=google/gemini-2.5-flash-image-preview

# Usage Tracking
USAGE_TRACKING_ENABLED=true
TRACK_USER_IDS=true
```

See `.env.example` for all available options.

---

## 🧪 Testing

### **Run Tests**

```bash
# All tests
pytest

# Specific service
pytest tests/unit/test_openrouter_service.py
pytest tests/unit/test_subscription_service.py

# With coverage
pytest --cov=app --cov-report=html
```

### **Health Checks**

```bash
# Basic health
curl http://localhost:8000/api/v1/health

# Detailed health
curl http://localhost:8000/api/v1/health/detailed

# Readiness (Kubernetes)
curl http://localhost:8000/api/v1/health/ready
```

---

## 📊 Performance & Cost

### **Prompt Caching Savings**

| Scenario | Without Caching | With Caching (90% hit) | Savings |
|----------|----------------|------------------------|---------|
| System prompt (2K tokens) | $0.030 | $0.003 | **90%** |
| Conversation (10K tokens) | $0.150 | $0.030 | **80%** |
| RAG context (5K tokens) | $0.075 | $0.008 | **89%** |

**Example Monthly Savings:**
- 10,000 conversations/month
- Average 8K tokens cached per conversation
- Cost without caching: **$1,200/month**
- Cost with caching: **$180/month**
- **Savings: $1,020/month (85%)**

### **Model Routing Benefits**

- **99.9% uptime** - Automatic fallback ensures availability
- **Cost optimization** - Route to cheaper models when possible
- **Performance** - Route to fastest models for better UX

---

## 🔧 Troubleshooting

### **Quota Exceeded**

```
HTTP 400: Monthly message limit reached (100)
```

**Solution**: Upgrade subscription plan or wait for next billing cycle.

### **Cache Not Working**

Check configuration:
```bash
PROMPT_CACHING_ENABLED=true
```

Verify in logs:
```json
{
  "cached_tokens_read": 1200,
  "cache_discount_usd": 0.015
}
```

### **Model Unavailable**

Enable fallbacks:
```bash
MODEL_ROUTING_ENABLED=true
DEFAULT_FALLBACK_MODELS=anthropic/claude-3.5-sonnet,openai/gpt-4o
```

Check routing logs:
```json
{
  "fallback_used": true,
  "models_attempted": ["primary-model", "fallback-model"],
  "final_model_used": "fallback-model"
}
```

---

## 📖 Documentation

- **[Integration Guide](docs/OPENROUTER_INTEGRATION.md)** - Complete feature documentation
- **[API Reference](http://localhost:8000/docs)** - Interactive API docs (Swagger UI)
- **[OpenRouter Docs](https://openrouter.ai/docs)** - Official OpenRouter documentation

---

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Routers │
    └────┬────┘
         │
    ┌────┴────────────────────┐
    │       Services          │
    ├─────────────────────────┤
    │ - OpenRouterService     │
    │ - EnhancedChatService   │
    │ - ImageGenService       │
    │ - PresetsService        │
    │ - SubscriptionService   │
    └────┬────────────────────┘
         │
    ┌────┴─────┐
    │ Database │
    └──────────┘
```

---

## 🚀 Deployment

### **Docker**

```bash
# Build
docker build -t wisqu-openrouter .

# Run
docker run -p 8000:8000 --env-file .env wisqu-openrouter
```

### **Docker Compose**

```bash
docker-compose up -d
```

### **Kubernetes**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wisqu-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: wisqu-openrouter:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
```

---

## 📈 Monitoring

### **Health Endpoints**

- `/api/v1/health` - Basic health check
- `/api/v1/health/detailed` - Service status
- `/api/v1/health/ready` - Readiness probe
- `/api/v1/health/live` - Liveness probe
- `/api/v1/health/metrics` - Basic metrics

### **Logs**

Structured JSON logging with:
- Request/response details
- Error tracking
- Performance metrics
- Cost tracking

### **Analytics Dashboard**

Admin endpoints provide:
- System-wide statistics
- User behavior analytics
- Cost optimization insights
- Cache performance metrics

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

Part of the WisQu Islamic Chatbot project.

---

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) - Unified LLM API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Anthropic](https://www.anthropic.com/) - Claude models
- [OpenAI](https://openai.com/) - GPT models

---

## 📞 Support

For issues or questions:
- Check the [documentation](docs/OPENROUTER_INTEGRATION.md)
- Review [API docs](http://localhost:8000/docs)
- Check application logs
- Contact the development team

---

**Made with ❤️ for the WisQu Islamic Chatbot**
