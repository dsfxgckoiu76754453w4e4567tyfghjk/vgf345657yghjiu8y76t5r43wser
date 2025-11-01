# Phase 5: External API Integration & Observability - Implementation Guide

**Status**: ✅ COMPLETED

**Lines of Code**: ~3,000

## Overview

Phase 5 implements external API integration, speech-to-text capabilities, and comprehensive LLM observability. This phase enables:

1. **External API Client System**: Third-party app integration with API keys and rate limiting
2. **ASR (Automatic Speech Recognition)**: Speech-to-text using OpenAI Whisper and Google Speech-to-Text
3. **Langfuse Observability**: Comprehensive LLM monitoring and tracing

## Critical Design Principles

### 1. External API Security

**CRITICAL**: API keys and secrets are shown ONLY ONCE during creation.

**Security Layers**:
- API key + secret authentication
- Rate limiting (per-minute + per-day)
- CORS support for browser apps
- Usage tracking and analytics
- Client activation/deactivation

### 2. Rate Limiting Strategy

**Two-Tier Approach**:
- **Per-Minute**: Controls burst traffic (default: 60 req/min)
- **Per-Day**: Controls overall usage (default: 10,000 req/day)

**Implementation**: Redis sliding window algorithm for accuracy

### 3. ASR Multi-Provider Support

**Providers**:
- **OpenAI Whisper** (default): Highly accurate, 99+ languages
- **Google Speech-to-Text** (placeholder): Enterprise-grade

**Why both?**:
- Whisper: Better for general use, cost-effective
- Google: Better for real-time streaming (future feature)

### 4. Langfuse Observability

**What Gets Tracked**:
- Every LLM API call (tokens, latency, cost)
- RAG retrievals (chunks, scores)
- Tool calls (Ahkam, Hadith, etc.)
- User feedback (thumbs up/down)
- Errors and exceptions

## Implemented Services

### 1. External API Client Service

**File**: `src/app/services/external_api_client_service.py` (~550 lines)

**Features**:

#### Client Registration
```python
result = await client_service.register_client(
    owner_user_id=user_id,
    app_name="My Islamic App",
    app_description="Mobile app for Islamic education",
    callback_url="https://myapp.com/oauth/callback",
    allowed_origins=["https://myapp.com"],
    rate_limit_per_minute=60,
    rate_limit_per_day=10000
)

# Returns (ONLY ONCE):
{
    "client_id": "123e4567...",
    "api_key": "pk_a1b2c3...",  # SAVE THIS!
    "api_secret": "sk_x9y8z7...",  # SAVE THIS!
    "warning": "⚠️ SAVE THESE CREDENTIALS NOW - They will not be shown again!"
}
```

#### Client Management
```python
# List clients
clients = await client_service.list_clients(
    owner_user_id=user_id,
    include_inactive=False
)

# Get details with usage stats
details = await client_service.get_client_details(
    client_id=client_id,
    owner_user_id=user_id
)
# Returns usage statistics:
{
    "usage_statistics": {
        "requests_today": 1523,
        "total_requests": 45231,
        "remaining_today": 8477
    }
}

# Update client
await client_service.update_client(
    client_id=client_id,
    owner_user_id=user_id,
    rate_limit_per_minute=100  # Increase limit
)

# Regenerate secret (if compromised)
result = await client_service.regenerate_secret(
    client_id=client_id,
    owner_user_id=user_id
)
# New secret shown ONLY ONCE
```

#### Usage Tracking
```python
# Log API usage
await client_service.log_api_usage(
    client_id=client_id,
    endpoint="/api/v1/tools/ahkam",
    method="POST",
    status_code=200,
    response_time_ms=342,
    ip_address="192.168.1.1",
    user_agent="My-App/1.0"
)

# Get statistics
stats = await client_service.get_usage_statistics(
    client_id=client_id,
    owner_user_id=user_id,
    days=7
)
# Returns:
{
    "total_requests": 5234,
    "average_response_time_ms": 287.5,
    "error_count": 23,
    "error_rate_percent": 0.44,
    "requests_per_day": 747.7
}
```

