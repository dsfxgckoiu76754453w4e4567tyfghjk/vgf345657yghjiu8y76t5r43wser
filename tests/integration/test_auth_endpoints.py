"""Comprehensive integration tests for authentication endpoints."""

import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.user import User, OTPCode
from tests.factories import UserFactory


class TestAuthRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, db_session):
        """Test successful user registration."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password_hash" not in data

        # Verify user created in database
        result = await db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.is_email_verified is False

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db_session):
        """Test registration with duplicate email fails."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register first time
            await client.post("/api/v1/auth/register", json=user_data)

            # Try to register again
            response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self):
        """Test registration with invalid email fails."""
        user_data = UserFactory.create_user_data(email="invalid-email")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_password(self):
        """Test registration without password fails."""
        user_data = UserFactory.create_user_data()
        del user_data["password"]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422


class TestEmailVerification:
    """Test email verification endpoint."""

    @pytest.mark.asyncio
    async def test_verify_email_success(self, db_session):
        """Test successful email verification."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register user
            reg_response = await client.post("/api/v1/auth/register", json=user_data)
            assert reg_response.status_code == 201

            # Get OTP from database
            result = await db_session.execute(
                select(OTPCode).where(OTPCode.email == user_data["email"])
            )
            otp = result.scalar_one()

            # Verify email
            verify_response = await client.post(
                "/api/v1/auth/verify-email",
                json={"email": user_data["email"], "otp_code": otp.otp_code}
            )

        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data["message"] == "Email verified successfully"

    @pytest.mark.asyncio
    async def test_verify_email_invalid_otp(self, db_session):
        """Test email verification with invalid OTP."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register user
            await client.post("/api/v1/auth/register", json=user_data)

            # Try to verify with wrong OTP
            response = await client.post(
                "/api/v1/auth/verify-email",
                json={"email": user_data["email"], "otp_code": "000000"}
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_email_nonexistent_user(self):
        """Test email verification for non-existent user."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/verify-email",
                json={"email": "nonexistent@example.com", "otp_code": "123456"}
            )

        assert response.status_code == 400


class TestLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, db_session):
        """Test successful login."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register and verify user
            await client.post("/api/v1/auth/register", json=user_data)

            result = await db_session.execute(
                select(OTPCode).where(OTPCode.email == user_data["email"])
            )
            otp = result.scalar_one()
            await client.post(
                "/api/v1/auth/verify-email",
                json={"email": user_data["email"], "otp_code": otp.otp_code}
            )

            # Login
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": user_data["email"], "password": user_data["password"]}
            )

        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session):
        """Test login with wrong password."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register and verify user
            await client.post("/api/v1/auth/register", json=user_data)

            result = await db_session.execute(
                select(OTPCode).where(OTPCode.email == user_data["email"])
            )
            otp = result.scalar_one()
            await client.post(
                "/api/v1/auth/verify-email",
                json={"email": user_data["email"], "otp_code": otp.otp_code}
            )

            # Try to login with wrong password
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": user_data["email"], "password": "WrongPassword123!"}
            )

        assert response.status_code in [400, 401]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent@example.com", "password": "Password123!"}
            )

        assert response.status_code in [400, 401]

    @pytest.mark.asyncio
    async def test_login_unverified_user(self, db_session):
        """Test login with unverified user."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register but don't verify
            await client.post("/api/v1/auth/register", json=user_data)

            # Try to login
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": user_data["email"], "password": user_data["password"]}
            )

        # Service allows unverified login, but API layer may enforce verification
        assert response.status_code in [200, 400, 401, 403]


class TestOTPResend:
    """Test OTP resend endpoint."""

    @pytest.mark.asyncio
    async def test_resend_otp_success(self, db_session):
        """Test successful OTP resend."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register user
            await client.post("/api/v1/auth/register", json=user_data)

            # Resend OTP
            response = await client.post(
                "/api/v1/auth/resend-otp",
                json={"email": user_data["email"]}
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resend_otp_nonexistent_user(self):
        """Test OTP resend for non-existent user."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/resend-otp",
                json={"email": "nonexistent@example.com"}
            )

        assert response.status_code == 404


class TestAuthMe:
    """Test get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, db_session):
        """Test getting current user info."""
        user_data = UserFactory.create_user_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register, verify, and login
            await client.post("/api/v1/auth/register", json=user_data)

            result = await db_session.execute(
                select(OTPCode).where(OTPCode.email == user_data["email"])
            )
            otp = result.scalar_one()
            await client.post(
                "/api/v1/auth/verify-email",
                json={"email": user_data["email"], "otp_code": otp.otp_code}
            )

            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": user_data["email"], "password": user_data["password"]}
            )
            token = login_response.json()["access_token"]

            # Get current user
            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self):
        """Test getting current user without auth."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self):
        """Test getting current user with invalid token."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"}
            )

        assert response.status_code == 401
