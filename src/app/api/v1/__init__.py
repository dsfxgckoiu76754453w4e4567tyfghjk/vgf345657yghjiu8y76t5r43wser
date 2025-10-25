"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, documents, leaderboard, support, tools

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents & RAG"])
api_router.include_router(tools.router, prefix="/tools", tags=["Specialized Tools"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Moderation"])
api_router.include_router(support.router, prefix="/support", tags=["Support Tickets"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboards"])

# TODO: Add more routers as they are implemented
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
