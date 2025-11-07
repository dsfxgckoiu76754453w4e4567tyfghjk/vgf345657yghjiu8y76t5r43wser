"""Unit tests for intent detector service."""

import pytest

from app.services.intent_detector import intent_detector


class TestIntentDetector:
    """Test cases for IntentDetector."""

    def test_detect_image_intent_with_generate_keyword(self):
        """Test detection with 'generate image' keyword."""
        message = "Generate an image of a beautiful mosque at sunset"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is True
        assert prompt is not None
        assert "mosque" in prompt.lower()

    def test_detect_image_intent_with_create_keyword(self):
        """Test detection with 'create picture' keyword."""
        message = "Can you create a picture of Islamic calligraphy?"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is True
        assert prompt is not None

    def test_detect_image_intent_with_image_of_pattern(self):
        """Test detection with 'image of' pattern."""
        message = "I want an image of the Kaaba in Mecca"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is True
        assert prompt is not None
        assert "kaaba" in prompt.lower()

    def test_detect_image_intent_with_draw_keyword(self):
        """Test detection with 'draw' keyword."""
        message = "Please draw an illustration of a minaret"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is True
        assert prompt is not None
        assert "minaret" in prompt.lower()

    def test_no_image_intent_general_question(self):
        """Test that general questions are not detected as image requests."""
        message = "What is the capital of France?"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is False
        assert prompt is None

    def test_no_image_intent_normal_chat(self):
        """Test that normal chat is not detected as image request."""
        message = "Tell me about Islamic history and the five pillars"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is False
        assert prompt is None

    def test_should_generate_image_explicit_request(self):
        """Test explicit request via button."""
        message = "A beautiful sunset over the ocean"
        should_generate, prompt = intent_detector.should_generate_image(
            message=message,
            explicit_request=True,
        )

        assert should_generate is True
        assert prompt == message

    def test_should_generate_image_auto_detect(self):
        """Test automatic detection."""
        message = "Generate an image of a cat"
        should_generate, prompt = intent_detector.should_generate_image(
            message=message,
            explicit_request=False,
        )

        assert should_generate is True
        assert prompt is not None

    def test_extract_prompt_from_generate_image(self):
        """Test prompt extraction from 'generate image of X'."""
        message = "Generate an image of a beautiful mosque at sunset"
        _, prompt = intent_detector.detect_image_intent(message)

        assert "mosque" in prompt.lower()
        assert "sunset" in prompt.lower()

    def test_extract_prompt_from_create_picture(self):
        """Test prompt extraction from 'create picture of X'."""
        message = "Create a picture of Islamic architecture with domes"
        _, prompt = intent_detector.detect_image_intent(message)

        assert "islamic" in prompt.lower()
        assert "architecture" in prompt.lower()
        assert "domes" in prompt.lower()

    def test_arabic_keyword_detection(self):
        """Test detection with Arabic keywords."""
        message = "صورة مسجد جميل"
        should_generate, prompt = intent_detector.detect_image_intent(message)

        assert should_generate is True
        assert prompt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
