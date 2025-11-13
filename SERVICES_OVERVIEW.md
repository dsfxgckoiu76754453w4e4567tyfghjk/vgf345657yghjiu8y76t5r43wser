# WisQu Services Architecture & Communication Map

## 🎯 Development Setup (Current Configuration)

**FastAPI App**: Running LOCALLY via `poetry run uvicorn` (NOT in Docker)
**Supporting Services**: Running in Docker containers

This setup allows **agile development** - make code changes without rebuilding Docker images!

---

## 📦 Docker Services (6 Containers)

| Service | Container Name | Ports | Status | Purpose |
|---------|---------------|-------|--------|---------|
| **PostgreSQL** | `shia-chatbot-postgres` | `5433:5432` | ✅ Healthy | Main database |
| **Redis** | `shia-chatbot-redis` | `6379:6379` | ✅ Healthy | Cache & message broker |
| **Qdrant** | `shia-chatbot-qdrant` | `6333:6333`, `6334:6334` | ✅ Healthy | Vector database for embeddings |
| **MinIO** | `shia-chatbot-minio` | `9000:9000`, `9001:9001` | ✅ Healthy | Object storage (S3-compatible) |
| **Celery Worker** | `shia-chatbot-celery-worker` | N/A | 🔄 Starting | Async task execution |
| **Flower** | `shia-chatbot-flower` | `5555:5555` | ✅ Running | Celery monitoring dashboard |

---

## 🌐 Service Communication Map

```
┌─────────────────────────────────────────────────────────────────────┐
│  LOCALHOST (Your Machine)                                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  FastAPI Application (Port 8000)                           │    │
│  │  Running: poetry run uvicorn src.app.main:app --reload    │    │
│  └────────────────────────────────────────────────────────────┘    │
│         │                                                           │
│         │  Communicates with Docker services via localhost         │
│         ▼                                                           │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ TCP/IP via localhost
         │
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DOCKER NETWORK: chatbot-network                                     │
│                                                                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │  PostgreSQL  │     │    Redis     │     │   Qdrant     │        │
│  │  Port: 5433  │     │  Port: 6379  │     │  Port: 6333  │        │
│  │              │     │              │     │              │        │
│  │ Stores:      │     │ Stores:      │     │ Stores:      │        │
│  │ - Users      │     │ - Cache      │     │ - Embeddings │        │
│  │ - Chats      │     │ - Sessions   │     │ - Vectors    │        │
│  │ - Documents  │     │ - Task Queue │     │ - RAG Data   │        │
│  │ - Tickets    │     │              │     │              │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│         ▲                     ▲                    ▲                │
│         │                     │                    │                │
│         └─────────┬───────────┴────────────────────┘                │
│                   │                                                 │
│  ┌────────────────┴────────────────┐                               │
│  │     Celery Worker               │                               │
│  │  (Async Task Processor)         │                               │
│  │                                 │                               │
│  │  Executes:                      │                               │
│  │  - Chat message processing      │                               │
│  │  - Image generation             │                               │
│  │  - Audio transcription (ASR)    │                               │
│  │  - Web search tasks             │                               │
│  │  - Embedding generation         │                               │
│  │  - Email notifications          │                               │
│  │  - File storage operations      │                               │
│  │  - Cleanup jobs                 │                               │
│  │  - Dataset processing           │                               │
│  │  - Langfuse analytics           │                               │
│  │  - Leaderboard updates          │                               │
│  │  - Environment promotion        │                               │
│  └─────────────────────────────────┘                               │
│         │                     ▲                                     │
│         │                     │                                     │
│         ▼                     │                                     │
│  ┌──────────────┐     ┌──────────────┐                            │
│  │    MinIO     │     │    Flower    │                            │
│  │  Port: 9000  │     │  Port: 5555  │                            │
│  │  (Web: 9001) │     │  (Dashboard) │                            │
│  │              │     │              │                            │
│  │ Stores:      │     │ Monitors:    │                            │
│  │ - Images     │     │ - Tasks      │                            │
│  │ - Documents  │     │ - Workers    │                            │
│  │ - Audio      │     │ - Queues     │                            │
│  │ - Backups    │     │ - Stats      │                            │
│  └──────────────┘     └──────────────┘                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 External Services (Cloud-based)

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Langfuse Cloud** | LLM observability & tracing | `LANGFUSE_HOST=https://cloud.langfuse.com` |
| **OpenRouter** | Unified LLM API (100+ models) | `OPENROUTER_API_KEY` configured |
| **OpenAI** | GPT models (fallback) | `OPENAI_API_KEY` configured |
| **Cohere** | Reranking & embeddings | `COHERE_API_KEY` configured |

