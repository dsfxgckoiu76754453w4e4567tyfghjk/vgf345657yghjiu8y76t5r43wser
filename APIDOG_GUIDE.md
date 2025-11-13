# API Documentation & Apidog Guide

Complete API reference with Apidog/Postman examples for WisQu Islamic Chatbot.

---

## Base URL

```
http://localhost:8000
```

**Production:** `https://api.wisqu.com`

---

## Authentication

All endpoints (except auth & health) require JWT Bearer token.

### Header Format
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### 1.1 Register with Email/Password

**Endpoint:** `POST /api/v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!",
  "name": "Ahmed Ali"
}
```

**Response:**
```json
{
  "message": "Registration successful. Please verify your email with the OTP sent.",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Notes:**
- OTP code sent via Mailgun (SMTP fallback)
- 6-digit code, valid for 10 minutes

---

### 1.2 Verify OTP

**Endpoint:** `POST /api/v1/auth/verify-otp`

**Request:**
```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "Ahmed Ali",
    "is_verified": true
  }
}
```

---

### 1.3 Login

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "Ahmed Ali",
    "subscription_plan": "free"
  }
}
```

---

### 1.4 Google OAuth (Authorization Code Flow)

**Endpoint:** `POST /api/v1/auth/google/auth-code`

**Request:**
```json
{
  "id_token": "ya29.a0AfB_byD..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "is_new_user": false,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@gmail.com",
    "name": "Ahmed Ali"
  }
}
```

**Notes:**
- Unified accounts: same email = ONE user
- Auto-links Google OAuth to existing email/password account

---

### 1.5 Google OAuth (ID Token Flow)

**Endpoint:** `POST /api/v1/auth/google/id-token`

**Request:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

**Response:** Same as 1.4

---

### 1.6 Resend OTP

**Endpoint:** `POST /api/v1/auth/resend-otp`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "OTP resent successfully"
}
```

---

### 1.7 Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 2. Chat Endpoints

### 2.1 Send Message (Non-Streaming)

**Endpoint:** `POST /api/v1/chat/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "What are the 5 pillars of Islam?",
  "model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.7,
  "max_tokens": 2048,
  "enable_caching": true,
  "stream": false,
  "auto_detect_images": true
}
```

**Response:**
```json
{
  "message_id": "8d0e7890-8536-51ef-a65c-f18fc2g01bf8",
  "content": "The five pillars of Islam are:\n1. Shahada (Faith)\n2. Salah (Prayer)\n3. Zakat (Charity)\n4. Sawm (Fasting)\n5. Hajj (Pilgrimage)",
  "model": "anthropic/claude-3.5-sonnet",
  "usage": {
    "prompt_tokens": 245,
    "completion_tokens": 87,
    "total_tokens": 332
  },
  "cached_tokens_read": 150,
  "cached_tokens_write": 95,
  "cache_discount_usd": 0.00045,
  "total_cost_usd": 0.0012,
  "fallback_used": false,
  "final_model_used": "anthropic/claude-3.5-sonnet",
  "intent_results": null,
  "langfuse_trace_id": "trace_abc123"
}
```

---

### 2.2 Send Message with SSE Streaming ⚡

**Endpoint:** `POST /api/v1/chat/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: text/event-stream
```

**Request:**
```json
{
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "Explain the concept of Tawhid",
  "stream": true
}
```

**Response (SSE Stream):**
```
data: {"type": "content", "content": "Tawhid"}

data: {"type": "content", "content": " is"}

data: {"type": "content", "content": " the"}

data: {"type": "content", "content": " fundamental"}

data: {"type": "content", "content": " concept"}

data: {"type": "content", "content": " of"}

data: {"type": "content", "content": " monotheism"}

data: {"type": "content", "content": " in"}

data: {"type": "content", "content": " Islam"}