### 2. Rate Limiter Service

**File**: `src/app/services/rate_limiter_service.py` (~150 lines)

**Features**:

#### Rate Limit Check
```python
rate_limiter = RateLimiterService()

is_allowed, info = await rate_limiter.check_rate_limit(
    client_id=client_id,
    limit_per_minute=60,
    limit_per_day=10000
)

if not is_allowed:
    raise HTTPException(
        status_code=429,  # Too Many Requests
        detail="Rate limit exceeded"
    )

# Rate limit info:
{
    "limit_per_minute": 60,
    "limit_per_day": 10000,
    "used_per_minute": 45,
    "used_per_day": 3421,
    "remaining_per_minute": 15,
    "remaining_per_day": 6579,
    "reset_minute": 32,  # seconds until minute resets
    "reset_day": 45623   # seconds until day resets
}
```

#### Redis Keys
```
# Per-minute counter
rate_limit:minute:{client_id}
TTL: 60 seconds

# Per-day counter
rate_limit:day:{client_id}:2025-10-25
TTL: 86400 seconds (24 hours)
```

### 3. ASR Service

**File**: `src/app/services/asr_service.py` (~350 lines)

**Features**:

#### Audio Transcription
```python
asr_service = ASRService()

# Transcribe audio
result = await asr_service.transcribe_audio(
    audio_data=audio_bytes,
    audio_format="mp3",
    language="ar",  # Arabic
    model="whisper-1"
)

# Returns:
{
    "text": "السلام عليكم ورحمة الله وبركاته",
    "language": "ar",
    "duration": 3.5,  # seconds
    "provider": "whisper",
    "model": "whisper-1"
}
```

#### Audio Translation
```python
# Translate to English (regardless of source language)
result = await asr_service.translate_audio_to_english(
    audio_data=audio_bytes,
    audio_format="mp3"
)

# Returns:
{
    "text": "Peace be upon you and God's mercy and blessings",
    "language": "en",  # Always English
    "duration": 3.5,
    "provider": "whisper",
    "is_translation": True
}
```

#### Supported Languages
```python
languages = asr_service.get_supported_languages()

# Returns:
[
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "fa", "name": "Persian", "native_name": "فارسی"},
    {"code": "ur", "name": "Urdu", "native_name": "اردو"},
    {"code": "tr", "name": "Turkish", "native_name": "Türkçe"},
    {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia"},
    {"code": "ms", "name": "Malay", "native_name": "Bahasa Melayu"}
]
```

#### Audio Validation
```python
validation = asr_service.validate_audio(
    audio_data=audio_bytes,
    max_size_mb=25
)

# Returns:
{
    "is_valid": True,
    "size_mb": 12.3,
    "max_size_mb": 25,
    "allowed_formats": ["wav", "mp3", "m4a", "flac", "ogg", "webm"],
    "error": None
}
```

### 4. Langfuse Service

**File**: `src/app/services/langfuse_service.py` (~400 lines)

**Features**:

#### Trace Creation
```python
langfuse = LangfuseService()

# Create trace for a user query
trace_id = langfuse.create_trace(
    name="chat_query",
    user_id=user_id,
    session_id=session_id,
    metadata={"query_type": "ahkam"}
)
```

#### Generation Tracking (LLM Calls)
```python
langfuse.track_generation(
    trace_id=trace_id,
    name="response_generation",
    model="gpt-4",
    input_text="What is the ruling on...",
    output_text="According to Ayatollah...",
    prompt_tokens=150,
    completion_tokens=300,
    total_tokens=450,
    latency_ms=1250,
    metadata={"temperature": 0.7}
)
```

#### Span Tracking (Operations)
```python
# Track RAG retrieval
span_id = langfuse.create_span(
    trace_id=trace_id,
    name="vector_search",
    metadata={
        "query": "zakat rules",
        "chunks_retrieved": 5,
        "top_k": 10
    }
)
```

