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
from app.services.email_service import EmailService

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

        # Send OTP email
        email_service = EmailService()
        email_sent = await email_service.send_otp_email(
            to_email=email,
            otp_code=otp_code,
            purpose="email_verification"
        )

        if email_sent:
            logger.info("user_registered_otp_sent", user_id=str(user.id), email=email)
        else:
            logger.warning("user_registered_otp_send_failed", user_id=str(user.id), email=email)

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

        # Send OTP email
        email_service = EmailService()
        email_sent = await email_service.send_otp_email(
            to_email=email,
            otp_code=otp_code,
            purpose=purpose
        )

        if email_sent:
            logger.info("otp_resent_successfully", email=email, purpose=purpose)
        else:
            logger.warning("otp_resent_email_failed", email=email, purpose=purpose)

        return expires_at

    async def google_oauth_login(
        self,
        google_user_info: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[User, str, str, bool]:
        """
        Handle Google OAuth login with unified user account support.

        If a user with the same email already exists (from email/password registration),
        this method will link the Google OAuth provider to that existing user.

        Args:
            google_user_info: User info from Google ID token
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            tuple: (User, access_token, refresh_token, is_new_user)

        Raises:
            ValueError: If authentication fails
        """
        email = google_user_info.get("email")
        google_sub = google_user_info.get("sub")
        full_name = google_user_info.get("name")
        profile_picture_url = google_user_info.get("picture")

        if not email or not google_sub:
            raise ValueError("AUTH_INVALID_GOOGLE_TOKEN")

        # Check if user exists with this email (unified account logic)
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        is_new_user = False

        if existing_user:
            # User exists with this email - link Google OAuth if not already linked
            logger.info(
                "google_oauth_existing_user",
                user_id=str(existing_user.id),
                email=email,
            )

            # Check if Google provider is already linked
            provider_result = await self.db.execute(
                select(LinkedAuthProvider)
                .where(LinkedAuthProvider.user_id == existing_user.id)
                .where(LinkedAuthProvider.provider_type == "google")
            )
            existing_google_provider = provider_result.scalar_one_or_none()

            if not existing_google_provider:
                # Link Google OAuth to existing user
                google_provider = LinkedAuthProvider(
                    user_id=existing_user.id,
                    provider_type="google",
                    provider_user_id=google_sub,
                    provider_email=email,
                    is_primary=False,  # Email/password is primary
                    is_verified=True,  # Google accounts are pre-verified
                )
                self.db.add(google_provider)
                logger.info(
                    "google_provider_linked_to_existing_user",
                    user_id=str(existing_user.id),
                    email=email,
                )

            # Update user profile if needed
            if profile_picture_url and not existing_user.profile_picture_url:
                existing_user.profile_picture_url = profile_picture_url

            if full_name and not existing_user.full_name:
                existing_user.full_name = full_name

            # Mark email as verified (Google accounts are verified)
            existing_user.is_email_verified = True

            user = existing_user
        else:
            # Create new user with Google OAuth
            is_new_user = True

            user = User(
                email=email,
                full_name=full_name,
                profile_picture_url=profile_picture_url,
                account_type="free",
                is_email_verified=True,  # Google accounts are pre-verified
                is_active=True,
                password_hash=None,  # No password for OAuth-only users
            )

            self.db.add(user)
            await self.db.flush()  # Get user ID

            # Create Google OAuth provider
            google_provider = LinkedAuthProvider(
                user_id=user.id,
                provider_type="google",
                provider_user_id=google_sub,
                provider_email=email,
                is_primary=True,
                is_verified=True,
            )
            self.db.add(google_provider)

            # Create user settings
            settings = UserSettings(user_id=user.id)
            self.db.add(settings)

            logger.info("new_user_created_via_google_oauth", user_id=str(user.id), email=email)

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

        logger.info("google_oauth_login_successful", user_id=str(user.id), email=email, is_new_user=is_new_user)

        return user, access_token, refresh_token, is_new_user

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
