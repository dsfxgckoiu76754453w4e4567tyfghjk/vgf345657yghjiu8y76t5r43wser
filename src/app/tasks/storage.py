"""File storage tasks (MEDIUM PRIORITY)."""

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name='app.tasks.storage.upload_large_file',
    max_retries=2,
)
def upload_large_file(self, file_path: str, user_id: str):
    """Upload large file to MinIO."""
    # TODO: Implement large file upload
    logger.info("upload_large_file", task_id=self.request.id, file_path=file_path)
    return {'status': 'success', 'file_path': file_path}
