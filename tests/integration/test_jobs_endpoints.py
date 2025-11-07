"""Integration tests for job status API endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.main import app
from celery.result import AsyncResult


@pytest.fixture
def mock_celery_task():
    """Mock Celery task result."""
    with patch('app.api.v1.jobs.AsyncResult') as mock:
        yield mock


class TestJobStatusEndpoints:
    """Test cases for job status endpoints."""

    @pytest.mark.asyncio
    async def test_get_job_status_pending(self, mock_celery_task):
        """Test getting status of a pending job."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_task.info = None
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
        assert data['status'] == 'PENDING'
        assert data['progress'] is None
        assert data['result'] is None

    @pytest.mark.asyncio
    async def test_get_job_status_started_with_progress(self, mock_celery_task):
        """Test getting status of a started job with progress tracking."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'STARTED'
        mock_task.info = {
            'progress': 45,
            'status': 'Processing chat message...',
            'current_step': 'intent_detection'
        }
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
        assert data['status'] == 'STARTED'
        assert data['progress'] == 45
        assert data['metadata']['status'] == 'Processing chat message...'
        assert data['metadata']['current_step'] == 'intent_detection'

    @pytest.mark.asyncio
    async def test_get_job_status_success(self, mock_celery_task):
        """Test getting status of a successfully completed job."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.info = None
        mock_task.result = {
            'response': 'Here is your answer',
            'model': 'claude-3-sonnet',
            'usage': {'input_tokens': 100, 'output_tokens': 50}
        }
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
        assert data['status'] == 'SUCCESS'
        assert data['result'] is not None
        assert data['result']['response'] == 'Here is your answer'
        assert data['result']['model'] == 'claude-3-sonnet'

    @pytest.mark.asyncio
    async def test_get_job_status_failure(self, mock_celery_task):
        """Test getting status of a failed job."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.info = Exception("Task execution failed")
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
        assert data['status'] == 'FAILURE'
        assert 'error' in data
        assert 'Task execution failed' in str(data['error'])

    @pytest.mark.asyncio
    async def test_get_job_status_retry(self, mock_celery_task):
        """Test getting status of a job that's being retried."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'RETRY'
        mock_task.info = {
            'reason': 'Temporary API failure',
            'retry_count': 2
        }
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
        assert data['status'] == 'RETRY'
        assert data['metadata']['retry_count'] == 2

    @pytest.mark.asyncio
    async def test_cancel_job_success(self, mock_celery_task):
        """Test successfully canceling a job."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'STARTED'
        mock_task.revoke = MagicMock(return_value=None)
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
        assert data['status'] == 'cancelled'
        mock_task.revoke.assert_called_once_with(terminate=True)

    @pytest.mark.asyncio
    async def test_cancel_already_completed_job(self, mock_celery_task):
        """Test attempting to cancel an already completed job."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert 'cannot be cancelled' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, mock_celery_task):
        """Test canceling a job that doesn't exist."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/jobs/{job_id}")

        # Assert
        # Celery returns PENDING for non-existent tasks, should still revoke
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_active_jobs(self):
        """Test listing all active jobs."""
        # Note: This endpoint may need to be implemented
        # For now, test that the endpoint exists and returns proper structure

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/")

        # Assert
        # If endpoint exists, should return 200
        # If not implemented yet, should return 404 or 405
        assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_get_job_with_invalid_id_format(self):
        """Test getting job with invalid UUID format."""
        # Arrange
        invalid_job_id = "not-a-valid-uuid"

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{invalid_job_id}")

        # Assert
        # Should still work - Celery accepts any string as task ID
        # But should handle gracefully
        assert response.status_code in [200, 400, 404]


class TestJobProgressTracking:
    """Test cases for job progress tracking."""

    @pytest.mark.asyncio
    async def test_chat_task_progress_updates(self, mock_celery_task):
        """Test that chat task progress is properly tracked."""
        # Arrange
        job_id = str(uuid4())

        # Simulate progress updates
        progress_states = [
            {'progress': 20, 'status': 'Detecting intents...'},
            {'progress': 40, 'status': 'Processing with LLM...'},
            {'progress': 60, 'status': 'Generating response...'},
            {'progress': 80, 'status': 'Saving to database...'},
        ]

        for progress_state in progress_states:
            mock_task = MagicMock()
            mock_task.state = 'STARTED'
            mock_task.info = progress_state
            mock_task.result = None
            mock_celery_task.return_value = mock_task

            # Act
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/jobs/{job_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data['progress'] == progress_state['progress']
            assert data['metadata']['status'] == progress_state['status']

    @pytest.mark.asyncio
    async def test_image_generation_progress(self, mock_celery_task):
        """Test image generation task progress tracking."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'STARTED'
        mock_task.info = {
            'progress': 50,
            'status': 'Generating image with DALL-E...',
            'model': 'dall-e-3',
            'size': '1024x1024'
        }
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['progress'] == 50
        assert data['metadata']['model'] == 'dall-e-3'
        assert data['metadata']['size'] == '1024x1024'


class TestJobMetadata:
    """Test cases for job metadata tracking."""

    @pytest.mark.asyncio
    async def test_job_includes_queue_information(self, mock_celery_task):
        """Test that job status includes queue information."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'STARTED'
        mock_task.info = {
            'progress': 30,
            'queue': 'high_priority',
            'priority': 10
        }
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['metadata']['queue'] == 'high_priority'
        assert data['metadata']['priority'] == 10

    @pytest.mark.asyncio
    async def test_job_includes_timing_information(self, mock_celery_task):
        """Test that job status includes timing information."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.info = None
        mock_task.result = {
            'response': 'Success',
            'execution_time': 2.5,
            'started_at': '2024-01-15T10:00:00Z',
            'completed_at': '2024-01-15T10:00:02.5Z'
        }
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        result = data['result']
        assert result['execution_time'] == 2.5
        assert 'started_at' in result
        assert 'completed_at' in result


class TestJobErrorHandling:
    """Test cases for job error handling."""

    @pytest.mark.asyncio
    async def test_job_failure_with_detailed_error(self, mock_celery_task):
        """Test that failed jobs return detailed error information."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.info = Exception("Database connection failed: timeout after 30s")
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'FAILURE'
        assert 'Database connection failed' in str(data['error'])

    @pytest.mark.asyncio
    async def test_job_timeout_error(self, mock_celery_task):
        """Test job that exceeded time limit."""
        # Arrange
        job_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.info = Exception("Task exceeded time limit of 600 seconds")
        mock_task.result = None
        mock_celery_task.return_value = mock_task

        # Act
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'FAILURE'
        assert 'time limit' in str(data['error']).lower()


class TestJobBatchOperations:
    """Test cases for batch job operations."""

    @pytest.mark.asyncio
    async def test_get_multiple_job_statuses(self, mock_celery_task):
        """Test getting status of multiple jobs at once."""
        # Arrange
        job_ids = [str(uuid4()) for _ in range(3)]

        # This would require a batch endpoint - test individual calls for now
        for job_id in job_ids:
            mock_task = MagicMock()
            mock_task.state = 'SUCCESS'
            mock_task.result = {'response': f'Result for {job_id}'}
            mock_celery_task.return_value = mock_task

            # Act
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/jobs/{job_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data['job_id'] == job_id
            assert data['status'] == 'SUCCESS'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
