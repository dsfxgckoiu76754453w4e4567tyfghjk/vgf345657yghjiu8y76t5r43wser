# OpenRouter Advanced Features Integration

Complete integration of OpenRouter's advanced features including prompt caching, model routing, image generation, subscriptions, and analytics.

## 🎯 Overview

This implementation adds production-ready OpenRouter integration with:

- ✅ **Prompt Caching** - 50-90% cost savings
- ✅ **Model Routing & Fallbacks** - High availability
- ✅ **Streaming Responses** - Real-time user experience
- ✅ **Image Generation** - Multi-model support
- ✅ **Subscription Management** - Plan-based quotas
- ✅ **Analytics Dashboard** - Admin insights
- ✅ **Comprehensive API** - 20+ endpoints

---

## 📦 Components

### **Core Services**

#### 1. OpenRouterService (`src/app/services/openrouter_service.py`)
Comprehensive OpenRouter client with all advanced features.

**Features:**
- Prompt caching with automatic breakpoints
- Model routing with fallback arrays
- User tracking for cache stickiness
- Structured outputs with JSON schema
- Multimodal support (images, PDFs, audio)
- Detailed usage accounting

**Usage:**
```python
from app.services.openrouter_service import openrouter_service

result = await openrouter_service.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="anthropic/claude-3.5-sonnet",
    user_id=user_id,
    enable_caching=True,
    fallback_models=["openai/gpt-4o", "openai/gpt-4o-mini"],
)
```

#### 2. EnhancedChatService (`src/app/services/enhanced_chat_service.py`)
Full-featured chat service with conversation history and caching.

**Features:**
- Automatic conversation history loading
- Prompt caching for system prompts
- Streaming support (SSE)
- Quota checking
- Usage tracking
- Message persistence

**Usage:**
```python
from app.services.enhanced_chat_service import enhanced_chat_service

result = await enhanced_chat_service.chat(
    user_id=user_id,
    conversation_id=conversation_id,
    message_content="What is Salah?",
    enable_streaming=True,
)
```

#### 3. ImageGenerationService (`src/app/services/image_generation_service.py`)
Multi-model image generation with quota management.

**Supported Models:**
- Gemini Flash Image (`google/gemini-2.5-flash-image-preview`)
- DALL-E 3 (`openai/dall-e-3`)
- Flux Pro (`black-forest-labs/flux-pro`)
- Flux Schnell (`black-forest-labs/flux-schnell`)

#### 4. PresetsService (`src/app/services/presets_service.py`)
User-defined model configurations and templates.

#### 5. SubscriptionService (`src/app/services/subscription_service.py`)
Plan management, quota tracking, and usage accounting.

---

## 🔌 API Endpoints

### **Chat (`/api/v1/chat`)**

#### `POST /chat`
Send a chat message with optional streaming.

**Request:**
```json
{
  "conversation_id": "uuid",
  "message": "Explain the five pillars of Islam",
  "enable_caching": true,
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "content": "The five pillars...",
  "model": "anthropic/claude-3.5-sonnet",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 500,
    "total_tokens": 650
  },
  "cached_tokens_read": 120,
  "cache_discount_usd": 0.0015,
  "total_cost_usd": 0.0045
}
```

#### `POST /chat/structured`
Chat with JSON schema validation.

**Request:**
```json
{
  "conversation_id": "uuid",
  "message": "Rate this Islamic ruling",
  "response_schema": {
    "type": "object",
    "properties": {
      "rating": {"type": "number", "minimum": 1, "maximum": 5},
      "explanation": {"type": "string"}
    },
    "required": ["rating", "explanation"]
  }
}
```

#### `GET /chat/cache-stats/{conversation_id}`
Get caching statistics for a conversation.

**Response:**
```json
{
  "total_messages": 20,
  "cached_messages": 18,
  "total_cached_tokens": 45000,
  "total_cache_savings_usd": 0.015,
  "cache_hit_rate": 0.9
}
```

### **Conversations (`/api/v1/conversations`)**

#### `POST /conversations`
Create a new conversation.

#### `GET /conversations`
List user's conversations.

#### `GET /conversations/{id}`
Get conversation with all messages.

#### `PATCH /conversations/{id}`
Update conversation title/mode.

#### `DELETE /conversations/{id}`
Delete conversation and messages.

#### `POST /conversations/{id}/generate-title`
Auto-generate conversation title from messages.

### **Images (`/api/v1/images`)**

#### `POST /images/generate`
Generate an image.

