# Queue Management System - Complete Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Phase 1: COMPLETED ✅](#phase-1-completed-)
- [Dev Mode Setup](#dev-mode-setup)
- [Testing the System](#testing-the-system)
- [Phase 2: Docker Deployment](#phase-2-docker-deployment-coming-next)
- [API Usage](#api-usage)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

Your Shia Islamic Chatbot now has a **production-grade distributed queue management system** powered by Celery + Redis + PostgreSQL.

### What Was Implemented (Phase 1):

✅ **3-Tier Priority Queue System**
- **High Priority** (User-facing): Chat, Images, ASR, Web Search
- **Medium Priority** (Background): Embeddings, File Uploads, Promotions
- **Low Priority** (Fire-and-forget): Emails, Cleanup, Observability

✅ **Environment-Aware Configuration**
- Auto-configures for dev/stage/prod environments
- Separate Redis DBs per environment (dev: 0-2, stage: 6-8, prod: 9-11)
- Environment-specific task routing

✅ **Progress Tracking & Job Status API**
- Real-time progress updates
- RESTful endpoints to check task status
- Cancel running tasks
- List active jobs

✅ **Auto-Retry & Error Handling**
- Exponential backoff for transient errors
- Configurable max retries per task type
- Graceful degradation

✅ **Scheduled Tasks (Celery Beat)**
- Daily file cleanup (2 AM)
- Hourly task result cleanup
- Weekly leaderboard recalculation

---

## Phase 1: COMPLETED ✅

### Files Created:

**Core Infrastructure:**
- `src/app/core/celery_app.py` - Celery application with queue routing
- `src/app/core/config.py` - Updated with Celery configuration

**High Priority Tasks:**
- `src/app/tasks/chat.py` - Async chat processing
- `src/app/tasks/images.py` - Image generation
- `src/app/tasks/asr.py` - Audio transcription
- `src/app/tasks/web_search.py` - Web search

**Medium/Low Priority Tasks:**
- `src/app/tasks/email.py` - Email sending
- `src/app/tasks/cleanup.py` - File & task cleanup
- `src/app/tasks/embeddings.py` - Batch embeddings (stub)
- `src/app/tasks/storage.py` - File uploads (stub)
- `src/app/tasks/promotion.py` - Environment promotion (stub)
- `src/app/tasks/dataset.py` - Dataset creation (stub)
- `src/app/tasks/langfuse_tasks.py` - Observability (stub)
- `src/app/tasks/leaderboard.py` - Rankings (stub)

**API:**
- `src/app/api/v1/jobs.py` - Job status endpoints

### Dependencies Added:
```toml
celery = {extras = ["redis"], version = "^5.4.0"}
flower = "^2.0.0"
celery-progress = "^0.4.0"
kombu = "^5.4.0"
```

---

## Dev Mode Setup

### Option 1: Pure Local (No Docker) - RECOMMENDED FOR DEVELOPMENT

**Prerequisites:**
1. PostgreSQL running on port 5433
2. Redis running on port 6379
3. Python 3.11+ with Poetry

**Step 1: Install Dependencies**
```bash
poetry install
```

**Step 2: Set Environment Variables**
```bash
# Create .env file
cat > .env << 'EOF'
ENVIRONMENT=dev
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_NAME=shia_chatbot
REDIS_URL=redis://localhost:6379/0
EOF
```

**Step 3: Run FastAPI App** (Terminal 1)
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 4: Run Celery Worker** (Terminal 2)
```bash
poetry run celery -A app.core.celery_app worker --loglevel=info --queues=high_priority,medium_priority,low_priority --concurrency=4
```

**Step 5: Run Celery Beat** (Terminal 3 - Optional)
```bash
poetry run celery -A app.core.celery_app beat --loglevel=info
```

**Step 6: Run Flower Monitor** (Terminal 4 - Optional)
```bash
poetry run celery -A app.core.celery_app flower --port=5555
```

Access:
- **FastAPI**: http://localhost:8000
- **Flower**: http://localhost:5555
- **API Docs**: http://localhost:8000/docs

---

### Option 2: Docker Compose (Coming in Phase 2)

Full production-ready Docker setup with:
- 3 FastAPI replicas
- Multiple Celery workers
- NGINX load balancer
- Flower monitoring
- Auto-scaling

---

## Testing the System

### Test 1: Submit Chat Task

```bash
# Submit chat message (returns job_id immediately)
curl -X POST "http://localhost:8000/api/v1/jobs/test-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "conversation_id": "test-conv-456",
    "message_content": "What is Shia Islam?"
  }'

# Response:
{
  "job_id": "abc123-def456",
  "status": "PENDING",
  "message": "Task submitted to queue"
}
```

### Test 2: Check Job Status

```bash
# Poll for status
curl "http://localhost:8000/api/v1/jobs/abc123-def456"

# Response (STARTED):
{
  "job_id": "abc123-def456",
  "status": "STARTED",
  "progress": 50,
  "status_message": "Processing chat message...",
  "result": null
}

# Response (SUCCESS):
{
  "job_id": "abc123-def456",
  "status": "SUCCESS",
  "progress": 100,
  "status_message": "Task completed successfully",
  "result": {
    "response": "Shia Islam is...",
    "tokens": 1234,
    "cost": 0.002
  }
}
```

### Test 3: Image Generation Task

```bash
# Submit image generation
curl -X POST "http://localhost:8000/api/v1/images/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful mosque at sunset",
    "user_id": "test-user-123"
  }'

# Returns job_id, then poll /jobs/{job_id}
```

### Test 4: List Active Jobs

```bash
curl "http://localhost:8000/api/v1/jobs/"

# Response:
{
  "jobs": ["abc123", "def456", "ghi789"],
  "count": 3
}
```

### Test 5: Cancel Job

```bash
curl -X DELETE "http://localhost:8000/api/v1/jobs/abc123-def456"

# Response: 204 No Content
```

---

## Phase 2: Docker Deployment (COMING NEXT)

### What's Included:

1. **Multi-Replica FastAPI** (3 replicas for load balancing)
2. **NGINX Load Balancer** (Round-robin with health checks)
3. **Dedicated Celery Workers**
   - 2× High Priority Workers (concurrency: 10)
   - 1× Medium Priority Worker (concurrency: 5)
   - 1× Low Priority Worker (concurrency: 20)
4. **Celery Beat** (Scheduler for cron jobs)
5. **Flower** (Web UI for monitoring)
6. **Resource Limits** (Optimized for 16GB RAM / 4 cores)
7. **SSL Support** (Let's Encrypt or custom certs)
8. **Prometheus Metrics** (Integration with existing Grafana)

### Safety Measures:

✅ **Unique Container Names** (shia-chatbot-*)
✅ **Separate Network** (chatbot-network)
✅ **Unique Ports** (No conflicts with existing containers)
✅ **No Impact on Production** (Isolated from wisqu.ai containers)

---

## API Usage

### Endpoint: Submit Async Task

Any endpoint that returns a `job_id` is now async:

```python
# Example: Chat endpoint
@router.post("/chat/")
async def chat(message: str, user_id: UUID, conversation_id: UUID):
    # Submit to Celery queue
    from app.tasks.chat import process_chat_message

    task = process_chat_message.delay(
        user_id=str(user_id),
        conversation_id=str(conversation_id),
        message_content=message,
    )

    # Return job_id immediately
    return {
        "job_id": task.id,
        "status": "PENDING",
        "message": "Your request is being processed. Poll /jobs/{job_id} for status."
    }
```

### Endpoint: Check Job Status

```python
# Client-side polling (every 2 seconds)
async function pollJobStatus(jobId) {
    while (true) {
        const response = await fetch(`/api/v1/jobs/${jobId}`);
        const data = await response.json();

        if (data.status === 'SUCCESS') {
            return data.result;
        } else if (data.status === 'FAILURE') {
            throw new Error(data.error);
        }

        // Show progress to user
        updateProgressBar(data.progress);

        // Wait 2 seconds before next poll
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
}
```

---

## Monitoring

### Flower Dashboard

Access at: `http://localhost:5555`

**Credentials:**
- Username: `admin`
- Password: Set via `FLOWER_PASSWORD` env var

**Features:**
- Real-time worker status
- Task success/failure rates
- Queue lengths
- Task execution times
- Memory usage
- Worker restarts

### Celery Logs

```bash
# Worker logs
tail -f logs/celery-worker.log

# Beat logs
tail -f logs/celery-beat.log
```

### Task Signals

All tasks emit structured logs:
- `task_started` - When task begins
- `task_completed` - When task succeeds
- `task_failed` - When task fails
- `task_retrying` - When task retries

---

## Troubleshooting

### Problem: Tasks stuck in PENDING

**Cause:** Celery worker not running or can't connect to Redis

**Solution:**
```bash
# Check Redis connection
redis-cli -h localhost -p 6379 ping

# Check Celery worker logs
poetry run celery -A app.core.celery_app inspect active

# Restart worker
poetry run celery -A app.core.celery_app worker --loglevel=debug
```

### Problem: Tasks failing with DB connection error

**Cause:** PostgreSQL not accessible or wrong credentials

**Solution:**
```bash
# Check PostgreSQL connection
psql -h localhost -p 5433 -U postgres -d shia_chatbot

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

### Problem: Worker consuming too much memory

**Cause:** Memory leaks or large task payloads

**Solution:**
```bash
# Restart worker after 100 tasks (instead of 1000)
poetry run celery -A app.core.celery_app worker --max-tasks-per-child=100
```

### Problem: Can't see task progress

**Cause:** Task not updating state

**Solution:**
```python
# In task code, add progress updates:
self.update_state(
    state='STARTED',
    meta={'progress': 50, 'status': 'Processing...'}
)
```

---

## Resource Usage (16GB RAM, 4 cores)

### Current Allocation:

| Component | RAM | CPU | Priority |
|-----------|-----|-----|----------|
| FastAPI App (3 replicas) | 3GB | 1.5 cores | High |
| Celery High Workers (2×) | 2GB | 1.0 cores | High |
| Celery Medium Worker (1×) | 1GB | 0.5 cores | Medium |
| Celery Low Worker (1×) | 0.5GB | 0.25 cores | Low |
| PostgreSQL | 2GB | 0.5 cores | Critical |
| Redis | 1GB | 0.25 cores | Critical |
| Qdrant | 2GB | 0.5 cores | High |
| **Total** | **11.5GB** | **4.5 cores** | |
| **Reserved for OS** | **4.5GB** | **N/A** | |

**Note:** With existing production containers, you may need to reduce replicas to 2 FastAPI + 1 high-priority worker initially.

---

## Next Steps

1. ✅ **Phase 1 Complete** - Core queue system implemented
2. 🔄 **Phase 2 Next** - Docker configurations and deployment
3. ⏳ **Phase 3 Future** - Prometheus integration and advanced monitoring

**Ready for Phase 2?** Let me know and I'll create the complete Docker setup with safety measures for your production environment!
