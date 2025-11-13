#!/usr/bin/env bash
# ==============================================================================
# Celery Worker Startup Script - ALL QUEUES (Development Only)
# ==============================================================================
#
# This script starts a single Celery worker that processes ALL priority queues.
#
# ⚠️  WARNING: This is for LOCAL DEVELOPMENT ONLY!
# In production, always run separate workers per priority queue for:
# - Better resource isolation
# - Independent scaling
# - Failure isolation
# - Priority guarantee
#
# Usage:
#   ./scripts/celery/start_worker_all_queues.sh
#
# Production Usage:
#   Use the separate priority-specific worker scripts:
#   - start_worker_high_priority.sh
#   - start_worker_medium_priority.sh
#   - start_worker_low_priority.sh
#
# ==============================================================================

set -e  # Exit on error

# Worker configuration
WORKER_NAME="dev_all_queues"
QUEUES="high_priority,medium_priority,low_priority"
CONCURRENCY="${CELERY_CONCURRENCY:-4}"
LOGLEVEL="${CELERY_LOGLEVEL:-info}"
MAX_TASKS_PER_CHILD=100  # Lower for development

echo "🚀 Starting Celery worker (DEVELOPMENT MODE): $WORKER_NAME"
echo "   Queues: $QUEUES"
echo "   Concurrency: $CONCURRENCY"
echo "   Max tasks per child: $MAX_TASKS_PER_CHILD"
echo "   Log level: $LOGLEVEL"
echo ""
echo "⚠️  DEVELOPMENT MODE: Processing all queues"
echo "   For production, use priority-specific workers!"
echo ""

# Start worker with development settings
exec celery -A app.tasks worker \
  --hostname="$WORKER_NAME@%h" \
  --queues="$QUEUES" \
  --concurrency="$CONCURRENCY" \
  --max-tasks-per-child="$MAX_TASKS_PER_CHILD" \
  --loglevel="$LOGLEVEL" \
  --time-limit=600 \
  --soft-time-limit=540 \
  --prefetch-multiplier=1
