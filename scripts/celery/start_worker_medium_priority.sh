#!/usr/bin/env bash
# ==============================================================================
# Celery Worker Startup Script - MEDIUM PRIORITY Queue (Production)
# ==============================================================================
#
# Official Celery best practices for production deployment:
# https://docs.celeryproject.org/en/stable/userguide/workers.html
#
# This script starts a Celery worker optimized for medium-priority background tasks:
# - Batch embeddings generation
# - Large file uploads
# - Promotion operations
# - Dataset creation
#
# Usage:
#   ./scripts/celery/start_worker_medium_priority.sh
#
# ==============================================================================

set -e  # Exit on error

# Worker configuration
WORKER_NAME="medium_priority_worker"
QUEUE="medium_priority"
CONCURRENCY="${CELERY_CONCURRENCY:-6}"  # More concurrency for batch operations
LOGLEVEL="${CELERY_LOGLEVEL:-info}"
MAX_TASKS_PER_CHILD=500
AUTOSCALE_MIN="${CELERY_AUTOSCALE_MIN:-4}"
AUTOSCALE_MAX="${CELERY_AUTOSCALE_MAX:-12}"

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
  --time-limit=3600 \
  --soft-time-limit=3300 \
  --prefetch-multiplier=2 \
  --optimization=fair \
  --without-gossip \
  --without-mingle \
  --without-heartbeat
