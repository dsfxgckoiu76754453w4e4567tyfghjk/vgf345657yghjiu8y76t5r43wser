"""API endpoints for support tickets."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.admin import (
    AddTicketResponseRequest,
    AddTicketResponseResponse,
    AssignTicketRequest,
    AssignTicketResponse,
    CreateTicketRequest,
    TicketDetailResponse,
    TicketListResponse,
    TicketResponse,
    TicketStatisticsResponse,
    UpdateTicketStatusRequest,
    UpdateTicketStatusResponse,
)
from app.services.support_service import SupportService

logger = get_logger(__name__)

router = APIRouter(prefix="/support", tags=["support"])


# TODO: Add authentication dependency
# async def get_current_user(...) -> User:
#     pass


# ============================================================================
# Ticket Creation and Listing
# ============================================================================


@router.post(
    "/tickets",
    response_model=TicketResponse,
    summary="Create Support Ticket",
    description="""
    Create a new support ticket.

    Categories:
    - technical: Technical issues with the platform
    - content: Issues related to content quality or accuracy
    - account: Account-related issues
    - billing: Billing and payment issues
    - other: Other issues

    Priorities:
    - low: Non-urgent issues
    - medium: Standard priority (default)
    - high: Important issues
    - urgent: Critical issues requiring immediate attention
    """,
)
async def create_ticket(
    request: CreateTicketRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketResponse:
    """
    Create a support ticket.

    Args:
        request: Ticket creation request
        db: Database session

    Returns:
        Created ticket information
    """
    # TODO: Get actual user ID from authentication
    user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        support_service = SupportService(db)

        result = await support_service.create_ticket(
            user_id=user_id,
            subject=request.subject,
            description=request.description,
            category=request.category,
            priority=request.priority,
        )

        return TicketResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("create_ticket_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support ticket",
        )


@router.get(
    "/tickets/my",
    response_model=TicketListResponse,
    summary="List My Tickets",
    description="List tickets created by the current user.",
)
async def list_my_tickets(
    status_filter: Optional[str] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketListResponse:
    """
    List user's own tickets.

    Args:
        status_filter: Filter by status
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated ticket list
    """
    user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        support_service = SupportService(db)

        result = await support_service.list_user_tickets(
            user_id=user_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )

        return TicketListResponse(**result)

    except Exception as e:
        logger.error("list_my_tickets_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tickets",
        )


@router.get(
    "/tickets/all",
    response_model=TicketListResponse,
    summary="List All Tickets (Admin)",
    description="""
    List all support tickets with filtering (admin view).

    **ADMIN ONLY**
    """,
)
async def list_all_tickets(
    status_filter: Optional[str] = Query(default=None, description="Filter by status"),
    category_filter: Optional[str] = Query(default=None, description="Filter by category"),
    priority_filter: Optional[str] = Query(default=None, description="Filter by priority"),
    assigned_to_me: bool = Query(default=False, description="Show only my assigned tickets"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketListResponse:
    """
    List all tickets (admin view).

    Args:
        status_filter: Filter by status
        category_filter: Filter by category
        priority_filter: Filter by priority
        assigned_to_me: Show only assigned tickets
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated ticket list
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        support_service = SupportService(db)

        result = await support_service.list_all_tickets(
            admin_user_id=admin_user_id,
            status_filter=status_filter,
            category_filter=category_filter,
            priority_filter=priority_filter,
            assigned_to_me=assigned_to_me,
            page=page,
            page_size=page_size,
        )

        return TicketListResponse(**result)

    except Exception as e:
        logger.error("list_all_tickets_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tickets",
        )


# ============================================================================
# Ticket Details and Responses
# ============================================================================


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Get Ticket Details",
    description="Get full ticket details including all responses.",
)
async def get_ticket_details(
    ticket_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketDetailResponse:
    """
    Get ticket details.

    Args:
        ticket_id: Ticket ID
        db: Database session

    Returns:
        Full ticket details with responses
    """
    requesting_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        support_service = SupportService(db)

        result = await support_service.get_ticket_details(
            ticket_id=ticket_id,
            requesting_user_id=requesting_user_id,
        )

        return TicketDetailResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_ticket_details_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ticket details",
        )


@router.post(
    "/tickets/{ticket_id}/responses",
    response_model=AddTicketResponseResponse,
    summary="Add Ticket Response",
    description="Add a response to a support ticket (user or admin).",
)
async def add_ticket_response(
    ticket_id: UUID,
    request: AddTicketResponseRequest,
    is_staff: bool = Query(default=False, description="Is this a staff response?"),
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AddTicketResponseResponse:
    """
    Add a response to a ticket.

    Args:
        ticket_id: Ticket ID
        request: Response request
        is_staff: Whether this is a staff response
        db: Database session

    Returns:
        Created response information
    """
    responder_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        support_service = SupportService(db)

        result = await support_service.add_response(
            ticket_id=ticket_id,
            responder_user_id=responder_user_id,
            message=request.message,
            is_staff_response=is_staff,
        )

        return AddTicketResponseResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("add_ticket_response_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add ticket response",
        )


# ============================================================================
# Ticket Management (Admin)
# ============================================================================


@router.post(
    "/tickets/{ticket_id}/assign",
    response_model=AssignTicketResponse,
    summary="Assign Ticket (Admin)",
    description="""
    Assign a support ticket to an admin.

    **ADMIN ONLY**
    """,
)
async def assign_ticket(
    ticket_id: UUID,
    request: AssignTicketRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignTicketResponse:
    """
    Assign a ticket to an admin.

    Args:
        ticket_id: Ticket ID
        request: Assignment request
        db: Database session

    Returns:
        Assignment confirmation
    """
    admin_user_id = UUID("00000000-0000-0000-0000-000000000000")

    try:
        support_service = SupportService(db)

        result = await support_service.assign_ticket(
            admin_user_id=admin_user_id,
            ticket_id=ticket_id,
            assign_to_admin_id=request.assign_to_admin_id,
        )

        return AssignTicketResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("assign_ticket_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign ticket",
        )


@router.put(
    "/tickets/{ticket_id}/status",
    response_model=UpdateTicketStatusResponse,
    summary="Update Ticket Status",
    description="""
    Update ticket status (open, in_progress, resolved, closed).

    **ADMIN ONLY**
    """,
)
async def update_ticket_status(
    ticket_id: UUID,
    request: UpdateTicketStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UpdateTicketStatusResponse:
    """
    Update ticket status.

    Args:
        ticket_id: Ticket ID
        request: Status update request
        db: Database session

    Returns:
        Updated ticket information
    """
    try:
        support_service = SupportService(db)

        result = await support_service.update_ticket_status(
            ticket_id=ticket_id,
            new_status=request.new_status,
            resolution=request.resolution,
        )

        return UpdateTicketStatusResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("update_ticket_status_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket status",
        )


# ============================================================================
# Ticket Statistics
# ============================================================================


@router.get(
    "/statistics",
    response_model=TicketStatisticsResponse,
    summary="Get Ticket Statistics",
    description="""
    Get support ticket statistics.

    **ADMIN ONLY**
    """,
)
async def get_ticket_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TicketStatisticsResponse:
    """
    Get ticket statistics.

    Args:
        db: Database session

    Returns:
        Ticket statistics
    """
    try:
        support_service = SupportService(db)

        result = await support_service.get_ticket_statistics()

        return TicketStatisticsResponse(**result)

    except Exception as e:
        logger.error("get_ticket_statistics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ticket statistics",
        )
