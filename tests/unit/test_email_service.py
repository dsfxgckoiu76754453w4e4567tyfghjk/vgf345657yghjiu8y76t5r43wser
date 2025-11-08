"""Unit tests for email service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.services.email_service import EmailService


@pytest.fixture
def email_service():
    """Create email service instance."""
    with patch("app.services.email_service.get_settings") as mock_settings:
        mock_settings.return_value.smtp_host = "smtp.gmail.com"
        mock_settings.return_value.smtp_port = 587
        mock_settings.return_value.smtp_username = "test@example.com"
        mock_settings.return_value.smtp_password = "testpassword"
        mock_settings.return_value.from_email = "noreply@example.com"
        mock_settings.return_value.from_name = "Test Service"

        return EmailService()


# ============================================================================
# Test: Email Service Initialization
# ============================================================================


class TestEmailServiceInitialization:
    """Test cases for EmailService initialization."""

    @patch("app.services.email_service.get_settings")
    def test_initialization_with_settings(self, mock_get_settings):
        """Test that service initializes with SMTP settings."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_port = 465
        mock_settings.smtp_username = "user@test.com"
        mock_settings.smtp_password = "password123"
        mock_settings.from_email = "no-reply@test.com"
        mock_settings.from_name = "Test App"
        mock_get_settings.return_value = mock_settings

        service = EmailService()

        assert service.smtp_host == "smtp.test.com"
        assert service.smtp_port == 465
        assert service.smtp_username == "user@test.com"
        assert service.smtp_password == "password123"
        assert service.from_email == "no-reply@test.com"
        assert service.from_name == "Test App"

    @patch("app.services.email_service.get_settings")
    def test_initialization_with_defaults(self, mock_get_settings):
        """Test initialization with default values when settings missing."""
        mock_settings = MagicMock()
        # Remove attributes to test defaults
        for attr in ["smtp_host", "smtp_port", "smtp_username", "smtp_password", "from_email", "from_name"]:
            if hasattr(mock_settings, attr):
                delattr(mock_settings, attr)
        mock_get_settings.return_value = mock_settings

        service = EmailService()

        # Should use defaults
        assert service.smtp_host == "smtp.gmail.com"
        assert service.smtp_port == 587
        assert service.smtp_username is None
        assert service.smtp_password is None
        assert service.from_email == "noreply@example.com"
        assert service.from_name == "Shia Islamic Chatbot"


# ============================================================================
# Test: Send Email (Core Method)
# ============================================================================