**Request:**
```json
{
  "prompt": "A beautiful sunset over the desert",
  "aspect_ratio": "16:9",
  "model": "google/gemini-2.5-flash-image-preview",
  "output_format": "url"
}
```

#### `GET /images/history`
Get user's image generation history.

#### `GET /images/{id}`
Get specific image.

#### `DELETE /images/{id}`
Delete image.

### **Presets (`/api/v1/presets`)**

#### `POST /presets`
Create a model preset.

**Request:**
```json
{
  "name": "Creative Islamic Scholar",
  "slug": "creative-scholar",
  "model": "anthropic/claude-3.5-sonnet",
  "system_prompt": "You are a knowledgeable Islamic scholar...",
  "temperature": 0.9,
  "top_p": 0.95,
  "max_tokens": 4096,
  "is_public": false
}
```

#### `GET /presets`
List user's presets.

#### `POST /presets/{id}/duplicate`
Duplicate a preset.

### **Subscriptions (`/api/v1/subscriptions`)**

#### `GET /subscriptions/me`
Get current subscription.

#### `GET /subscriptions/usage`
Get usage statistics.

**Response:**
```json
{
  "messages": {"used": 150, "limit": 2000, "remaining": 1850},
  "tokens": {"used": 500000, "limit": 5000000, "remaining": 4500000},
  "images": {"used": 12, "limit": 100, "remaining": 88},
  "total_cost_usd": 2.45,
  "cache_savings_usd": 1.20
}
```

#### `GET /subscriptions/plans`
List all available plans.

#### `POST /subscriptions/cancel`
Cancel subscription.

### **Analytics (`/api/v1/analytics`) - Admin Only**

#### `GET /analytics/system-stats`
System-wide statistics.

#### `GET /analytics/plan-distribution`
Plan distribution breakdown.

#### `GET /analytics/usage-trends`
Usage trends over time.

#### `GET /analytics/top-users`
Top users by usage.

#### `GET /analytics/model-usage`
Model usage statistics.

#### `GET /analytics/cache-performance`
Cache performance metrics.

---

## 🗄️ Database Schema

### **New Tables**

#### `message_attachments`
Multimodal attachments (images, PDFs, audio).

#### `subscriptions`
User subscriptions and plan management.

#### `plan_limits`
Plan features and quota limits.

#### `monthly_usage_quotas`
Monthly usage tracking per user.

#### `generated_images`
Image generation history.

#### `model_presets`
User-defined model configurations.

### **Extended Tables**

#### `messages` - 13 new fields:
- `cached_tokens_read`, `cached_tokens_write`
- `cache_discount_usd`, `cache_breakpoint_count`
- `reasoning_tokens`, `audio_tokens`
- `upstream_inference_cost_usd`
- `routing_strategy`, `fallback_used`
- `models_attempted`, `final_model_used`
- `response_schema`, `structured_data`, `schema_validation_passed`

---

## 💰 Subscription Plans

| Plan | Messages/mo | Tokens/mo | Images/mo | Price/mo |
|------|------------|-----------|-----------|----------|
| **Free** | 100 | 100K | 5 | $0 |
| **Premium** | 2K | 5M | 100 | $19.99 |
| **Unlimited** | 10K | 50M | 1K | $99.99 |
| **Enterprise** | 100K | 500M | 10K | $499.99 |

**Features by Plan:**

| Feature | Free | Premium | Unlimited | Enterprise |
|---------|------|---------|-----------|------------|
| Web Search | ✅ | ✅ | ✅ | ✅ |
| Image Generation | ❌ | ✅ | ✅ | ✅ |
| PDF Processing | ❌ | ✅ | ✅ | ✅ |
| Audio Processing | ❌ | ✅ | ✅ | ✅ |
| Prompt Caching | ❌ | ✅ | ✅ | ✅ |
| Advanced Models | ❌ | ✅ | ✅ | ✅ |
| Presets | 3 | 20 | 100 | 500 |
| Max Context | 4K | 200K | 1M | 1M |
| Priority Support | ❌ | ❌ | ✅ | ✅ |

---

## ⚙️ Configuration

### **Environment Variables**

Add to `.env`:

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=WisQu Islamic Chatbot
OPENROUTER_APP_URL=https://wisqu.com

# LLM Configuration
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Prompt Caching
PROMPT_CACHING_ENABLED=true
CACHE_CONTROL_STRATEGY=auto
CACHE_MIN_TOKENS=1024

