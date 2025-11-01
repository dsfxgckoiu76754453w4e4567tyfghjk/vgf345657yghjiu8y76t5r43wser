"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ==================== Registration ====================


class UserRegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    marja_preference: Optional[str] = Field(None, max_length=100)
    preferred_language: str = Field(default="fa", max_length=10)


class UserRegisterResponse(BaseModel):
    """User registration response."""

    code: str = "AUTH_REGISTRATION_SUCCESS"
    message: str
    user_id: UUID
    email: str
    requires_verification: bool = True


# ==================== Login ====================


class UserLoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserLoginResponse(BaseModel):
    """User login response."""

    code: str = "AUTH_LOGIN_SUCCESS"
    message: str
    user: "UserResponse"
    tokens: TokenResponse


# ==================== Email Verification ====================


class EmailVerificationRequest(BaseModel):
    """Email verification request."""

    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)


class EmailVerificationResponse(BaseModel):
    """Email verification response."""

    code: str = "AUTH_EMAIL_VERIFIED"
    message: str
    email: str
    is_verified: bool = True


class ResendOTPRequest(BaseModel):
    """Resend OTP request."""

    email: EmailStr
    purpose: str = Field(..., pattern="^(email_verification|password_reset)$")


class ResendOTPResponse(BaseModel):
    """Resend OTP response."""

    code: str = "AUTH_OTP_SENT"
    message: str
    email: str
    expires_at: datetime


# ==================== Password Reset ====================


class PasswordResetRequest(BaseModel):
    """Password reset request (step 1: request OTP)."""

    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Password reset response."""

    code: str = "AUTH_PASSWORD_RESET_OTP_SENT"
    message: str
    email: str


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirm request (step 2: submit new password with OTP)."""

    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordResetConfirmResponse(BaseModel):
    """Password reset confirm response."""

    code: str = "AUTH_PASSWORD_RESET_SUCCESS"
    message: str
    email: str


# ==================== Token Refresh ====================


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response."""

    code: str = "AUTH_TOKEN_REFRESHED"
    message: str
    tokens: TokenResponse


# ==================== Google OAuth ====================


class GoogleOAuthRequest(BaseModel):
    """Google OAuth login request."""

    id_token: str  # Google ID token from frontend
    access_token: Optional[str] = None  # Google access token (optional)


class GoogleOAuthResponse(BaseModel):
    """Google OAuth response."""

    code: str = "AUTH_OAUTH_SUCCESS"
    message: str
    user: "UserResponse"
    tokens: TokenResponse
    is_new_user: bool = False


# ==================== Logout ====================


class LogoutResponse(BaseModel):
    """Logout response."""

    code: str = "AUTH_LOGOUT_SUCCESS"
    message: str


# ==================== User Response (for auth endpoints) ====================


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


# Forward references
UserLoginResponse.model_rebuild()
GoogleOAuthResponse.model_rebuild()
