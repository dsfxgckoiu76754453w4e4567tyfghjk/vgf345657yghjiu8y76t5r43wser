# Monitoring & Observability Guide

This guide covers the comprehensive monitoring setup for the Shia Islamic Chatbot queue system, including Prometheus metrics, Grafana dashboards, and integration with your existing monitoring infrastructure.

## Table of Contents

- [Overview](#overview)
- [Metrics Architecture](#metrics-architecture)
- [Prometheus Setup](#prometheus-setup)
- [Grafana Dashboards](#grafana-dashboards)
- [Available Metrics](#available-metrics)
- [Alerting](#alerting)
- [Troubleshooting](#troubleshooting)

---

## Overview

The queue system exports comprehensive metrics for:

- **HTTP Performance**: Request rates, response times, error rates
- **Celery Tasks**: Submission rates, completion rates, failures, retries, queue lengths
- **LLM Usage**: Token consumption, costs, cache hit rates, provider performance
- **Database**: Connection pools, query performance
- **Business Metrics**: Active users, conversations, messages, storage usage
- **System Health**: Worker status, rate limiting, errors

### Monitoring Stack

```
FastAPI Apps (3 replicas) ──┐
                             ├──> Prometheus ──> Grafana
Celery Workers (4 workers) ──┤
                             │
Flower Dashboard ────────────┘
```

---

## Metrics Architecture

### 1. Metrics Collection

**FastAPI Application** (`src/app/main.py`):
- Automatic HTTP instrumentation via `prometheus-fastapi-instrumentator`
- Custom metrics in `src/app/core/metrics.py`
- Metrics endpoint: `http://localhost:8100/metrics`

**Celery Workers** (`src/app/core/celery_app.py`):
- Signal handlers track task lifecycle events
- Metrics exported via FastAPI app (shared Prometheus registry)

**Flower Dashboard**:
- Built-in Celery monitoring UI
- Available at: `http://localhost:5556` (admin/changeme)

### 2. Metrics Export Flow

```
Task Execution ──> Celery Signals ──> Metrics Functions ──> Prometheus Registry
                                                                    │
HTTP Request ────> FastAPI Middleware ──> HTTP Metrics ────────────┤
                                                                    │
                                                                    v
                                                            /metrics endpoint
                                                                    │
                                                                    v
                                                            Prometheus Scraper
                                                                    │
                                                                    v
                                                            Grafana Dashboards
```

---

## Prometheus Setup

### 1. Add Scrape Configuration

Add the following to your existing Prometheus configuration:

```yaml
# /etc/prometheus/prometheus.yml

scrape_configs:
  # FastAPI replicas (direct access)
  - job_name: 'fastapi-queue-system'
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets:
          - 'shia-chatbot-app-1:8000'
          - 'shia-chatbot-app-2:8000'
          - 'shia-chatbot-app-3:8000'
        labels:
          service: 'fastapi'
          deployment: 'queue-system'

  # Or via NGINX (recommended)
  - job_name: 'fastapi-via-nginx'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets:
          - 'localhost:8100'  # NGINX load balancer
        labels:
          service: 'fastapi'
          access: 'nginx-frontend'
```

See `grafana/prometheus-scrape-config.yml` for complete configuration.

### 2. Docker Network Configuration

If Prometheus runs in a Docker container, ensure it's on the same network:

```bash
# Connect Prometheus to the queue system network
docker network connect chatbot-network prometheus-container
```

Or add to your `docker-compose.yml`:

```yaml
services:
  prometheus:
    networks:
      - chatbot-network

networks:
  chatbot-network:
    external: true
```

### 3. Verify Metrics Collection

Check Prometheus targets are healthy:

```bash
# Open Prometheus UI
http://localhost:9090/targets

# Test a query
http://localhost:9090/graph
# Query: celery_tasks_submitted_total
```

---

## Grafana Dashboards

### 1. Import Dashboards

Two pre-built dashboards are available in `grafana/dashboards/`:

#### **Celery Task Queue Monitoring** (`celery-monitoring.json`)

Monitors queue system health and performance:

- Task submission rates by queue
- Task success/failure rates
- Task duration percentiles
- Queue lengths and backlogs
- Active workers
- Task retries
- Priority distribution

**Import Steps**:
1. Open Grafana: `http://your-grafana:3000`
2. Navigate to **Dashboards** → **Import**
3. Upload `grafana/dashboards/celery-monitoring.json`
4. Select your Prometheus data source
5. Click **Import**

#### **Application Performance & Business Metrics** (`application-performance.json`)

Monitors application and business KPIs:

- HTTP request rates and response times
- Error rates (4xx/5xx)
- LLM token usage and costs
- LLM cache hit rates
- Database connection pools and query performance
- Active users by plan
- Messages and images generated
- Storage usage
- Rate limiting events
- Top errors

**Import Steps**: Same as above

### 2. Dashboard Templates

Both dashboards support environment filtering:

```
Variable: $environment
Values: dev, stage, prod
```

This allows you to switch between environments in the same dashboard.

### 3. Create Custom Views

Example custom queries:

```promql
# Cost per user (last 24h)
sum(increase(llm_cost_usd_total{environment="prod"}[24h]))
/
sum(users_active{environment="prod"})

# Average task duration by priority
avg(rate(celery_task_duration_seconds_sum[5m])) by (queue)
/
avg(rate(celery_task_duration_seconds_count[5m])) by (queue)

# Cache savings (estimated cost avoided)
sum(increase(llm_cache_hits_total{environment="prod"}[24h]))
* 0.01  # Adjust based on your average cost per request
```

---

## Available Metrics

### HTTP Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | method, endpoint, status_code, environment | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | method, endpoint, environment | Request duration |
| `http_requests_in_progress` | Gauge | method, endpoint, environment | Requests currently being processed |

### Celery Task Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `celery_tasks_submitted_total` | Counter | task_name, queue, environment | Tasks submitted |
| `celery_tasks_completed_total` | Counter | task_name, queue, environment | Tasks completed successfully |
| `celery_tasks_failed_total` | Counter | task_name, queue, environment | Tasks that failed |
| `celery_tasks_retried_total` | Counter | task_name, queue, environment | Task retries |
| `celery_task_duration_seconds` | Histogram | task_name, queue, environment | Task execution duration |
| `celery_queue_length` | Gauge | queue, environment | Tasks in queue |
| `celery_active_workers` | Gauge | hostname, environment | Active workers |

### LLM Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_requests_total` | Counter | provider, model, environment | Total LLM requests |
| `llm_tokens_used_total` | Counter | provider, model, type, environment | Tokens used (prompt/completion/cached) |
| `llm_request_duration_seconds` | Histogram | provider, model, environment | LLM request duration |
| `llm_cost_usd_total` | Counter | provider, model, environment | Total cost in USD |
| `llm_cache_hits_total` | Counter | provider, model, environment | Cache hits |

### Database Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `db_connections_active` | Gauge | pool, environment | Active DB connections |
| `db_connections_idle` | Gauge | pool, environment | Idle DB connections |
| `db_query_duration_seconds` | Histogram | operation, table, environment | Query duration |

### Business Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `users_active` | Gauge | plan, environment | Active users by plan |
| `conversations_active` | Gauge | environment | Active conversations |
| `messages_sent_total` | Counter | user_plan, environment | Messages sent |
| `images_generated_total` | Counter | model, environment | Images generated |
| `audio_transcribed_minutes_total` | Counter | provider, language, environment | Audio transcribed |

### Storage Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `storage_operations_total` | Counter | operation, bucket, environment | Storage operations |
| `storage_bytes_transferred_total` | Counter | operation, bucket, environment | Bytes transferred |
| `storage_quota_used_bytes` | Gauge | user_id, plan, environment | Storage quota used |

### Rate Limiting & Errors

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `rate_limit_exceeded_total` | Counter | endpoint, plan, environment | Rate limit exceeded events |
| `errors_total` | Counter | error_type, component, environment | Application errors |

---

## Alerting

### Recommended Alert Rules

Add these to your Prometheus `alert.rules.yml`:

```yaml
groups:
  - name: celery_critical
    interval: 30s
    rules:
      - alert: NoActiveWorkers
        expr: sum(celery_active_workers) == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "No active Celery workers"
          description: "All Celery workers are down. Queue processing stopped."

      - alert: HighTaskFailureRate
        expr: |
          rate(celery_tasks_failed_total[5m])
          /
          rate(celery_tasks_submitted_total[5m])
          > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Celery task failure rate"
          description: "Task {{ $labels.task_name }} has >10% failure rate"

      - alert: QueueBacklog
        expr: celery_queue_length > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue backlog"
          description: "Queue {{ $labels.queue }} has {{ $value }} pending tasks"

  - name: fastapi_critical
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
          > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP error rate"
          description: "HTTP 5xx error rate is {{ $value | humanizePercentage }}"

      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          description: "P95 response time is {{ $value }}s"

  - name: llm_cost
    interval: 1h
    rules:
      - alert: HighLLMCost
        expr: |
          sum(increase(llm_cost_usd_total{environment="prod"}[1h])) > 50
        labels:
          severity: warning
        annotations:
          summary: "High LLM cost"
          description: "LLM cost exceeded $50/hour: ${{ $value }}"

      - alert: LowCacheHitRate
        expr: |
          sum(rate(llm_cache_hits_total[1h]))
          /
          sum(rate(llm_requests_total[1h]))
          < 0.3
        for: 2h
        labels:
          severity: info
        annotations:
          summary: "Low LLM cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

### Alert Notification Channels

Configure in Grafana:

1. **Alerting** → **Notification channels**
2. Add channels: Slack, Email, PagerDuty, etc.
3. Link channels to dashboard alerts

---

## Troubleshooting

### Metrics Not Appearing

**1. Check metrics endpoint is accessible**:

```bash
# Via NGINX
curl http://localhost:8100/metrics

# Direct app access
curl http://localhost:8000/metrics  # If using port mapping
```

**2. Verify Prometheus scrape targets**:

```bash
# Check Prometheus UI
http://localhost:9090/targets

# Look for:
# - State: UP
# - Last Scrape: < 30s ago
# - Error: (none)
```

**3. Check Docker networking**:

```bash
# Verify containers can reach each other
docker exec prometheus-container ping shia-chatbot-app-1

# Check network connectivity
docker network inspect chatbot-network
```

**4. Check FastAPI logs**:

```bash
docker-compose -f docker-compose.queue.yml logs app-1 | grep metrics
```

### Metrics Have No Data

**1. Generate some traffic**:

```bash
# Trigger some tasks
curl -X POST http://localhost:8100/api/v1/chat/conversations \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

**2. Check task execution**:

```bash
# View Celery logs
docker-compose -f docker-compose.queue.yml logs celery-worker-high-1

# Open Flower dashboard
http://localhost:5556
```

**3. Verify metrics are being tracked**:

```bash
# Check metrics file for Celery metrics
curl http://localhost:8100/metrics | grep celery_tasks_submitted_total
```

### Grafana Dashboard Empty

**1. Check Prometheus data source**:
- Grafana → **Configuration** → **Data Sources**
- Test connection to Prometheus
- Verify URL is correct

**2. Check time range**:
- Dashboard time picker (top right)
- Try "Last 1 hour" or "Last 6 hours"

**3. Check variable configuration**:
- Dashboard settings → **Variables**
- Verify `$environment` variable has values
- Try setting to "All"

**4. Run test query in Grafana**:
```promql
# Should return data
up{job="fastapi-queue-system"}
```

### High Memory Usage

**1. Check metrics cardinality**:

```bash
# Count unique metric series
curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data | length'

# Check series count per metric
curl -s http://localhost:9090/api/v1/series?match[]={__name__=~".+"} | jq '.data | length'
```

**2. Reduce label cardinality** if needed:

In `src/app/core/metrics.py`, avoid high-cardinality labels like:
- ❌ `user_id` (use `user_plan` instead)
- ❌ `conversation_id`
- ❌ Full error messages (use `error_type` instead)

### Performance Impact

Metrics collection has minimal overhead:

- **HTTP instrumentation**: ~1-2ms per request
- **Celery signals**: ~0.1ms per task
- **Memory**: ~50MB for registry (varies by cardinality)

**Optimization tips**:
1. Use histogram buckets wisely (don't over-bucket)
2. Set appropriate scrape intervals (15-30s)
3. Configure Prometheus retention policy
4. Use recording rules for expensive queries

---

## Best Practices

### 1. Metric Naming

Follow Prometheus naming conventions:
- `<namespace>_<name>_<unit>_<suffix>`
- Example: `celery_task_duration_seconds`

### 2. Label Usage

**Good labels** (low cardinality):
- `environment` (dev/stage/prod)
- `task_name` (limited set)
- `queue` (high/medium/low)
- `provider` (anthropic/openai/google)

**Bad labels** (high cardinality):
- `user_id` (unbounded)
- `request_id` (unique per request)
- `timestamp` (unique)

### 3. Dashboard Organization

**By Role**:
- **DevOps**: Infrastructure, system health, errors
- **Product**: Business metrics, user activity
- **Finance**: LLM costs, resource usage

**By Environment**:
- Use `$environment` variable for filtering
- Clone dashboard for permanent env-specific views

### 4. Cost Monitoring

Track LLM costs daily:

```promql
# Daily cost
sum(increase(llm_cost_usd_total{environment="prod"}[24h]))

# Cost per active user
sum(increase(llm_cost_usd_total[24h])) / avg(users_active)

# Most expensive models
topk(5, sum by (model) (increase(llm_cost_usd_total[24h])))
```

---

## Additional Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **Celery Monitoring**: https://docs.celeryq.dev/en/stable/userguide/monitoring.html
- **FastAPI Metrics**: https://github.com/trallnag/prometheus-fastapi-instrumentator

---

## Support

For issues or questions:

1. Check logs: `docker-compose -f docker-compose.queue.yml logs`
2. Review metrics endpoint: `curl http://localhost:8100/metrics`
3. Check Flower dashboard: `http://localhost:5556`
4. Verify Prometheus targets: `http://localhost:9090/targets`

**Happy monitoring! 🚀📊**
