"""Security utilities for JWT tokens and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: UUID,
    additional_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User ID to encode in token
        additional_claims: Additional claims to include
        expires_delta: Token expiration time

    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(
    user_id: UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID to encode in token
        expires_delta: Token expiration time

    Returns:
        str: Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        dict: Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        raise JWTError(f"Could not validate token: {str(e)}")


def get_user_id_from_token(token: str) -> UUID:
    """
    Extract user ID from a JWT token.

    Args:
        token: JWT token

    Returns:
        UUID: User ID

    Raises:
        JWTError: If token is invalid or user ID is missing
    """
    payload = decode_token(token)
    user_id_str = payload.get("sub")

    if user_id_str is None:
        raise JWTError("Token does not contain user ID")

    try:
        return UUID(user_id_str)
    except ValueError:
        raise JWTError("Invalid user ID in token")


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key (for external API clients).

    Args:
        api_key: Plain API key

    Returns:
        str: Hashed API key
    """
    return pwd_context.hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verify an API key against a hash.

    Args:
        plain_api_key: Plain API key
        hashed_api_key: Hashed API key

    Returns:
        bool: True if API key matches
    """
    return pwd_context.verify(plain_api_key, hashed_api_key)


def generate_api_key_prefix(api_key: str, length: int = 8) -> str:
    """
    Generate a prefix from an API key for display purposes.

    Args:
        api_key: Full API key
        length: Length of prefix

    Returns:
        str: API key prefix (e.g., "sk_live_")
    """
    return api_key[:length] if len(api_key) >= length else api_key
