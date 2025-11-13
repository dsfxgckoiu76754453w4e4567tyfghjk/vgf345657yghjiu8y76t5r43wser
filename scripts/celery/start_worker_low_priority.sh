#!/usr/bin/env bash
# ==============================================================================
# Celery Worker Startup Script - LOW PRIORITY Queue (Production)
# ==============================================================================
#
# Official Celery best practices for production deployment:
# https://docs.celeryproject.org/en/stable/userguide/workers.html
#
# This script starts a Celery worker optimized for low-priority fire-and-forget tasks:
# - Email notifications
# - Langfuse trace submissions
# - File cleanup
# - Old task cleanup
# - Leaderboard recalculation
#
# Usage:
#   ./scripts/celery/start_worker_low_priority.sh
#
# ==============================================================================

set -e  # Exit on error

# Worker configuration
WORKER_NAME="low_priority_worker"
QUEUE="low_priority"
CONCURRENCY="${CELERY_CONCURRENCY:-2}"  # Fewer workers for low priority
LOGLEVEL="${CELERY_LOGLEVEL:-warning}"  # Less verbose logging
MAX_TASKS_PER_CHILD=2000
AUTOSCALE_MIN="${CELERY_AUTOSCALE_MIN:-1}"
AUTOSCALE_MAX="${CELERY_AUTOSCALE_MAX:-4}"

echo "🚀 Starting Celery worker: $WORKER_NAME"
echo "   Queue: $QUEUE"
echo "   Concurrency: $CONCURRENCY"
echo "   Autoscale: $AUTOSCALE_MIN-$AUTOSCALE_MAX"
echo "   Max tasks per child: $MAX_TASKS_PER_CHILD"
echo "   Log level: $LOGLEVEL"
echo ""

# Start worker with production-optimized settings
exec celery -A app.tasks worker \
  --hostname="$WORKER_NAME@%h" \
  --queues="$QUEUE" \
  --concurrency="$CONCURRENCY" \
  --autoscale="$AUTOSCALE_MAX,$AUTOSCALE_MIN" \
  --max-tasks-per-child="$MAX_TASKS_PER_CHILD" \
  --loglevel="$LOGLEVEL" \
  --time-limit=7200 \
  --soft-time-limit=6900 \
  --prefetch-multiplier=4 \
  --optimization=fair \
  --without-gossip \
  --without-mingle \
  --without-heartbeat
