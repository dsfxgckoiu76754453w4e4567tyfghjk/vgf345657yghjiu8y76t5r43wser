#!/usr/bin/env bash
# ==============================================================================
# Celery Worker Startup Script - HIGH PRIORITY Queue (Production)
# ==============================================================================
#
# Official Celery best practices for production deployment:
# https://docs.celeryproject.org/en/stable/userguide/workers.html
#
# This script starts a Celery worker optimized for high-priority user-facing tasks:
# - Chat message processing
# - Image generation
# - Audio transcription
# - Web search
#
# Usage:
#   ./scripts/celery/start_worker_high_priority.sh
#
# ==============================================================================

set -e  # Exit on error

# Worker configuration
WORKER_NAME="high_priority_worker"
QUEUE="high_priority"
CONCURRENCY="${CELERY_CONCURRENCY:-4}"  # Override via env var
LOGLEVEL="${CELERY_LOGLEVEL:-info}"
MAX_TASKS_PER_CHILD=1000
AUTOSCALE_MIN="${CELERY_AUTOSCALE_MIN:-2}"
AUTOSCALE_MAX="${CELERY_AUTOSCALE_MAX:-8}"

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
  --time-limit=600 \
  --soft-time-limit=540 \
  --prefetch-multiplier=1 \
  --optimization=fair \
  --without-gossip \
  --without-mingle \
  --without-heartbeat
