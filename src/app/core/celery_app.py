"""
Celery application configuration for distributed task queue.

This module sets up Celery with:
- Redis broker for message queue
- PostgreSQL result backend for task state
- Environment-aware configuration
- Priority-based queue routing
- Auto-discovery of tasks
"""

from celery import Celery, signals
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# CELERY APPLICATION INITIALIZATION
# ============================================================================

celery_app = Celery(
    "wisqu_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,  # Track task start time
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit (graceful)
    task_acks_late=True,  # Acknowledge after completion (for reliability)
    task_reject_on_worker_lost=True,  # Requeue tasks if worker crashes
    worker_prefetch_multiplier=1,  # Prefetch only 1 task per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (memory leak prevention)

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store more task metadata
    result_compression='gzip',  # Compress results

    # Database result backend configuration
    database_table_names={
        'task': 'celery_taskmeta',
        'group': 'celery_groupmeta',
    },
    database_short_lived_sessions=True,  # Use short-lived DB sessions

    # Broker settings (Redis)
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_transport_options={
        'visibility_timeout': 43200,  # 12 hours
        'fanout_prefix': True,
        'fanout_patterns': True,
        'socket_keepalive': True,
        'health_check_interval': 30,
    },

    # Task result backend transport options
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },

    # Worker settings
    worker_send_task_events=True,  # Send task events for monitoring
    task_send_sent_event=True,  # Send task-sent events

    # Beat scheduler settings (for periodic tasks)
    beat_schedule_filename='/tmp/celerybeat-schedule',
    beat_sync_every=1,  # Sync schedule every 1 task

    # Monitoring
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# ============================================================================
# QUEUE DEFINITIONS (Priority-Based Routing)
# ============================================================================

default_exchange = Exchange('tasks', type='topic')

celery_app.conf.task_default_queue = 'medium_priority'
celery_app.conf.task_default_exchange = 'tasks'
celery_app.conf.task_default_routing_key = 'task.default'

celery_app.conf.task_queues = (
    # High priority: User-facing operations (Chat, Images, ASR)
    Queue(
        'high_priority',
        exchange=default_exchange,
        routing_key='high.*',
        queue_arguments={
            'x-max-priority': 10,  # Enable priority support
            'x-message-ttl': 3600000,  # 1 hour TTL
        },
    ),

    # Medium priority: Background processing (Embeddings, Files, Promotion)
    Queue(
        'medium_priority',
        exchange=default_exchange,
        routing_key='medium.*',
        queue_arguments={
            'x-max-priority': 5,
            'x-message-ttl': 7200000,  # 2 hours TTL
        },
    ),

    # Low priority: Fire-and-forget (Emails, Langfuse, Cleanup)
    Queue(
        'low_priority',
        exchange=default_exchange,
        routing_key='low.*',
        queue_arguments={
            'x-max-priority': 1,
            'x-message-ttl': 14400000,  # 4 hours TTL
        },
    ),
)

# ============================================================================
# TASK ROUTING CONFIGURATION
# ============================================================================

celery_app.conf.task_routes = {
    # 🔴 HIGH PRIORITY - User-facing operations
    'app.tasks.chat.process_chat_message': {
        'queue': 'high_priority',
        'routing_key': 'high.chat',
        'priority': 10,
    },
    'app.tasks.images.generate_image': {
        'queue': 'high_priority',
        'routing_key': 'high.image',
        'priority': 9,
    },
    'app.tasks.asr.transcribe_audio': {
        'queue': 'high_priority',
        'routing_key': 'high.asr',
        'priority': 8,
    },
    'app.tasks.web_search.search_web': {
        'queue': 'high_priority',
        'routing_key': 'high.search',
        'priority': 7,
    },

    # 🟡 MEDIUM PRIORITY - Background processing
    'app.tasks.embeddings.generate_batch_embeddings': {
        'queue': 'medium_priority',
        'routing_key': 'medium.embeddings',
        'priority': 5,
    },
    'app.tasks.storage.upload_large_file': {
        'queue': 'medium_priority',
        'routing_key': 'medium.storage',
        'priority': 5,
    },
    'app.tasks.promotion.execute_promotion': {
        'queue': 'medium_priority',
        'routing_key': 'medium.promotion',
        'priority': 4,
    },
    'app.tasks.dataset.create_dataset': {
        'queue': 'medium_priority',
        'routing_key': 'medium.dataset',
        'priority': 3,
    },

    # 🟢 LOW PRIORITY - Fire-and-forget
    'app.tasks.email.send_email': {
        'queue': 'low_priority',
        'routing_key': 'low.email',
        'priority': 2,
    },
    'app.tasks.langfuse_tasks.submit_trace': {
        'queue': 'low_priority',
        'routing_key': 'low.langfuse',
        'priority': 1,
    },
    'app.tasks.cleanup.clean_expired_files': {
        'queue': 'low_priority',
        'routing_key': 'low.cleanup',
        'priority': 1,
    },
    'app.tasks.cleanup.cleanup_old_tasks': {
        'queue': 'low_priority',
        'routing_key': 'low.cleanup',
        'priority': 1,
    },
}

# ============================================================================
# CELERY BEAT SCHEDULE (Periodic Tasks / Cron Jobs)
# ============================================================================

celery_app.conf.beat_schedule = {
    # Daily cleanup at 2 AM (environment-aware via cleanup task)
    'cleanup-expired-files-daily': {
        'task': 'app.tasks.cleanup.clean_expired_files',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'queue': 'low_priority',
            'expires': 3600,  # Expire after 1 hour if not executed
        },
    },

    # Hourly cleanup of old Celery task results
    'cleanup-old-task-results-hourly': {
        'task': 'app.tasks.cleanup.cleanup_old_tasks',
        'schedule': crontab(minute=0),
        'options': {
            'queue': 'low_priority',
            'expires': 1800,
        },
    },

    # Weekly leaderboard recalculation (Monday 3 AM)
    'recalculate-leaderboard-weekly': {
        'task': 'app.tasks.leaderboard.recalculate_rankings',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
        'options': {
            'queue': 'medium_priority',
            'expires': 7200,
        },
    },
}

# ============================================================================
# CELERY SIGNALS (Logging and Monitoring)
# ============================================================================


@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log task start."""
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task.name,
        queue=task.request.delivery_info.get('routing_key') if hasattr(task, 'request') else None,
        args=str(kwargs.get('args', []))[:100],
        kwargs_keys=list(kwargs.get('kwargs', {}).keys()),
        environment=settings.environment,
    )


@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """Log task completion."""
    state = kwargs.get('state', 'UNKNOWN')
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=sender.name,
        state=state,
        result_preview=str(retval)[:100] if retval else None,
        environment=settings.environment,
    )


@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failure."""
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
    """Log task retry."""
    logger.warning(
        "task_retrying",
        task_id=task_id,
        task_name=sender.name,
        reason=str(reason),
        request_retries=kwargs.get('request', {}).get('retries', 0),
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
