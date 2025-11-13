"""Google OAuth authentication service."""

from typing import Dict

import requests
from fastapi import HTTPException, status
from google.auth.transport import requests as google_auth_requests
from google.oauth2 import id_token

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""

    def __init__(self):
        """Initialize Google OAuth service."""
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

    def _validate_config(self) -> None:
        """Validate that Google OAuth is properly configured."""
        if not self.client_id or not self.client_secret:
            logger.error("google_oauth_not_configured", message="Google OAuth credentials not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth is not configured. Please contact administrator.",
            )

    def _validate_id_token_claims(self, idinfo: Dict, expected_client_id: str) -> None:
        """
        Validate standard claims of a decoded Google ID token.

        Args:
            idinfo: Decoded ID token payload (dictionary)
            expected_client_id: Expected Google Client ID (audience)

        Raises:
            ValueError: If any claim is invalid or missing
        """
        # Validate issuer
        if "iss" not in idinfo or idinfo["iss"] not in [
            "accounts.google.com",
            "https://accounts.google.com",
        ]:
            logger.error("invalid_issuer", issuer=idinfo.get("iss"))
            raise ValueError("Invalid token issuer")

        # Validate audience
        if "aud" not in idinfo or idinfo["aud"] != expected_client_id:
            logger.error(
                "invalid_audience",
                audience=idinfo.get("aud"),
                expected=expected_client_id,
            )
            raise ValueError("Invalid token audience")

        # Validate subject
        if "sub" not in idinfo or not idinfo["sub"]:
            logger.error("missing_subject")
            raise ValueError("Token missing 'sub' field")

        # Validate email
        if "email" not in idinfo or not idinfo["email"]:
            logger.error("missing_email")
            raise ValueError("Token missing 'email' field")

    async def exchange_auth_code_for_token(self, authorization_code: str) -> Dict:
        """
        Exchange Google authorization code for ID token and user info.

        Args:
            authorization_code: Authorization code from Google OAuth flow

        Returns:
            dict: User information from ID token

        Raises:
            HTTPException: If exchange or verification fails
        """
        self._validate_config()

        if not self.redirect_uri:
            logger.error("redirect_uri_not_configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth redirect URI not configured.",
            )

        # Prepare token exchange request
        token_request_data = {
            "code": authorization_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            # Exchange authorization code for tokens
            response = requests.post(GOOGLE_TOKEN_URL, data=token_request_data, timeout=10)
            response.raise_for_status()
            token_data = response.json()

        except requests.exceptions.Timeout:
            logger.error("google_token_exchange_timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Google authentication service timed out. Please try again.",
            )
        except requests.exceptions.HTTPError as e:
            response_text = e.response.text if e.response is not None else "No response"
            logger.error(
                "google_token_exchange_failed",
                status_code=e.response.status_code if e.response is not None else "Unknown",
                response=response_text,
            )

            error_detail = "Failed to exchange authorization code with Google."

            if e.response is not None:
                try:
                    error_json = e.response.json()
                    error_desc = error_json.get(
                        "error_description",
                        "Invalid request to Google token endpoint.",
                    )
                    google_error_code = error_json.get("error", "")

                    if "redirect_uri_mismatch" in google_error_code:
                        error_detail = "Redirect URI mismatch. Please contact administrator."
                    elif e.response.status_code == 400:
                        error_detail = f"Google authentication error: {error_desc}"
                    elif e.response.status_code == 401:
                        error_detail = "Google authentication failed. Invalid credentials."
                except requests.exceptions.JSONDecodeError:
                    logger.warning("non_json_error_response", response=e.response.text)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_detail,
            )
        except Exception as e:
            logger.error("unexpected_token_exchange_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during Google authentication.",
            )

        # Extract ID token
        google_id_token_jwt = token_data.get("id_token")
        if not google_id_token_jwt:
            logger.error("id_token_missing_in_response", response=token_data)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve ID token from Google.",
            )

        # Verify and decode ID token
        try:
            auth_request = google_auth_requests.Request()
            idinfo = id_token.verify_oauth2_token(
                google_id_token_jwt,
                auth_request,
                self.client_id,
            )
            self._validate_id_token_claims(idinfo, self.client_id)

            logger.info(
                "google_auth_code_exchanged_successfully",
                email=idinfo.get("email"),
                sub=idinfo.get("sub"),
            )

            return idinfo

        except ValueError as e:
            logger.error("id_token_verification_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google ID token: {str(e)}",
            )
        except Exception as e:
            logger.error("unexpected_verification_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google token verification failed.",
            )

    async def verify_id_token(self, token: str) -> Dict:
        """
        Verify Google ID token (client-side login flow).

        Args:
            token: Google ID token from client

        Returns:
            dict: User information from ID token

        Raises:
            HTTPException: If verification fails
        """
        self._validate_config()

        try:
            auth_request = google_auth_requests.Request()
            idinfo = id_token.verify_oauth2_token(
                token,
                auth_request,
                self.client_id,
            )
            self._validate_id_token_claims(idinfo, self.client_id)

            logger.info(
                "google_id_token_verified",
                email=idinfo.get("email"),
                sub=idinfo.get("sub"),
            )

            return idinfo

        except ValueError as e:
            logger.error("id_token_verification_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google ID token: {str(e)}",
            )
        except Exception as e:
            logger.error("unexpected_verification_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google token verification failed.",
            )
