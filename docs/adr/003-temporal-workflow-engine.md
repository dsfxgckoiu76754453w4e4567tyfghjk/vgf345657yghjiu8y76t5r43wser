# ADR-003: Migrate from Celery to Temporal Workflow Engine

**Status**: Accepted
**Date**: 2025-01-14
**Impact**: Critical

---

## Problem
Celery as our async task queue had several limitations:
- No built-in workflow orchestration (complex multi-step tasks)
- Limited visibility into task execution history
- Manual retry logic and state management
- No versioning support for task definitions
- Debugging long-running workflows was difficult

---

## Decision
Replace Celery with Temporal as our workflow orchestration engine for all async background processing.

**Key Changes:**
- Remove all Celery dependencies and configuration
- Implement workflows using Temporal SDK
- Migrate existing tasks to Temporal activities
- Use Temporal UI for monitoring (replaces Flower)
- Update metrics from Celery-specific to Temporal workflow metrics

---

## Why
- **Durable Execution**: Workflows survive worker crashes and restarts
- **Built-in Observability**: Complete execution history and state visibility via Temporal UI
- **Workflow Versioning**: Safe deployment of workflow changes without breaking in-flight executions
- **Declarative Workflows**: Code-as-workflow with full IDE support and type safety
- **Better Developer Experience**: Easier to debug, test, and maintain complex workflows
- **Production-Grade**: Used by major companies (Netflix, Stripe, Coinbase)
- **Activity Retries**: Automatic retry logic with configurable policies per activity
- **Real-time State Queries**: Query workflow state without complex database queries

---

## Alternatives Rejected
- **Keep Celery**: Lacks workflow orchestration, versioning, and modern observability
- **Apache Airflow**: Designed for batch/scheduled jobs, not real-time workflows
- **AWS Step Functions**: Vendor lock-in, limited local development, higher costs
- **Custom Solution**: High maintenance burden, reinventing the wheel

---

## Impact

**Changed Components:**
- `src/app/workflows/` - New Temporal workflows (ChatWorkflow)
- `src/app/core/config.py` - Removed 4 Celery fields, added 4 Temporal fields
- `src/app/core/metrics.py` - Replaced 7 Celery metrics with 8 Temporal metrics
- `.env.example` - Removed Celery/Flower configs, added Temporal configs
- `docker-compose.base.yml` - Temporal server + UI (port 8233)

**Deleted:**
- `tests/unit/test_celery_tasks.py` - Obsolete Celery tests
- `tests/integration/test_jobs_endpoints.py` - Celery AsyncResult usage
- `grafana/dashboards/celery-monitoring.json` - Celery Grafana dashboard
- `scripts/start-queue-system.sh` - Obsolete Celery worker script

**Breaking Changes:** Yes
- All Celery task definitions removed
- Flower monitoring dashboard no longer available
- Environment variables changed (CELERY_* → TEMPORAL_*)

**Migration Required:** Yes
- Update deployment configs to use Temporal environment variables
- Redeploy all environments with new docker-compose configurations
- Monitor Temporal UI instead of Flower (port 8233 instead of 5555)

---

## Notes
- **Temporal UI**: http://localhost:8233 (when using docker-compose.base.yml)
- **Migration PR**: Full details in commit `ccf272a`
- **Monitoring**: Prometheus metrics updated to track workflow execution
- **Current Implementation**: ChatWorkflow for RAG pipeline (5 activities)
- **Future Work**: Migrate remaining async operations to Temporal workflows
- **Documentation**: CLAUDE.md and TECH_STACK.md already reflect this change
