"""Pydantic schemas for external API and ASR."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# External API Client Schemas
# ============================================================================


class RegisterClientRequest(BaseModel):
    """Request schema for registering external API client."""

    app_name: str = Field(..., min_length=3, max_length=100, description="Application name")
    app_description: str = Field(
        ..., min_length=10, max_length=500, description="Application description"
    )
    callback_url: Optional[HttpUrl] = Field(default=None, description="OAuth callback URL")
    allowed_origins: Optional[list[str]] = Field(
        default=None, description="CORS allowed origins"
    )
    rate_limit_per_minute: int = Field(
        default=60, ge=1, le=1000, description="Requests per minute"
    )
    rate_limit_per_day: int = Field(
        default=10000, ge=1, le=1000000, description="Requests per day"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "app_name": "My Islamic App",
                "app_description": "Mobile app for Islamic education",
                "callback_url": "https://myapp.com/oauth/callback",
                "allowed_origins": ["https://myapp.com", "https://app.myapp.com"],
                "rate_limit_per_minute": 60,
                "rate_limit_per_day": 10000,
            }
        }


class RegisterClientResponse(BaseModel):
    """Response schema for client registration."""

    client_id: str
    app_name: str
    api_key: str  # ONLY returned once
    api_secret: str  # ONLY returned once
    rate_limit_per_minute: int
    rate_limit_per_day: int
    created_at: str
    warning: str


class ClientListItem(BaseModel):
    """Single client in list."""

    client_id: str
    app_name: str
    app_description: str
    callback_url: Optional[str]
    allowed_origins: list[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    created_at: str
    last_used_at: Optional[str]


class ClientDetailsResponse(BaseModel):
    """Detailed client information with usage statistics."""

    client_id: str
    app_name: str
    app_description: str
    callback_url: Optional[str]
    allowed_origins: list[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    created_at: str
    last_used_at: Optional[str]
    usage_statistics: dict


class UpdateClientRequest(BaseModel):
    """Request schema for updating client."""

    app_name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    app_description: Optional[str] = Field(default=None, min_length=10, max_length=500)
    callback_url: Optional[HttpUrl] = None
    allowed_origins: Optional[list[str]] = None
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, le=1000)
    rate_limit_per_day: Optional[int] = Field(default=None, ge=1, le=1000000)

    class Config:
        json_schema_extra = {
            "example": {
                "app_name": "My Islamic App v2",
                "rate_limit_per_minute": 100,
            }
        }


class UpdateClientResponse(BaseModel):
    """Response schema for client update."""

    client_id: str
    app_name: str
    app_description: str
    updated_at: str


class RegenerateSecretResponse(BaseModel):
    """Response schema for secret regeneration."""

    client_id: str
    api_secret: str  # ONLY returned once
    regenerated_at: str
    warning: str


class ClientStatusResponse(BaseModel):
    """Response schema for activate/deactivate."""

    client_id: str
    app_name: str
    status: str
    activated_at: Optional[str] = None
    deactivated_at: Optional[str] = None


class UsageStatisticsResponse(BaseModel):
    """Response schema for usage statistics."""

    client_id: str
    period_days: int
    total_requests: int
    average_response_time_ms: float
    error_count: int
    error_rate_percent: float
    requests_per_day: float


# ============================================================================
# ASR (Speech-to-Text) Schemas
# ============================================================================


class TranscribeAudioRequest(BaseModel):
    """Request schema for audio transcription."""

    language: str = Field(
        default="fa", description="Language code (fa, en, ar, ur, tr, id, ms)"
    )
    model: Optional[str] = Field(default=None, description="Specific model (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "language": "fa",
                "model": "whisper-1",
            }
        }


class TranscribeAudioResponse(BaseModel):
    """Response schema for audio transcription."""

    text: str
    language: str
    duration: Optional[float] = None
    provider: str
    model: Optional[str] = None
    is_translation: bool = False


class TranslateAudioRequest(BaseModel):
    """Request schema for audio translation to English."""

    # No parameters needed - always translates to English


class SupportedLanguage(BaseModel):
    """Supported language information."""

    code: str
    name: str
    native_name: str


class SupportedLanguagesResponse(BaseModel):
    """Response schema for supported languages."""

    languages: list[SupportedLanguage]
    provider: str


class AudioValidationResponse(BaseModel):
    """Response schema for audio validation."""

    is_valid: bool
    size_mb: float
    max_size_mb: int
    allowed_formats: list[str]
    error: Optional[str]
