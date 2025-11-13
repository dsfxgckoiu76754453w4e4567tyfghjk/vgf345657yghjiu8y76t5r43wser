# Celery Production Deployment Guide

This directory contains production-ready Celery worker and beat scheduler startup scripts following official Celery best practices.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [Development Setup](#development-setup)
- [Worker Configuration](#worker-configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### Priority-Based Queue System

The application uses a **3-tier priority queue system** for optimal resource utilization:

| Priority | Queue Name | Tasks | Workers | Concurrency |
|----------|------------|-------|---------|-------------|
| **HIGH** | `high_priority` | Chat, Images, ASR, Web Search | 2-8 (autoscale) | 4 base |
| **MEDIUM** | `medium_priority` | Embeddings, Storage, Promotion, Dataset | 4-12 (autoscale) | 6 base |
| **LOW** | `low_priority` | Email, Cleanup, Langfuse, Leaderboard | 1-4 (autoscale) | 2 base |

### Official Celery Pattern

This implementation follows the **official Celery application factory pattern**:

```
src/app/
├── celeryconfig.py          # Official config module (all settings)
├── core/
│   └── celery_app.py        # Application factory pattern
└── tasks/
    ├── __init__.py          # Exports celery_app for CLI
    ├── chat.py              # High priority tasks
    ├── images.py
    ├── embeddings.py        # Medium priority tasks
    └── cleanup.py           # Low priority tasks
```

**Key Benefits:**
- ✅ Separation of concerns (config in `celeryconfig.py`)
- ✅ Better testability (factory pattern)
- ✅ Easy configuration management
- ✅ Official Celery documentation compliance

## 🚀 Quick Start

### Development (All Queues)

For local development, use a single worker that processes all queues:

```bash
# Using Make (recommended)
make celery-worker-dev

# Or direct script execution
./scripts/celery/start_worker_all_queues.sh
```

### Production (Separate Workers)

In production, run **separate workers per priority queue**:

```bash
# Start all priority workers
make celery-worker-all-prod

# Or start individually
make celery-worker-high     # High priority (user-facing)
make celery-worker-medium   # Medium priority (background)
make celery-worker-low      # Low priority (fire-and-forget)
```

### Beat Scheduler (Periodic Tasks)

Start the beat scheduler for periodic tasks:

```bash
make celery-beat
```

⚠️ **IMPORTANT:** Only run **ONE** beat scheduler instance per deployment!

## 🏭 Production Deployment

### Recommended Production Setup

For a production deployment handling high traffic:

```bash
# Terminal 1: High priority workers (2 instances)
CELERY_AUTOSCALE_MAX=8 ./scripts/celery/start_worker_high_priority.sh &
CELERY_AUTOSCALE_MAX=8 ./scripts/celery/start_worker_high_priority.sh &

# Terminal 2: Medium priority workers (2 instances)
CELERY_AUTOSCALE_MAX=12 ./scripts/celery/start_worker_medium_priority.sh &
CELERY_AUTOSCALE_MAX=12 ./scripts/celery/start_worker_medium_priority.sh &

# Terminal 3: Low priority worker (1 instance)
./scripts/celery/start_worker_low_priority.sh &

# Terminal 4: Beat scheduler (1 instance only!)
./scripts/celery/start_beat.sh
```

### Docker Production Deployment

For Docker deployments, add to your `docker-compose` file:

```yaml
services:
  celery-worker-high:
    image: your-app:latest
    command: ./scripts/celery/start_worker_high_priority.sh
    environment:
      - CELERY_AUTOSCALE_MAX=8
      - CELERY_AUTOSCALE_MIN=2
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  celery-worker-medium:
    image: your-app:latest
    command: ./scripts/celery/start_worker_medium_priority.sh
    environment:
      - CELERY_AUTOSCALE_MAX=12
      - CELERY_AUTOSCALE_MIN=4
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '4.0'
          memory: 4G

  celery-worker-low:
    image: your-app:latest
    command: ./scripts/celery/start_worker_low_priority.sh
    environment:
      - CELERY_AUTOSCALE_MAX=4
      - CELERY_AUTOSCALE_MIN=1
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  celery-beat:
    image: your-app:latest
    command: ./scripts/celery/start_beat.sh
    deploy:
      replicas: 1  # MUST be 1!
```

### Kubernetes Production Deployment

For Kubernetes, create separate Deployments per priority:

```yaml
# High Priority Worker Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker-high
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: worker
        image: your-app:latest
        command: ["./scripts/celery/start_worker_high_priority.sh"]
        env:
        - name: CELERY_AUTOSCALE_MAX
          value: "8"
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
```

## 🔧 Worker Configuration

### Environment Variables

All worker scripts support the following environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CELERY_CONCURRENCY` | Base concurrency level | Varies by priority | `4` |
| `CELERY_AUTOSCALE_MIN` | Minimum autoscale workers | Varies | `2` |
| `CELERY_AUTOSCALE_MAX` | Maximum autoscale workers | Varies | `8` |
| `CELERY_LOGLEVEL` | Log verbosity | `info` | `debug`, `warning` |
| `CELERY_BEAT_SCHEDULE` | Beat schedule file path | `/tmp/celerybeat-schedule` | `/var/lib/celery/beat` |

### Worker Optimization Flags

All production scripts use these optimizations (from official Celery docs):

```bash
--optimization=fair              # Fair task distribution
--without-gossip                 # Disable gossip protocol (reduces overhead)
--without-mingle                 # Disable mingle at startup (faster startup)
--without-heartbeat              # Disable heartbeat (Redis handles it)
--prefetch-multiplier=1          # Prefetch 1 task per worker (fair distribution)
--max-tasks-per-child=1000       # Restart worker after 1000 tasks (memory leak prevention)
```

### Autoscaling

Workers automatically scale based on queue length:

- **High priority**: 2-8 workers (aggressive scaling for low latency)
- **Medium priority**: 4-12 workers (batch processing optimization)
- **Low priority**: 1-4 workers (resource-efficient)

## 📊 Monitoring

### Flower Dashboard

Start the Flower web UI for real-time monitoring:

```bash
make flower
# Visit: http://localhost:5555
```

Flower provides:
- Real-time task monitoring
- Worker pool inspection
- Queue length visualization
- Task success/failure rates
- Performance metrics

### CLI Inspection

Use Make commands for quick inspection:

```bash
# View active workers and tasks
make celery-inspect

# View detailed worker statistics
make celery-stats

# View task history
poetry run celery -A app.tasks events
```

### Prometheus Metrics

The application exports Prometheus metrics:

- `celery_task_submissions_total` - Task submission counter
- `celery_task_completions_total` - Task completion counter
- `celery_task_failures_total` - Task failure counter
- `celery_task_retries_total` - Task retry counter
- `celery_task_duration_seconds` - Task duration histogram

## 🐛 Troubleshooting

### Workers Not Starting

**Issue:** Worker fails to start with import errors

**Solution:**
```bash
# Ensure tasks are discoverable
python -c "from app.tasks import celery_app; print(celery_app.tasks.keys())"

# Check configuration
python -c "from app import celeryconfig; print(celeryconfig.broker_url)"
```

### Tasks Stuck in Queue

**Issue:** Tasks remain in queue but aren't processed

**Solution:**
```bash
# Check worker status
make celery-inspect

# Verify queue routing
poetry run celery -A app.tasks inspect active_queues

# Check broker connection
poetry run celery -A app.tasks inspect ping
```

### Memory Leaks

**Issue:** Worker memory usage grows over time

**Solution:**
- Workers automatically restart after `max-tasks-per-child` tasks
- Adjust `MAX_TASKS_PER_CHILD` in worker scripts (default: 1000)
- Monitor with: `docker stats` or `htop`

### Beat Scheduler Running Multiple Times

**Issue:** Periodic tasks execute multiple times

**Solution:**
- **ONLY run ONE beat scheduler instance!**
- Check for stale PID files: `rm /tmp/celerybeat.pid`
- Verify with: `ps aux | grep celery.*beat`

## 📚 Additional Resources

- **Official Celery Docs:** https://docs.celeryproject.org/
- **Production Best Practices:** https://docs.celeryproject.org/en/stable/userguide/workers.html
- **Configuration Reference:** https://docs.celeryproject.org/en/stable/userguide/configuration.html
- **Periodic Tasks:** https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html

## 🔐 Security Notes

- Never expose Redis/broker URLs in logs
- Use TLS for broker connections in production
- Rotate credentials regularly
- Implement task rate limiting for external APIs
- Monitor for suspicious task patterns

## 📝 License

This implementation follows the official Celery documentation and best practices.
