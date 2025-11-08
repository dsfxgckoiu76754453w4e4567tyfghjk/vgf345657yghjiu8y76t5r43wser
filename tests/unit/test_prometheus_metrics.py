"""Unit tests for Prometheus metrics collection."""

import pytest
from unittest.mock import patch, MagicMock

from app.core import metrics


class TestTaskMetrics:
    """Test cases for Celery task metrics."""

    @patch('app.core.metrics.celery_tasks_submitted')
    def test_track_task_submission(self, mock_counter):
        """Test tracking task submission increments counter."""
        # Arrange
        task_name = "app.tasks.chat.process_chat_message"
        queue = "high_priority"

        # Act
        metrics.track_task_submission(task_name, queue)

        # Assert
        mock_counter.labels.assert_called_once_with(task_name, queue, metrics.settings.environment)
        mock_counter.labels().inc.assert_called_once()

    @patch('app.core.metrics.celery_tasks_completed')
    @patch('app.core.metrics.celery_task_duration_seconds')
    def test_track_task_completion(self, mock_histogram, mock_counter):
        """Test tracking task completion records metrics."""
        # Arrange
        task_name = "app.tasks.images.generate_image"
        queue = "high_priority"
        duration = 5.5

        # Act
        metrics.track_task_completion(task_name, queue, duration)

        # Assert
        mock_counter.labels.assert_called_once_with(task_name, queue, metrics.settings.environment)
        mock_counter.labels().inc.assert_called_once()
        mock_histogram.labels.assert_called_once_with(task_name, queue, metrics.settings.environment)
        mock_histogram.labels().observe.assert_called_once_with(duration)

    @patch('app.core.metrics.celery_tasks_failed')
    def test_track_task_failure(self, mock_counter):
        """Test tracking task failure increments counter."""
        # Arrange
        task_name = "app.tasks.asr.transcribe_audio"
        queue = "high_priority"

        # Act
        metrics.track_task_failure(task_name, queue)

        # Assert
        mock_counter.labels.assert_called_once_with(task_name, queue, metrics.settings.environment)
        mock_counter.labels().inc.assert_called_once()

    @patch('app.core.metrics.celery_tasks_retried')
    def test_track_task_retry(self, mock_counter):
        """Test tracking task retry increments counter."""
        # Arrange
        task_name = "app.tasks.web_search.search_web"
        queue = "high_priority"

        # Act
        metrics.track_task_retry(task_name, queue)

        # Assert
        mock_counter.labels.assert_called_once_with(task_name, queue, metrics.settings.environment)
        mock_counter.labels().inc.assert_called_once()


class TestLLMMetrics:
    """Test cases for LLM usage metrics."""

    @patch('app.core.metrics.llm_requests_total')
    @patch('app.core.metrics.llm_tokens_used')
    @patch('app.core.metrics.llm_cost_usd')
    @patch('app.core.metrics.llm_request_duration_seconds')
    def test_track_llm_request(self, mock_duration, mock_cost, mock_tokens, mock_requests):
        """Test tracking LLM request records all metrics."""
        # Arrange
        provider = "anthropic"
        model = "claude-3-sonnet"
        duration = 2.5
        tokens = {"prompt": 100, "completion": 50}
        cost = 0.15

        # Act
        metrics.track_llm_request(provider, model, duration, tokens, cost)

        # Assert
        mock_requests.labels.assert_called_once_with(provider, model, metrics.settings.environment)
        mock_requests.labels().inc.assert_called_once()
        mock_duration.observe.assert_called_once_with(duration)
        mock_cost.labels.assert_called_with(provider, model, metrics.settings.environment)
        # Should track prompt and completion tokens
        assert mock_tokens.labels.call_count >= 2

    @patch('app.core.metrics.llm_cache_hits')
    def test_track_cache_hit(self, mock_counter):
        """Test tracking cache hit increments counter."""
        # Arrange
        provider = "anthropic"
        model = "claude-3-sonnet"

        # Act
        metrics.track_cache_hit(provider, model)

        # Assert
        mock_counter.labels.assert_called_once_with(provider, model, metrics.settings.environment)
        mock_counter.labels().inc.assert_called_once()


class TestHTTPMetrics:
    """Test cases for HTTP request metrics."""

    def test_http_metrics_defined(self):
        """Test that HTTP metrics are properly defined."""
        # Assert
        assert hasattr(metrics, 'http_requests_total')
        assert hasattr(metrics, 'http_request_duration_seconds')
        assert hasattr(metrics, 'http_requests_in_progress')

    def test_http_metrics_have_correct_labels(self):
        """Test that HTTP metrics have correct labels."""
        # Arrange & Act
        http_requests = metrics.http_requests_total

        # Assert
        # Should have labels for method, endpoint, status_code, environment
        assert http_requests._labelnames == ('method', 'endpoint', 'status_code', 'environment')