data: {"type": "metadata", "message_id": "8d0e7890-8536-51ef-a65c-f18fc2g01bf8", "model": "anthropic/claude-3.5-sonnet", "usage": {"prompt_tokens": 123, "completion_tokens": 456, "total_tokens": 579}}
```

**SSE Implementation in JavaScript:**
```javascript
const eventSource = new EventSource('/api/v1/chat/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    conversation_id: conversationId,
    message: userMessage,
    stream: true
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'content') {
    // Append content token-by-token
    appendToChat(data.content);
  } else if (data.type === 'metadata') {
    // Stream completed, show metadata
    console.log('Message ID:', data.message_id);
    console.log('Usage:', data.usage);
  } else if (data.type === 'error') {
    // Handle error
    console.error('Error:', data.error);
  }
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

**Apidog SSE Testing:**
1. Set method to `POST`
2. Set `Accept: text/event-stream` header
3. Enable "SSE Mode" in Apidog
4. You'll see token-by-token streaming in real-time

---

### 2.3 Image Generation via Intent Detection

**Endpoint:** `POST /api/v1/chat/`

**Request:**
```json
{
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "Generate an image of a beautiful mosque at sunset",
  "auto_detect_images": true
}
```

**Response:**
```json
{
  "message_id": "...",
  "content": "I've generated an image of a beautiful mosque at sunset for you.",
  "model": "anthropic/claude-3.5-sonnet",
  "usage": {...},
  "generated_image": {
    "id": "img_abc123",
    "url": "https://storage.wisqu.com/images/...",
    "prompt": "beautiful mosque at sunset",
    "model": "google/gemini-2.5-flash-image-preview",
    "size": "1024x1024"
  },
  "intent_results": {
    "generated_image": {
      "id": "img_abc123",
      "url": "https://storage.wisqu.com/images/..."
    }
  }
}
```

---

### 2.4 Structured Output

**Endpoint:** `POST /api/v1/chat/structured`

**Request:**
```json
{
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "Is fasting obligatory in Islam?",
  "response_schema": {
    "type": "object",
    "properties": {
      "answer": {"type": "string"},
      "ruling": {"type": "string", "enum": ["obligatory", "recommended", "permissible", "disliked", "forbidden"]},
      "confidence": {"type": "number", "minimum": 0, "maximum": 1},
      "sources": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["answer", "ruling", "confidence"]
  }
}
```

**Response:**
```json
{
  "message_id": "...",
  "content": "{\"answer\": \"Yes, fasting during Ramadan is obligatory...\", \"ruling\": \"obligatory\", \"confidence\": 0.98, \"sources\": [\"Quran 2:183\", \"Sahih Bukhari\"]}",
  "model": "anthropic/claude-3.5-sonnet",
  "usage": {...}
}
```

---

### 2.5 Async Chat (Temporal Workflow)

**Endpoint:** `POST /api/v1/chat/async`

**Request:**
```json
{
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "Explain the history of Islamic caliphates in detail",
  "model": "anthropic/claude-3.5-sonnet"
}
```

**Response:**
```json
{
  "workflow_id": "chat-7d8e9f10-9647-62fg-b76d-g29gd3h12cg9",
  "status": "processing",
  "workflow_url": "/api/v1/chat/workflows/chat-7d8e9f10-9647-62fg-b76d-g29gd3h12cg9"
}
```

**Check Status:**
```
GET /api/v1/chat/workflows/{workflow_id}
```

---

### 2.6 Cache Statistics

**Endpoint:** `GET /api/v1/chat/cache-stats/{conversation_id}`

**Response:**
```json
{
  "total_messages": 25,
  "cached_messages": 18,
  "total_cached_tokens": 12450,
  "total_cache_savings_usd": 0.037,
  "cache_hit_rate": 0.72
}
```

---

## 3. Conversations

### 3.1 Create Conversation

**Endpoint:** `POST /api/v1/conversations/`

**Request:**
```json
{
  "title": "Islamic Jurisprudence Discussion"
}
```

