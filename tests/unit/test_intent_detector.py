"""Comprehensive unit tests for intent detector service."""

import pytest

from app.services.intent_detector import intent_detector, IntentType, Intent


class TestIntentDetector:
    """Test cases for comprehensive IntentDetector."""

    # ===== IMAGE GENERATION TESTS =====

    def test_detect_image_generation_explicit(self):
        """Test detection of explicit image generation request."""
        message = "Generate an image of a beautiful mosque at sunset"
        intents = intent_detector.detect_intents(message)

        assert len(intents) >= 1
        image_intent = next((i for i in intents if i.intent_type == IntentType.IMAGE_GENERATION), None)
        assert image_intent is not None
        assert image_intent.confidence >= 0.90
        assert "mosque" in image_intent.extracted_query.lower()

    def test_detect_image_generation_implicit(self):
        """Test detection of implicit image request."""
        message = "I want to see a picture of Islamic calligraphy"
        intents = intent_detector.detect_intents(message)

        image_intent = next((i for i in intents if i.intent_type == IntentType.IMAGE_GENERATION), None)
        assert image_intent is not None
        assert "calligraphy" in image_intent.extracted_query.lower()

    def test_detect_image_with_create_keyword(self):
        """Test detection with 'create picture' keyword."""
        message = "Can you create a picture of the Kaaba?"
        intents = intent_detector.detect_intents(message)

        image_intent = next((i for i in intents if i.intent_type == IntentType.IMAGE_GENERATION), None)
        assert image_intent is not None
        assert "kaaba" in image_intent.extracted_query.lower()

    # ===== WEB SEARCH TESTS =====

    def test_detect_web_search_explicit(self):
        """Test detection of explicit web search request."""
        message = "Search the web for Islamic history"
        intents = intent_detector.detect_intents(message)

        web_intent = next((i for i in intents if i.intent_type == IntentType.WEB_SEARCH), None)
        assert web_intent is not None
        assert web_intent.confidence >= 0.80
        assert "islamic history" in web_intent.extracted_query.lower()

    def test_detect_web_search_google(self):
        """Test detection of Google search request."""
        message = "Google the five pillars of Islam"
        intents = intent_detector.detect_intents(message)

        web_intent = next((i for i in intents if i.intent_type == IntentType.WEB_SEARCH), None)
        assert web_intent is not None
        assert "five pillars" in web_intent.extracted_query.lower()

    def test_detect_web_search_lookup(self):
        """Test detection of 'look up' pattern."""
        message = "Look up information about Ramadan online"
        intents = intent_detector.detect_intents(message)

        web_intent = next((i for i in intents if i.intent_type == IntentType.WEB_SEARCH), None)
        assert web_intent is not None

    # ===== DEEP WEB SEARCH TESTS =====

    def test_detect_deep_web_search(self):
        """Test detection of deep web search request."""
        message = "Do a thorough search for Islamic scholars"
        intents = intent_detector.detect_intents(message)

        deep_search_intent = next((i for i in intents if i.intent_type == IntentType.DEEP_WEB_SEARCH), None)
        assert deep_search_intent is not None
        assert deep_search_intent.confidence >= 0.85
        assert "islamic scholars" in deep_search_intent.extracted_query.lower()

    def test_detect_deep_search_comprehensive(self):
        """Test detection of comprehensive search request."""
        message = "Search comprehensively for Hadith collections"
        intents = intent_detector.detect_intents(message)

        deep_search_intent = next((i for i in intents if i.intent_type == IntentType.DEEP_WEB_SEARCH), None)
        assert deep_search_intent is not None

    def test_deep_search_priority_over_regular(self):
        """Test that deep search is detected instead of regular search."""
        message = "Do an in-depth search for Quran interpretations"
        intents = intent_detector.detect_intents(message)

        # Should detect deep search, not regular web search
        deep_search_intent = next((i for i in intents if i.intent_type == IntentType.DEEP_WEB_SEARCH), None)
        web_search_intent = next((i for i in intents if i.intent_type == IntentType.WEB_SEARCH), None)

        assert deep_search_intent is not None
        assert web_search_intent is None  # Should not detect both

    # ===== DOCUMENT SEARCH TESTS =====

    def test_detect_document_search_explicit(self):
        """Test detection of explicit document search."""
        message = "Search my documents for prayer times"
        context = {"has_documents": True}
        intents = intent_detector.detect_intents(message, context)

        doc_intent = next((i for i in intents if i.intent_type == IntentType.DOCUMENT_SEARCH), None)
        assert doc_intent is not None
        assert doc_intent.confidence >= 0.90
        assert "prayer times" in doc_intent.extracted_query.lower()

    def test_detect_document_search_implicit(self):
        """Test detection of implicit document search."""
        message = "What do my documents say about fasting?"
        intents = intent_detector.detect_intents(message)

        doc_intent = next((i for i in intents if i.intent_type == IntentType.DOCUMENT_SEARCH), None)
        assert doc_intent is not None

    def test_document_search_confidence_with_context(self):
        """Test that confidence is higher with document context."""
        message = "Search my files for Islamic teachings"

        # Without context
        intents_no_context = intent_detector.detect_intents(message, {})
        doc_intent_no_context = next((i for i in intents_no_context if i.intent_type == IntentType.DOCUMENT_SEARCH), None)

        # With context
        intents_with_context = intent_detector.detect_intents(message, {"has_documents": True})
        doc_intent_with_context = next((i for i in intents_with_context if i.intent_type == IntentType.DOCUMENT_SEARCH), None)

        assert doc_intent_with_context.confidence > doc_intent_no_context.confidence

    # ===== AUDIO TRANSCRIPTION TESTS =====

    def test_detect_audio_transcription(self):
        """Test detection of audio transcription request."""
        message = "Transcribe this audio recording"
        context = {"has_audio": True}
        intents = intent_detector.detect_intents(message, context)

        audio_intent = next((i for i in intents if i.intent_type == IntentType.AUDIO_TRANSCRIPTION), None)
        assert audio_intent is not None
        assert audio_intent.confidence >= 0.90

    def test_detect_speech_to_text(self):
        """Test detection of speech to text request."""
        message = "Convert this speech to text"
        intents = intent_detector.detect_intents(message)

        audio_intent = next((i for i in intents if i.intent_type == IntentType.AUDIO_TRANSCRIPTION), None)
        assert audio_intent is not None

    # ===== ANALYSIS TESTS =====

    def test_detect_document_analysis(self):
        """Test detection of document analysis request."""
        message = "Analyze this PDF document"
        context = {"has_documents": True}
        intents = intent_detector.detect_intents(message, context)

        analysis_intent = next((i for i in intents if i.intent_type == IntentType.DOCUMENT_ANALYSIS), None)
        assert analysis_intent is not None
        assert analysis_intent.confidence >= 0.80

    def test_detect_code_analysis(self):
        """Test detection of code analysis request."""
        message = "Review this code and explain what it does"
        context = {"has_code": True}
        intents = intent_detector.detect_intents(message, context)

        code_intent = next((i for i in intents if i.intent_type == IntentType.CODE_ANALYSIS), None)
        assert code_intent is not None

    def test_code_vs_document_analysis(self):
        """Test that code analysis is detected over document analysis when 'code' is mentioned."""
        message = "Analyze this code snippet"
        intents = intent_detector.detect_intents(message)

        # Should detect code analysis specifically
        analysis_intents = [i for i in intents if i.intent_type in [IntentType.CODE_ANALYSIS, IntentType.DOCUMENT_ANALYSIS]]
        assert len(analysis_intents) > 0
        assert analysis_intents[0].intent_type == IntentType.CODE_ANALYSIS

    # ===== QUESTION ANSWER TESTS =====

    def test_detect_question_what(self):
        """Test detection of 'what' question."""
        message = "What is the capital of France?"
        intents = intent_detector.detect_intents(message)

        question_intent = next((i for i in intents if i.intent_type == IntentType.QUESTION_ANSWER), None)
        assert question_intent is not None

    def test_detect_question_how(self):
        """Test detection of 'how' question."""
        message = "How do Muslims pray?"
        intents = intent_detector.detect_intents(message)

        question_intent = next((i for i in intents if i.intent_type == IntentType.QUESTION_ANSWER), None)
        assert question_intent is not None

    # ===== MULTI-INTENT TESTS =====

    def test_multiple_intents_detected(self):
        """Test that multiple intents can be detected in one message."""
        message = "Search the web for mosque images and generate a picture based on the results"
        intents = intent_detector.detect_intents(message)

        # Should detect both web search and image generation
        intent_types = [i.intent_type for i in intents]
        assert IntentType.WEB_SEARCH in intent_types or IntentType.DEEP_WEB_SEARCH in intent_types
        assert IntentType.IMAGE_GENERATION in intent_types

    def test_intent_priority_ordering(self):
        """Test that intents are ordered by priority."""
        message = "Generate an image and search for information online"
        intents = intent_detector.detect_intents(message)

        # Intents should be sorted by priority (highest first)
        for i in range(len(intents) - 1):
            assert intents[i].priority >= intents[i + 1].priority

    # ===== CONVERSATION FALLBACK TESTS =====

    def test_conversation_fallback(self):
        """Test that normal conversation is detected when no strong intent."""
        message = "Hello, how are you today?"
        intents = intent_detector.detect_intents(message)

        # Should have conversation intent as fallback
        conv_intent = next((i for i in intents if i.intent_type == IntentType.CONVERSATION), None)
        assert conv_intent is not None

    def test_no_false_positives(self):
        """Test that general statements don't trigger action intents."""
        message = "I like to search for good books to read"
        intents = intent_detector.detect_intents(message)

        # Should not trigger web search with high confidence
        web_intents = [i for i in intents if i.intent_type in [IntentType.WEB_SEARCH, IntentType.DEEP_WEB_SEARCH]]
        # Either no web intent, or low confidence
        if web_intents:
            assert all(i.confidence < 0.80 for i in web_intents)

    # ===== PRIMARY INTENT TESTS =====

    def test_get_primary_intent(self):
        """Test getting the primary (highest priority) intent."""
        message = "Generate an image of a mosque"
        primary = intent_detector.get_primary_intent(message)

        assert primary is not None
        assert primary.intent_type == IntentType.IMAGE_GENERATION

    def test_primary_intent_with_multiple(self):
        """Test primary intent selection with multiple intents."""
        message = "Search online for mosque images and generate a picture"
        primary = intent_detector.get_primary_intent(message)

        assert primary is not None
        # Image generation has higher priority (10) than web search (8)
        assert primary.intent_type == IntentType.IMAGE_GENERATION

    # ===== BACKWARD COMPATIBILITY TESTS =====

    def test_backward_compat_detect_image_intent(self):
        """Test backward compatibility method for image detection."""
        message = "Generate an image of a beautiful sunset"
        is_image, prompt = intent_detector.detect_image_intent(message)

        assert is_image is True
        assert prompt is not None
        assert "sunset" in prompt.lower()

    def test_backward_compat_should_generate_image(self):
        """Test backward compatibility method for image generation decision."""
        message = "Create a picture of mountains"
        should_gen, prompt = intent_detector.should_generate_image(message)

        assert should_gen is True
        assert prompt is not None

    def test_backward_compat_explicit_request(self):
        """Test backward compatibility with explicit request flag."""
        message = "A beautiful landscape"
        should_gen, prompt = intent_detector.should_generate_image(message, explicit_request=True)

        assert should_gen is True
        assert prompt == message

    # ===== ARABIC SUPPORT TESTS =====

    def test_arabic_image_keyword(self):
        """Test detection with Arabic image keywords."""
        message = "صورة مسجد جميل"
        intents = intent_detector.detect_intents(message)

        image_intent = next((i for i in intents if i.intent_type == IntentType.IMAGE_GENERATION), None)
        assert image_intent is not None

    def test_arabic_search_keyword(self):
        """Test detection with Arabic search keywords."""
        message = "ابحث في الإنترنت عن التاريخ الإسلامي"
        intents = intent_detector.detect_intents(message)

        web_intent = next((i for i in intents if i.intent_type == IntentType.WEB_SEARCH), None)
        assert web_intent is not None


class TestIntentClass:
    """Test the Intent dataclass."""

    def test_intent_creation(self):
        """Test creating an Intent instance."""
        intent = Intent(
            intent_type=IntentType.IMAGE_GENERATION,
            confidence=0.95,
            extracted_query="a beautiful mosque",
            priority=10,
            metadata={"test": "value"}
        )

        assert intent.intent_type == IntentType.IMAGE_GENERATION
        assert intent.confidence == 0.95
        assert intent.extracted_query == "a beautiful mosque"
        assert intent.priority == 10
        assert intent.metadata == {"test": "value"}

    def test_intent_repr(self):
        """Test Intent string representation."""
        intent = Intent(
            intent_type=IntentType.WEB_SEARCH,
            confidence=0.85,
            extracted_query="Islamic history and traditions",
            priority=8
        )

        repr_str = repr(intent)
        assert "web_search" in repr_str
        assert "0.85" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
