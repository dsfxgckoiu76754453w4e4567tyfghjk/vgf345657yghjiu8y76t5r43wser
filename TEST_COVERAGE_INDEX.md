# Test Coverage Analysis - Complete File Index

## Executive Summary
- **Overall Coverage:** 40% (CRITICAL - ACTION REQUIRED)
- **Services:** 11/31 tested (35.5%)
- **API Endpoints:** 8/18 tested (44.4%)
- **Untested Methods:** 165
- **Untested Routes:** 48

---

## Critical Untested Components

### TIER 1 - CRITICAL (Do Immediately)

#### 1. Document Management & RAG
- **Service Path:** `/src/app/services/document_service.py`
  - `create_document()` - Create and chunk documents
  - `generate_embeddings_for_document()` - Generate vector embeddings
  - `search_similar_chunks()` - Semantic search
  
- **API Path:** `/src/app/api/v1/documents.py`
  - `POST /upload` - Upload document
  - `POST /embeddings/generate` - Generate embeddings
  - `POST /search` - Search documents
  - `GET /qdrant/status` - Check status

#### 2. Main Chat Feature
- **API Path:** `/src/app/api/v1/chat.py`
  - `POST /` - `send_message()` - Main chat endpoint
  - `POST /structured` - `send_structured_message()` - Structured output
  - `GET /cache-stats/{conversation_id}` - Cache statistics

#### 3. File Storage
- **Service Path:** `/src/app/services/minio_storage_service.py` (15 public methods)
  - `upload_file()` - Upload file to MinIO
  - `download_file()` - Download file from MinIO
  - `delete_file()` - Delete file
  - `get_presigned_url()` - Get signed URL
  - `list_files()` - List bucket files
  - `upload_rag_document()` - Upload for RAG
  - `upload_islamic_audio()` - Upload audio
  - `upload_user_voice_message()` - Voice messages
  - `upload_ticket_attachment()` - Support attachments
  - `upload_generated_image()` - Generated images
  - `health_check()` - Health monitoring
  
- **API Path:** `/src/app/api/v1/storage.py`
  - `POST /upload` - Upload file
  - `GET /{file_id}` - Get file info
  - `DELETE /{file_id}` - Delete file
  - `GET /quota/me` - Storage quota

#### 4. Vector Database (RAG Backbone)
- **Service Path:** `/src/app/services/qdrant_service.py` (9 methods)
  - `ensure_collection_exists()` - Create/verify collection
  - `add_points()` - Add vector points
  - `search()` - Vector similarity search
  - `delete_points()` - Delete vectors
  - `get_points_by_ids()` - Retrieve vectors
  - `copy_points_to_collection()` - Copy data between collections
  - `get_collection_info()` - Collection metadata

#### 5. Email Notifications
- **Service Path:** `/src/app/services/email_service.py` (8 methods)
  - `send_email()` - Base email sending
  - `send_ticket_created_notification()` - Support ticket
  - `send_ticket_response_notification()` - Support response
  - `send_ticket_resolved_notification()` - Support resolved
  - `send_document_approved_notification()` - Document approved
  - `send_document_rejected_notification()` - Document rejected
  - `send_account_ban_notification()` - Account banned
  - `send_account_unban_notification()` - Account reinstated

#### 6. Admin Service
- **Service Path:** `/src/app/services/admin_service.py` (12 methods)
  - `create_api_key()` - Create API keys
  - `list_api_keys()` - List API keys
  - `revoke_api_key()` - Revoke API keys
  - `list_users()` - List all users
  - `ban_user()` - Ban user accounts
  - `unban_user()` - Unban users
  - `change_user_role()` - Change user roles
  - `get_pending_content()` - Get content for moderation
  - `moderate_content()` - Approve/reject content
  - `get_system_statistics()` - System stats

#### 7. Embeddings Service
- **Service Path:** `/src/app/services/embeddings_service.py` (3 methods)
  - `embed_text()` - Embed single text
  - `embed_documents()` - Batch embed documents
  - `estimate_cost()` - Cost estimation

---

## High Priority Untested (TIER 2)

### Services

- **leaderboard_service.py** (6 methods)
  - Leaderboard management
  - *Note: API endpoints ARE tested*

