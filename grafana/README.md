# Grafana Dashboards & Prometheus Configuration

This directory contains pre-built Grafana dashboards and Prometheus scrape configuration for monitoring the Shia Islamic Chatbot queue system.

## 📊 Available Dashboards

### 1. Celery Task Queue Monitoring
**File**: `dashboards/celery-monitoring.json`

Comprehensive monitoring of the Celery task queue system:

- **Task Metrics**: Submission rates, completion rates, failures, retries
- **Performance**: Task duration (p95), queue backlogs
- **Workers**: Active worker count, worker health
- **Distribution**: Tasks by priority queue
- **Troubleshooting**: Top 10 slowest tasks

**Use Cases**:
- Monitor queue health and performance
- Detect task failures and backlogs
- Optimize worker allocation
- Troubleshoot slow tasks

### 2. Application Performance & Business Metrics
**File**: `dashboards/application-performance.json`

Application-wide monitoring including HTTP, LLM, database, and business metrics:

- **HTTP Performance**: Request rates, response times, error rates
- **LLM Monitoring**: Token usage, costs, cache hit rates, provider performance
- **Database**: Connection pools, query performance
- **Business KPIs**: Active users, conversations, messages, images generated
- **Storage**: Usage by plan, quota tracking
- **Errors**: Rate limiting events, top error types

**Use Cases**:
- Monitor application health and performance
- Track LLM costs and optimize usage
- Analyze business metrics and user activity
- Identify performance bottlenecks

## 🚀 Quick Start

### 1. Import Dashboards to Grafana

```bash
# Via Grafana UI
1. Open Grafana: http://your-grafana:3000
2. Navigate to Dashboards → Import
3. Upload JSON file
4. Select Prometheus data source
5. Click Import

# Via API (automated)
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @dashboards/celery-monitoring.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @dashboards/application-performance.json
```

### 2. Configure Prometheus

Add the scrape configuration to your Prometheus server:

```bash
# Option 1: Merge with existing config
cat prometheus-scrape-config.yml >> /etc/prometheus/prometheus.yml

# Option 2: Include as separate file
# Add to /etc/prometheus/prometheus.yml:
# scrape_configs:
#   - job_name: 'include-queue-system'
#     file_sd_configs:
#       - files:
#           - '/path/to/prometheus-scrape-config.yml'

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# Or restart
systemctl restart prometheus
```

### 3. Verify Metrics Collection

```bash
# Check Prometheus targets
http://localhost:9090/targets

# Test metric query
http://localhost:9090/graph
# Query: celery_tasks_submitted_total

# Check metrics endpoint
curl http://localhost:8100/metrics | grep celery
```

## 📈 Dashboard Features

### Environment Filtering

Both dashboards support environment-based filtering via the `$environment` variable:

- **dev**: Development environment
- **stage**: Staging environment
- **prod**: Production environment
- **All**: All environments (aggregate view)

Change environment using the dropdown at the top of the dashboard.

### Alerting

Dashboards include pre-configured alert rules:

**Celery Monitoring**:
- ✅ High task failure rate (>10%)
- ✅ Queue backlog (>100 tasks)
- ✅ No active workers

**Application Performance**:
- ✅ High HTTP error rate (>5%)
- ✅ High response time (p95 >2s)

Configure notification channels in Grafana:
1. **Alerting** → **Notification channels**
2. Add Slack, Email, PagerDuty, etc.
3. Test notification

### Auto-Refresh

Dashboards auto-refresh:
- **Celery Monitoring**: 10 seconds
- **Application Performance**: 30 seconds

Adjust in dashboard settings if needed.

## 🔧 Customization

### Add Custom Panels

Example: Add "Cost per User" panel:

```json
{
  "title": "Cost per Active User (24h)",
  "type": "stat",
  "targets": [
    {
      "expr": "sum(increase(llm_cost_usd_total{environment=\"$environment\"}[24h])) / sum(users_active{environment=\"$environment\"})",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "currencyUSD",
      "decimals": 2
    }
  }
}
```

### Create Recording Rules

Optimize expensive queries with Prometheus recording rules:

