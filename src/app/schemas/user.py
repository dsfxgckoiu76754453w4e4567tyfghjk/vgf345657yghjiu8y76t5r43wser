"""Pydantic schemas for user management."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    email: Optional[str]
    full_name: Optional[str]
    profile_picture_url: Optional[str]
    marja_preference: Optional[str]
    preferred_language: str
    is_email_verified: bool
    is_active: bool
    account_type: str
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """User update request."""

    full_name: Optional[str] = Field(None, max_length=255)
    marja_preference: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=10)
    profile_picture_url: Optional[str] = Field(None, max_length=500)


class UserUpdateResponse(BaseModel):
    """User update response."""

    code: str = "USER_UPDATE_SUCCESS"
    message: str
    user: UserResponse


class UserSettingsResponse(BaseModel):
    """User settings response."""

    user_id: UUID
    theme: str
    font_size: str
    default_chat_mode: str
    auto_play_quranic_audio: bool
    email_notifications_enabled: bool
    push_notifications_enabled: bool
    allow_data_for_training: bool
    show_in_leaderboard: bool
    rate_limit_tier: str

    model_config = {"from_attributes": True}


class UserSettingsUpdateRequest(BaseModel):
    """User settings update request."""

    theme: Optional[str] = Field(None, pattern="^(light|dark|auto)$")
    font_size: Optional[str] = Field(None, pattern="^(small|medium|large)$")
    default_chat_mode: Optional[str] = None
    auto_play_quranic_audio: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    push_notifications_enabled: Optional[bool] = None
    allow_data_for_training: Optional[bool] = None
    show_in_leaderboard: Optional[bool] = None


class UserSettingsUpdateResponse(BaseModel):
    """User settings update response."""

    code: str = "USER_SETTINGS_UPDATE_SUCCESS"
    message: str
    settings: UserSettingsResponse
