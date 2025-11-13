"""
Temporal client configuration and dependency injection.

Provides:
- Temporal client initialization
- Dependency injection for FastAPI
- Worker configuration
"""

from typing import Optional

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from app.core.config import settings
from app.core.logging import get_logger
from app.workflows.chat_workflow import ChatWorkflow, chat_activities

logger = get_logger(__name__)

# Global Temporal client (initialized on startup)
_temporal_client: Optional[Client] = None


async def init_temporal_client() -> Client:
    """
    Initialize Temporal client.
    
    Called during application startup.
    
    Returns:
        Temporal Client instance
    """
    global _temporal_client
    
    try:
        # Connect to Temporal server
        temporal_host = getattr(settings, 'temporal_host', 'localhost:7233')
        temporal_namespace = getattr(settings, 'temporal_namespace', 'default')
        
        logger.info(
            "temporal_client_connecting",
            host=temporal_host,
            namespace=temporal_namespace,
        )
        
        _temporal_client = await Client.connect(
            target_host=temporal_host,
            namespace=temporal_namespace,
        )
        
        logger.info(
            "temporal_client_connected",
            host=temporal_host,
            namespace=temporal_namespace,
        )
        
        return _temporal_client
        
    except Exception as e:
        logger.error(
            "temporal_client_connection_failed",
            error=str(e),
        )
        raise


async def close_temporal_client():
    """Close Temporal client connection."""
    global _temporal_client
    
    if _temporal_client:
        try:
            await _temporal_client.close()
            logger.info("temporal_client_closed")
        except Exception as e:
            logger.error("temporal_client_close_error", error=str(e))
        finally:
            _temporal_client = None


def get_temporal_client() -> Client:
    """
    Get Temporal client instance (for dependency injection).
    
    Returns:
        Temporal Client
        
    Raises:
        RuntimeError: If client not initialized
    """
    if _temporal_client is None:
        raise RuntimeError(
            "Temporal client not initialized. "
            "Call init_temporal_client() during application startup."
        )
    return _temporal_client


async def create_temporal_worker(
    task_queue: str = "chat-queue",
    max_concurrent_activities: int = 10,
    max_concurrent_workflows: int = 100,
) -> Worker:
    """
    Create Temporal worker for processing workflows.
    
    Args:
        task_queue: Task queue name
        max_concurrent_activities: Max concurrent activities
        max_concurrent_workflows: Max concurrent workflows
        
    Returns:
        Configured Worker instance
    """
    client = get_temporal_client()
    
    logger.info(
        "temporal_worker_creating",
        task_queue=task_queue,
        workflows=[ChatWorkflow.__name__],
        activities=len(chat_activities),
    )
    
    worker = Worker(
        client=client,
        task_queue=task_queue,
        workflows=[ChatWorkflow],
        activities=chat_activities,
        max_concurrent_activities=max_concurrent_activities,
        max_concurrent_workflows=max_concurrent_workflows,
    )
    
    logger.info(
        "temporal_worker_created",
        task_queue=task_queue,
    )
    
    return worker
