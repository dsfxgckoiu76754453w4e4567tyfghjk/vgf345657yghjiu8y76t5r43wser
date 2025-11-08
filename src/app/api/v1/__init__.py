"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    asr,
    auth,
    chat,
    conversations,
    documents,
    external_api,
    feedback,
    health,
    images,
    jobs,
    leaderboard,
    presets,
    storage,
    subscriptions,
    support,
    tools,
)

api_router = APIRouter()

# Health checks (no auth required)
api_router.include_router(health.router, prefix="/health", tags=["Health & Monitoring"])

# Background job status (no auth required for now - can add auth later)
api_router.include_router(jobs.router, prefix="/jobs", tags=["Background Jobs"])

# Include all v1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents & RAG"])
api_router.include_router(tools.router, prefix="/tools", tags=["Specialized Tools"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Moderation"])
api_router.include_router(support.router, prefix="/support", tags=["Support Tickets"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboards"])
api_router.include_router(external_api.router, prefix="/external-api", tags=["External API Integration"])
api_router.include_router(asr.router, prefix="/asr", tags=["Speech-to-Text (ASR)"])

# OpenRouter Advanced Features
api_router.include_router(chat.router, prefix="/chat", tags=["Chat with Advanced Features"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversation Management"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["User Feedback & Scoring"])
api_router.include_router(images.router, prefix="/images", tags=["Image Generation"])
api_router.include_router(storage.router, prefix="/storage", tags=["File Storage (MinIO)"])
api_router.include_router(presets.router, prefix="/presets", tags=["Model Presets"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics (Admin)"])

# TODO: Add more routers as they are implemented
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