```yaml
# /etc/prometheus/rules/queue-system.yml
groups:
  - name: queue_system_recordings
    interval: 60s
    rules:
      # Pre-calculate task success rate
      - record: job:celery_task_success_rate:rate5m
        expr: |
          rate(celery_tasks_completed_total[5m])
          /
          rate(celery_tasks_submitted_total[5m])

      # Pre-calculate average task duration
      - record: job:celery_task_duration_avg:rate5m
        expr: |
          rate(celery_task_duration_seconds_sum[5m])
          /
          rate(celery_task_duration_seconds_count[5m])

      # Pre-calculate daily LLM cost
      - record: job:llm_cost_daily:increase24h
        expr: sum(increase(llm_cost_usd_total[24h]))
```

## 📊 Metrics Reference

### Available Metric Prefixes

- `http_*`: HTTP request/response metrics
- `celery_*`: Celery task queue metrics
- `llm_*`: LLM usage and cost metrics
- `db_*`: Database connection and query metrics
- `redis_*`: Redis operations
- `storage_*`: MinIO/storage operations
- `users_*`: User activity metrics
- `conversations_*`: Conversation metrics
- `messages_*`: Message metrics
- `images_*`: Image generation metrics
- `rate_limit_*`: Rate limiting events
- `errors_*`: Application errors

### Label Conventions

Common labels across all metrics:
- `environment`: dev, stage, prod
- `task_name`: Celery task name
- `queue`: high_priority, medium_priority, low_priority
- `provider`: anthropic, openai, google
- `model`: Model identifier
- `endpoint`: API endpoint path
- `status_code`: HTTP status code

See `docs/MONITORING_GUIDE.md` for complete metrics documentation.

## 🔍 Troubleshooting

### Dashboard Shows "No Data"

**1. Check Prometheus data source**:
```bash
# In Grafana UI
Configuration → Data Sources → Prometheus
Test connection
```

**2. Check metrics are being scraped**:
```bash
# Open Prometheus UI
http://localhost:9090/targets

# Verify targets are UP
# Check Last Scrape < 30s
```

**3. Check time range**:
- Dashboard time picker (top right)
- Try "Last 1 hour"

**4. Generate test traffic**:
```bash
# Trigger some tasks
curl -X POST http://localhost:8100/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}'
```

### Metrics Not Appearing in Prometheus

**1. Verify metrics endpoint**:
```bash
curl http://localhost:8100/metrics | grep celery
```

**2. Check Prometheus logs**:
```bash
# Docker
docker logs prometheus-container

# Systemd
journalctl -u prometheus -f
```

**3. Check scrape config**:
```bash
# View loaded config
curl http://localhost:9090/api/v1/status/config
```

**4. Check network connectivity**:
```bash
# From Prometheus container
docker exec prometheus-container ping shia-chatbot-app-1

# Check Docker network
docker network inspect chatbot-network
```

### High Memory Usage

**Reduce metrics cardinality**:

1. Check series count:
```bash
curl http://localhost:9090/api/v1/label/__name__/values | jq '.data | length'
```

2. Identify high-cardinality metrics:
```bash
# Check series per metric
curl 'http://localhost:9090/api/v1/series?match[]={__name__=~".+"}' | jq '.data | length'
```

3. Configure Prometheus retention:
```yaml
# prometheus.yml
storage:
  tsdb:
    retention.time: 15d
    retention.size: 10GB
```

## 📚 Additional Resources

- **Full Monitoring Guide**: `docs/MONITORING_GUIDE.md`
- **Queue Management Guide**: `docs/QUEUE_MANAGEMENT.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/

## 🎯 Best Practices

1. **Use environment filtering**: Always filter by `$environment` in production
2. **Set up alerting**: Configure notification channels for critical alerts
3. **Monitor costs**: Track LLM costs daily using the cost panels
4. **Optimize caching**: Monitor cache hit rates and improve where possible
5. **Regular reviews**: Review dashboards weekly for anomalies
6. **Recording rules**: Use for expensive queries that run frequently
7. **Backup dashboards**: Export and version control dashboard JSON files

## 🚀 Next Steps

1. Import both dashboards to Grafana
2. Configure Prometheus scrape targets
3. Set up alert notification channels
4. Review dashboards after 24 hours of data collection
5. Customize panels based on your specific needs
6. Create team-specific dashboard views

**Happy monitoring! 📊🎉**
