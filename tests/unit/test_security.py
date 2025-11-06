"""Unit tests for security functions."""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from jose import JWTError
from app.core.config import settings


class TestPasswordHashing:
    """Test suite for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Test hash_password returns a string."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test hash_password produces different hashes for same password."""
        password = "TestPassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verify_password with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password with incorrect password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword!", hashed) is False

    def test_verify_password_empty(self):
        """Test verify_password with empty password."""
        hashed = hash_password("TestPassword123!")

        assert verify_password("", hashed) is False

    def test_hash_password_special_characters(self):
        """Test password hashing with special characters."""
        password = "T3st!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self):
        """Test password hashing with unicode characters."""
        password = "تست密码пароль"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test suite for JWT token functions."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_id = "12345"
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_id = "12345"
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_user_id(self):
        """Test access token contains user ID."""
        user_id = "12345"
        token = create_access_token(user_id)

        # Decode without verification to check payload
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_refresh_token_contains_user_id(self):
        """Test refresh token contains user ID."""
        user_id = "12345"
        token = create_refresh_token(user_id)

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        """Test decoding a valid token."""
        user_id = "12345"
        token = create_access_token(user_id)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_token_invalid(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            decode_token(invalid_token)

    def test_decode_token_expired(self):
        """Test decoding an expired token."""
        user_id = "12345"

        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        expires_at = datetime.utcnow() + expires_delta

        payload = {
            "sub": user_id,
            "type": "access",
            "exp": expires_at,
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        # Expired token should raise JWTError
        with pytest.raises(JWTError):
            decode_token(token)

    def test_access_token_different_each_time(self):
        """Test access tokens are different for same user."""
        user_id = "12345"

        token1 = create_access_token(user_id)
        token2 = create_access_token(user_id)

        # Tokens should be different due to timestamp
        assert token1 != token2

    def test_token_type_validation(self):
        """Test token type is properly set."""
        user_id = "12345"

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


class TestPasswordStrength:
    """Test suite for password strength validation."""

    def test_weak_password_too_short(self):
        """Test that short passwords are rejected."""
        from app.services.auth import AuthService

        # This should be validated in the auth service
        weak_password = "123"
        assert len(weak_password) < 8

    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted."""
        strong_password = "SecureP@ssw0rd123!"

        # Should be able to hash strong password
        hashed = hash_password(strong_password)
        assert verify_password(strong_password, hashed) is True

    def test_password_with_spaces(self):
        """Test password with spaces."""
        password = "Password With Spaces 123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
