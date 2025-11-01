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
        display_name = "Test User"

        user, otp_code = await auth_service.register_user(
            email=email,
            password=password,
            display_name=display_name,
        )

        assert user.email == email
        assert user.display_name == display_name
        assert user.is_verified is False
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
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user(email=email, password=password)

    @pytest.mark.asyncio
    async def test_register_weak_password(self, auth_service):
        """Test registration with weak password fails."""
        email = f"test_{uuid4()}@example.com"
        weak_password = "123"

        with pytest.raises(ValueError, match="Password must be at least"):
            await auth_service.register_user(email=email, password=weak_password)

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
        assert verified_user.is_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_otp(self, auth_service):
        """Test email verification with invalid OTP fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        await auth_service.register_user(email=email, password=password)

        # Try to verify with wrong OTP
        with pytest.raises(ValueError, match="Invalid or expired OTP"):
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

        result = await db_session.execute(
            select(OTPCode).where(OTPCode.user_id == user.id)
        )
        otp = result.scalar_one()
        otp.expires_at = datetime.utcnow() - timedelta(minutes=1)
        await db_session.commit()

        # Try to verify with expired OTP
        with pytest.raises(ValueError, match="Invalid or expired OTP"):
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
        result = await auth_service.login(email=email, password=password)

        assert result["user"]["id"] == str(user.id)
        assert result["user"]["email"] == email
        assert "access_token" in result
        assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_login_unverified_user(self, auth_service):
        """Test login with unverified user fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register but don't verify
        await auth_service.register_user(email=email, password=password)

        # Try to login
        with pytest.raises(ValueError, match="Email not verified"):
            await auth_service.login(email=email, password=password)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service):
        """Test login with wrong password fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Try to login with wrong password
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login(email=email, password="WrongPassword!")

    @pytest.mark.asyncio
    async def test_login_banned_user(self, auth_service, db_session):
        """Test login with banned user fails."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Ban the user
        user.is_banned = True
        user.ban_reason = "Test ban"
        await db_session.commit()

        # Try to login
        with pytest.raises(ValueError, match="Account is banned"):
            await auth_service.login(email=email, password=password)

    # ========================================================================
    # Token Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service):
        """Test successful token refresh."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register, verify, and login
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)
        login_result = await auth_service.login(email=email, password=password)

        refresh_token = login_result["refresh_token"]

        # Refresh token
        new_tokens = await auth_service.refresh_access_token(refresh_token=refresh_token)

        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != login_result["access_token"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """Test token refresh with invalid token fails."""
        with pytest.raises(ValueError, match="Invalid refresh token"):
            await auth_service.refresh_access_token(refresh_token="invalid_token")

    # ========================================================================
    # Password Reset Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_password_reset_request_success(self, auth_service):
        """Test successful password reset request."""
        email = f"test_{uuid4()}@example.com"
        password = "SecurePassword123!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Request password reset
        reset_otp = await auth_service.request_password_reset(email=email)

        assert len(reset_otp) == 6
        assert reset_otp.isdigit()

    @pytest.mark.asyncio
    async def test_password_reset_complete_success(self, auth_service):
        """Test successful password reset completion."""
        email = f"test_{uuid4()}@example.com"
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"

        # Register and verify user
        user, otp_code = await auth_service.register_user(email=email, password=old_password)
        await auth_service.verify_email(email=email, otp_code=otp_code)

        # Request password reset
        reset_otp = await auth_service.request_password_reset(email=email)

        # Reset password
        await auth_service.reset_password(
            email=email, otp_code=reset_otp, new_password=new_password
        )

        # Verify can login with new password
        login_result = await auth_service.login(email=email, password=new_password)
        assert login_result["user"]["email"] == email

        # Verify cannot login with old password
        with pytest.raises(ValueError):
            await auth_service.login(email=email, password=old_password)


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
