"""API endpoints for admin operations."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.admin import (
    APIKeyResponse,
    BanUserRequest,
    BanUserResponse,
    ChangeUserRoleRequest,
    ChangeUserRoleResponse,
    CreateAPIKeyRequest,
    ModerateContentRequest,
    ModerateContentResponse,
    PendingContentItem,
    RevokeAPIKeyResponse,
    SystemStatisticsResponse,
    UnbanUserResponse,
    UserListPaginatedResponse,
)
from app.services.admin_service import AdminService

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# TODO: Add authentication dependency to verify admin role
# async def get_current_admin_user(...) -> User:
#     # Verify JWT token and check if user has admin/super_admin role
#     pass


# ============================================================================
# API Key Management
# ============================================================================


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    summary="Create Admin API Key",
    description="""
    Create a new super-admin API key.

    **CRITICAL**: Only super-admins can create API keys.

    The API key is returned ONLY ONCE during creation. Save it immediately!

    Permissions can include:
    - user:read, user:write
    - content:read, content:write, content:moderate
    - admin:read, admin:write
    """,
)
async def create_api_key(
    request: CreateAPIKeyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    # current_admin: Annotated[User, Depends(get_current_admin_user)],
) -> APIKeyResponse:
    """
    Create a new admin API key.

    Args:
        request: API key creation request
        db: Database session

    Returns:
        API key with the generated key (ONLY SHOWN ONCE)
    """
    # TODO: Verify super-admin role
    # For now, using placeholder admin_user_id
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.create_api_key(
            admin_user_id=admin_user_id,
            key_name=request.key_name,
            permissions=request.permissions,
            expires_in_days=request.expires_in_days,
        )

        return APIKeyResponse(**result)

    except Exception as e:
        logger.error("create_api_key_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.get(
    "/api-keys",
    response_model=list[APIKeyResponse],
    summary="List API Keys",
    description="List all admin API keys (without the actual key values).",
)
async def list_api_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    include_expired: bool = Query(default=False, description="Include expired keys"),
) -> list[APIKeyResponse]:
    """
    List all API keys.

    Args:
        include_expired: Include expired keys
        db: Database session

    Returns:
        List of API keys
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        keys = await admin_service.list_api_keys(
            admin_user_id=admin_user_id,
            include_expired=include_expired,
        )

        return [APIKeyResponse(**key) for key in keys]

    except Exception as e:
        logger.error("list_api_keys_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys",
        )


@router.post(
    "/api-keys/{api_key_id}/revoke",
    response_model=RevokeAPIKeyResponse,
    summary="Revoke API Key",
    description="Revoke an admin API key, making it immediately inactive.",
)
async def revoke_api_key(
    api_key_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RevokeAPIKeyResponse:
    """
    Revoke an API key.

    Args:
        api_key_id: ID of API key to revoke
        db: Database session

    Returns:
        Revocation confirmation
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.revoke_api_key(
            admin_user_id=admin_user_id,
            api_key_id=api_key_id,
        )

        return RevokeAPIKeyResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("revoke_api_key_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )


# ============================================================================
# User Management
# ============================================================================


@router.get(
    "/users",
    response_model=UserListPaginatedResponse,
    summary="List Users",
    description="List all users with filtering and pagination.",
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    search_query: Optional[str] = Query(default=None, description="Search by email or name"),
    role_filter: Optional[str] = Query(default=None, description="Filter by role"),
) -> UserListPaginatedResponse:
    """
    List all users.

    Args:
        page: Page number
        page_size: Items per page
        search_query: Search query
        role_filter: Role filter
        db: Database session

    Returns:
        Paginated user list
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.list_users(
            admin_user_id=admin_user_id,
            page=page,
            page_size=page_size,
            search_query=search_query,
            role_filter=role_filter,
        )

        return UserListPaginatedResponse(**result)

    except Exception as e:
        logger.error("list_users_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users",
        )


@router.post(
    "/users/{user_id}/ban",
    response_model=BanUserResponse,
    summary="Ban User",
    description="Ban a user for a specified duration or permanently.",
)
async def ban_user(
    user_id: UUID,
    request: BanUserRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BanUserResponse:
    """
    Ban a user.

    Args:
        user_id: ID of user to ban
        request: Ban request with reason and duration
        db: Database session

    Returns:
        Ban confirmation
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.ban_user(
            admin_user_id=admin_user_id,
            user_id=user_id,
            reason=request.reason,
            ban_duration_days=request.ban_duration_days,
        )

        return BanUserResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("ban_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user",
        )


@router.post(
    "/users/{user_id}/unban",
    response_model=UnbanUserResponse,
    summary="Unban User",
    description="Unban a previously banned user.",
)
async def unban_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UnbanUserResponse:
    """
    Unban a user.

    Args:
        user_id: ID of user to unban
        db: Database session

    Returns:
        Unban confirmation
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.unban_user(
            admin_user_id=admin_user_id,
            user_id=user_id,
        )

        return UnbanUserResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("unban_user_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user",
        )


@router.post(
    "/users/{user_id}/role",
    response_model=ChangeUserRoleResponse,
    summary="Change User Role",
    description="Change a user's role (user, moderator, admin, super_admin).",
)
async def change_user_role(
    user_id: UUID,
    request: ChangeUserRoleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChangeUserRoleResponse:
    """
    Change a user's role.

    Args:
        user_id: ID of user
        request: Role change request
        db: Database session

    Returns:
        Role change confirmation
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.change_user_role(
            admin_user_id=admin_user_id,
            user_id=user_id,
            new_role=request.new_role,
        )

        return ChangeUserRoleResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("change_user_role_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change user role",
        )


# ============================================================================
# Content Moderation
# ============================================================================


@router.get(
    "/content/pending",
    response_model=list[PendingContentItem],
    summary="Get Pending Content",
    description="Get content items pending moderation.",
)
async def get_pending_content(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100, description="Maximum items to return"),
) -> list[PendingContentItem]:
    """
    Get pending content.

    Args:
        limit: Maximum items to return
        db: Database session

    Returns:
        List of pending content items
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        items = await admin_service.get_pending_content(
            admin_user_id=admin_user_id,
            limit=limit,
        )

        return [PendingContentItem(**item) for item in items]

    except Exception as e:
        logger.error("get_pending_content_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending content",
        )


@router.post(
    "/content/{content_type}/{content_id}/moderate",
    response_model=ModerateContentResponse,
    summary="Moderate Content",
    description="Approve or reject content.",
)
async def moderate_content(
    content_type: str,
    content_id: UUID,
    request: ModerateContentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModerateContentResponse:
    """
    Moderate content.

    Args:
        content_type: Type of content (document, conversation, etc.)
        content_id: ID of content
        request: Moderation action
        db: Database session

    Returns:
        Moderation confirmation
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.moderate_content(
            admin_user_id=admin_user_id,
            content_id=content_id,
            content_type=content_type,
            action=request.action,
            reason=request.reason,
        )

        return ModerateContentResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("moderate_content_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to moderate content",
        )


# ============================================================================
# System Statistics
# ============================================================================


@router.get(
    "/statistics",
    response_model=SystemStatisticsResponse,
    summary="Get System Statistics",
    description="Get system-wide statistics (users, content, chat).",
)
async def get_system_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SystemStatisticsResponse:
    """
    Get system statistics.

    Args:
        db: Database session

    Returns:
        System statistics
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        admin_service = AdminService(db)

        result = await admin_service.get_system_statistics(admin_user_id=admin_user_id)

        return SystemStatisticsResponse(**result)

    except Exception as e:
        logger.error("get_system_statistics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system statistics",
        )
