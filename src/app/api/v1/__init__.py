"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# TODO: Add more routers as they are implemented
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
# api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
