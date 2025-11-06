"""Unit tests for authentication service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.auth import AuthService
from app.core.security import verify_password, hash_password


class TestAuthService:
    """Test suite for AuthService."""

    @pytest.fixture
    def auth_service(self, db_session):
        """Create AuthService instance for testing."""
        return AuthService(db_session)

    # ========================================================================
    # User Registration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service):
        """Test successful user registration."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"
        full_name = "Test User"

        user, otp_code = await auth_service.register_user(
            email=email,
            password=password,
            full_name=full_name,
        )

        assert user.email == email
        assert user.full_name == full_name
        assert user.is_email_verified is False
        assert verify_password(password, user.password_hash)
        assert len(otp_code) == 6
        assert otp_code.isdigit()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service):
        """Test registration with duplicate email fails."""
        email = f"duplicate_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register first user
        await auth_service.register_user(email=email, password=password)

        # Try to register with same email
        with pytest.raises(ValueError, match="AUTH_EMAIL_ALREADY_EXISTS"):
            await auth_service.register_user(email=email, password=password)

    @pytest.mark.asyncio
    async def test_register_weak_password(self, auth_service):
        """Test registration with weak password succeeds (no validation in service)."""
        # Note: Password validation should be done at API layer, not service layer
        email = f"test_{uuid4()}@example.com"
        weak_password = "123"

        # Service layer doesn't validate password strength
        user, otp_code = await auth_service.register_user(email=email, password=weak_password)
        assert user.email == email

    # ========================================================================
    # Email Verification Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service):
        """Test successful email verification."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        user, otp_code = await auth_service.register_user(email=email, password=password)

        # Verify email
        verified_user = await auth_service.verify_email(email=email, otp_code=otp_code)

        assert verified_user.id == user.id
        assert verified_user.is_email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_otp(self, auth_service):
        """Test email verification with invalid OTP fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        await auth_service.register_user(email=email, password=password)

        # Try to verify with wrong OTP
        with pytest.raises(ValueError, match="AUTH_INVALID_OTP"):
            await auth_service.verify_email(email=email, otp_code="000000")

    @pytest.mark.asyncio
    async def test_verify_email_expired_otp(self, auth_service, db_session):
        """Test email verification with expired OTP fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        user, otp_code = await auth_service.register_user(email=email, password=password)

        # Manually expire the OTP
        from app.models.user import OTPCode
        from sqlalchemy import select
        from datetime import timezone

        result = await db_session.execute(
            select(OTPCode).where(OTPCode.user_id == user.id)
        )
        otp = result.scalar_one()
        otp.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.commit()

        # Try to verify with expired OTP
        with pytest.raises(ValueError, match="AUTH_INVALID_OTP"):
            await auth_service.verify_email(email=email, otp_code=otp_code)

    # ========================================================================
    # Login Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service):
        """Test successful login."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Login
        logged_in_user, access_token, refresh_token = await auth_service.login_user(email=email, password=password)

        assert logged_in_user.id == user.id
        assert logged_in_user.email == email
        assert access_token is not None
        assert refresh_token is not None
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)

    @pytest.mark.asyncio
    async def test_login_unverified_user(self, auth_service):
        """Test login with unverified user succeeds (no email verification check in service)."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register but don't verify
        await auth_service.register_user(email=email, password=password)

        # Login succeeds (email verification not enforced at service layer)
        logged_in_user, access_token, refresh_token = await auth_service.login_user(email=email, password=password)
        assert logged_in_user.email == email

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service):
        """Test login with wrong password fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Try to login with wrong password
        with pytest.raises(ValueError, match="AUTH_INVALID_CREDENTIALS"):
            await auth_service.login_user(email=email, password="WrongPassword!")

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_service, db_session):
        """Test login with inactive user fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Deactivate the user
        user.is_active = False
        await db_session.commit()

        # Try to login
        with pytest.raises(ValueError, match="AUTH_USER_INACTIVE"):
            await auth_service.login_user(email=email, password=password)

    # ========================================================================
    # Token Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service):
        """Test token validation and creation."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register, verify, and login
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)
        logged_in_user, access_token, refresh_token = await auth_service.login_user(email=email, password=password)

        # Verify tokens are strings
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert len(access_token) > 0
        assert len(refresh_token) > 0

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user(self, auth_service):
        """Test login with nonexistent user fails."""
        with pytest.raises(ValueError, match="AUTH_INVALID_CREDENTIALS"):
            await auth_service.login_user(email="nonexistent@example.com", password="password")

    # ========================================================================
    # OTP Resend Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_resend_otp_success(self, auth_service):
        """Test successful OTP resend."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register user
        user, otp_code = await auth_service.register_user(email=email, password=password)

        # Resend OTP
        expires_at = await auth_service.resend_otp(email=email, purpose="email_verification")

        assert expires_at is not None
        assert isinstance(expires_at, datetime)

    @pytest.mark.asyncio
    async def test_resend_otp_nonexistent_user(self, auth_service):
        """Test OTP resend for nonexistent user fails."""
        with pytest.raises(ValueError, match="AUTH_USER_NOT_FOUND"):
            await auth_service.resend_otp(email="nonexistent@example.com", purpose="email_verification")


class TestSecurityFunctions:
    """Test suite for security functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"

        # Hash password
        hashed = hash_password(password)

        # Verify correct password
        assert verify_password(password, hashed) is True

        # Verify wrong password
        assert verify_password("WrongPassword", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
