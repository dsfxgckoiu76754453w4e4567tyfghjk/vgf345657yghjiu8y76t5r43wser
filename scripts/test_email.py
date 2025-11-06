"""Test email configuration."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.config import get_settings

settings = get_settings()


async def test_email():
    """Test email configuration by sending a test message."""
    print("📧 Testing Email Configuration...")
    print("=" * 50)

    try:
        # Check if email service is available
        try:
            from app.services.email_service import EmailService
            email_service = EmailService()
        except ImportError:
            print("⚠️  EmailService not fully implemented yet")
            print("   Testing SMTP configuration manually...")

            # Manual SMTP test
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_host = getattr(settings, 'smtp_host', None)
            smtp_port = getattr(settings, 'smtp_port', 587)
            smtp_user = getattr(settings, 'smtp_user', None)
            smtp_password = getattr(settings, 'smtp_password', None)
            smtp_use_tls = getattr(settings, 'smtp_use_tls', True)

            if not all([smtp_host, smtp_user, smtp_password]):
                print("❌ SMTP configuration missing!")
                print("   Required: SMTP_HOST, SMTP_USER, SMTP_PASSWORD")
                return

            print(f"📡 Connecting to {smtp_host}:{smtp_port}")

            # Create test message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "WisQu Email Configuration Test"
            msg['From'] = smtp_user
            msg['To'] = smtp_user  # Send to self for testing

            text_content = "Email Configuration Successful! Your SMTP settings are working correctly."
            html_content = """
            <html>
              <body>
                <h1 style="color: #4CAF50;">✅ Email Configuration Successful!</h1>
                <p>Your SMTP settings are working correctly.</p>
                <hr>
                <p><small>This is a test email from WisQu setup script.</small></p>
              </body>
            </html>
            """

            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            print(f"✅ Test email sent successfully to: {smtp_user}")
            print()
            print("⚠️  Check your inbox (and spam folder) for the test email")
            return

        # If EmailService is available, use it
        test_email_to = input("Enter email address to send test to: ").strip()
        if not test_email_to:
            test_email_to = settings.smtp_user

        await email_service.send_email(
            to_email=test_email_to,
            subject="WisQu Email Configuration Test",
            html_content="""
            <html>
              <body>
                <h1 style="color: #4CAF50;">✅ Email Configuration Successful!</h1>
                <p>Your SMTP settings are working correctly.</p>
                <hr>
                <p><small>This is a test email from WisQu setup script.</small></p>
              </body>
            </html>
            """,
            text_content="Email Configuration Successful! Your SMTP settings are working correctly."
        )

        print(f"✅ Test email sent successfully to: {test_email_to}")
        print()
        print("⚠️  Check your inbox (and spam folder) for the test email")

    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env")
        print("2. For Gmail: Enable 2FA and use App Password")
        print("3. For SendGrid: Use 'apikey' as username and API key as password")
        print("4. Check firewall rules allow outbound SMTP connections")
        raise


if __name__ == "__main__":
    asyncio.run(test_email())
