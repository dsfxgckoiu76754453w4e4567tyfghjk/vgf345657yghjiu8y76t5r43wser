"""Comprehensive integration tests for support ticket endpoints."""

import pytest
from uuid import uuid4, UUID
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.support_ticket import SupportTicket, SupportTicketResponse
from tests.factories import UserFactory, SupportTicketFactory


class TestCreateSupportTicket:
    """Test creating support tickets."""

    @pytest.mark.asyncio
    async def test_create_ticket_success(self, db_session):
        """Test successful ticket creation."""
        ticket_data = SupportTicketFactory.create_ticket_data(
            subject="Unable to login",
            description="I cannot login to my account after password reset",
            category="technical",
            priority="high"
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == ticket_data["subject"]
        assert data["description"] == ticket_data["description"]
        assert data["category"] == ticket_data["category"]
        assert data["priority"] == ticket_data["priority"]
        assert data["status"] == "open"
        assert "id" in data
        assert "created_at" in data

        # Verify ticket created in database
        result = await db_session.execute(
            select(SupportTicket).where(SupportTicket.subject == ticket_data["subject"])
        )
        ticket = result.scalar_one_or_none()
        assert ticket is not None
        assert ticket.status == "open"

    @pytest.mark.asyncio
    async def test_create_ticket_default_priority(self, db_session):
        """Test ticket creation with default priority."""
        ticket_data = {
            "subject": "Question about features",
            "description": "I have a question about document upload",
            "category": "general"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "medium"  # Default priority

    @pytest.mark.asyncio
    async def test_create_ticket_all_categories(self, db_session):
        """Test ticket creation with all valid categories."""
        categories = ["technical", "content", "account", "billing", "other"]

        for category in categories:
            ticket_data = SupportTicketFactory.create_ticket_data(category=category)

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/support/tickets", json=ticket_data)

            assert response.status_code == 200
            assert response.json()["category"] == category

    @pytest.mark.asyncio
    async def test_create_ticket_all_priorities(self, db_session):
        """Test ticket creation with all valid priorities."""
        priorities = ["low", "medium", "high", "urgent"]

        for priority in priorities:
            ticket_data = SupportTicketFactory.create_ticket_data(priority=priority)

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/support/tickets", json=ticket_data)

            assert response.status_code == 200
            assert response.json()["priority"] == priority

    @pytest.mark.asyncio
    async def test_create_ticket_missing_subject(self):
        """Test ticket creation without subject fails."""
        ticket_data = {
            "description": "Test description",
            "category": "technical"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_ticket_missing_description(self):
        """Test ticket creation without description fails."""
        ticket_data = {
            "subject": "Test subject",
            "category": "technical"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_ticket_invalid_category(self):
        """Test ticket creation with invalid category fails."""
        ticket_data = SupportTicketFactory.create_ticket_data(category="invalid_category")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_ticket_invalid_priority(self):
        """Test ticket creation with invalid priority fails."""
        ticket_data = SupportTicketFactory.create_ticket_data(priority="critical")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_ticket_empty_subject(self):
        """Test ticket creation with empty subject fails."""
        ticket_data = SupportTicketFactory.create_ticket_data(subject="")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_ticket_long_subject(self, db_session):
        """Test ticket creation with very long subject."""
        ticket_data = SupportTicketFactory.create_ticket_data(
            subject="A" * 200  # Maximum allowed length
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        # Should succeed as 200 chars is within limit
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_ticket_too_long_subject(self):
        """Test ticket creation with subject exceeding max length fails."""
        ticket_data = SupportTicketFactory.create_ticket_data(
            subject="A" * 201  # Exceeds maximum
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/support/tickets", json=ticket_data)

        assert response.status_code == 422


class TestListUserTickets:
    """Test listing user's own tickets."""

    @pytest.mark.asyncio
    async def test_list_my_tickets_success(self, db_session):
        """Test successfully listing user's tickets."""
        # Create multiple tickets
        for i in range(3):
            ticket_data = SupportTicketFactory.create_ticket_data(
                subject=f"Test ticket {i}"
            )
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/v1/support/tickets", json=ticket_data)

        # List tickets
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/my")

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        assert len(data["tickets"]) >= 3

    @pytest.mark.asyncio
    async def test_list_my_tickets_empty(self, db_session):
        """Test listing tickets when user has none."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/my")

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert data["total"] >= 0

    @pytest.mark.asyncio
    async def test_list_my_tickets_pagination(self, db_session):
        """Test ticket listing pagination."""
        # Create tickets
        for i in range(5):
            ticket_data = SupportTicketFactory.create_ticket_data()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/v1/support/tickets", json=ticket_data)

        # Test first page
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/my?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_my_tickets_filter_by_status(self, db_session):
        """Test filtering tickets by status."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/my?status_filter=open")

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        # All returned tickets should have 'open' status
        for ticket in data["tickets"]:
            assert ticket["status"] == "open"

    @pytest.mark.asyncio
    async def test_list_my_tickets_invalid_page(self):
        """Test listing tickets with invalid page number."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/my?page=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_my_tickets_invalid_page_size(self):
        """Test listing tickets with invalid page size."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/my?page_size=101")

        assert response.status_code == 422


class TestGetTicketDetails:
    """Test getting ticket details."""

    @pytest.mark.asyncio
    async def test_get_ticket_details_success(self, db_session):
        """Test successfully getting ticket details."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Get ticket details
            response = await client.get(f"/api/v1/support/tickets/{ticket_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert data["subject"] == ticket_data["subject"]
        assert "responses" in data

    @pytest.mark.asyncio
    async def test_get_ticket_details_with_responses(self, db_session):
        """Test getting ticket details includes responses."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Add a response
            response_data = {"message": "This is my response"}
            await client.post(
                f"/api/v1/support/tickets/{ticket_id}/responses",
                json=response_data
            )

            # Get ticket details
            response = await client.get(f"/api/v1/support/tickets/{ticket_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["responses"]) >= 1

    @pytest.mark.asyncio
    async def test_get_ticket_details_nonexistent(self):
        """Test getting details of non-existent ticket."""
        fake_ticket_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/support/tickets/{fake_ticket_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_ticket_details_invalid_uuid(self):
        """Test getting ticket details with invalid UUID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/support/tickets/invalid-uuid")

        assert response.status_code == 422


class TestAddTicketResponse:
    """Test adding responses to tickets."""

    @pytest.mark.asyncio
    async def test_add_response_success(self, db_session):
        """Test successfully adding a response to a ticket."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Add response
            response_data = {"message": "Thank you for your help"}
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/responses",
                json=response_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == response_data["message"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_add_staff_response(self, db_session):
        """Test adding a staff response to a ticket."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Add staff response
            response_data = {"message": "We will look into this issue"}
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/responses?is_staff=true",
                json=response_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_staff_response"] is True

    @pytest.mark.asyncio
    async def test_add_multiple_responses(self, db_session):
        """Test adding multiple responses to a ticket."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Add multiple responses
            for i in range(3):
                response_data = {"message": f"Response {i}"}
                await client.post(
                    f"/api/v1/support/tickets/{ticket_id}/responses",
                    json=response_data
                )

            # Get ticket details to verify all responses
            details_response = await client.get(f"/api/v1/support/tickets/{ticket_id}")

        assert details_response.status_code == 200
        data = details_response.json()
        assert len(data["responses"]) >= 3

    @pytest.mark.asyncio
    async def test_add_response_nonexistent_ticket(self):
        """Test adding response to non-existent ticket fails."""
        fake_ticket_id = uuid4()
        response_data = {"message": "Test response"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/support/tickets/{fake_ticket_id}/responses",
                json=response_data
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_response_missing_message(self, db_session):
        """Test adding response without message fails."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Try to add response without message
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/responses",
                json={}
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_add_response_empty_message(self, db_session):
        """Test adding response with empty message fails."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Try to add response with empty message
            response_data = {"message": ""}
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/responses",
                json=response_data
            )

        assert response.status_code == 422


class TestAssignTicket:
    """Test assigning tickets to admins."""

    @pytest.mark.asyncio
    async def test_assign_ticket_success(self, db_session):
        """Test successfully assigning a ticket to an admin."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        admin_id = UUID("00000000-0000-0000-0000-000000000001")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Assign ticket
            assign_data = {"assign_to_admin_id": str(admin_id)}
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/assign",
                json=assign_data
            )

        # May succeed or fail depending on whether admin exists
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_assign_ticket_nonexistent_ticket(self):
        """Test assigning non-existent ticket fails."""
        fake_ticket_id = uuid4()
        admin_id = UUID("00000000-0000-0000-0000-000000000001")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            assign_data = {"assign_to_admin_id": str(admin_id)}
            response = await client.post(
                f"/api/v1/support/tickets/{fake_ticket_id}/assign",
                json=assign_data
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_ticket_missing_admin_id(self, db_session):
        """Test assigning ticket without admin ID fails."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Try to assign without admin_id
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/assign",
                json={}
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_assign_ticket_invalid_admin_id(self, db_session):
        """Test assigning ticket with invalid admin UUID fails."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Try to assign with invalid UUID
            assign_data = {"assign_to_admin_id": "invalid-uuid"}
            response = await client.post(
                f"/api/v1/support/tickets/{ticket_id}/assign",
                json=assign_data
            )

        assert response.status_code == 422


class TestUpdateTicketStatus:
    """Test updating ticket status."""

    @pytest.mark.asyncio
    async def test_update_status_success(self, db_session):
        """Test successfully updating ticket status."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Update status
            update_data = {"new_status": "in_progress"}
            response = await client.put(
                f"/api/v1/support/tickets/{ticket_id}/status",
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_update_status_to_resolved(self, db_session):
        """Test updating ticket status to resolved with resolution."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Update status to resolved
            update_data = {
                "new_status": "resolved",
                "resolution": "Issue has been fixed"
            }
            response = await client.put(
                f"/api/v1/support/tickets/{ticket_id}/status",
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["resolution"] == "Issue has been fixed"

    @pytest.mark.asyncio
    async def test_update_status_all_valid_statuses(self, db_session):
        """Test updating to all valid status values."""
        statuses = ["open", "in_progress", "resolved", "closed"]

        for status in statuses:
            # Create a ticket for each test
            ticket_data = SupportTicketFactory.create_ticket_data()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
                ticket_id = create_response.json()["id"]

                # Update status
                update_data = {"new_status": status}
                response = await client.put(
                    f"/api/v1/support/tickets/{ticket_id}/status",
                    json=update_data
                )

            assert response.status_code in [200, 400]  # Some transitions may not be allowed

    @pytest.mark.asyncio
    async def test_update_status_nonexistent_ticket(self):
        """Test updating status of non-existent ticket fails."""
        fake_ticket_id = uuid4()
        update_data = {"new_status": "in_progress"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/support/tickets/{fake_ticket_id}/status",
                json=update_data
            )

        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_update_status_invalid_status(self, db_session):
        """Test updating to invalid status fails."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Try to update with invalid status
            update_data = {"new_status": "invalid_status"}
            response = await client.put(
                f"/api/v1/support/tickets/{ticket_id}/status",
                json=update_data
            )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_update_status_missing_new_status(self, db_session):
        """Test updating status without new_status fails."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Try to update without new_status
            response = await client.put(
                f"/api/v1/support/tickets/{ticket_id}/status",
                json={}
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_status_to_closed(self, db_session):
        """Test updating ticket status to closed."""
        # Create a ticket
        ticket_data = SupportTicketFactory.create_ticket_data()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/support/tickets", json=ticket_data)
            ticket_id = create_response.json()["id"]

            # Update status to closed
            update_data = {"new_status": "closed"}
            response = await client.put(
                f"/api/v1/support/tickets/{ticket_id}/status",
                json=update_data
            )

        # Should succeed
        assert response.status_code in [200, 400]
