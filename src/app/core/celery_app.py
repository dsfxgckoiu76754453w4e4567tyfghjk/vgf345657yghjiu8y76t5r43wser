"""
Celery application configuration for distributed task queue (Official best practice).

This module follows the official Celery application factory pattern:
https://docs.celeryproject.org/en/stable/userguide/application.html

Key features:
- Application factory pattern for better testability
- Configuration loaded from celeryconfig.py (official pattern)
- Signal handlers for logging and Prometheus metrics
- Auto-discovery of tasks from app.tasks
- Production-ready worker management
"""

import time
from celery import Celery, signals

from app.core.config import settings
from app.core.logging import get_logger
from app.core import metrics

logger = get_logger(__name__)

# Task timing storage (for duration tracking in signals)
_task_start_times = {}


# ============================================================================
# CELERY APPLICATION FACTORY (Official Pattern)
# ============================================================================


def create_celery_app() -> Celery:
    """
    Factory function to create Celery application (Official best practice).

    This follows the official Celery pattern:
    https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html#django-first-steps

    Benefits:
    - Separation of concerns (config in celeryconfig.py)
    - Better testability (can create multiple instances)
    - Easier configuration management
    - Follows official Celery documentation

    Returns:
        Configured Celery application instance
    """
    # Create Celery app instance
    app = Celery("wisqu_tasks")

    # Load configuration from celeryconfig.py (official pattern)
    # This replaces inline configuration with a dedicated config module
    app.config_from_object("app.celeryconfig")

    # Auto-discover tasks in app.tasks module
    # force=True ensures tasks are discovered even if already imported
    app.autodiscover_tasks(["app.tasks"], force=True)

    logger.info(
        "celery_app_created",
        app_name=app.main,
        config_module="app.celeryconfig",
        broker_url_masked=settings.celery_broker_url.split("@")[-1]
        if "@" in settings.celery_broker_url
        else settings.celery_broker_url,
        result_backend="postgresql",
        environment=settings.environment,
        task_always_eager=settings.celery_task_always_eager,
    )

    return app


# Create the Celery app instance using factory pattern
celery_app = create_celery_app()

# ============================================================================
# CELERY SIGNALS (Logging and Monitoring)
# ============================================================================


@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log task start and track metrics."""
    # Extract queue name from routing key
    queue = 'unknown'
    if hasattr(task, 'request') and hasattr(task.request, 'delivery_info'):
        routing_key = task.request.delivery_info.get('routing_key', '')
        if 'high' in routing_key:
            queue = 'high_priority'
        elif 'medium' in routing_key:
            queue = 'medium_priority'
        elif 'low' in routing_key:
            queue = 'low_priority'

    # Track task submission in Prometheus
    metrics.track_task_submission(task.name, queue)

    # Store start time for duration calculation
    _task_start_times[task_id] = time.time()

    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task.name,
        queue=queue,
        args=str(kwargs.get('args', []))[:100],
        kwargs_keys=list(kwargs.get('kwargs', {}).keys()),
        environment=settings.environment,
    )


@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """Log task completion and track metrics."""
    state = kwargs.get('state', 'UNKNOWN')

    # Extract queue name
    queue = 'unknown'
    if hasattr(task, 'request') and hasattr(task.request, 'delivery_info'):
        routing_key = task.request.delivery_info.get('routing_key', '')
        if 'high' in routing_key:
            queue = 'high_priority'
        elif 'medium' in routing_key:
            queue = 'medium_priority'
        elif 'low' in routing_key:
            queue = 'low_priority'

    # Calculate duration
    duration = 0.0
    if task_id in _task_start_times:
        duration = time.time() - _task_start_times[task_id]
        del _task_start_times[task_id]

    # Track task completion in Prometheus
    if state == 'SUCCESS':
        metrics.track_task_completion(sender.name, queue, duration)

    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=sender.name,
        state=state,
        duration=f"{duration:.2f}s",
        result_preview=str(retval)[:100] if retval else None,
        environment=settings.environment,
    )


@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failure and track metrics."""
    # Extract queue name
    queue = 'unknown'
    task = kwargs.get('task')
    if task and hasattr(task, 'request') and hasattr(task.request, 'delivery_info'):
        routing_key = task.request.delivery_info.get('routing_key', '')
        if 'high' in routing_key:
            queue = 'high_priority'
        elif 'medium' in routing_key:
            queue = 'medium_priority'
        elif 'low' in routing_key:
            queue = 'low_priority'

    # Track task failure in Prometheus
    metrics.track_task_failure(sender.name, queue)

    # Clean up start time if exists
    if task_id in _task_start_times:
        del _task_start_times[task_id]

    logger.error(
        "task_failed",
        task_id=task_id,
        task_name=sender.name,
        exception=str(exception),
        exception_type=type(exception).__name__,
        traceback_preview=str(kwargs.get('traceback', ''))[:500],
        environment=settings.environment,
    )


@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **kwargs):
    """Log task retry and track metrics."""
    # Extract queue name
    queue = 'unknown'
    request = kwargs.get('request')
    if request and hasattr(request, 'delivery_info'):
        routing_key = request.delivery_info.get('routing_key', '')
        if 'high' in routing_key:
            queue = 'high_priority'
        elif 'medium' in routing_key:
            queue = 'medium_priority'
        elif 'low' in routing_key:
            queue = 'low_priority'

    # Track task retry in Prometheus
    metrics.track_task_retry(sender.name, queue)

    logger.warning(
        "task_retrying",
        task_id=task_id,
        task_name=sender.name,
        reason=str(reason),
        request_retries=request.retries if request and hasattr(request, 'retries') else 0,
        environment=settings.environment,
    )


@signals.worker_ready.connect
def worker_ready_handler(**kwargs):
    """Log when worker is ready."""
    logger.info(
        "celery_worker_ready",
        hostname=kwargs.get('sender').hostname if kwargs.get('sender') else 'unknown',
        environment=settings.environment,
    )


@signals.worker_shutdown.connect
def worker_shutdown_handler(**kwargs):
    """Log when worker is shutting down."""
    logger.info(
        "celery_worker_shutdown",
        hostname=kwargs.get('sender').hostname if kwargs.get('sender') else 'unknown',
        environment=settings.environment,
    )


# ============================================================================
# AUTO-DISCOVER TASKS
# ============================================================================

# Celery will automatically discover tasks in these modules
celery_app.autodiscover_tasks(['app.tasks'], force=True)

logger.info(
    "celery_app_configured",
    broker=settings.celery_broker_url.split('@')[-1] if '@' in settings.celery_broker_url else settings.celery_broker_url,
    result_backend='postgresql',
    environment=settings.environment,
    task_always_eager=settings.celery_task_always_eager,
)