- **support_service.py** (9 methods)
  - Support ticket management
  - *Note: API endpoints ARE tested*

- **image_generation_service.py** (13 methods)
  - Image generation feature
  - Significant business logic

### API Endpoints

- **conversations.py** (6 endpoints)
  - `POST /` - Create conversation
  - `GET /` - List conversations
  - `GET /{conversation_id}` - Get conversation
  - `PATCH /{conversation_id}` - Update conversation
  - `DELETE /{conversation_id}` - Delete conversation
  - `POST /{conversation_id}/generate-title` - Auto-title

- **subscriptions.py** (6 endpoints)
  - `GET /me` - Get current subscription
  - `POST /` - Create subscription
  - `GET /usage` - Get usage stats
  - `POST /cancel` - Cancel subscription
  - `GET /plans` - List plans
  - `GET /plans/{plan_type}` - Get plan details

- **health.py** (5 endpoints)
  - System health checks

---

## Complete Service List

### UNTESTED Services (20)

| Service | Methods | Type | File Path |
|---------|---------|------|-----------|
| admin_service | 12 | Core | `/src/app/services/admin_service.py` |
| ahkam_service | 9 | Feature | `/src/app/services/ahkam_service.py` |
| chonkie_service | 6 | Utility | `/src/app/services/chonkie_service.py` |
| dataset_service | 4 | Feature | `/src/app/services/dataset_service.py` |
| datetime_service | 5 | Utility | `/src/app/services/datetime_service.py` |
| document_service | 4 | Core | `/src/app/services/document_service.py` |
| email_service | 8 | Core | `/src/app/services/email_service.py` |
| embeddings_service | 4 | Core | `/src/app/services/embeddings_service.py` |
| evaluation_service | 10 | Feature | `/src/app/services/evaluation_service.py` |
| hadith_service | 6 | Feature | `/src/app/services/hadith_service.py` |
| image_generation_service | 13 | Feature | `/src/app/services/image_generation_service.py` |
| langgraph_service | 8 | Feature | `/src/app/services/langgraph_service.py` |
| leaderboard_service | 6 | Feature | `/src/app/services/leaderboard_service.py` |
| math_service | 6 | Utility | `/src/app/services/math_service.py` |
| minio_storage_service | 19 | Core | `/src/app/services/minio_storage_service.py` |
| promotion_service | 12 | Feature | `/src/app/services/promotion_service.py` |
| prompt_manager | 7 | Utility | `/src/app/services/prompt_manager.py` |
| qdrant_service | 10 | Core | `/src/app/services/qdrant_service.py` |
| rate_limiter_service | 6 | Utility | `/src/app/services/rate_limiter_service.py` |
| support_service | 9 | Core | `/src/app/services/support_service.py` |

### TESTED Services (11)

| Service | Test File | File Path | Status |
|---------|-----------|-----------|--------|
| asr_service | test_asr_service.py | `/src/app/services/asr_service.py` | TESTED |
| auth | test_auth_service.py | `/src/app/services/auth.py` | TESTED |
| enhanced_chat_service | test_enhanced_chat_service.py | `/src/app/services/enhanced_chat_service.py` | TESTED |
| external_api_client_service | test_external_api_client_service.py | `/src/app/services/external_api_client_service.py` | TESTED |
| intent_detector | test_intent_detector.py | `/src/app/services/intent_detector.py` | TESTED |
| langfuse_service | test_langfuse.py | `/src/app/services/langfuse_service.py` | TESTED |
| openrouter_service | test_openrouter_service.py | `/src/app/services/openrouter_service.py` | TESTED |
| presets_service | test_presets_service.py | `/src/app/services/presets_service.py` | TESTED |
| subscription_service | test_subscription_service.py | `/src/app/services/subscription_service.py` | TESTED |
| tool_orchestration_service | test_tool_orchestration_service.py | `/src/app/services/tool_orchestration_service.py` | TESTED |
| web_search_service | test_web_search_service.py | `/src/app/services/web_search_service.py` | TESTED |

---

## Complete API Endpoint List

### UNTESTED API Endpoints (10)

