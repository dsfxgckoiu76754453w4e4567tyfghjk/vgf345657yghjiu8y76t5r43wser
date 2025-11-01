"""Support ticket service."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.support_ticket import SupportTicket, SupportTicketResponse
from app.models.user import User

logger = get_logger(__name__)


class SupportService:
    """Service for handling support tickets."""

    def __init__(self, db: AsyncSession):
        """Initialize support service.

        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # Ticket Creation
    # ========================================================================

    async def create_ticket(
        self,
        user_id: UUID,
        subject: str,
        description: str,
        category: str = "other",
        priority: str = "medium",
    ) -> dict:
        """
        Create a new support ticket.

        Args:
            user_id: ID of user creating the ticket
            subject: Ticket subject
            description: Detailed description
            category: Ticket category
            priority: Ticket priority

        Returns:
            Created ticket information
        """
        # Validate category
        if category not in ["technical", "content", "account", "billing", "other"]:
            raise ValueError("Invalid category")

        # Validate priority
        if priority not in ["low", "medium", "high", "urgent"]:
            raise ValueError("Invalid priority")

        # Create ticket
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            status="open",
        )

        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)

        logger.info(
            "support_ticket_created",
            ticket_id=str(ticket.id),
            user_id=str(user_id),
            category=category,
            priority=priority,
        )

        return {
            "ticket_id": str(ticket.id),
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat(),
        }

    # ========================================================================
    # Ticket Listing
    # ========================================================================

    async def list_user_tickets(
        self,
        user_id: UUID,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        List tickets for a specific user.

        Args:
            user_id: ID of user
            status_filter: Filter by status
            page: Page number
            page_size: Items per page

        Returns:
            Paginated ticket list
        """
        query = select(SupportTicket).where(SupportTicket.user_id == user_id)

        if status_filter:
            query = query.where(SupportTicket.status == status_filter)

        query = query.order_by(SupportTicket.created_at.desc())

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        tickets = result.scalars().all()

        return {
            "tickets": [
                {
                    "ticket_id": str(ticket.id),
                    "subject": ticket.subject,
                    "category": ticket.category,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "created_at": ticket.created_at.isoformat(),
                    "updated_at": ticket.updated_at.isoformat(),
                    "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                }
                for ticket in tickets
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    async def list_all_tickets(
        self,
        admin_user_id: UUID,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        assigned_to_me: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List all tickets (admin view).

        Args:
            admin_user_id: ID of admin viewing tickets
            status_filter: Filter by status
            category_filter: Filter by category
            priority_filter: Filter by priority
            assigned_to_me: Show only tickets assigned to this admin
            page: Page number
            page_size: Items per page

        Returns:
            Paginated ticket list with user information
        """
        query = select(SupportTicket).options(selectinload(SupportTicket.responses))

        # Apply filters
        if status_filter:
            query = query.where(SupportTicket.status == status_filter)

        if category_filter:
            query = query.where(SupportTicket.category == category_filter)

        if priority_filter:
            query = query.where(SupportTicket.priority == priority_filter)

        if assigned_to_me:
            query = query.where(SupportTicket.assigned_to_admin_id == admin_user_id)

        query = query.order_by(
            SupportTicket.priority.desc(), SupportTicket.created_at.desc()
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        tickets = result.scalars().all()

        return {
            "tickets": [
                {
                    "ticket_id": str(ticket.id),
                    "user_id": str(ticket.user_id),
                    "subject": ticket.subject,
                    "description": ticket.description[:200] + "..." if len(ticket.description) > 200 else ticket.description,
                    "category": ticket.category,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "assigned_to": str(ticket.assigned_to_admin_id)
                    if ticket.assigned_to_admin_id
                    else None,
                    "response_count": len(ticket.responses),
                    "created_at": ticket.created_at.isoformat(),
                    "updated_at": ticket.updated_at.isoformat(),
                }
                for ticket in tickets
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    # ========================================================================
    # Ticket Details
    # ========================================================================

    async def get_ticket_details(self, ticket_id: UUID, requesting_user_id: UUID) -> dict:
        """
        Get full ticket details with responses.

        Args:
            ticket_id: ID of ticket
            requesting_user_id: ID of user requesting details (for permission check)

        Returns:
            Full ticket information with responses
        """
        query = select(SupportTicket).where(SupportTicket.id == ticket_id).options(
            selectinload(SupportTicket.responses)
        )

        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise ValueError("Ticket not found")

        # Permission check (user can only view their own tickets unless admin)
        # This would need to check user role in production
        # For now, we'll allow the requesting user to view

        return {
            "ticket_id": str(ticket.id),
            "user_id": str(ticket.user_id),
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "assigned_to": str(ticket.assigned_to_admin_id)
            if ticket.assigned_to_admin_id
            else None,
            "resolution": ticket.resolution,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
            "responses": [
                {
                    "response_id": str(response.id),
                    "responder_user_id": str(response.responder_user_id),
                    "message": response.message,
                    "is_staff_response": response.is_staff_response,
                    "created_at": response.created_at.isoformat(),
                }
                for response in sorted(ticket.responses, key=lambda r: r.created_at)
            ],
        }

    # ========================================================================
    # Ticket Responses
    # ========================================================================

    async def add_response(
        self,
        ticket_id: UUID,
        responder_user_id: UUID,
        message: str,
        is_staff_response: bool = False,
    ) -> dict:
        """
        Add a response to a ticket.

        Args:
            ticket_id: ID of ticket
            responder_user_id: ID of user responding
            message: Response message
            is_staff_response: True if response is from staff/admin

        Returns:
            Created response information
        """
        # Verify ticket exists
        result = await self.db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise ValueError("Ticket not found")

        # Create response
        response = SupportTicketResponse(
            ticket_id=ticket_id,
            responder_user_id=responder_user_id,
            message=message,
            is_staff_response=is_staff_response,
        )

        self.db.add(response)

        # Update ticket status if staff is responding
        if is_staff_response and ticket.status == "open":
            ticket.status = "in_progress"

        await self.db.commit()
        await self.db.refresh(response)

        logger.info(
            "support_ticket_response_added",
            ticket_id=str(ticket_id),
            responder_user_id=str(responder_user_id),
            is_staff=is_staff_response,
        )

        return {
            "response_id": str(response.id),
            "ticket_id": str(ticket_id),
            "message": message,
            "is_staff_response": is_staff_response,
            "created_at": response.created_at.isoformat(),
        }

    # ========================================================================
    # Ticket Management
    # ========================================================================

    async def assign_ticket(
        self, admin_user_id: UUID, ticket_id: UUID, assign_to_admin_id: UUID
    ) -> dict:
        """
        Assign a ticket to an admin.

        Args:
            admin_user_id: ID of admin performing assignment
            ticket_id: ID of ticket to assign
            assign_to_admin_id: ID of admin to assign to

        Returns:
            Assignment confirmation
        """
        result = await self.db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise ValueError("Ticket not found")

        ticket.assigned_to_admin_id = assign_to_admin_id

        if ticket.status == "open":
            ticket.status = "in_progress"

        await self.db.commit()

        logger.info(
            "support_ticket_assigned",
            ticket_id=str(ticket_id),
            assigned_by=str(admin_user_id),
            assigned_to=str(assign_to_admin_id),
        )

        return {
            "ticket_id": str(ticket_id),
            "assigned_to": str(assign_to_admin_id),
            "status": ticket.status,
            "assigned_at": datetime.utcnow().isoformat(),
        }

    async def update_ticket_status(
        self,
        ticket_id: UUID,
        new_status: str,
        resolution: Optional[str] = None,
    ) -> dict:
        """
        Update ticket status.

        Args:
            ticket_id: ID of ticket
            new_status: New status
            resolution: Resolution message (required for resolved/closed)

        Returns:
            Updated ticket information
        """
        if new_status not in ["open", "in_progress", "resolved", "closed"]:
            raise ValueError("Invalid status")

        result = await self.db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise ValueError("Ticket not found")

        ticket.status = new_status

        if new_status == "resolved":
            ticket.resolved_at = datetime.utcnow()
            if resolution:
                ticket.resolution = resolution

        elif new_status == "closed":
            ticket.closed_at = datetime.utcnow()
            if not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()
            if resolution:
                ticket.resolution = resolution

        await self.db.commit()

        logger.info(
            "support_ticket_status_updated",
            ticket_id=str(ticket_id),
            new_status=new_status,
        )

        return {
            "ticket_id": str(ticket_id),
            "status": new_status,
            "resolution": ticket.resolution,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
            "updated_at": ticket.updated_at.isoformat(),
        }

    # ========================================================================
    # Statistics
    # ========================================================================

    async def get_ticket_statistics(self) -> dict:
        """
        Get support ticket statistics.

        Returns:
            Ticket statistics
        """
        # Total tickets
        total_result = await self.db.execute(select(func.count(SupportTicket.id)))
        total = total_result.scalar()

        # Open tickets
        open_result = await self.db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "open")
        )
        open_count = open_result.scalar()

        # In progress tickets
        in_progress_result = await self.db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "in_progress")
        )
        in_progress_count = in_progress_result.scalar()

        # Resolved tickets
        resolved_result = await self.db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "resolved")
        )
        resolved_count = resolved_result.scalar()

        # Closed tickets
        closed_result = await self.db.execute(
            select(func.count(SupportTicket.id)).where(SupportTicket.status == "closed")
        )
        closed_count = closed_result.scalar()

        return {
            "total": total,
            "by_status": {
                "open": open_count,
                "in_progress": in_progress_count,
                "resolved": resolved_count,
                "closed": closed_count,
            },
            "resolution_rate": (resolved_count + closed_count) / total if total > 0 else 0.0,
        }