**Response:**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "title": "Islamic Jurisprudence Discussion",
  "created_at": "2025-01-13T10:30:00Z",
  "message_count": 0
}
```

---

### 3.2 List Conversations

**Endpoint:** `GET /api/v1/conversations/?limit=20&offset=0`

**Response:**
```json
{
  "total": 15,
  "conversations": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "title": "Islamic Jurisprudence Discussion",
      "created_at": "2025-01-13T10:30:00Z",
      "last_message_at": "2025-01-13T11:45:00Z",
      "message_count": 12
    }
  ]
}
```

---

### 3.3 Get Conversation

**Endpoint:** `GET /api/v1/conversations/{conversation_id}`

**Response:**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "title": "Islamic Jurisprudence Discussion",
  "created_at": "2025-01-13T10:30:00Z",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "What is Ijtihad?",
      "created_at": "2025-01-13T10:31:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Ijtihad refers to independent reasoning...",
      "model_used": "anthropic/claude-3.5-sonnet",
      "tokens_used": 245,
      "created_at": "2025-01-13T10:31:05Z"
    }
  ]
}
```

---

### 3.4 Delete Conversation

**Endpoint:** `DELETE /api/v1/conversations/{conversation_id}`

**Response:**
```json
{
  "message": "Conversation deleted successfully"
}
```

---

## 4. Documents (RAG)

### 4.1 Upload Document

**Endpoint:** `POST /api/v1/documents/upload`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request (Form Data):**
```
file: [PDF/TXT/DOCX file]
title: "Sahih Bukhari - Volume 1"
category: "hadith"
```

**Response:**
```json
{
  "id": "doc_abc123",
  "title": "Sahih Bukhari - Volume 1",
  "category": "hadith",
  "status": "processing",
  "file_size_bytes": 2048576,
  "chunks_created": 0
}
```

---

### 4.2 Search Documents

**Endpoint:** `POST /api/v1/documents/search`

**Request:**
```json
{
  "query": "What does Islam say about charity?",
  "limit": 10,
  "use_reranker": true
}
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "chunk_001",
      "document_title": "Quran Translation",
      "chunk_text": "...charity is mentioned in Quran 2:177...",
      "vector_score": 0.89,
      "rerank_score": 0.94,
      "metadata": {
        "page": 15,
        "verse": "2:177"
      }
    }
  ],
  "total_results": 10,
  "reranking_used": true
}
```

**Notes:**
- 2-Stage Retrieval: Vector search (Qdrant) → Reranking (Cohere)
- 20-40% quality improvement with reranker

---

## 5. Health Check

### 5.1 API Health

**Endpoint:** `GET /api/v1/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": "connected",
    "redis": "connected",
    "qdrant": "connected",
    "temporal": "connected"
  },
  "timestamp": "2025-01-13T12:00:00Z"
}
```

---

## 6. Admin Endpoints

### 6.1 Get System Stats (Admin Only)

**Endpoint:** `GET /api/v1/admin/stats`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "total_users": 1250,
  "total_conversations": 8945,
  "total_messages": 42378,
  "total_documents": 567,
  "active_users_24h": 234,
  "cache_hit_rate": 0.68,
  "avg_response_time_ms": 450
}
```

---

## Testing in Apidog

### Import Steps:

1. **Create New Project** → "WisQu Islamic Chatbot"
2. **Import Collection** → Use JSON file `apidog-collection.json`
3. **Set Environment Variables:**
   - `base_url`: `http://localhost:8000`
   - `access_token`: Your JWT token after login
4. **Test SSE Streaming:**
   - Enable "SSE Mode" in request settings
   - Set `Accept: text/event-stream` header
   - Watch token-by-token streaming

### Environment Variables:
```json
{
  "base_url": "http://localhost:8000",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "conversation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

---

## Common Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

---

## Rate Limits

| Plan | Requests/Minute |
|------|-----------------|
| Anonymous | 5 |
| Free | 10 |
| Premium | 50 |
| Unlimited | 1000 |

---

**Documentation Version:** 1.0.0
**Last Updated:** 2025-01-13