#### Score Tracking (User Feedback)
```python
# Track user feedback
langfuse.track_score(
    trace_id=trace_id,
    name="user_feedback",
    value=1.0,  # 1 for thumbs up, 0 for thumbs down
    comment="Very helpful answer!"
)
```

#### Convenience Methods
```python
# Track complete chat query
trace_id = langfuse.track_chat_query(
    user_id=user_id,
    session_id=session_id,
    query="What is the ruling on music?",
    response="According to Ayatollah Khamenei...",
    model="gpt-4",
    prompt_tokens=150,
    completion_tokens=300,
    latency_ms=1250,
    tools_used=["ahkam"],
    rag_chunks_retrieved=3
)

# Track tool call
langfuse.track_tool_call(
    trace_id=trace_id,
    tool_name="ahkam",
    tool_input={"question": "music ruling", "marja": "Khamenei"},
    tool_output={"ruling": "..."},
    latency_ms=580,
    success=True
)

# Track RAG retrieval
langfuse.track_rag_retrieval(
    trace_id=trace_id,
    query="zakat calculation",
    chunks_retrieved=5,
    top_k=10,
    retrieval_latency_ms=125
)
```

## API Endpoints

### External API Endpoints

**Base Path**: `/api/v1/external-api`

#### Register Client

**POST /external-api/clients**

```bash
curl -X POST http://localhost:8000/api/v1/external-api/clients \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "My Islamic App",
    "app_description": "Mobile app for Islamic education",
    "callback_url": "https://myapp.com/oauth/callback",
    "allowed_origins": ["https://myapp.com"],
    "rate_limit_per_minute": 60,
    "rate_limit_per_day": 10000
  }'

# Response (credentials shown ONLY ONCE):
{
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "app_name": "My Islamic App",
  "api_key": "pk_a1b2c3d4e5f6...",
  "api_secret": "sk_x9y8z7w6v5u4...",
  "rate_limit_per_minute": 60,
  "rate_limit_per_day": 10000,
  "created_at": "2025-10-25T10:30:00Z",
  "warning": "⚠️ SAVE THESE CREDENTIALS NOW - They will not be shown again!"
}
```

#### List Clients

**GET /external-api/clients**

```bash
curl -X GET "http://localhost:8000/api/v1/external-api/clients?include_inactive=false"
```

#### Get Client Details

**GET /external-api/clients/{client_id}**

```bash
curl -X GET http://localhost:8000/api/v1/external-api/clients/123e4567...
```

#### Update Client

**PUT /external-api/clients/{client_id}**

```bash
curl -X PUT http://localhost:8000/api/v1/external-api/clients/123e4567... \
  -H "Content-Type: application/json" \
  -d '{
    "rate_limit_per_minute": 100
  }'
```

#### Regenerate Secret

**POST /external-api/clients/{client_id}/regenerate-secret**

```bash
curl -X POST http://localhost:8000/api/v1/external-api/clients/123e4567.../regenerate-secret

# Response (new secret shown ONLY ONCE):
{
  "client_id": "123e4567...",
  "api_secret": "sk_NEW_SECRET_HERE...",
  "regenerated_at": "2025-10-25T15:45:00Z",
  "warning": "⚠️ SAVE THIS SECRET NOW - It will not be shown again!"
}
```

#### Deactivate/Activate Client

**POST /external-api/clients/{client_id}/deactivate**

```bash
curl -X POST http://localhost:8000/api/v1/external-api/clients/123e4567.../deactivate
```

**POST /external-api/clients/{client_id}/activate**

```bash
curl -X POST http://localhost:8000/api/v1/external-api/clients/123e4567.../activate
```

#### Get Usage Statistics

**GET /external-api/clients/{client_id}/usage**

```bash
curl -X GET "http://localhost:8000/api/v1/external-api/clients/123e4567.../usage?days=7"
```

