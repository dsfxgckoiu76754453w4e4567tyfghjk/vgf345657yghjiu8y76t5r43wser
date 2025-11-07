"""Intent detection service for chat messages."""

import re
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentDetector:
    """
    Detect user intents from chat messages.

    Detects:
    - Image generation requests
    - Document upload requests
    - Other special intents
    """

    # Keywords that indicate image generation intent
    IMAGE_KEYWORDS = [
        # English
        "generate image", "create image", "make image", "draw image",
        "generate picture", "create picture", "make picture", "draw picture",
        "generate photo", "create photo", "make photo",
        "show me image", "show me picture", "show me photo",
        "i want image", "i want picture", "i want photo",
        "can you generate", "can you create", "can you make", "can you draw",
        "generate an image", "create an image", "make an image",
        "image of", "picture of", "photo of", "illustration of",
        # Arabic (common phrases)
        "صورة", "رسم", "اصنع صورة", "أنشئ صورة",
    ]

    # Patterns that indicate image generation
    IMAGE_PATTERNS = [
        r"(?:generate|create|make|draw|show|design)\s+(?:a|an|me)?\s*(?:image|picture|photo|illustration)",
        r"i\s+(?:want|need)\s+(?:a|an)?\s*(?:image|picture|photo)",
        r"(?:image|picture|photo)\s+of\s+",
        r"can\s+you\s+(?:generate|create|make|draw|show)",
    ]

    def __init__(self):
        """Initialize intent detector."""
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.IMAGE_PATTERNS]

    def detect_image_intent(self, message: str) -> tuple[bool, Optional[str]]:
        """
        Detect if the message is requesting image generation.

        Args:
            message: User message text

        Returns:
            Tuple of (is_image_request, extracted_prompt)
            - is_image_request: True if image generation is requested
            - extracted_prompt: The extracted image description (or None)
        """
        message_lower = message.lower().strip()

        # Check keywords
        for keyword in self.IMAGE_KEYWORDS:
            if keyword in message_lower:
                logger.info("image_intent_detected_keyword", keyword=keyword)
                prompt = self._extract_image_prompt(message, keyword)
                return True, prompt

        # Check patterns
        for pattern in self.compiled_patterns:
            if pattern.search(message):
                logger.info("image_intent_detected_pattern", pattern=pattern.pattern)
                prompt = self._extract_image_prompt_from_pattern(message, pattern)
                return True, prompt

        return False, None

    def _extract_image_prompt(self, message: str, keyword: str) -> str:
        """
        Extract the image description from the message.

        Args:
            message: Full user message
            keyword: Detected keyword

        Returns:
            Extracted image prompt
        """
        message_lower = message.lower()
        keyword_pos = message_lower.find(keyword)

        if keyword_pos == -1:
            return message

        # Try to extract everything after the keyword
        after_keyword = message[keyword_pos + len(keyword):].strip()

        # Remove common connecting words
        after_keyword = re.sub(r'^(?:of|:|for|that shows?|showing)\s+', '', after_keyword, flags=re.IGNORECASE)

        # If we have meaningful content after keyword, use it
        if len(after_keyword) > 10:
            return after_keyword

        # Otherwise, try to find content before keyword (e.g., "a mosque, generate image")
        before_keyword = message[:keyword_pos].strip()
        if len(before_keyword) > 10:
            # Remove trailing punctuation
            before_keyword = re.sub(r'[,;.!?]+$', '', before_keyword)
            return before_keyword

        # Fallback: use the entire message
        return message

    def _extract_image_prompt_from_pattern(self, message: str, pattern: re.Pattern) -> str:
        """
        Extract image prompt based on regex pattern match.

        Args:
            message: Full user message
            pattern: Matched regex pattern

        Returns:
            Extracted image prompt
        """
        match = pattern.search(message)
        if not match:
            return message

        # Get everything after the match
        after_match = message[match.end():].strip()

        # Remove common connecting words
        after_match = re.sub(r'^(?:of|:|for|that shows?|showing)\s+', '', after_match, flags=re.IGNORECASE)

        if len(after_match) > 10:
            return after_match

        # Fallback
        return message

    def should_generate_image(
        self,
        message: str,
        explicit_request: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if an image should be generated.

        Args:
            message: User message
            explicit_request: If True, user explicitly requested via button

        Returns:
            Tuple of (should_generate, image_prompt)
        """
        # If explicit request via button, always generate
        if explicit_request:
            return True, message

        # Otherwise, detect intent from message
        return self.detect_image_intent(message)


# Global intent detector instance
intent_detector = IntentDetector()
