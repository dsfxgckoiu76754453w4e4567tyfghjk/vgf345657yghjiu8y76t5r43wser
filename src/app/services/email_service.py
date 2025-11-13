"""Email notification service with Mailgun and SMTP support."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.templates.email_templates import EmailTemplates

logger = get_logger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending email notifications via Mailgun or SMTP."""

    def __init__(self):
        """Initialize email service."""
        self.provider = settings.email_provider

        # Mailgun configuration
        self.mailgun_api_key = settings.mailgun_api_key
        self.mailgun_domain = settings.mailgun_domain
        self.mailgun_from_email = settings.mailgun_from_email
        self.mailgun_from_name = settings.mailgun_from_name

        # SMTP configuration (fallback)
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.smtp_from_email = settings.smtp_from_email
        self.smtp_from_name = settings.smtp_from_name

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
        Send an email using configured provider (Mailgun or SMTP).

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if self.provider == "mailgun" and self.mailgun_api_key and self.mailgun_domain:
            return await self._send_via_mailgun(to_email, subject, html_body, text_body)
        elif self.smtp_username and self.smtp_password:
            return await self._send_via_smtp(to_email, subject, html_body, text_body)
        else:
            logger.error(
                "email_not_configured",
                message="No email provider configured. Please set up Mailgun or SMTP credentials.",
            )
            return False

    async def _send_via_mailgun(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email via Mailgun API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            from mailgun.client import Client

            # Initialize Mailgun client
            client = Client(auth=("api", self.mailgun_api_key))

            # Prepare email data
            data = {
                "from": f"{self.mailgun_from_name} <{self.mailgun_from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_body,
            }

            # Add plain text body if provided
            if text_body:
                data["text"] = text_body

            # Send via Mailgun
            response = client.messages.create(data=data, domain=self.mailgun_domain)

            if response.status_code == 200:
                logger.info(
                    "email_sent_via_mailgun",
                    to_email=to_email,
                    subject=subject,
                    message_id=response.json().get("id"),
                )
                return True
            else:
                logger.error(
                    "mailgun_send_failed",
                    to_email=to_email,
                    status_code=response.status_code,
                    response=response.text,
                )
                return False

        except ImportError:
            logger.error(
                "mailgun_not_installed",
                message="mailgun-python package not installed. Install with: pip install mailgun-python",
            )
            # Fallback to SMTP
            return await self._send_via_smtp(to_email, subject, html_body, text_body)
        except Exception as e:
            logger.error(
                "mailgun_send_error",
                error=str(e),
                to_email=to_email,
            )
            # Fallback to SMTP
            return await self._send_via_smtp(to_email, subject, html_body, text_body)

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email via SMTP (fallback method).

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
            msg["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
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

                logger.info("email_sent_via_smtp", to_email=to_email, subject=subject)
                return True
            else:
                logger.error(
                    "smtp_not_configured",
                    message="SMTP credentials not configured.",
                )
                return False

        except Exception as e:
            logger.error("smtp_send_failed", error=str(e), to_email=to_email)
            return False

    # ========================================================================
    # OTP & Authentication Emails
    # ========================================================================

    async def send_otp_email(
        self,
        to_email: str,
        otp_code: str,
        purpose: str = "email_verification",
    ) -> bool:
        """
        Send OTP verification email.

        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            purpose: Purpose (email_verification or password_reset)

        Returns:
            True if sent successfully
        """
        subject = "Verify Your Email" if purpose == "email_verification" else "Reset Your Password"
        html_body, text_body = EmailTemplates.otp_verification_email(otp_code, purpose)

        return await self.send_email(to_email, subject, html_body, text_body)

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """
        Send welcome email after successful registration.

        Args:
            to_email: User's email address
            user_name: User's full name

        Returns:
            True if sent successfully
        """
        subject = "Welcome to WisQu - Your Islamic Knowledge Companion"
        html_body, text_body = EmailTemplates.welcome_email(user_name, to_email)

        return await self.send_email(to_email, subject, html_body, text_body)

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