---

## 📊 Data Flow Examples

### 1. Chat Message Flow
```
User → FastAPI (/api/v1/chat)
  ↓
FastAPI → Celery Task (process_chat_message)
  ↓
Celery Worker:
  1. Query Qdrant for relevant context (RAG)
  2. Call OpenRouter API for LLM response
  3. Store conversation in PostgreSQL
  4. Cache result in Redis
  5. Track with Langfuse
  ↓
Response → User
```

### 2. File Upload Flow
```
User → FastAPI (/api/v1/storage/upload)
  ↓
FastAPI:
  1. Validate file
  2. Store in MinIO
  3. Create metadata in PostgreSQL
  4. Queue embedding generation task
  ↓
Celery Worker:
  1. Generate embeddings
  2. Store vectors in Qdrant
  3. Update status in PostgreSQL
```

### 3. Audio Transcription Flow
```
User → FastAPI (/api/v1/asr/transcribe)
  ↓
Celery Task (transcribe_audio)
  ↓
Worker:
  1. Get audio from MinIO
  2. Call ASR service (Google Speech/Whisper)
  3. Store transcript in PostgreSQL
  4. Generate embeddings → Qdrant
```

---

## 🌐 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| FastAPI App | `http://localhost:8000` | N/A |
| API Documentation | `http://localhost:8000/docs` | N/A |
| Flower Dashboard | `http://localhost:5555` | `admin:changeme_in_production` |
| MinIO Console | `http://localhost:9001` | `minioadmin:minioadmin` |
| PostgreSQL | `localhost:5433` | `postgres:postgres` |
| Redis | `localhost:6379` | No password |
| Qdrant | `localhost:6333` | No auth |

---

## 🔧 Configuration Files

### Environment Variables (.env)
```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_NAME=shia_chatbot

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=postgresql

# Qdrant
QDRANT_URL=http://localhost:6333

# MinIO
MINIO_ENABLED=true
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Inside Docker Network
Containers use service names instead of localhost:
```bash
DATABASE_HOST=postgres       # NOT localhost
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
MINIO_ENDPOINT=minio:9000
```

---

## 🚀 Quick Commands

### Start All Services
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker logs -f shia-chatbot-celery-worker
docker logs -f shia-chatbot-postgres
```

### Check Service Health
```bash
docker-compose ps
docker ps --filter "name=shia-chatbot"
```

### Start FastAPI Locally
```bash
poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Migrations
```bash
poetry run alembic upgrade head
```

### Monitor Celery Tasks
Open browser: `http://localhost:5555`

### Access MinIO Storage
Open browser: `http://localhost:9001`

---

## 📈 Monitoring & Debugging

### PostgreSQL
```bash
# Connect to database
docker exec -it shia-chatbot-postgres psql -U postgres -d shia_chatbot

# Check tables
\dt

# Query users
SELECT * FROM users LIMIT 10;
```

### Redis
```bash
# Connect to Redis CLI
docker exec -it shia-chatbot-redis redis-cli

# Monitor commands
MONITOR

# Check keys
KEYS *

# Get cache stats
INFO stats
```

### Qdrant
```bash
# Check collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/islamic_knowledge
```

### MinIO
```bash
# List buckets
docker exec shia-chatbot-minio mc ls local/

# Check bucket size
docker exec shia-chatbot-minio mc du local/dev-wisqu-images
```

---

## 🔐 Security Notes

### Development (Current)
- ⚠️ Default credentials in use
- ⚠️ No authentication on some services
- ⚠️ Services exposed to localhost only

### Production Recommendations
1. Change all default passwords
2. Enable TLS/SSL for all services
3. Use secrets management (Docker secrets, Vault)
4. Enable authentication on Qdrant, Redis
5. Use private Docker network
6. Implement firewall rules
7. Enable audit logging

---

## 🧪 Testing Communication

### Test PostgreSQL Connection
```bash
curl http://localhost:8000/api/v1/health/
```

### Test Redis Connection
```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # Should return True
```

### Test Qdrant Connection
```bash
curl http://localhost:6333/healthz
```

### Test MinIO Connection
```bash
curl http://localhost:9000/minio/health/live
```

### Test Celery Workers
```bash
# Submit a test task via API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "conversation_id": null}'

# Check task status in Flower
open http://localhost:5555
```

---

## 📚 Additional Documentation

- **API Documentation**: http://localhost:8000/docs
- **Langfuse Setup**: docs/LANGFUSE_SETUP.md
- **Docker Compose**: docker-compose.yml
- **Environment Config**: .env
- **Database Migrations**: alembic/versions/

---

Generated: 2025-11-08
Last Updated: When services were started
