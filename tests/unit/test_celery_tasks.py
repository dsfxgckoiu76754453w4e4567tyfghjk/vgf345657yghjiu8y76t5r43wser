"""Comprehensive unit tests for Celery tasks."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.tasks.chat import process_chat_message
from app.tasks.asr import transcribe_audio
from app.tasks.images import generate_image
from app.tasks.web_search import search_web
from app.tasks.cleanup import clean_expired_files, cleanup_old_tasks
from app.tasks.email import send_email


class TestChatTask:
    """Test cases for chat processing task."""

    @patch('app.tasks.chat.EnhancedChatService')
    @patch('app.tasks.chat.get_async_session')
    def test_process_chat_message_success(self, mock_session, mock_service):
        """Test successful chat message processing."""
        # Arrange
        user_id = str(uuid4())
        conversation_id = str(uuid4())
        message_content = "What is prayer in Islam?"

        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.process_message.return_value = {
            'response': 'Prayer is one of the five pillars of Islam...',
            'model': 'claude-3-sonnet',
            'usage': {'input_tokens': 100, 'output_tokens': 50}
        }

        # Act
        result = process_chat_message(user_id, conversation_id, message_content)

        # Assert
        assert result['status'] == 'success'
        assert 'response' in result['result']
        assert result['result']['response'] == 'Prayer is one of the five pillars of Islam...'

    @patch('app.tasks.chat.EnhancedChatService')
    def test_process_chat_message_with_image_generation(self, mock_service):
        """Test chat message that triggers image generation."""
        # Arrange
        user_id = str(uuid4())
        conversation_id = str(uuid4())
        message_content = "Generate an image of a beautiful mosque"

        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.process_message.return_value = {
            'response': 'Here is your image of a mosque',
            'intent_results': {
                'generated_image': {
                    'url': 'https://storage.example.com/image.png',
                    'prompt': 'beautiful mosque'
                }
            }
        }

        # Act
        result = process_chat_message(user_id, conversation_id, message_content)

        # Assert
        assert result['status'] == 'success'
        assert 'intent_results' in result['result']
        assert 'generated_image' in result['result']['intent_results']

    @patch('app.tasks.chat.EnhancedChatService')
    def test_process_chat_message_failure_with_retry(self, mock_service):
        """Test chat message processing failure triggers retry."""
        # Arrange
        user_id = str(uuid4())
        conversation_id = str(uuid4())
        message_content = "Test message"

        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.process_message.side_effect = Exception("API unavailable")

        # Act & Assert
        with pytest.raises(Exception):
            process_chat_message(user_id, conversation_id, message_content)


class TestASRTask:
    """Test cases for audio transcription task."""

    @patch('app.tasks.asr.ASRService')
    @patch('app.tasks.asr.get_async_session')
    @patch('app.tasks.asr.MinIOStorageService')
    def test_transcribe_audio_success_persian(self, mock_storage, mock_session, mock_asr):
        """Test successful audio transcription with Persian (default language)."""
        # Arrange
        user_id = str(uuid4())
        audio_file_key = "audio/test.wav"
        language = "fa"  # Persian default

        mock_asr_instance = AsyncMock()
        mock_asr.return_value = mock_asr_instance
        mock_storage_instance = AsyncMock()
        mock_storage.return_value = mock_storage_instance

        # Mock audio file retrieval
        mock_storage_instance.get_file_content.return_value = b"fake_audio_data"

        # Mock transcription
        mock_asr_instance.transcribe_audio.return_value = {
            'text': 'سلام علیکم',
            'language': 'fa',
            'duration': 2.5,
            'provider': 'whisper'
        }

        # Act
        result = transcribe_audio(user_id, audio_file_key, language)

        # Assert
        assert result['status'] == 'success'
        assert result['result']['text'] == 'سلام علیکم'
        assert result['result']['language'] == 'fa'
        mock_asr_instance.transcribe_audio.assert_called_once()

    @patch('app.tasks.asr.ASRService')
    @patch('app.tasks.asr.MinIOStorageService')
    def test_transcribe_audio_english(self, mock_storage, mock_asr):
        """Test audio transcription with English language."""
        # Arrange
        user_id = str(uuid4())
        audio_file_key = "audio/test.wav"
        language = "en"

        mock_asr_instance = AsyncMock()
        mock_asr.return_value = mock_asr_instance
        mock_storage_instance = AsyncMock()
        mock_storage.return_value = mock_storage_instance

        mock_storage_instance.get_file_content.return_value = b"fake_audio_data"
        mock_asr_instance.transcribe_audio.return_value = {
            'text': 'Hello world',
            'language': 'en',
            'duration': 1.5
        }

        # Act
        result = transcribe_audio(user_id, audio_file_key, language)

        # Assert
        assert result['status'] == 'success'
        assert result['result']['text'] == 'Hello world'
        assert result['result']['language'] == 'en'

    @patch('app.tasks.asr.MinIOStorageService')
    def test_transcribe_audio_invalid_file(self, mock_storage):
        """Test transcription with invalid audio file."""
        # Arrange
        user_id = str(uuid4())
        audio_file_key = "audio/nonexistent.wav"

        mock_storage_instance = AsyncMock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.get_file_content.side_effect = FileNotFoundError("File not found")

        # Act & Assert
        with pytest.raises(Exception):
            transcribe_audio(user_id, audio_file_key, "fa")


class TestImageTask:
    """Test cases for image generation task."""

    @patch('app.tasks.images.ImageGenerationService')
    @patch('app.tasks.images.get_async_session')
    def test_generate_image_success(self, mock_session, mock_image_service):
        """Test successful image generation."""
        # Arrange
        user_id = str(uuid4())
        prompt = "A beautiful mosque at sunset"
        model = "dall-e-3"

        mock_service_instance = AsyncMock()
        mock_image_service.return_value = mock_service_instance
        mock_service_instance.generate_image.return_value = {
            'url': 'https://storage.example.com/mosque.png',
            'prompt': prompt,
            'model': model,
            'size': '1024x1024'
        }

        # Act
        result = generate_image(user_id, prompt, model)

        # Assert
        assert result['status'] == 'success'
        assert result['result']['url'] == 'https://storage.example.com/mosque.png'
        assert result['result']['prompt'] == prompt

    @patch('app.tasks.images.ImageGenerationService')
    @patch('app.tasks.images.get_async_session')
    def test_generate_image_quota_exceeded(self, mock_session, mock_image_service):
        """Test image generation with quota exceeded."""
        # Arrange
        user_id = str(uuid4())
        prompt = "Test image"

        mock_service_instance = AsyncMock()
        mock_image_service.return_value = mock_service_instance
        mock_service_instance.generate_image.side_effect = ValueError("Image quota exceeded")

        # Act & Assert
        with pytest.raises(ValueError, match="Image quota exceeded"):
            generate_image(user_id, prompt, "dall-e-3")

    @patch('app.tasks.images.ImageGenerationService')
    def test_generate_image_invalid_prompt(self, mock_image_service):
        """Test image generation with invalid prompt."""
        # Arrange
        user_id = str(uuid4())
        prompt = ""  # Empty prompt

        mock_service_instance = AsyncMock()
        mock_image_service.return_value = mock_service_instance
        mock_service_instance.generate_image.side_effect = ValueError("Invalid prompt")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid prompt"):
            generate_image(user_id, prompt, "dall-e-3")


class TestWebSearchTask:
    """Test cases for web search task."""

    @patch('app.tasks.web_search.WebSearchService')
    @patch('app.tasks.web_search.get_async_session')
    def test_search_web_success(self, mock_session, mock_search_service):
        """Test successful web search."""
        # Arrange
        user_id = str(uuid4())
        query = "Islamic history"

        mock_service_instance = AsyncMock()
        mock_search_service.return_value = mock_service_instance
        mock_service_instance.search.return_value = {
            'results': [
                {'title': 'Islamic History', 'url': 'https://example.com', 'snippet': 'Test snippet'}
            ],
            'query': query
        }

        # Act
        result = search_web(user_id, query)

        # Assert
        assert result['status'] == 'success'
        assert len(result['result']['results']) > 0
        assert result['result']['query'] == query

    @patch('app.tasks.web_search.WebSearchService')
    def test_search_web_empty_query(self, mock_search_service):
        """Test web search with empty query."""
        # Arrange
        user_id = str(uuid4())
        query = ""

        mock_service_instance = AsyncMock()
        mock_search_service.return_value = mock_service_instance
        mock_service_instance.search.side_effect = ValueError("Empty query")

        # Act & Assert
        with pytest.raises(ValueError, match="Empty query"):
            search_web(user_id, query)


class TestCleanupTasks:
    """Test cases for cleanup tasks."""

    @patch('app.tasks.cleanup.get_async_session')
    @patch('app.tasks.cleanup.MinIOStorageService')
    def test_clean_expired_files_success(self, mock_storage, mock_session):
        """Test successful cleanup of expired files."""
        # Arrange
        mock_storage_instance = AsyncMock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.cleanup_expired_files.return_value = 5  # 5 files deleted

        # Act
        result = clean_expired_files()

        # Assert
        assert result['status'] == 'success'
        assert result['files_deleted'] == 5
        mock_storage_instance.cleanup_expired_files.assert_called_once()

    @patch('app.tasks.cleanup.get_async_session')
    def test_cleanup_old_tasks_success(self, mock_session):
        """Test successful cleanup of old Celery tasks."""
        # Arrange
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        # Mock database query to delete old tasks
        mock_db.execute = AsyncMock(return_value=MagicMock(rowcount=10))

        # Act
        result = cleanup_old_tasks()

        # Assert
        assert result['status'] == 'success'
        assert result['tasks_deleted'] >= 0


class TestEmailTask:
    """Test cases for email sending task."""

    @patch('app.tasks.email.EmailService')
    def test_send_email_success(self, mock_email_service):
        """Test successful email sending."""
        # Arrange
        to_email = "user@example.com"
        subject = "Test Email"
        body = "Test body"

        mock_service_instance = AsyncMock()
        mock_email_service.return_value = mock_service_instance
        mock_service_instance.send_email.return_value = True

        # Act
        result = send_email(to_email, subject, body)

        # Assert
        assert result['status'] == 'success'
        mock_service_instance.send_email.assert_called_once()

    @patch('app.tasks.email.EmailService')
    def test_send_email_invalid_address(self, mock_email_service):
        """Test email sending with invalid address."""
        # Arrange
        to_email = "invalid-email"
        subject = "Test"
        body = "Test"

        mock_service_instance = AsyncMock()
        mock_email_service.return_value = mock_service_instance
        mock_service_instance.send_email.side_effect = ValueError("Invalid email")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email"):
            send_email(to_email, subject, body)


class TestTaskRouting:
    """Test cases for task queue routing."""

    def test_chat_task_routed_to_high_priority(self):
        """Test that chat tasks are routed to high priority queue."""
        from app.core.celery_app import celery_app

        # Check routing configuration
        route = celery_app.conf.task_routes.get('app.tasks.chat.process_chat_message')
        assert route is not None
        assert route['queue'] == 'high_priority'
        assert route['priority'] == 10

    def test_image_task_routed_to_high_priority(self):
        """Test that image tasks are routed to high priority queue."""
        from app.core.celery_app import celery_app

        route = celery_app.conf.task_routes.get('app.tasks.images.generate_image')
        assert route is not None
        assert route['queue'] == 'high_priority'
        assert route['priority'] == 9

    def test_email_task_routed_to_low_priority(self):
        """Test that email tasks are routed to low priority queue."""
        from app.core.celery_app import celery_app

        route = celery_app.conf.task_routes.get('app.tasks.email.send_email')
        assert route is not None
        assert route['queue'] == 'low_priority'
        assert route['priority'] == 2

    def test_cleanup_task_routed_to_low_priority(self):
        """Test that cleanup tasks are routed to low priority queue."""
        from app.core.celery_app import celery_app

        route = celery_app.conf.task_routes.get('app.tasks.cleanup.clean_expired_files')
        assert route is not None
        assert route['queue'] == 'low_priority'
        assert route['priority'] == 1


class TestTaskConfiguration:
    """Test cases for Celery task configuration."""

    def test_celery_app_configuration(self):
        """Test Celery app is properly configured."""
        from app.core.celery_app import celery_app

        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True

    def test_queue_configuration(self):
        """Test queue configurations."""
        from app.core.celery_app import celery_app

        queues = {q.name: q for q in celery_app.conf.task_queues}

        # Check all three priority queues exist
        assert 'high_priority' in queues
        assert 'medium_priority' in queues
        assert 'low_priority' in queues

        # Check priority levels
        assert queues['high_priority'].queue_arguments['x-max-priority'] == 10
        assert queues['medium_priority'].queue_arguments['x-max-priority'] == 5
        assert queues['low_priority'].queue_arguments['x-max-priority'] == 1

    def test_beat_schedule_configuration(self):
        """Test Celery Beat periodic task schedule."""
        from app.core.celery_app import celery_app

        assert 'cleanup-expired-files-daily' in celery_app.conf.beat_schedule
        assert 'cleanup-old-task-results-hourly' in celery_app.conf.beat_schedule
        assert 'recalculate-leaderboard-weekly' in celery_app.conf.beat_schedule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
