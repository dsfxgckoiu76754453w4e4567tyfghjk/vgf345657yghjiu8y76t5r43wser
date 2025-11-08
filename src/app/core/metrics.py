"""
Prometheus metrics exporter for FastAPI application.

Exports application-level metrics including:
- HTTP request duration
- HTTP request count
- HTTP response status codes
- Active requests
- Custom business metrics
"""

from prometheus_client import Counter, Gauge, Histogram, Info
from app.core.config import settings

# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'environment']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'environment'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint', 'environment']
)

# ============================================================================
# APPLICATION METRICS
# ============================================================================

app_info = Info(
    'app_info',
    'Application information'
)
app_info.info({
    'name': settings.app_name,
    'version': settings.app_version,
    'environment': settings.environment,
})

# ============================================================================
# CELERY METRICS (Custom)
# ============================================================================

celery_tasks_submitted = Counter(
    'celery_tasks_submitted_total',
    'Total tasks submitted to Celery',
    ['task_name', 'queue', 'environment']
)

celery_tasks_completed = Counter(
    'celery_tasks_completed_total',
    'Total tasks completed successfully',
    ['task_name', 'queue', 'environment']
)

celery_tasks_failed = Counter(
    'celery_tasks_failed_total',
    'Total tasks that failed',
    ['task_name', 'queue', 'environment']
)

celery_tasks_retried = Counter(
    'celery_tasks_retried_total',
    'Total task retries',
    ['task_name', 'queue', 'environment']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Task execution duration in seconds',
    ['task_name', 'queue', 'environment'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in queue',
    ['queue', 'environment']
)

celery_active_workers = Gauge(
    'celery_active_workers',
    'Number of active Celery workers',
    ['hostname', 'environment']
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    ['pool', 'environment']
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle database connections',
    ['pool', 'environment']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table', 'environment'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# ============================================================================
# LLM METRICS
# ============================================================================

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'environment']
)

llm_tokens_used = Counter(
    'llm_tokens_used_total',
    'Total tokens used',
    ['provider', 'model', 'type', 'environment']  # type: prompt, completion, cached
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model', 'environment'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

llm_cost_usd = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model', 'environment']
)

llm_cache_hits = Counter(
    'llm_cache_hits_total',
    'Total prompt cache hits',
    ['provider', 'model', 'environment']
)

# ============================================================================
# REDIS METRICS
# ============================================================================

redis_commands_total = Counter(
    'redis_commands_total',
    'Total Redis commands',
    ['command', 'environment']
)

redis_connections_active = Gauge(
    'redis_connections_active',
    'Number of active Redis connections',
    ['pool', 'environment']
)

# ============================================================================
# STORAGE METRICS (MinIO)
# ============================================================================

storage_operations_total = Counter(
    'storage_operations_total',
    'Total storage operations',
    ['operation', 'bucket', 'environment']  # operation: upload, download, delete
)

storage_bytes_transferred = Counter(
    'storage_bytes_transferred_total',
    'Total bytes transferred to/from storage',
    ['operation', 'bucket', 'environment']
)

storage_quota_used_bytes = Gauge(
    'storage_quota_used_bytes',
    'Storage quota used in bytes',
    ['user_id', 'plan', 'environment']
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

users_active = Gauge(
    'users_active',
    'Number of active users',
    ['plan', 'environment']
)

conversations_active = Gauge(
    'conversations_active',
    'Number of active conversations',
    ['environment']
)

messages_sent_total = Counter(
    'messages_sent_total',
    'Total messages sent',
    ['user_plan', 'environment']
)

images_generated_total = Counter(
    'images_generated_total',
    'Total images generated',
    ['model', 'environment']
)

audio_transcribed_minutes = Counter(
    'audio_transcribed_minutes_total',
    'Total minutes of audio transcribed',
    ['provider', 'language', 'environment']
)

# ============================================================================
# RATE LIMITING METRICS
# ============================================================================

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['endpoint', 'plan', 'environment']
)

# ============================================================================
# ERROR METRICS
# ============================================================================

errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'component', 'environment']
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_task_submission(task_name: str, queue: str):
    """Track task submission to Celery."""
    celery_tasks_submitted.labels(
        task_name=task_name,
        queue=queue,
        environment=settings.environment
    ).inc()


def track_task_completion(task_name: str, queue: str, duration: float):
    """Track task completion."""
    celery_tasks_completed.labels(
        task_name=task_name,
        queue=queue,
        environment=settings.environment
    ).inc()

    celery_task_duration_seconds.labels(
        task_name=task_name,
        queue=queue,
        environment=settings.environment
    ).observe(duration)


def track_task_failure(task_name: str, queue: str):
    """Track task failure."""
    celery_tasks_failed.labels(
        task_name=task_name,
        queue=queue,
        environment=settings.environment
    ).inc()


def track_task_retry(task_name: str, queue: str):
    """Track task retry."""
    celery_tasks_retried.labels(
        task_name=task_name,
        queue=queue,
        environment=settings.environment
    ).inc()


def track_llm_request(provider: str, model: str, duration: float, tokens: dict, cost: float):
    """Track LLM API request."""
    llm_requests_total.labels(
        provider=provider,
        model=model,
        environment=settings.environment
    ).inc()

    llm_request_duration_seconds.labels(
        provider=provider,
        model=model,
        environment=settings.environment
    ).observe(duration)

    # Track tokens
    for token_type, count in tokens.items():
        llm_tokens_used.labels(
            provider=provider,
            model=model,
            type=token_type,
            environment=settings.environment
        ).inc(count)

    # Track cost
    llm_cost_usd.labels(
        provider=provider,
        model=model,
        environment=settings.environment
    ).inc(cost)


def track_cache_hit(provider: str, model: str):
    """Track prompt cache hit."""
    llm_cache_hits.labels(
        provider=provider,
        model=model,
        environment=settings.environment
    ).inc()