# Model Routing
MODEL_ROUTING_ENABLED=true
DEFAULT_FALLBACK_MODELS=anthropic/claude-3.5-sonnet,openai/gpt-4o
ROUTING_STRATEGY=auto
ENABLE_AUTO_ROUTER=false

# Usage Tracking
USAGE_TRACKING_ENABLED=true
TRACK_USER_IDS=true

# Image Generation
IMAGE_GENERATION_ENABLED=true
IMAGE_GENERATION_MODELS=google/gemini-2.5-flash-image-preview
IMAGE_STORAGE_TYPE=database
IMAGE_MAX_SIZE_MB=10

# Structured Outputs
STRUCTURED_OUTPUTS_ENABLED=true

# Multimodal
PDF_PROCESSING_ENABLED=true
AUDIO_PROCESSING_ENABLED=true
PDF_SKIP_PARSING=false
```

---

## 🚀 Setup & Deployment

### **1. Install Dependencies**

```bash
poetry install
```

### **2. Run Database Migrations**

```bash
alembic upgrade head
```

### **3. Seed Plan Data**

```bash
python scripts/seed_plan_limits.py
```

### **4. Start Server**

```bash
uvicorn app.main:app --reload
```

### **5. Access API Documentation**

Visit `http://localhost:8000/docs` for interactive API docs.

---

## 🧪 Testing

### **Run Unit Tests**

```bash
pytest tests/unit/test_openrouter_service.py
pytest tests/unit/test_subscription_service.py
pytest tests/unit/test_presets_service.py
```

### **Test Endpoints**

```bash
# Create conversation
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode": "standard"}'

# Send chat message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "uuid",
    "message": "Hello",
    "enable_caching": true
  }'

# Generate image
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful mosque",
    "aspect_ratio": "16:9"
  }'

# Check usage
curl http://localhost:8000/api/v1/subscriptions/usage \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Performance & Cost Optimization

### **Prompt Caching Savings**

With prompt caching enabled:
- **System prompts**: 90% cost reduction
- **Conversation history**: 50-80% cost reduction
- **RAG context**: 80-90% cost reduction

**Example:**
- Without caching: 10K tokens × $0.015/1K = $0.15
- With caching (90% hit rate): 1K tokens × $0.015/1K = $0.015
- **Savings: $0.135 per request (90%)**

### **Model Routing**

Automatic fallbacks ensure high availability:
- Primary model fails → Try fallback #1
- Fallback #1 fails → Try fallback #2
- Track which model succeeded
- Monitor fallback frequency

### **Streaming**

Reduces perceived latency:
- Start showing response immediately
- Chunks sent as they're generated
- Better user experience
- Lower abandonment rate

---

## 📈 Analytics & Monitoring

### **System-Wide Metrics**

- Total users and active users (30d)
- Total conversations and messages
- Token usage and costs
- Cache hit rate and savings
- Image generation count

### **Plan Distribution**

- Users per plan type
- Revenue breakdown
- Conversion rates

### **Usage Trends**

- Daily/monthly usage graphs
- Cost trends
- Cache performance over time

### **Top Users**

- Highest usage users
- Cost per user
- Cache savings per user

---

## 🔐 Security

### **Authentication**

All endpoints require JWT authentication via `get_current_user` dependency.

### **Authorization**

- Users can only access their own data
- Admin endpoints require `role="admin"`
- Quota enforcement before requests

### **Rate Limiting**

Configured per plan:
- Free: 5 req/min
- Premium: 50 req/min
- Unlimited: 1000 req/min
- Enterprise: Custom

---

## 🐛 Troubleshooting

### **Quota Exceeded**

```
HTTP 400: Monthly message limit reached (100)
```

**Solution**: Upgrade plan or wait for next billing cycle.

### **Cache Not Working**

Check settings:
```bash
PROMPT_CACHING_ENABLED=true
CACHE_CONTROL_STRATEGY=auto
```

Verify cache stats:
```bash
GET /api/v1/chat/cache-stats/{conversation_id}
```

### **Model Fallback Issues**

Check logs for routing attempts:
```python
{
  "routing_strategy": "auto",
  "fallback_used": true,
  "models_attempted": ["model1", "model2"],
  "final_model_used": "model2"
}
```

---

## 📚 References

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Prompt Caching Guide](https://openrouter.ai/docs#prompt-caching)
- [Model Routing](https://openrouter.ai/docs#model-routing)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## 🤝 Support

For issues or questions:
- Check logs for detailed error messages
- Review API documentation at `/docs`
- Contact support team

---

## 📝 License

This integration is part of the WisQu Islamic Chatbot project.