| Endpoint | Routes | File Path | Status |
|----------|--------|-----------|--------|
| analytics | 6 | `/src/app/api/v1/analytics.py` | NOT TESTED |
| chat | 3 | `/src/app/api/v1/chat.py` | NOT TESTED |
| conversations | 6 | `/src/app/api/v1/conversations.py` | NOT TESTED |
| documents | 4 | `/src/app/api/v1/documents.py` | NOT TESTED |
| feedback | 3 | `/src/app/api/v1/feedback.py` | NOT TESTED |
| health | 5 | `/src/app/api/v1/health.py` | NOT TESTED |
| images | 4 | `/src/app/api/v1/images.py` | NOT TESTED |
| presets | 7 | `/src/app/api/v1/presets.py` | NOT TESTED |
| storage | 4 | `/src/app/api/v1/storage.py` | NOT TESTED |
| subscriptions | 6 | `/src/app/api/v1/subscriptions.py` | NOT TESTED |

### TESTED API Endpoints (8)

| Endpoint | Test File | File Path | Status |
|----------|-----------|-----------|--------|
| admin | test_admin_endpoints.py | `/src/app/api/v1/admin.py` | TESTED |
| asr | test_asr_endpoints.py | `/src/app/api/v1/asr.py` | TESTED |
| auth | test_auth_endpoints.py | `/src/app/api/v1/auth.py` | TESTED |
| external_api | test_external_api_endpoints.py | `/src/app/api/v1/external_api.py` | TESTED |
| jobs | test_jobs_endpoints.py | `/src/app/api/v1/jobs.py` | TESTED |
| leaderboard | test_leaderboard_endpoints.py | `/src/app/api/v1/leaderboard.py` | TESTED |
| support | test_support_endpoints.py | `/src/app/api/v1/support.py` | TESTED |
| tools | test_tools_endpoints.py | `/src/app/api/v1/tools.py` | TESTED |

---

## Test Files Location

```
tests/
├── unit/
│   ├── test_asr_service.py
│   ├── test_celery_tasks.py
│   ├── test_database_config.py
│   ├── test_enhanced_chat_service.py
│   ├── test_environment_promotion.py
│   ├── test_external_api_client_service.py
│   ├── test_health.py
│   ├── test_intent_detector.py
│   ├── test_langfuse.py
│   ├── test_openrouter_service.py
│   ├── test_presets_service.py
│   ├── test_prometheus_metrics.py
│   ├── test_security.py
│   ├── test_subscription_service.py
│   ├── test_tool_orchestration_service.py
│   ├── test_web_search_config.py
│   └── test_web_search_service.py
├── integration/
│   ├── test_admin_endpoints.py
│   ├── test_api_health.py
│   ├── test_asr_endpoints.py
│   ├── test_auth_endpoints.py
│   ├── test_document_endpoints.py
│   ├── test_external_api_endpoints.py
│   ├── test_jobs_endpoints.py
│   ├── test_leaderboard_endpoints.py
│   ├── test_support_endpoints.py
│   └── test_tools_endpoints.py
├── e2e/
├── conftest.py
├── factories.py
└── test_auth_service.py (root)
```

---

## Quick Reference

### Most Critical (Do First)
1. `/src/app/api/v1/chat.py` - Main product feature
2. `/src/app/services/document_service.py` + `/src/app/api/v1/documents.py` - Core RAG
3. `/src/app/services/minio_storage_service.py` + `/src/app/api/v1/storage.py` - File handling
4. `/src/app/services/qdrant_service.py` - Vector DB
5. `/src/app/services/email_service.py` - Notifications

### Estimated Testing Effort
- Tier 1 (Critical): 70-100 tests, 1-2 weeks
- Tier 2 (High): 50-70 tests, 1-2 weeks
- Tier 3 (Medium): 80+ tests, 2-3 weeks
- **Total:** 200+ tests to reach 80% coverage

---

## Additional Resources

- **Detailed Report:** `TEST_COVERAGE_REPORT.md`
- **Quick Summary:** `QUICK_COVERAGE_SUMMARY.txt`
- **This Index:** `TEST_COVERAGE_INDEX.md`

---

Generated: 2025-11-07
