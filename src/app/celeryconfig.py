"""
Celery configuration module (Official Celery best practice).

This file follows the official Celery configuration pattern:
https://docs.celeryproject.org/en/stable/userguide/configuration.html

All Celery settings should be defined here, prefixed with 'CELERY_'.
"""

from kombu import Exchange, Queue
from app.core.config import settings

# ============================================================================
# BROKER SETTINGS
# ============================================================================

# Broker URL (Redis)
broker_url = settings.celery_broker_url

# Broker connection retry on startup
broker_connection_retry_on_startup = True
broker_connection_max_retries = 10

# Broker transport options
broker_transport_options = {
    'visibility_timeout': 43200,  # 12 hours
    'fanout_prefix': True,
    'fanout_patterns': True,
    'socket_keepalive': True,
    'health_check_interval': 30,
}

# ============================================================================
# RESULT BACKEND SETTINGS
# ============================================================================

# Result backend (PostgreSQL)
result_backend = settings.celery_result_backend

# Result backend transport options
result_backend_transport_options = {
    'master_name': 'mymaster',
    'visibility_timeout': 3600,
}

# Result settings
result_expires = 3600  # 1 hour
result_extended = True  # Store more metadata
result_compression = 'gzip'  # Compress results

# Database result backend configuration
database_table_names = {
    'task': 'celery_taskmeta',
    'group': 'celery_groupmeta',
}
database_short_lived_sessions = True

# ============================================================================
# TASK SETTINGS
# ============================================================================

# Task serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

# Task execution
task_track_started = True  # Track when tasks start
task_time_limit = 600  # 10 minutes hard limit
task_soft_time_limit = 540  # 9 minutes soft limit (warning)
task_acks_late = True  # Acknowledge after completion (reliability)
task_reject_on_worker_lost = True  # Requeue if worker crashes
task_acks_on_failure_or_timeout = True  # Acknowledge failed tasks
task_ignore_result = False  # Store all results

# Task routing
task_default_queue = 'medium_priority'
task_default_exchange = 'tasks'
task_default_routing_key = 'task.default'

# Task compression
task_compression = 'gzip'  # Compress task messages

# ============================================================================
# WORKER SETTINGS
# ============================================================================

# Worker prefetch
worker_prefetch_multiplier = 1  # Prefetch only 1 task (fair distribution)

# Worker pool
worker_pool = 'prefork'  # Use prefork pool (default, most stable)
worker_concurrency = None  # Auto-detect CPU count

# Worker shutdown
worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks (prevent memory leaks)
worker_disable_rate_limits = False  # Enable rate limits

# Worker events
worker_send_task_events = True  # Send events for Flower monitoring
task_send_sent_event = True  # Send task-sent events

# Worker log format
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# ============================================================================
# BEAT SCHEDULER SETTINGS (Periodic Tasks)
# ============================================================================

# Beat schedule file location
beat_schedule_filename = '/tmp/celerybeat-schedule'
beat_sync_every = 1  # Sync schedule every 1 task

# Beat max loop interval
beat_max_loop_interval = 5  # Check for new tasks every 5 seconds

# ============================================================================
# TIMEZONE SETTINGS
# ============================================================================

timezone = 'UTC'
enable_utc = True

# ============================================================================
# QUEUE DEFINITIONS (Priority-Based Routing)
# ============================================================================

# Define exchange
default_exchange = Exchange('tasks', type='topic', durable=True)

# Define queues with priorities
task_queues = (
    # High priority: User-facing operations (Chat, Images, ASR)
    Queue(
        'high_priority',
        exchange=default_exchange,
        routing_key='high.*',
        queue_arguments={
            'x-max-priority': 10,  # Enable priority support
            'x-message-ttl': 3600000,  # 1 hour TTL
            'x-max-length': 10000,  # Max 10k messages
        },
        durable=True,
    ),
    
    # Medium priority: Background processing
    Queue(
        'medium_priority',
        exchange=default_exchange,
        routing_key='medium.*',
        queue_arguments={
            'x-max-priority': 5,
            'x-message-ttl': 7200000,  # 2 hours TTL
            'x-max-length': 50000,
        },
        durable=True,
    ),
    
    # Low priority: Fire-and-forget
    Queue(
        'low_priority',
        exchange=default_exchange,
        routing_key='low.*',
        queue_arguments={
            'x-max-priority': 1,
            'x-message-ttl': 14400000,  # 4 hours TTL
            'x-max-length': 100000,
        },
        durable=True,
    ),
)

# ============================================================================
# TASK ROUTING CONFIGURATION
# ============================================================================

task_routes = {
    # HIGH PRIORITY - User-facing operations
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
    
    # MEDIUM PRIORITY - Background processing
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
    
    # LOW PRIORITY - Fire-and-forget
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
# BEAT SCHEDULE (Periodic Tasks)
# ============================================================================

from celery.schedules import crontab

beat_schedule = {
    # Daily cleanup at 2 AM
    'cleanup-expired-files-daily': {
        'task': 'app.tasks.cleanup.clean_expired_files',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'queue': 'low_priority',
            'expires': 3600,
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
# SECURITY SETTINGS
# ============================================================================

# Secure serialization (prevent pickle attacks)
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

# Worker hijacking protection
worker_pool_restarts = True

# ============================================================================
# MONITORING & LOGGING
# ============================================================================

# Task result extended
result_extended = True

# Enable task revoked events
worker_send_task_events = True
task_send_sent_event = True

# ============================================================================
# OPTIMIZATION SETTINGS
# ============================================================================

# Worker optimization
worker_disable_rate_limits = False
worker_prefetch_multiplier = 1  # Fair task distribution

# Task optimization
task_compression = 'gzip'
result_compression = 'gzip'

# Connection pool optimization
broker_pool_limit = 10  # Max connections to broker
redis_max_connections = 50  # Max Redis connections

# ============================================================================
# ERROR HANDLING
# ============================================================================

# Task retry settings (can be overridden per task)
task_autoretry_for = (Exception,)  # Auto-retry for exceptions
task_retry_backoff = True  # Exponential backoff
task_retry_backoff_max = 600  # Max 10 minutes backoff
task_retry_jitter = True  # Add random jitter to retries