class TestDatabaseMetrics:
    """Test cases for database metrics."""

    def test_database_metrics_defined(self):
        """Test that database metrics are properly defined."""
        # Assert
        assert hasattr(metrics, 'db_connections_active')
        assert hasattr(metrics, 'db_connections_idle')
        assert hasattr(metrics, 'db_query_duration_seconds')

    def test_db_connections_are_gauges(self):
        """Test that connection metrics are Gauge type."""
        # Assert
        from prometheus_client import Gauge
        assert isinstance(metrics.db_connections_active, Gauge)
        assert isinstance(metrics.db_connections_idle, Gauge)


class TestBusinessMetrics:
    """Test cases for business metrics."""

    def test_business_metrics_defined(self):
        """Test that business metrics are properly defined."""
        # Assert
        assert hasattr(metrics, 'users_active')
        assert hasattr(metrics, 'conversations_active')
        assert hasattr(metrics, 'messages_sent_total')
        assert hasattr(metrics, 'images_generated_total')

    def test_business_metrics_have_environment_labels(self):
        """Test that business metrics include environment label."""
        # Assert
        assert 'environment' in metrics.users_active._labelnames
        assert 'environment' in metrics.messages_sent_total._labelnames


class TestStorageMetrics:
    """Test cases for storage metrics."""

    def test_storage_metrics_defined(self):
        """Test that storage metrics are properly defined."""
        # Assert
        assert hasattr(metrics, 'storage_operations_total')
        assert hasattr(metrics, 'storage_bytes_transferred_total')
        assert hasattr(metrics, 'storage_quota_used_bytes')


class TestRateLimitMetrics:
    """Test cases for rate limit metrics."""

    def test_rate_limit_metrics_defined(self):
        """Test that rate limiting metrics are defined."""
        # Assert
        assert hasattr(metrics, 'rate_limit_exceeded_total')

    def test_rate_limit_metrics_have_correct_labels(self):
        """Test that rate limit metrics have endpoint and plan labels."""
        # Assert
        assert 'endpoint' in metrics.rate_limit_exceeded_total._labelnames
        assert 'plan' in metrics.rate_limit_exceeded_total._labelnames
        assert 'environment' in metrics.rate_limit_exceeded_total._labelnames


class TestErrorMetrics:
    """Test cases for error tracking metrics."""

    def test_error_metrics_defined(self):
        """Test that error metrics are defined."""
        # Assert
        assert hasattr(metrics, 'errors_total')

    def test_error_metrics_have_type_labels(self):
        """Test that error metrics categorize by error type."""
        # Assert
        assert 'error_type' in metrics.errors_total._labelnames
        assert 'component' in metrics.errors_total._labelnames


class TestQueueMetrics:
    """Test cases for queue length metrics."""

    def test_queue_length_metric_defined(self):
        """Test that queue length gauge is defined."""
        # Assert
        assert hasattr(metrics, 'celery_queue_length')

    def test_queue_length_is_gauge(self):
        """Test that queue length is a Gauge (not Counter)."""
        # Assert
        from prometheus_client import Gauge
        assert isinstance(metrics.celery_queue_length, Gauge)


class TestMetricsIntegration:
    """Integration tests for metrics collection."""

    def test_all_metric_collectors_initialized(self):
        """Test that all metric collectors are initialized."""
        # Assert - Check that all major metric types are present
        required_metrics = [
            'http_requests_total',
            'celery_tasks_submitted',
            'celery_tasks_completed',
            'celery_tasks_failed',
            'llm_requests_total',
            'llm_tokens_used',
            'llm_cost_usd',
            'db_connections_active',
            'users_active',
            'storage_operations_total',
            'rate_limit_exceeded_total',
            'errors_total'
        ]

        for metric_name in required_metrics:
            assert hasattr(metrics, metric_name), f"Missing metric: {metric_name}"

    def test_metrics_include_environment_label(self):
        """Test that critical metrics include environment label."""
        # Assert
        critical_metrics = [
            metrics.celery_tasks_submitted,
            metrics.llm_requests_total,
            metrics.users_active,
        ]

        for metric in critical_metrics:
            assert 'environment' in metric._labelnames


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
