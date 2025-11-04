"""Authentication service with business logic."""

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import LinkedAuthProvider, OTPCode, User, UserSession, UserSettings

logger = get_logger(__name__)


class AuthService:
    """Authentication service for user registration, login, and verification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        marja_preference: Optional[str] = None,
        preferred_language: str = "fa",
    ) -> tuple[User, str]:
        """
        Register a new user with email and password.

        Args:
            email: User email
            password: Plain password
            full_name: User's full name
            marja_preference: User's preferred Marja
            preferred_language: User's preferred language

        Returns:
            tuple: (User, OTP code)

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("AUTH_EMAIL_ALREADY_EXISTS")

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            marja_preference=marja_preference,
            preferred_language=preferred_language,
            account_type="free",
            is_email_verified=False,
            is_active=True,
        )

        self.db.add(user)
        await self.db.flush()  # Get user ID

        # Create linked auth provider for email
        linked_provider = LinkedAuthProvider(
            user_id=user.id,
            provider_type="email",
            provider_email=email,
            is_primary=True,
            is_verified=False,
        )
        self.db.add(linked_provider)

        # Create user settings
        settings = UserSettings(user_id=user.id)
        self.db.add(settings)

        # Generate OTP for email verification
        otp_code = self._generate_otp()
        await self._create_otp(email, otp_code, "email_verification", user.id)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info("user_registered", user_id=str(user.id), email=email)

        return user, otp_code

    async def login_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[User, str, str]:
        """
        Login user with email and password.

        Args:
            email: User email
            password: Plain password
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            tuple: (User, access_token, refresh_token)

        Raises:
            ValueError: If credentials are invalid
        """
        # Find user
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise ValueError("AUTH_INVALID_CREDENTIALS")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise ValueError("AUTH_INVALID_CREDENTIALS")

        if not user.is_active:
            raise ValueError("AUTH_USER_INACTIVE")

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True,
        )
        self.db.add(session)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info("user_logged_in", user_id=str(user.id), email=email)

        return user, access_token, refresh_token

    async def verify_email(self, email: str, otp_code: str) -> User:
        """
        Verify user email with OTP code.

        Args:
            email: User email
            otp_code: OTP code

        Returns:
            User: Verified user

        Raises:
            ValueError: If OTP is invalid or expired
        """
        # Find OTP
        result = await self.db.execute(
            select(OTPCode)
            .where(OTPCode.email == email)
            .where(OTPCode.otp_code == otp_code)
            .where(OTPCode.purpose == "email_verification")
            .where(OTPCode.is_used == False)
            .where(OTPCode.expires_at > datetime.now(timezone.utc))
            .order_by(OTPCode.created_at.desc())
        )
        otp = result.scalar_one_or_none()

        if not otp:
            raise ValueError("AUTH_INVALID_OTP")

        # Check attempts
        if otp.attempts_count >= otp.max_attempts:
            raise ValueError("AUTH_OTP_MAX_ATTEMPTS_EXCEEDED")

        # Mark OTP as used
        otp.is_used = True
        otp.used_at = datetime.now(timezone.utc)

        # Find and verify user
        user_result = await self.db.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("AUTH_USER_NOT_FOUND")

        user.is_email_verified = True

        # Update linked provider
        provider_result = await self.db.execute(
            select(LinkedAuthProvider)
            .where(LinkedAuthProvider.user_id == user.id)
            .where(LinkedAuthProvider.provider_type == "email")
        )
        provider = provider_result.scalar_one_or_none()
        if provider:
            provider.is_verified = True

        await self.db.commit()
        await self.db.refresh(user)

        logger.info("email_verified", user_id=str(user.id), email=email)

        return user

    async def resend_otp(self, email: str, purpose: str) -> datetime:
        """
        Resend OTP code.

        Args:
            email: User email
            purpose: OTP purpose (email_verification or password_reset)

        Returns:
            datetime: OTP expiration time

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("AUTH_USER_NOT_FOUND")

        # Generate new OTP
        otp_code = self._generate_otp()
        expires_at = await self._create_otp(email, otp_code, purpose, user.id)

        # TODO: Send email with OTP code
        logger.info("otp_resent", email=email, purpose=purpose, otp_code=otp_code)

        return expires_at

    def _generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code."""
        return "".join(random.choices(string.digits, k=length))

    async def _create_otp(
        self,
        email: str,
        otp_code: str,
        purpose: str,
        user_id: Optional[UUID] = None,
        expires_minutes: int = 10,
    ) -> datetime:
        """Create an OTP record."""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

        otp = OTPCode(
            email=email,
            otp_code=otp_code,
            purpose=purpose,
            user_id=user_id,
            expires_at=expires_at,
            is_used=False,
            attempts_count=0,
            max_attempts=3,
        )

        self.db.add(otp)
        await self.db.flush()

        return expires_at
