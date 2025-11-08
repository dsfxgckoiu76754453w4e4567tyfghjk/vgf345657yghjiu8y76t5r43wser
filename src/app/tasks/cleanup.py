"""Cleanup tasks (LOW PRIORITY)."""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

async_engine = create_async_engine(settings.database_url)
async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(
    bind=True,
    name='app.tasks.cleanup.clean_expired_files',
)
def clean_expired_files(self):
    """Clean expired files from MinIO based on lifecycle policies."""
    logger.info("clean_expired_files_started", task_id=self.request.id, environment=settings.environment)
    
    # TODO: Implement MinIO file cleanup based on environment retention policies
    # Use settings.environment_data_retention_days
    
    return {'status': 'success', 'environment': settings.environment}


@celery_app.task(
    bind=True,
    name='app.tasks.cleanup.cleanup_old_tasks',
)
def cleanup_old_tasks(self):
    """Cleanup old Celery task results from database."""
    try:
        logger.info("cleanup_old_tasks_started", task_id=self.request.id)
        
        async def _cleanup():
            async with async_session_maker() as db:
                # Delete task results older than 24 hours
                cutoff_date = datetime.utcnow() - timedelta(hours=24)
                
                # Note: Adjust table name based on your Celery result backend config
                # Default is 'celery_taskmeta'
                result = await db.execute(
                    delete(db.bind.dialect.get_table('celery_taskmeta'))
                    .where(db.bind.dialect.get_table('celery_taskmeta').c.date_done < cutoff_date)
                )
                await db.commit()
                
                deleted_count = result.rowcount
                logger.info("cleanup_old_tasks_completed", deleted=deleted_count)
                return deleted_count
        
        deleted = asyncio.run(_cleanup())
        return {'status': 'success', 'deleted': deleted}
    except Exception as exc:
        logger.error("cleanup_old_tasks_failed", error=str(exc))
        return {'status': 'error', 'error': str(exc)}
