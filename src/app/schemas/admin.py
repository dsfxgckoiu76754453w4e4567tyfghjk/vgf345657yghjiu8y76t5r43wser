"""Pydantic schemas for admin, support tickets, and leaderboards."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Admin API Key Schemas
# ============================================================================


class CreateAPIKeyRequest(BaseModel):
    """Request schema for creating admin API key."""

    key_name: str = Field(..., min_length=3, max_length=100, description="Descriptive key name")
    permissions: list[str] = Field(..., min_items=1, description="List of permissions")
    expires_in_days: Optional[int] = Field(
        default=None, ge=1, le=365, description="Expiration in days (None = never)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "key_name": "Production Admin Key",
                "permissions": ["user:read", "user:write", "content:moderate"],
                "expires_in_days": 90,
            }
        }


class APIKeyResponse(BaseModel):
    """Response schema for API key."""

    api_key_id: str
    key_name: str
    api_key: Optional[str] = None  # Only returned on creation
    permissions: list[str]
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool
    warning: Optional[str] = None


class RevokeAPIKeyResponse(BaseModel):
    """Response schema for revoking API key."""

    api_key_id: str
    key_name: str
    status: str
    revoked_at: str


# ============================================================================
# User Management Schemas
# ============================================================================


class UserListResponse(BaseModel):
    """Response schema for user list."""

    user_id: str
    email: EmailStr
    display_name: Optional[str]
    role: str
    is_verified: bool
    is_banned: bool
    created_at: str
    last_login: Optional[str]


class UserListPaginatedResponse(BaseModel):
    """Paginated user list response."""

    users: list[UserListResponse]
    pagination: dict


class BanUserRequest(BaseModel):
    """Request schema for banning a user."""

    reason: str = Field(..., min_length=10, max_length=500, description="Reason for ban")
    ban_duration_days: Optional[int] = Field(
        default=None, ge=1, description="Duration in days (None = permanent)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Violation of community guidelines - spam content",
                "ban_duration_days": 7,
            }
        }


class BanUserResponse(BaseModel):
    """Response schema for ban action."""

    user_id: str
    email: EmailStr
    status: str
    reason: str
    ban_expires_at: Optional[str]
    banned_at: str


class UnbanUserResponse(BaseModel):
    """Response schema for unban action."""

    user_id: str
    email: EmailStr
    status: str
    unbanned_at: str


class ChangeUserRoleRequest(BaseModel):
    """Request schema for changing user role."""

    new_role: Literal["user", "moderator", "admin", "super_admin"]

    class Config:
        json_schema_extra = {"example": {"new_role": "moderator"}}


class ChangeUserRoleResponse(BaseModel):
    """Response schema for role change."""

    user_id: str
    email: EmailStr
    old_role: str
    new_role: str
    changed_at: str


# ============================================================================
# Content Moderation Schemas
# ============================================================================


class PendingContentItem(BaseModel):
    """Pending content item."""

    content_id: str
    content_type: str
    title: str
    uploaded_by: Optional[str]
    created_at: str
    moderation_status: str


class ModerateContentRequest(BaseModel):
    """Request schema for moderating content."""

    action: Literal["approve", "reject"]
    reason: Optional[str] = Field(default=None, description="Required for reject action")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "reject",
                "reason": "Content does not meet quality standards",
            }
        }


class ModerateContentResponse(BaseModel):
    """Response schema for content moderation."""

    content_id: str
    content_type: str
    action: str
    reason: Optional[str]
    moderated_by: str
    moderated_at: str


# ============================================================================
# System Statistics Schemas
# ============================================================================


class SystemStatisticsResponse(BaseModel):
    """Response schema for system statistics."""

    users: dict
    content: dict
    chat: dict
    generated_at: str


# ============================================================================
# Support Ticket Schemas
# ============================================================================


class CreateTicketRequest(BaseModel):
    """Request schema for creating support ticket."""

    subject: str = Field(..., min_length=5, max_length=200, description="Ticket subject")
    description: str = Field(
        ..., min_length=20, max_length=2000, description="Detailed description"
    )
    category: Literal["technical", "content", "account", "billing", "other"] = Field(
        default="other"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="medium")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Unable to upload documents",
                "description": "I'm getting an error when trying to upload PDF documents. The error message says...",
                "category": "technical",
                "priority": "medium",
            }
        }


class TicketResponse(BaseModel):
    """Response schema for ticket."""

    ticket_id: str
    subject: str
    description: Optional[str] = None
    category: str
    priority: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    resolved_at: Optional[str] = None


class TicketListResponse(BaseModel):
    """Paginated ticket list response."""

    tickets: list[TicketResponse]
    pagination: dict


class TicketDetailResponse(BaseModel):
    """Detailed ticket response with responses."""

    ticket_id: str
    user_id: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[str]
    resolution: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    closed_at: Optional[str]
    responses: list[dict]


class AddTicketResponseRequest(BaseModel):
    """Request schema for adding ticket response."""

    message: str = Field(..., min_length=10, max_length=2000, description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Thank you for reporting this issue. We are investigating and will update you soon."
            }
        }


class AddTicketResponseResponse(BaseModel):
    """Response schema for ticket response."""

    response_id: str
    ticket_id: str
    message: str
    is_staff_response: bool
    created_at: str


class AssignTicketRequest(BaseModel):
    """Request schema for assigning ticket."""

    assign_to_admin_id: UUID

    class Config:
        json_schema_extra = {"example": {"assign_to_admin_id": "123e4567-e89b-12d3-a456-426614174000"}}


class AssignTicketResponse(BaseModel):
    """Response schema for ticket assignment."""

    ticket_id: str
    assigned_to: str
    status: str
    assigned_at: str


class UpdateTicketStatusRequest(BaseModel):
    """Request schema for updating ticket status."""

    new_status: Literal["open", "in_progress", "resolved", "closed"]
    resolution: Optional[str] = Field(
        default=None, description="Resolution message (required for resolved/closed)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "new_status": "resolved",
                "resolution": "Issue fixed. The document upload feature is now working correctly.",
            }
        }


class UpdateTicketStatusResponse(BaseModel):
    """Response schema for ticket status update."""

    ticket_id: str
    status: str
    resolution: Optional[str]
    resolved_at: Optional[str]
    closed_at: Optional[str]
    updated_at: str


class TicketStatisticsResponse(BaseModel):
    """Response schema for ticket statistics."""

    total: int
    by_status: dict
    resolution_rate: float


# ============================================================================
# Leaderboard Schemas
# ============================================================================


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""

    rank: int
    user_id: str
    display_name: str
    email: EmailStr
    upload_count: Optional[int] = None
    message_count: Optional[int] = None
    conversation_count: Optional[int] = None
    total_score: Optional[int] = None
    breakdown: Optional[dict] = None


class LeaderboardResponse(BaseModel):
    """Response schema for leaderboard."""

    leaderboard: list[LeaderboardEntry]
    timeframe: str
    generated_at: str


class UserStatisticsResponse(BaseModel):
    """Response schema for user statistics."""

    user_id: str
    display_name: str
    email: EmailStr
    statistics: dict
    rank: Optional[int]
    member_since: str
