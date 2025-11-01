"""Authentication API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    LogoutResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    ResendOTPRequest,
    ResendOTPResponse,
    TokenResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter()
logger = get_logger(__name__)


def _get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserRegisterResponse:
    """
    Register a new user with email and password.

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: Optional user's full name
    - **marja_preference**: Optional preferred Marja
    - **preferred_language**: Preferred language (default: fa)

    Returns user ID and sends verification email.
    """
    auth_service = AuthService(db)

    try:
        user, otp_code = await auth_service.register_user(
            email=request_data.email,
            password=request_data.password,
            full_name=request_data.full_name,
            marja_preference=request_data.marja_preference,
            preferred_language=request_data.preferred_language,
        )

        # TODO: Send email with OTP code
        logger.info("registration_otp_generated", email=request_data.email, otp_code=otp_code)

        return UserRegisterResponse(
            message="Registration successful. Please check your email for verification code.",
            user_id=user.id,
            email=user.email or "",
            requires_verification=True,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request_data: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserLoginResponse:
    """
    Login with email and password.

    - **email**: Registered email address
    - **password**: User password

    Returns JWT tokens and user info.
    """
    auth_service = AuthService(db)
    ip_address, user_agent = _get_client_info(request)

    try:
        user, access_token, refresh_token = await auth_service.login_user(
            email=request_data.email,
            password=request_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return UserLoginResponse(
            message="Login successful",
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800,  # 30 minutes
            ),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailVerificationResponse:
    """
    Verify email with OTP code.

    - **email**: Email address to verify
    - **otp_code**: 6-digit OTP code from email

    Marks email as verified.
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.verify_email(
            email=request_data.email,
            otp_code=request_data.otp_code,
        )

        return EmailVerificationResponse(
            message="Email verified successfully",
            email=user.email or "",
            is_verified=True,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/resend-otp", response_model=ResendOTPResponse)
async def resend_otp(
    request_data: ResendOTPRequest,
    db: AsyncSession = Depends(get_db),
) -> ResendOTPResponse:
    """
    Resend OTP code.

    - **email**: Email address
    - **purpose**: email_verification or password_reset

    Sends a new OTP code to the email.
    """
    auth_service = AuthService(db)

    try:
        expires_at = await auth_service.resend_otp(
            email=request_data.email,
            purpose=request_data.purpose,
        )

        return ResendOTPResponse(
            message="OTP code sent successfully",
            email=request_data.email,
            expires_at=expires_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/password-reset", response_model=PasswordResetResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetResponse:
    """
    Request password reset (step 1).

    - **email**: Registered email address

    Sends OTP code for password reset.
    """
    auth_service = AuthService(db)

    try:
        await auth_service.resend_otp(
            email=request_data.email,
            purpose="password_reset",
        )

        return PasswordResetResponse(
            message="Password reset code sent to your email",
            email=request_data.email,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
async def confirm_password_reset(
    request_data: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetConfirmResponse:
    """
    Confirm password reset with OTP (step 2).

    - **email**: Email address
    - **otp_code**: 6-digit OTP code from email
    - **new_password**: New password (minimum 8 characters)

    Resets password if OTP is valid.
    """
    # TODO: Implement password reset confirmation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset confirmation not yet implemented",
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutResponse:
    """
    Logout current user.

    Revokes current session.
    """
    # TODO: Implement session revocation
    logger.info("user_logged_out", user_id=str(current_user.id))

    return LogoutResponse(
        message="Logged out successfully",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid JWT token.
    """
    return UserResponse.model_validate(current_user)
