"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    asr,
    auth,
    documents,
    external_api,
    images,
    leaderboard,
    presets,
    subscriptions,
    support,
    tools,
)

api_router = APIRouter()

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
api_router.include_router(images.router, prefix="/images", tags=["Image Generation"])
api_router.include_router(presets.router, prefix="/presets", tags=["Model Presets"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])

# TODO: Add more routers as they are implemented
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
