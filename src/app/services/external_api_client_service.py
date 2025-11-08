"""External API client service for third-party integrations."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.external_api import ExternalAPIClient, APIUsageLog

logger = get_logger(__name__)


class ExternalAPIClientService:
    """Service for managing external API clients."""

    def __init__(self, db: AsyncSession):
        """Initialize external API client service.

        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # API Client Registration
    # ========================================================================

    async def register_client(
        self,
        owner_user_id: UUID,
        app_name: str,
        app_description: str,
        callback_url: Optional[str] = None,
        allowed_origins: Optional[list[str]] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_day: int = 10000,
    ) -> dict:
        """
        Register a new external API client.

        CRITICAL: Returns API key and secret ONLY ONCE.

        Args:
            owner_user_id: User who owns this client
            app_name: Application name
            app_description: Application description
            callback_url: OAuth callback URL
            allowed_origins: CORS allowed origins
            rate_limit_per_minute: Requests per minute
            rate_limit_per_day: Requests per day

        Returns:
            Client information with API key and secret
        """
        # Generate API key and secret
        api_key = f"pk_{secrets.token_urlsafe(32)}"
        api_secret = f"sk_{secrets.token_urlsafe(48)}"

        # In production, hash the secret
        api_key_hash = secrets.token_hex(16)
        api_secret_hash = secrets.token_hex(24)

        # Create client
        client = ExternalAPIClient(
            owner_user_id=owner_user_id,
            app_name=app_name,
            app_description=app_description,
            api_key_hash=api_key_hash,
            api_secret_hash=api_secret_hash,
            callback_url=callback_url,
            allowed_origins=allowed_origins or [],
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_day=rate_limit_per_day,
            is_active=True,
        )

        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)

        logger.info(
            "external_api_client_registered",
            client_id=str(client.id),
            app_name=app_name,
            owner_user_id=str(owner_user_id),
        )

        return {
            "client_id": str(client.id),
            "app_name": app_name,
            "api_key": api_key,  # ONLY returned once
            "api_secret": api_secret,  # ONLY returned once
            "rate_limit_per_minute": rate_limit_per_minute,
            "rate_limit_per_day": rate_limit_per_day,
            "created_at": client.created_at.isoformat(),
            "warning": "⚠️ SAVE THESE CREDENTIALS NOW - They will not be shown again!",
        }

    # ========================================================================
    # Client Management
    # ========================================================================

    async def list_clients(
        self, owner_user_id: UUID, include_inactive: bool = False
    ) -> list[dict]:
        """
        List API clients for a user.

        Args:
            owner_user_id: Owner user ID
            include_inactive: Include inactive clients

        Returns:
            List of clients (without secrets)
        """
        query = select(ExternalAPIClient).where(ExternalAPIClient.owner_user_id == owner_user_id)

        if not include_inactive:
            query = query.where(ExternalAPIClient.is_active == True)

        result = await self.db.execute(query)
        clients = result.scalars().all()

        return [
            {
                "client_id": str(client.id),
                "app_name": client.app_name,
                "app_description": client.app_description,
                "callback_url": client.callback_url,
                "allowed_origins": client.allowed_origins,
                "rate_limit_per_minute": client.rate_limit_per_minute,
                "rate_limit_per_day": client.rate_limit_per_day,
                "is_active": client.is_active,
                "created_at": client.created_at.isoformat(),
                "last_used_at": client.last_used_at.isoformat() if client.last_used_at else None,
            }
            for client in clients
        ]

    async def get_client_details(self, client_id: UUID, owner_user_id: UUID) -> dict:
        """
        Get detailed client information.

        Args:
            client_id: Client ID
            owner_user_id: Owner user ID (for authorization)

        Returns:
            Client details with usage statistics
        """
        result = await self.db.execute(
            select(ExternalAPIClient).where(
                and_(
                    ExternalAPIClient.id == client_id,
                    ExternalAPIClient.owner_user_id == owner_user_id,
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            raise ValueError("Client not found")

        # Get usage statistics
        today = datetime.utcnow().date()
        usage_today_result = await self.db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.client_id == client_id,
                    func.date(APIUsageLog.timestamp) == today,
                )
            )
        )
        usage_today = usage_today_result.scalar() or 0

        # Get total usage
        total_usage_result = await self.db.execute(
            select(func.count(APIUsageLog.id)).where(
                APIUsageLog.client_id == client_id
            )
        )
        total_usage = total_usage_result.scalar() or 0

        return {
            "client_id": str(client.id),
            "app_name": client.app_name,
            "app_description": client.app_description,
            "callback_url": client.callback_url,
            "allowed_origins": client.allowed_origins,
            "rate_limit_per_minute": client.rate_limit_per_minute,
            "rate_limit_per_day": client.rate_limit_per_day,
            "is_active": client.is_active,
            "created_at": client.created_at.isoformat(),
            "last_used_at": client.last_used_at.isoformat() if client.last_used_at else None,
            "usage_statistics": {
                "requests_today": usage_today,
                "total_requests": total_usage,
                "remaining_today": max(0, client.rate_limit_per_day - usage_today),
            },
        }

    async def update_client(
        self,
        client_id: UUID,
        owner_user_id: UUID,
        app_name: Optional[str] = None,
        app_description: Optional[str] = None,
        callback_url: Optional[str] = None,
        allowed_origins: Optional[list[str]] = None,
        rate_limit_per_minute: Optional[int] = None,
        rate_limit_per_day: Optional[int] = None,
    ) -> dict:
        """
        Update client information.

        Args:
            client_id: Client ID
            owner_user_id: Owner user ID (for authorization)
            app_name: New app name
            app_description: New description
            callback_url: New callback URL
            allowed_origins: New allowed origins
            rate_limit_per_minute: New per-minute limit
            rate_limit_per_day: New per-day limit

        Returns:
            Updated client information
        """
        result = await self.db.execute(
            select(ExternalAPIClient).where(
                and_(
                    ExternalAPIClient.id == client_id,
                    ExternalAPIClient.owner_user_id == owner_user_id,
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            raise ValueError("Client not found")

        # Update fields
        if app_name is not None:
            client.app_name = app_name
        if app_description is not None:
            client.app_description = app_description
        if callback_url is not None:
            client.callback_url = callback_url
        if allowed_origins is not None:
            client.allowed_origins = allowed_origins
        if rate_limit_per_minute is not None:
            client.rate_limit_per_minute = rate_limit_per_minute
        if rate_limit_per_day is not None:
            client.rate_limit_per_day = rate_limit_per_day

        await self.db.commit()
        await self.db.refresh(client)

        logger.info(
            "external_api_client_updated",
            client_id=str(client_id),
            owner_user_id=str(owner_user_id),
        )

        return {
            "client_id": str(client.id),
            "app_name": client.app_name,
            "app_description": client.app_description,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def regenerate_secret(self, client_id: UUID, owner_user_id: UUID) -> dict:
        """
        Regenerate API secret for a client.

        CRITICAL: Returns new secret ONLY ONCE.

        Args:
            client_id: Client ID
            owner_user_id: Owner user ID (for authorization)

        Returns:
            New API secret
        """
        result = await self.db.execute(
            select(ExternalAPIClient).where(
                and_(
                    ExternalAPIClient.id == client_id,
                    ExternalAPIClient.owner_user_id == owner_user_id,
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            raise ValueError("Client not found")

        # Generate new secret
        new_api_secret = f"sk_{secrets.token_urlsafe(48)}"
        new_api_secret_hash = secrets.token_hex(24)

        client.api_secret_hash = new_api_secret_hash

        await self.db.commit()

        logger.info(
            "external_api_secret_regenerated",
            client_id=str(client_id),
            owner_user_id=str(owner_user_id),
        )

        return {
            "client_id": str(client_id),
            "api_secret": new_api_secret,  # ONLY returned once
            "regenerated_at": datetime.utcnow().isoformat(),
            "warning": "⚠️ SAVE THIS SECRET NOW - It will not be shown again!",
        }

    async def deactivate_client(self, client_id: UUID, owner_user_id: UUID) -> dict:
        """
        Deactivate an API client.

        Args:
            client_id: Client ID
            owner_user_id: Owner user ID (for authorization)

        Returns:
            Deactivation confirmation
        """
        result = await self.db.execute(
            select(ExternalAPIClient).where(
                and_(
                    ExternalAPIClient.id == client_id,
                    ExternalAPIClient.owner_user_id == owner_user_id,
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            raise ValueError("Client not found")

        client.is_active = False

        await self.db.commit()

        logger.info(
            "external_api_client_deactivated",
            client_id=str(client_id),
            owner_user_id=str(owner_user_id),
        )

        return {
            "client_id": str(client_id),
            "app_name": client.app_name,
            "status": "inactive",
            "deactivated_at": datetime.utcnow().isoformat(),
        }

    async def activate_client(self, client_id: UUID, owner_user_id: UUID) -> dict:
        """
        Activate an API client.

        Args:
            client_id: Client ID
            owner_user_id: Owner user ID (for authorization)

        Returns:
            Activation confirmation
        """
        result = await self.db.execute(
            select(ExternalAPIClient).where(
                and_(
                    ExternalAPIClient.id == client_id,
                    ExternalAPIClient.owner_user_id == owner_user_id,
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            raise ValueError("Client not found")

        client.is_active = True

        await self.db.commit()

        logger.info(
            "external_api_client_activated",
            client_id=str(client_id),
            owner_user_id=str(owner_user_id),
        )

        return {
            "client_id": str(client_id),
            "app_name": client.app_name,
            "status": "active",
            "activated_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # Usage Tracking
    # ========================================================================

    async def log_api_usage(
        self,
        client_id: UUID,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log API usage for tracking and analytics.

        Args:
            client_id: Client ID
            endpoint: API endpoint called
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            ip_address: Client IP address
            user_agent: User agent string
        """
        usage_log = APIUsageLog(
            client_id=client_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(usage_log)

        # Update last_used_at on client
        result = await self.db.execute(
            select(ExternalAPIClient).where(ExternalAPIClient.id == client_id)
        )
        client = result.scalar_one_or_none()
        if client:
            client.last_used_at = datetime.utcnow()

        await self.db.commit()

    async def get_usage_statistics(
        self, client_id: UUID, owner_user_id: UUID, days: int = 7
    ) -> dict:
        """
        Get usage statistics for a client.

        Args:
            client_id: Client ID
            owner_user_id: Owner user ID (for authorization)
            days: Number of days to analyze

        Returns:
            Usage statistics
        """
        # Verify ownership
        result = await self.db.execute(
            select(ExternalAPIClient).where(
                and_(
                    ExternalAPIClient.id == client_id,
                    ExternalAPIClient.owner_user_id == owner_user_id,
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            raise ValueError("Client not found")

        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total requests
        total_requests_result = await self.db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.client_id == client_id,
                    APIUsageLog.timestamp >= start_date,
                )
            )
        )
        total_requests = total_requests_result.scalar() or 0

        # Average response time
        avg_response_time_result = await self.db.execute(
            select(func.avg(APIUsageLog.response_time_ms)).where(
                and_(
                    APIUsageLog.client_id == client_id,
                    APIUsageLog.timestamp >= start_date,
                )
            )
        )
        avg_response_time = avg_response_time_result.scalar() or 0

        # Error rate (4xx and 5xx)
        error_count_result = await self.db.execute(
            select(func.count(APIUsageLog.id)).where(
                and_(
                    APIUsageLog.client_id == client_id,
                    APIUsageLog.timestamp >= start_date,
                    APIUsageLog.status_code >= 400,
                )
            )
        )
        error_count = error_count_result.scalar() or 0

        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "client_id": str(client_id),
            "period_days": days,
            "total_requests": total_requests,
            "average_response_time_ms": round(avg_response_time, 2),
            "error_count": error_count,
            "error_rate_percent": round(error_rate, 2),
            "requests_per_day": round(total_requests / days, 2),
        }
