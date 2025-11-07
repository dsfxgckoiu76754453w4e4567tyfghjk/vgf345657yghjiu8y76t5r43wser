"""Email sending tasks (LOW PRIORITY)."""

import asyncio
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.services.email_service import EmailService

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name='app.tasks.email.send_email',
    max_retries=5,
    default_retry_delay=60,
)
def send_email(self, to_email: str, subject: str, body: str, html: bool = False):
    """Send email asynchronously."""
    try:
        logger.info("sending_email", to=to_email, subject=subject)
        
        async def _send_email():
            email_service = EmailService()
            await email_service.send_email(
                to=to_email,
                subject=subject,
                body=body,
                html=html,
            )
        
        asyncio.run(_send_email())
        logger.info("email_sent", to=to_email)
        return {'status': 'success', 'to': to_email}
    except Exception as exc:
        logger.error("email_failed", to=to_email, error=str(exc))
        raise self.retry(exc=exc)