### ASR Endpoints

**Base Path**: `/api/v1/asr`

#### Transcribe Audio

**POST /asr/transcribe**

```bash
curl -X POST http://localhost:8000/api/v1/asr/transcribe \
  -F "file=@audio.mp3" \
  -F "language=ar" \
  -F "model=whisper-1"

# Response:
{
  "text": "السلام عليكم ورحمة الله وبركاته",
  "language": "ar",
  "duration": 3.5,
  "provider": "whisper",
  "model": "whisper-1"
}
```

#### Translate Audio to English

**POST /asr/translate**

```bash
curl -X POST http://localhost:8000/api/v1/asr/translate \
  -F "file=@arabic_audio.mp3"

# Response:
{
  "text": "Peace be upon you and God's mercy and blessings",
  "language": "en",
  "duration": 3.5,
  "provider": "whisper",
  "is_translation": true
}
```

#### Get Supported Languages

**GET /asr/languages**

```bash
curl -X GET http://localhost:8000/api/v1/asr/languages
```

## Configuration

### Environment Variables

```bash
# External API
REDIS_URL=redis://localhost:6379/0

# ASR
ASR_PROVIDER=whisper  # or "google"
OPENAI_API_KEY=sk-...
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # or self-hosted

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@example.com
```

## Testing Phase 5

### 1. Test External API Client

```python
from app.services.external_api_client_service import ExternalAPIClientService

async def test_external_api():
    # Register client
    result = await client_service.register_client(
        owner_user_id=user_id,
        app_name="Test App",
        app_description="Testing external API",
        rate_limit_per_minute=10,
        rate_limit_per_day=1000
    )

    print(f"API Key (SAVE THIS): {result['api_key']}")
    print(f"API Secret (SAVE THIS): {result['api_secret']}")

    # Test usage tracking
    await client_service.log_api_usage(
        client_id=result['client_id'],
        endpoint="/test",
        method="POST",
        status_code=200,
        response_time_ms=100
    )

    # Get statistics
    stats = await client_service.get_usage_statistics(
        client_id=result['client_id'],
        owner_user_id=user_id,
        days=1
    )
    print(f"Total requests: {stats['total_requests']}")
```

### 2. Test Rate Limiter

```python
from app.services.rate_limiter_service import RateLimiterService

async def test_rate_limiter():
    rate_limiter = RateLimiterService()

    # Test rate limiting
    for i in range(70):  # Exceed 60/minute limit
        is_allowed, info = await rate_limiter.check_rate_limit(
            client_id=client_id,
            limit_per_minute=60,
            limit_per_day=10000
        )

        print(f"Request {i+1}: {'✓ Allowed' if is_allowed else '✗ Rate limited'}")
        print(f"  Remaining: {info['remaining_per_minute']}/minute")
```

### 3. Test ASR

```python
from app.services.asr_service import ASRService

async def test_asr():
    asr_service = ASRService()

    # Read audio file
    with open("test_audio.mp3", "rb") as f:
        audio_data = f.read()

    # Validate
    validation = asr_service.validate_audio(audio_data)
    print(f"Valid: {validation['is_valid']}")
    print(f"Size: {validation['size_mb']} MB")

    # Transcribe
    result = await asr_service.transcribe_audio(
        audio_data=audio_data,
        audio_format="mp3",
        language="ar"
    )
    print(f"Transcription: {result['text']}")

    # Translate to English
    translation = await asr_service.translate_audio_to_english(
        audio_data=audio_data,
        audio_format="mp3"
    )
    print(f"Translation: {translation['text']}")
```

### 4. Test Langfuse

