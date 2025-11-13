#!/usr/bin/env bash
# ==============================================================================
# Celery Beat Scheduler Startup Script (Production)
# ==============================================================================
#
# Official Celery best practices for periodic task scheduling:
# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
#
# This script starts the Celery Beat scheduler for periodic tasks:
# - Daily file cleanup (2 AM)
# - Hourly old task cleanup
# - Weekly leaderboard recalculation (Monday 3 AM)
#
# IMPORTANT: Only run ONE beat scheduler instance per deployment!
# Running multiple beat instances will cause duplicate task execution.
#
# Usage:
#   ./scripts/celery/start_beat.sh
#
# ==============================================================================

set -e  # Exit on error

# Beat configuration
LOGLEVEL="${CELERY_LOGLEVEL:-info}"
SCHEDULE_FILE="${CELERY_BEAT_SCHEDULE:-/tmp/celerybeat-schedule}"
PIDFILE="${CELERY_BEAT_PIDFILE:-/tmp/celerybeat.pid}"

echo "📅 Starting Celery Beat scheduler"
echo "   Schedule file: $SCHEDULE_FILE"
echo "   PID file: $PIDFILE"
echo "   Log level: $LOGLEVEL"
echo ""
echo "⚠️  IMPORTANT: Ensure only ONE beat instance runs per deployment!"
echo ""

# Remove stale PID file if exists
if [ -f "$PIDFILE" ]; then
    echo "⚠️  Found stale PID file, removing: $PIDFILE"
    rm -f "$PIDFILE"
fi

# Start beat scheduler with production-optimized settings
exec celery -A app.tasks beat \
  --loglevel="$LOGLEVEL" \
  --schedule="$SCHEDULE_FILE" \
  --pidfile="$PIDFILE" \
  --max-interval=60
