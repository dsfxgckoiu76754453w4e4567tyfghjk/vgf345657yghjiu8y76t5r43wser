"""Email notification service."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        """Initialize email service."""
        # Email configuration from settings
        self.smtp_host = getattr(settings, "smtp_host", "smtp.gmail.com")
        self.smtp_port = getattr(settings, "smtp_port", 587)
        self.smtp_username = getattr(settings, "smtp_username", None)
        self.smtp_password = getattr(settings, "smtp_password", None)
        self.from_email = getattr(settings, "from_email", "noreply@example.com")
        self.from_name = getattr(settings, "from_name", "Shia Islamic Chatbot")

    # ========================================================================
    # Core Email Sending
    # ========================================================================

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add text part
            if text_body:
                text_part = MIMEText(text_body, "plain")
                msg.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Send email
            if self.smtp_username and self.smtp_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

                logger.info("email_sent", to_email=to_email, subject=subject)
                return True
            else:
                logger.warn(
                    "email_not_configured",
                    message="SMTP credentials not configured. Email not sent.",
                    to_email=to_email,
                    subject=subject,
                )
                return False

        except Exception as e:
            logger.error("email_send_failed", error=str(e), to_email=to_email)
            return False

    # ========================================================================
    # Support Ticket Notifications
    # ========================================================================

    async def send_ticket_created_notification(
        self, to_email: str, ticket_id: str, subject: str
    ) -> bool:
        """
        Send notification when a support ticket is created.

        Args:
            to_email: User's email
            ticket_id: Ticket ID
            subject: Ticket subject

        Returns:
            True if sent successfully
        """
        email_subject = f"Support Ticket Created: {subject}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #4CAF50;">Support Ticket Created</h2>
            <p>Your support ticket has been created successfully.</p>

            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p><strong>Ticket ID:</strong> {ticket_id}</p>
                <p><strong>Subject:</strong> {subject}</p>
            </div>

            <p>Our support team will review your ticket and respond as soon as possible.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
Support Ticket Created

Your support ticket has been created successfully.

Ticket ID: {ticket_id}
Subject: {subject}

Our support team will review your ticket and respond as soon as possible.
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)

    async def send_ticket_response_notification(
        self, to_email: str, ticket_id: str, subject: str, response_preview: str
    ) -> bool:
        """
        Send notification when a ticket receives a response.

        Args:
            to_email: User's email
            ticket_id: Ticket ID
            subject: Ticket subject
            response_preview: Preview of the response

        Returns:
            True if sent successfully
        """
        email_subject = f"New Response to Your Support Ticket: {subject}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2196F3;">New Response to Your Support Ticket</h2>
            <p>Your support ticket has received a new response from our team.</p>

            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p><strong>Ticket ID:</strong> {ticket_id}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Response Preview:</strong></p>
                <p style="font-style: italic; color: #666;">{response_preview}...</p>
            </div>

            <p>
                <a href="#" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Full Ticket
                </a>
            </p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
New Response to Your Support Ticket

Your support ticket has received a new response from our team.

Ticket ID: {ticket_id}
Subject: {subject}

Response Preview:
{response_preview}...

Please log in to view the full response.
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)

    async def send_ticket_resolved_notification(
        self, to_email: str, ticket_id: str, subject: str, resolution: str
    ) -> bool:
        """
        Send notification when a ticket is resolved.

        Args:
            to_email: User's email
            ticket_id: Ticket ID
            subject: Ticket subject
            resolution: Resolution message

        Returns:
            True if sent successfully
        """
        email_subject = f"Support Ticket Resolved: {subject}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #4CAF50;">Support Ticket Resolved</h2>
            <p>Your support ticket has been resolved.</p>

            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p><strong>Ticket ID:</strong> {ticket_id}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Resolution:</strong></p>
                <p style="color: #666;">{resolution}</p>
            </div>

            <p>If you have any further questions, please feel free to create a new ticket.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
Support Ticket Resolved

Your support ticket has been resolved.

Ticket ID: {ticket_id}
Subject: {subject}

Resolution:
{resolution}

If you have any further questions, please feel free to create a new ticket.
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)

    # ========================================================================
    # Document Moderation Notifications
    # ========================================================================

    async def send_document_approved_notification(
        self, to_email: str, document_id: str, document_title: str
    ) -> bool:
        """
        Send notification when a document is approved.

        Args:
            to_email: User's email
            document_id: Document ID
            document_title: Document title

        Returns:
            True if sent successfully
        """
        email_subject = f"Document Approved: {document_title}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #4CAF50;">Document Approved</h2>
            <p>Your uploaded document has been reviewed and approved!</p>

            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p><strong>Document ID:</strong> {document_id}</p>
                <p><strong>Title:</strong> {document_title}</p>
            </div>

            <p>Your document is now available in the system and will be used to improve responses.</p>

            <p>Thank you for your contribution to the community!</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
Document Approved

Your uploaded document has been reviewed and approved!

Document ID: {document_id}
Title: {document_title}

Your document is now available in the system and will be used to improve responses.

Thank you for your contribution to the community!
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)

    async def send_document_rejected_notification(
        self, to_email: str, document_id: str, document_title: str, reason: str
    ) -> bool:
        """
        Send notification when a document is rejected.

        Args:
            to_email: User's email
            document_id: Document ID
            document_title: Document title
            reason: Rejection reason

        Returns:
            True if sent successfully
        """
        email_subject = f"Document Rejected: {document_title}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #f44336;">Document Rejected</h2>
            <p>Unfortunately, your uploaded document could not be approved.</p>

            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p><strong>Document ID:</strong> {document_id}</p>
                <p><strong>Title:</strong> {document_title}</p>
                <p><strong>Reason:</strong></p>
                <p style="color: #666;">{reason}</p>
            </div>

            <p>If you have questions about this decision, please contact our support team.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
Document Rejected

Unfortunately, your uploaded document could not be approved.

Document ID: {document_id}
Title: {document_title}

Reason:
{reason}

If you have questions about this decision, please contact our support team.
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)

    # ========================================================================
    # Account Notifications
    # ========================================================================

    async def send_account_ban_notification(
        self, to_email: str, ban_reason: str, ban_duration: Optional[str] = None
    ) -> bool:
        """
        Send notification when an account is banned.

        Args:
            to_email: User's email
            ban_reason: Reason for ban
            ban_duration: Duration of ban (None for permanent)

        Returns:
            True if sent successfully
        """
        duration_text = f"for {ban_duration}" if ban_duration else "permanently"
        email_subject = "Account Suspended"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #f44336;">Account Suspended</h2>
            <p>Your account has been suspended {duration_text}.</p>

            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p><strong>Reason:</strong></p>
                <p style="color: #666;">{ban_reason}</p>
            </div>

            <p>If you believe this was done in error, please contact our support team.</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
Account Suspended

Your account has been suspended {duration_text}.

Reason:
{ban_reason}

If you believe this was done in error, please contact our support team.
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)

    async def send_account_unban_notification(self, to_email: str) -> bool:
        """
        Send notification when an account is unbanned.

        Args:
            to_email: User's email

        Returns:
            True if sent successfully
        """
        email_subject = "Account Reinstated"

        html_body = """
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #4CAF50;">Account Reinstated</h2>
            <p>Your account has been reinstated and you can now log in again.</p>

            <p>Welcome back!</p>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = """
Account Reinstated

Your account has been reinstated and you can now log in again.

Welcome back!
        """

        return await self.send_email(to_email, email_subject, html_body, text_body)