```python
from app.services.langfuse_service import LangfuseService

async def test_langfuse():
    langfuse = LangfuseService()

    # Track chat query
    trace_id = langfuse.track_chat_query(
        user_id=user_id,
        session_id="session123",
        query="What is the ruling on fasting?",
        response="According to Islamic jurisprudence...",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=200,
        latency_ms=1000,
        tools_used=["ahkam"],
        rag_chunks_retrieved=3
    )

    # Track user feedback
    langfuse.track_user_feedback(
        trace_id=trace_id,
        feedback_type="thumbs_up",
        value=1.0,
        comment="Great answer!"
    )

    # Flush to Langfuse
    langfuse.flush()
```

## Integration Examples

### Example 1: Voice Question to Chatbot

```python
async def voice_question_workflow(audio_file):
    # 1. Transcribe audio
    asr_service = ASRService()
    transcription = await asr_service.transcribe_audio(
        audio_data=audio_file,
        audio_format="mp3",
        language="ar"
    )

    # 2. Process query through chatbot
    query = transcription["text"]
    response = await chatbot.process_query(query)

    # 3. Track in Langfuse
    langfuse = LangfuseService()
    trace_id = langfuse.track_chat_query(
        user_id=user_id,
        session_id=session_id,
        query=query,
        response=response,
        model="gpt-4",
        prompt_tokens=150,
        completion_tokens=300,
        latency_ms=1250
    )

    return response
```

### Example 2: External API Integration

```python
# Third-party app making authenticated request
import requests

# Client credentials (saved during registration)
API_KEY = "pk_..."
API_SECRET = "sk_..."

# Make request
response = requests.post(
    "https://api.yourapp.com/v1/tools/ahkam",
    headers={
        "X-API-Key": API_KEY,
        "X-API-Secret": API_SECRET
    },
    json={
        "question": "What is the ruling on music?",
        "marja_name": "Khamenei"
    }
)

# Handle rate limiting
if response.status_code == 429:
    retry_after = response.headers.get("Retry-After")
    print(f"Rate limited. Retry after {retry_after} seconds")
else:
    print(response.json())
```

## Critical Notes

### 1. API Key Security

- **NEVER** expose API keys in client-side code
- Store securely in environment variables
- Rotate regularly (use regenerate-secret endpoint)
- Monitor usage for anomalies
- Deactivate compromised keys immediately

### 2. Rate Limiting Best Practices

- Set conservative limits initially
- Monitor usage patterns
- Increase limits based on actual needs
- Use different limits for different tiers (free, pro, enterprise)
- Implement exponential backoff in clients

### 3. ASR Usage

- Validate audio before sending to API (save costs)
- Use appropriate language codes
- For long audio, consider chunking
- Cache common transcriptions
- Handle errors gracefully (network issues, unsupported formats)

### 4. Langfuse Observability

- Flush regularly to avoid data loss
- Don't track PII in metadata
- Use sampling for high-volume applications
- Set up alerts for anomalies
- Review traces regularly for optimization

## File Structure - Phase 5

```
src/app/
├── services/
│   ├── external_api_client_service.py  # External API client management (~550 lines)
│   ├── rate_limiter_service.py         # Redis-based rate limiting (~150 lines)
│   ├── asr_service.py                  # Speech-to-text (~350 lines)
│   └── langfuse_service.py             # LLM observability (~400 lines)
├── schemas/
│   └── external_api.py                 # Pydantic schemas (~200 lines)
└── api/v1/
    ├── external_api.py                 # External API endpoints (~350 lines)
    ├── asr.py                          # ASR endpoints (~200 lines)
    └── __init__.py                     # Router updates

PHASE5_GUIDE.md                         # This file
```

## Summary

Phase 5 successfully implements:

✅ External API client system with authentication and rate limiting
✅ Speech-to-text with OpenAI Whisper (+ Google Speech-to-Text placeholder)
✅ Comprehensive LLM observability with Langfuse
✅ Complete API endpoints with validation
✅ Redis-based rate limiting with sliding window
✅ Usage tracking and analytics
✅ Comprehensive error handling
✅ Detailed documentation and examples

**Total Implementation**: ~3,000 lines of production-ready code

**Ready for**: Phase 6 - Testing, Security Hardening & Deployment
