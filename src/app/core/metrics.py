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
# TEMPORAL WORKFLOW METRICS
# ============================================================================

temporal_workflows_started = Counter(
    'temporal_workflows_started_total',
    'Total workflows started',
    ['workflow_type', 'task_queue', 'environment']
)

temporal_workflows_completed = Counter(
    'temporal_workflows_completed_total',
    'Total workflows completed successfully',
    ['workflow_type', 'task_queue', 'environment']
)

temporal_workflows_failed = Counter(
    'temporal_workflows_failed_total',
    'Total workflows that failed',
    ['workflow_type', 'task_queue', 'environment']
)

temporal_workflows_canceled = Counter(
    'temporal_workflows_canceled_total',
    'Total workflows that were canceled',
    ['workflow_type', 'task_queue', 'environment']
)

temporal_workflow_duration_seconds = Histogram(
    'temporal_workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type', 'task_queue', 'environment'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)

temporal_activity_executions = Counter(
    'temporal_activity_executions_total',
    'Total activity executions',
    ['activity_type', 'status', 'environment']  # status: success, failed, retry
)

temporal_activity_duration_seconds = Histogram(
    'temporal_activity_duration_seconds',
    'Activity execution duration in seconds',
    ['activity_type', 'environment'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0)
)

temporal_active_workers = Gauge(
    'temporal_active_workers',
    'Number of active Temporal workers',
    ['task_queue', 'environment']
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

def track_workflow_start(workflow_type: str, task_queue: str):
    """Track workflow start."""
    temporal_workflows_started.labels(
        workflow_type=workflow_type,
        task_queue=task_queue,
        environment=settings.environment
    ).inc()


def track_workflow_completion(workflow_type: str, task_queue: str, duration: float):
    """Track workflow completion."""
    temporal_workflows_completed.labels(
        workflow_type=workflow_type,
        task_queue=task_queue,
        environment=settings.environment
    ).inc()

    temporal_workflow_duration_seconds.labels(
        workflow_type=workflow_type,
        task_queue=task_queue,
        environment=settings.environment
    ).observe(duration)


def track_workflow_failure(workflow_type: str, task_queue: str):
    """Track workflow failure."""
    temporal_workflows_failed.labels(
        workflow_type=workflow_type,
        task_queue=task_queue,
        environment=settings.environment
    ).inc()


def track_workflow_cancel(workflow_type: str, task_queue: str):
    """Track workflow cancellation."""
    temporal_workflows_canceled.labels(
        workflow_type=workflow_type,
        task_queue=task_queue,
        environment=settings.environment
    ).inc()


def track_activity_execution(activity_type: str, status: str, duration: float = None):
    """
    Track activity execution.

    Args:
        activity_type: Name of the activity
        status: Execution status (success, failed, retry)
        duration: Optional execution duration in seconds
    """
    temporal_activity_executions.labels(
        activity_type=activity_type,
        status=status,
        environment=settings.environment
    ).inc()

    if duration is not None:
        temporal_activity_duration_seconds.labels(
            activity_type=activity_type,
            environment=settings.environment
        ).observe(duration)


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
