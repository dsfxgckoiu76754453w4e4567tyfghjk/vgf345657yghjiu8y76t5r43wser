"""API endpoints for external API client management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.external_api import (
    ClientDetailsResponse,
    ClientListItem,
    ClientStatusResponse,
    RegisterClientRequest,
    RegisterClientResponse,
    RegenerateSecretResponse,
    UpdateClientRequest,
    UpdateClientResponse,
    UsageStatisticsResponse,
)
from app.services.external_api_client_service import ExternalAPIClientService

logger = get_logger(__name__)

router = APIRouter()


# TODO: Add authentication dependency
# async def get_current_user(...) -> User:
#     pass


# ============================================================================
# Client Registration and Management
# ============================================================================


@router.post(
    "/clients",
    response_model=RegisterClientResponse,
    summary="Register External API Client",
    description="""
    Register a new external API client for third-party integrations.

    **CRITICAL**: Returns API key and secret ONLY ONCE. Save them immediately!

    Use Cases:
    - Mobile apps integrating the chatbot
    - Web applications
    - Third-party services
    - Custom integrations

    Rate Limits:
    - Per-minute: Controls burst traffic
    - Per-day: Controls overall usage

    CORS:
    - Specify allowed_origins for browser-based apps
    - Use ["*"] for development only (NOT recommended for production)
    """,
)
async def register_client(
    request: RegisterClientRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterClientResponse:
    """
    Register a new external API client.

    Args:
        request: Client registration request
        db: Database session

    Returns:
        Client credentials (API key and secret shown ONLY once)
    """
    # TODO: Get actual user ID from authentication
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.register_client(
            owner_user_id=owner_user_id,
            app_name=request.app_name,
            app_description=request.app_description,
            callback_url=str(request.callback_url) if request.callback_url else None,
            allowed_origins=request.allowed_origins,
            rate_limit_per_minute=request.rate_limit_per_minute,
            rate_limit_per_day=request.rate_limit_per_day,
        )

        return RegisterClientResponse(**result)

    except Exception as e:
        logger.error("register_client_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register external API client",
        )


@router.get(
    "/clients",
    response_model=list[ClientListItem],
    summary="List API Clients",
    description="List all API clients owned by the current user.",
)
async def list_clients(
    db: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: bool = Query(default=False, description="Include inactive clients"),
) -> list[ClientListItem]:
    """
    List API clients.

    Args:
        include_inactive: Include inactive clients
        db: Database session

    Returns:
        List of clients
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        clients = await client_service.list_clients(
            owner_user_id=owner_user_id,
            include_inactive=include_inactive,
        )

        return [ClientListItem(**client) for client in clients]

    except Exception as e:
        logger.error("list_clients_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API clients",
        )


@router.get(
    "/clients/{client_id}",
    response_model=ClientDetailsResponse,
    summary="Get Client Details",
    description="Get detailed information about an API client including usage statistics.",
)
async def get_client_details(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientDetailsResponse:
    """
    Get client details.

    Args:
        client_id: Client ID
        db: Database session

    Returns:
        Client details with usage statistics
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.get_client_details(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        return ClientDetailsResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_client_details_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client details",
        )


@router.put(
    "/clients/{client_id}",
    response_model=UpdateClientResponse,
    summary="Update Client",
    description="Update client information (name, description, rate limits, etc.).",
)
async def update_client(
    client_id: UUID,
    request: UpdateClientRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UpdateClientResponse:
    """
    Update client information.

    Args:
        client_id: Client ID
        request: Update request
        db: Database session

    Returns:
        Updated client information
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.update_client(
            client_id=client_id,
            owner_user_id=owner_user_id,
            app_name=request.app_name,
            app_description=request.app_description,
            callback_url=str(request.callback_url) if request.callback_url else None,
            allowed_origins=request.allowed_origins,
            rate_limit_per_minute=request.rate_limit_per_minute,
            rate_limit_per_day=request.rate_limit_per_day,
        )

        return UpdateClientResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("update_client_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client",
        )


# ============================================================================
# Security Operations
# ============================================================================


@router.post(
    "/clients/{client_id}/regenerate-secret",
    response_model=RegenerateSecretResponse,
    summary="Regenerate API Secret",
    description="""
    Regenerate API secret for a client.

    **CRITICAL**: New secret is shown ONLY ONCE. Save it immediately!

    Use this when:
    - Secret is compromised
    - Regular security rotation
    - Lost/forgotten secret
    """,
)
async def regenerate_secret(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegenerateSecretResponse:
    """
    Regenerate API secret.

    Args:
        client_id: Client ID
        db: Database session

    Returns:
        New API secret (shown ONLY once)
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.regenerate_secret(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        return RegenerateSecretResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("regenerate_secret_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate secret",
        )


@router.post(
    "/clients/{client_id}/deactivate",
    response_model=ClientStatusResponse,
    summary="Deactivate Client",
    description="Deactivate an API client. Deactivated clients cannot make API calls.",
)
async def deactivate_client(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientStatusResponse:
    """
    Deactivate API client.

    Args:
        client_id: Client ID
        db: Database session

    Returns:
        Deactivation confirmation
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.deactivate_client(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        return ClientStatusResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("deactivate_client_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate client",
        )


@router.post(
    "/clients/{client_id}/activate",
    response_model=ClientStatusResponse,
    summary="Activate Client",
    description="Activate a previously deactivated API client.",
)
async def activate_client(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientStatusResponse:
    """
    Activate API client.

    Args:
        client_id: Client ID
        db: Database session

    Returns:
        Activation confirmation
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.activate_client(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        return ClientStatusResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("activate_client_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate client",
        )


# ============================================================================
# Usage Statistics
# ============================================================================


@router.get(
    "/clients/{client_id}/usage",
    response_model=UsageStatisticsResponse,
    summary="Get Usage Statistics",
    description="""
    Get usage statistics for an API client.

    Metrics include:
    - Total requests
    - Average response time
    - Error rate
    - Requests per day

    Useful for:
    - Monitoring API usage
    - Detecting unusual patterns
    - Capacity planning
    """,
)
async def get_usage_statistics(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
) -> UsageStatisticsResponse:
    """
    Get usage statistics.

    Args:
        client_id: Client ID
        days: Number of days to analyze
        db: Database session

    Returns:
        Usage statistics
    """
    owner_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        client_service = ExternalAPIClientService(db)

        result = await client_service.get_usage_statistics(
            client_id=client_id,
            owner_user_id=owner_user_id,
            days=days,
        )

        return UsageStatisticsResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_usage_statistics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage statistics",
        )