class TestEmailServiceSendEmail:
    """Test cases for core email sending."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_email_success(self, mock_smtp, email_service):
        """Test sending email successfully."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send email
        result = await email_service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
        )

        # Verify success
        assert result is True

        # Verify SMTP operations
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "testpassword")
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_email_without_text_body(self, mock_smtp, email_service):
        """Test sending email with only HTML body."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_without_credentials(self):
        """Test sending email when SMTP credentials not configured."""
        with patch("app.services.email_service.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.smtp_host = "smtp.gmail.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_username = None  # No credentials
            mock_settings.smtp_password = None
            mock_settings.from_email = "noreply@example.com"
            mock_settings.from_name = "Test"
            mock_get_settings.return_value = mock_settings

            service = EmailService()

            result = await service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            # Should return False when credentials not configured
            assert result is False

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_email_handles_smtp_error(self, mock_smtp, email_service):
        """Test handling SMTP errors during email sending."""
        # Mock SMTP to raise exception
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP connection failed")

        result = await email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        # Should return False on error
        assert result is False


# ============================================================================
# Test: Support Ticket Notifications
# ============================================================================


class TestEmailServiceTicketNotifications:
    """Test cases for support ticket notifications."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_ticket_created_notification(self, mock_smtp, email_service):
        """Test sending ticket created notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_ticket_created_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            subject="Cannot access my account",
        )

        # Verify success
        assert result is True

        # Verify send_message was called
        mock_server.send_message.assert_called_once()

        # Verify message content
        call_args = mock_server.send_message.call_args[0][0]
        assert "TICKET-123" in str(call_args)
        assert "Cannot access my account" in str(call_args)

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_ticket_response_notification(self, mock_smtp, email_service):
        """Test sending ticket response notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_ticket_response_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            subject="Cannot access my account",
            response_preview="We have reviewed your issue and...",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify response preview in message
        call_args = mock_server.send_message.call_args[0][0]
        assert "We have reviewed your issue and..." in str(call_args)

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_ticket_resolved_notification(self, mock_smtp, email_service):
        """Test sending ticket resolved notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_ticket_resolved_notification(
            to_email="user@example.com",
            ticket_id="TICKET-123",
            subject="Cannot access my account",
            resolution="Your account has been restored. You can now log in.",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify resolution in message
        call_args = mock_server.send_message.call_args[0][0]
        assert "Your account has been restored" in str(call_args)


# ============================================================================
# Test: Document Moderation Notifications
# ============================================================================


class TestEmailServiceDocumentNotifications:
    """Test cases for document moderation notifications."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_document_approved_notification(self, mock_smtp, email_service):
        """Test sending document approved notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_document_approved_notification(
            to_email="user@example.com",
            document_id="DOC-456",
            document_title="Islamic History Overview",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify document details in message
        call_args = mock_server.send_message.call_args[0][0]
        assert "DOC-456" in str(call_args)
        assert "Islamic History Overview" in str(call_args)
        assert "approved" in str(call_args).lower()

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_document_rejected_notification(self, mock_smtp, email_service):
        """Test sending document rejected notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_document_rejected_notification(
            to_email="user@example.com",
            document_id="DOC-789",
            document_title="Test Document",
            reason="Content does not meet quality standards",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify rejection details in message
        call_args = mock_server.send_message.call_args[0][0]
        assert "DOC-789" in str(call_args)
        assert "Test Document" in str(call_args)
        assert "Content does not meet quality standards" in str(call_args)


# ============================================================================
# Test: Account Notifications
# ============================================================================


class TestEmailServiceAccountNotifications:
    """Test cases for account notifications."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_account_ban_notification_permanent(
        self,
        mock_smtp,
        email_service,
    ):
        """Test sending permanent account ban notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_account_ban_notification(
            to_email="user@example.com",
            ban_reason="Violation of terms of service",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify ban details in message
        call_args = mock_server.send_message.call_args[0][0]
        assert "permanently" in str(call_args).lower()
        assert "Violation of terms of service" in str(call_args)

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_account_ban_notification_temporary(
        self,
        mock_smtp,
        email_service,
    ):
        """Test sending temporary account ban notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_account_ban_notification(
            to_email="user@example.com",
            ban_reason="Spam behavior detected",
            ban_duration="7 days",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify ban duration in message
        call_args = mock_server.send_message.call_args[0][0]
        assert "7 days" in str(call_args)
        assert "Spam behavior detected" in str(call_args)

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_send_account_unban_notification(self, mock_smtp, email_service):
        """Test sending account unban notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_account_unban_notification(
            to_email="user@example.com",
        )

        # Verify success
        assert result is True
        mock_server.send_message.assert_called_once()

        # Verify reinstatement message
        call_args = mock_server.send_message.call_args[0][0]
        assert "reinstated" in str(call_args).lower()
        assert "Welcome back" in str(call_args)


# ============================================================================
# Test: Email Content Formatting
# ============================================================================


class TestEmailServiceContentFormatting:
    """Test cases for email content formatting."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_email_contains_both_html_and_text(self, mock_smtp, email_service):
        """Test that email contains both HTML and text parts."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        await email_service.send_email(
            to_email="user@example.com",
            subject="Test Email",
            html_body="<h1>HTML Content</h1>",
            text_body="Text Content",
        )

        # Get the message that was sent
        call_args = mock_server.send_message.call_args[0][0]

        # Verify it's a multipart message
        assert call_args.is_multipart()

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_email_from_header_format(self, mock_smtp, email_service):
        """Test that From header is properly formatted."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        await email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        # Get the message
        call_args = mock_server.send_message.call_args[0][0]

        # Verify From header format
        assert "Test Service" in call_args["From"]
        assert "noreply@example.com" in call_args["From"]

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_notification_emails_include_disclaimer(
        self,
        mock_smtp,
        email_service,
    ):
        """Test that notification emails include automated notification disclaimer."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test ticket notification
        await email_service.send_ticket_created_notification(
            to_email="user@example.com",
            ticket_id="TICKET-001",
            subject="Test Ticket",
        )

        call_args = mock_server.send_message.call_args[0][0]
        assert "automated notification" in str(call_args).lower()
        assert "do not reply" in str(call_args).lower()


# ============================================================================
# Test: Error Handling
# ============================================================================


class TestEmailServiceErrorHandling:
    """Test cases for error handling."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_handles_authentication_error(self, mock_smtp, email_service):
        """Test handling authentication errors."""
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        # Should return False on error
        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_handles_send_message_error(self, mock_smtp, email_service):
        """Test handling send message errors."""
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("Failed to send")
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        # Should return False on error
        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.email_service.smtplib.SMTP")
    async def test_notification_methods_return_false_on_error(
        self,
        mock_smtp,
        email_service,
    ):
        """Test that notification methods return False on error."""
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("Send failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test various notification methods
        result1 = await email_service.send_ticket_created_notification(
            "user@example.com", "TICKET-1", "Subject"
        )
        result2 = await email_service.send_document_approved_notification(
            "user@example.com", "DOC-1", "Title"
        )
        result3 = await email_service.send_account_ban_notification(
            "user@example.com", "Reason"
        )

        # All should return False
        assert result1 is False
        assert result2 is False
        assert result3 is False
