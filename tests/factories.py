"""Test factories for creating test data."""

from datetime import datetime, timezone
from uuid import uuid4
from faker import Faker

fake = Faker()


class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create_user_data(
        email: str = None,
        password: str = "TestPassword123!",
        full_name: str = None,
        **kwargs
    ) -> dict:
        """Create user registration data."""
        return {
            "email": email or f"test_{uuid4()}@example.com",
            "password": password,
            "full_name": full_name or fake.name(),
            "marja_preference": kwargs.get("marja_preference", "sistani"),
            "preferred_language": kwargs.get("preferred_language", "fa"),
        }


class DocumentFactory:
    """Factory for creating test documents."""

    @staticmethod
    def create_document_data(
        title: str = None,
        content: str = None,
        **kwargs
    ) -> dict:
        """Create document upload data."""
        return {
            "title": title or fake.sentence(),
            "content": content or fake.text(500),
            "language": kwargs.get("language", "fa"),
            "source": kwargs.get("source", "test"),
            "category": kwargs.get("category", "general"),
        }


class SupportTicketFactory:
    """Factory for creating test support tickets."""

    @staticmethod
    def create_ticket_data(
        subject: str = None,
        description: str = None,
        **kwargs
    ) -> dict:
        """Create support ticket data."""
        return {
            "subject": subject or fake.sentence(),
            "description": description or fake.text(200),
            "category": kwargs.get("category", "general"),
            "priority": kwargs.get("priority", "medium"),
        }


class AdminFactory:
    """Factory for creating admin-related test data."""

    @staticmethod
    def create_admin_api_key_data(name: str = None, **kwargs) -> dict:
        """Create admin API key data."""
        return {
            "name": name or f"test_key_{uuid4().hex[:8]}",
            "expires_in_days": kwargs.get("expires_in_days", 30),
            "permissions": kwargs.get("permissions", ["read", "write"]),
        }
