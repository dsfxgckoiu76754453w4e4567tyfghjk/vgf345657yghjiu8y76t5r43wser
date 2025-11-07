"""Dataset creation tasks (MEDIUM PRIORITY)."""

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name='app.tasks.dataset.create_dataset',
    max_retries=2,
)
def create_dataset(self, dataset_name: str, conversation_ids: list):
    """Create dataset from conversations."""
    # TODO: Implement dataset creation
    logger.info("create_dataset", task_id=self.request.id, dataset_name=dataset_name)
    return {'status': 'success', 'dataset_name': dataset_name}
