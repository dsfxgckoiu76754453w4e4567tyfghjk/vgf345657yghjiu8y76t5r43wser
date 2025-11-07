"""Comprehensive intent detection service for chat messages."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Types of user intents that can be detected."""

    # Primary action intents
    IMAGE_GENERATION = "image_generation"
    WEB_SEARCH = "web_search"
    DEEP_WEB_SEARCH = "deep_web_search"
    DOCUMENT_SEARCH = "document_search"
    AUDIO_TRANSCRIPTION = "audio_transcription"

    # Analysis intents
    DOCUMENT_ANALYSIS = "document_analysis"
    CODE_ANALYSIS = "code_analysis"

    # Information intents
    QUESTION_ANSWER = "question_answer"
    CONVERSATION = "conversation"

    # Tool intents
    TOOL_USAGE = "tool_usage"


@dataclass
class Intent:
    """Detected intent with metadata."""

    intent_type: IntentType
    confidence: float  # 0.0 to 1.0
    extracted_query: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    priority: int = 0  # Higher priority executes first

    def __repr__(self) -> str:
        return f"Intent({self.intent_type.value}, conf={self.confidence:.2f}, query={self.extracted_query[:30] if self.extracted_query else None})"


class IntentDetector:
    """
    Comprehensive intent detection service for chat messages.

    Detects multiple types of user intents:
    - Image generation requests
    - Web search requests (general and deep)
    - Document/RAG search requests
    - Audio transcription requests
    - Document/code analysis requests
    - Question answering
    - Tool usage

    Features:
    - Multi-intent detection (can detect multiple intents in one message)
    - Confidence scoring
    - Priority ordering
    - Query extraction for each intent
    - Support for English and Arabic
    """

    # ===== IMAGE GENERATION =====
    IMAGE_KEYWORDS = [
        # English - Explicit
        "generate image", "create image", "make image", "draw image",
        "generate picture", "create picture", "make picture", "draw picture",
        "generate photo", "create photo", "make photo",
        "design image", "design picture",
        # English - Implicit
        "show me image", "show me picture", "show me photo",
        "i want image", "i want picture", "i want photo", "need an image",
        "visualize", "illustration of",
        # Arabic
        "صورة", "رسم", "اصنع صورة", "أنشئ صورة", "ارسم",
    ]

    IMAGE_PATTERNS = [
        r"(?:generate|create|make|draw|show|design)\s+(?:a|an|me)?\s*(?:image|picture|photo|illustration|visual|graphic)",
        r"i\s+(?:want|need)\s+(?:a|an)?\s*(?:image|picture|photo)",
        r"(?:image|picture|photo|illustration)\s+(?:of|showing|depicting)\s+",
        r"can\s+you\s+(?:generate|create|make|draw|show|design)",
        r"visuali[sz]e\s+",
    ]

    # ===== WEB SEARCH =====
    WEB_SEARCH_KEYWORDS = [
        # English
        "search web", "search online", "search internet", "google",
        "search for", "look up", "find online", "web search",
        "search the web", "search the internet",
        "what does the internet say", "check online",
        "browse", "surf for",
        # Arabic
        "ابحث في الإنترنت", "ابحث على الويب", "بحث",
    ]

    WEB_SEARCH_PATTERNS = [
        r"(?:search|look|find|google|check)\s+(?:for|up|on|about|the)?\s*(?:web|internet|online)",
        r"what\s+(?:does|is)\s+(?:the\s+)?(?:web|internet|online)\s+(?:say|saying|show)",
        r"(?:search|look)\s+(?:this|that|it)\s+up\s+(?:online|on\s+the\s+web)",
        r"is\s+there\s+(?:any|anything|information)\s+online\s+about",
    ]

    # ===== DEEP WEB SEARCH =====
    DEEP_WEB_SEARCH_KEYWORDS = [
        # English
        "deep search", "thorough search", "comprehensive search",
        "search thoroughly", "extensive search", "detailed search",
        "deep dive", "research online", "in-depth search",
        "search everything", "search all sources",
        # Arabic
        "بحث شامل", "بحث عميق", "بحث مفصل",
    ]

    DEEP_WEB_SEARCH_PATTERNS = [
        r"(?:deep|thorough|comprehensive|extensive|detailed|in-depth)\s+(?:search|look|research|dive)",
        r"search\s+(?:thoroughly|extensively|comprehensively|in\s+depth|everywhere)",
        r"(?:research|investigate)\s+(?:this|that|it)\s+(?:online|on\s+the\s+web|thoroughly)",
    ]

    # ===== DOCUMENT SEARCH (RAG) =====
    DOCUMENT_SEARCH_KEYWORDS = [
        # English - Explicit
        "search documents", "search my documents", "search files",
        "find in documents", "look in my files", "check my documents",
        "search uploads", "search my uploads",
        # English - Implicit
        "in my documents", "from my files", "based on my documents",
        "according to my documents", "what do my documents say",
        # Arabic
        "ابحث في المستندات", "ابحث في الملفات", "من مستنداتي",
    ]

    DOCUMENT_SEARCH_PATTERNS = [
        r"(?:search|find|look|check)\s+(?:in|through|my)?\s*(?:document|file|upload|pdf)",
        r"what\s+(?:do|does)\s+my\s+(?:document|file|upload)s?\s+say",
        r"(?:based\s+on|according\s+to|from)\s+my\s+(?:document|file|upload)s?",
        r"in\s+my\s+(?:document|file|upload)s?",
    ]

    # ===== AUDIO TRANSCRIPTION =====
    AUDIO_KEYWORDS = [
        # English
        "transcribe", "transcription", "speech to text",
        "convert audio", "audio to text", "listen to",
        "what does the audio say", "transcribe audio",
        # Arabic
        "تفريغ صوتي", "تحويل صوت", "نص من صوت",
    ]

    AUDIO_PATTERNS = [
        r"(?:transcribe|convert)\s+(?:this|the|my)?\s*(?:audio|voice|speech|recording)",
        r"(?:audio|voice|speech)\s+to\s+text",
        r"what\s+(?:does|is)\s+(?:the|this)\s+audio\s+(?:say|saying)",
    ]

    # ===== DOCUMENT/CODE ANALYSIS =====
    ANALYSIS_KEYWORDS = [
        # Document analysis
        "analyze document", "analyze file", "review document",
        "summarize document", "explain document", "what is in",
        # Code analysis
        "analyze code", "review code", "explain code",
        "what does this code do", "code review",
        # Arabic
        "حلل", "راجع", "اشرح المستند",
    ]

    ANALYSIS_PATTERNS = [
        r"(?:analyze|review|summarize|explain|interpret)\s+(?:this|the|my)?\s*(?:document|file|code|pdf)",
        r"what\s+(?:is|does)\s+(?:this|the)\s+(?:document|file|code)\s+(?:say|do|about)",
        r"(?:give\s+me\s+a\s+)?(?:summary|analysis|review)\s+of\s+(?:this|the)",
    ]

    # ===== QUESTION KEYWORDS (Lower priority) =====
    QUESTION_PATTERNS = [
        r"^(?:what|who|when|where|why|how|which|whose)\s+",
        r"^(?:is|are|was|were|do|does|did|can|could|would|will|should)\s+",
        r"^tell\s+me\s+about",
        r"^explain\s+",
        r"\?$",  # Ends with question mark
    ]

    def __init__(self):
        """Initialize comprehensive intent detector."""
        # Compile patterns for efficiency
        self.image_patterns = [re.compile(p, re.IGNORECASE) for p in self.IMAGE_PATTERNS]
        self.web_search_patterns = [re.compile(p, re.IGNORECASE) for p in self.WEB_SEARCH_PATTERNS]
        self.deep_search_patterns = [re.compile(p, re.IGNORECASE) for p in self.DEEP_WEB_SEARCH_PATTERNS]
        self.doc_search_patterns = [re.compile(p, re.IGNORECASE) for p in self.DOCUMENT_SEARCH_PATTERNS]
        self.audio_patterns = [re.compile(p, re.IGNORECASE) for p in self.AUDIO_PATTERNS]
        self.analysis_patterns = [re.compile(p, re.IGNORECASE) for p in self.ANALYSIS_PATTERNS]
        self.question_patterns = [re.compile(p, re.IGNORECASE) for p in self.QUESTION_PATTERNS]

        logger.info("intent_detector_initialized", patterns_loaded=7)

    def detect_intents(self, message: str, context: Optional[dict] = None) -> list[Intent]:
        """
        Detect all intents in a message with confidence scores.

        Args:
            message: User message text
            context: Optional context (e.g., has_documents, has_audio, etc.)

        Returns:
            List of detected intents, sorted by priority (highest first)
        """
        message_lower = message.lower().strip()
        intents = []
        context = context or {}

        # 1. Check for image generation (Priority: 10)
        if self._check_intent(message_lower, self.IMAGE_KEYWORDS, self.image_patterns):
            extracted_prompt = self._extract_image_prompt(message)
            intents.append(Intent(
                intent_type=IntentType.IMAGE_GENERATION,
                confidence=0.95,
                extracted_query=extracted_prompt,
                priority=10,
                metadata={"prompt": extracted_prompt}
            ))

        # 2. Check for deep web search (Priority: 9 - must check before regular web search)
        if self._check_intent(message_lower, self.DEEP_WEB_SEARCH_KEYWORDS, self.deep_search_patterns):
            query = self._extract_search_query(message, self.DEEP_WEB_SEARCH_KEYWORDS)
            intents.append(Intent(
                intent_type=IntentType.DEEP_WEB_SEARCH,
                confidence=0.90,
                extracted_query=query,
                priority=9,
                metadata={"search_type": "deep", "query": query}
            ))

        # 3. Check for regular web search (Priority: 8)
        elif self._check_intent(message_lower, self.WEB_SEARCH_KEYWORDS, self.web_search_patterns):
            query = self._extract_search_query(message, self.WEB_SEARCH_KEYWORDS)
            intents.append(Intent(
                intent_type=IntentType.WEB_SEARCH,
                confidence=0.85,
                extracted_query=query,
                priority=8,
                metadata={"search_type": "web", "query": query}
            ))

        # 4. Check for document search (Priority: 9 - high because it's user's own data)
        if self._check_intent(message_lower, self.DOCUMENT_SEARCH_KEYWORDS, self.doc_search_patterns):
            query = self._extract_search_query(message, self.DOCUMENT_SEARCH_KEYWORDS)
            confidence = 0.92 if context.get("has_documents") else 0.70
            intents.append(Intent(
                intent_type=IntentType.DOCUMENT_SEARCH,
                confidence=confidence,
                extracted_query=query,
                priority=9,
                metadata={"search_type": "documents", "query": query}
            ))

        # 5. Check for audio transcription (Priority: 8)
        if self._check_intent(message_lower, self.AUDIO_KEYWORDS, self.audio_patterns):
            confidence = 0.95 if context.get("has_audio") else 0.75
            intents.append(Intent(
                intent_type=IntentType.AUDIO_TRANSCRIPTION,
                confidence=confidence,
                extracted_query=None,
                priority=8,
                metadata={"has_audio_attachment": context.get("has_audio", False)}
            ))

        # 6. Check for analysis requests (Priority: 7)
        if self._check_intent(message_lower, self.ANALYSIS_KEYWORDS, self.analysis_patterns):
            confidence = 0.85 if (context.get("has_documents") or context.get("has_code")) else 0.65
            # Determine if it's code or document analysis
            if "code" in message_lower or context.get("has_code"):
                intent_type = IntentType.CODE_ANALYSIS
            else:
                intent_type = IntentType.DOCUMENT_ANALYSIS

            intents.append(Intent(
                intent_type=intent_type,
                confidence=confidence,
                extracted_query=message,
                priority=7,
                metadata={"analysis_type": intent_type.value}
            ))

        # 7. Check if it's a question (Priority: 3 - lower priority, most messages might match)
        if any(pattern.search(message) for pattern in self.question_patterns):
            intents.append(Intent(
                intent_type=IntentType.QUESTION_ANSWER,
                confidence=0.60,
                extracted_query=message,
                priority=3,
                metadata={"is_question": True}
            ))

        # 8. Default to conversation if no strong intents detected (Priority: 1)
        if not intents or all(i.confidence < 0.70 for i in intents):
            intents.append(Intent(
                intent_type=IntentType.CONVERSATION,
                confidence=0.50,
                extracted_query=message,
                priority=1,
                metadata={"default_intent": True}
            ))

        # Sort by priority (highest first)
        intents.sort(key=lambda x: x.priority, reverse=True)

        # Log detected intents
        if intents:
            logger.info(
                "intents_detected",
                message_length=len(message),
                intent_count=len(intents),
                primary_intent=intents[0].intent_type.value if intents else None,
                all_intents=[i.intent_type.value for i in intents]
            )

        return intents

    def get_primary_intent(self, message: str, context: Optional[dict] = None) -> Optional[Intent]:
        """
        Get the highest priority intent from a message.

        Args:
            message: User message text
            context: Optional context

        Returns:
            Primary intent or None
        """
        intents = self.detect_intents(message, context)
        return intents[0] if intents else None

    def _check_intent(
        self,
        message_lower: str,
        keywords: list[str],
        patterns: list[re.Pattern]
    ) -> bool:
        """Check if message matches keywords or patterns."""
        # Check keywords
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return True

        # Check patterns
        for pattern in patterns:
            if pattern.search(message_lower):
                return True

        return False

    def _extract_image_prompt(self, message: str) -> str:
        """
        Extract the image description from the message.

        Args:
            message: Full user message

        Returns:
            Extracted image prompt
        """
        message_lower = message.lower()

        # Try to find and extract after keywords
        for keyword in self.IMAGE_KEYWORDS:
            keyword_pos = message_lower.find(keyword.lower())
            if keyword_pos != -1:
                after_keyword = message[keyword_pos + len(keyword):].strip()
                after_keyword = re.sub(r'^(?:of|:|for|that shows?|showing)\s+', '', after_keyword, flags=re.IGNORECASE)
                if len(after_keyword) > 10:
                    return after_keyword

        # Try patterns
        for pattern in self.image_patterns:
            match = pattern.search(message)
            if match:
                after_match = message[match.end():].strip()
                after_match = re.sub(r'^(?:of|:|for|that shows?|showing)\s+', '', after_match, flags=re.IGNORECASE)
                if len(after_match) > 10:
                    return after_match

        # Fallback: return entire message
        return message

    def _extract_search_query(self, message: str, keywords: list[str]) -> str:
        """
        Extract search query from message.

        Args:
            message: Full user message
            keywords: Keywords to remove from query

        Returns:
            Extracted search query
        """
        query = message

        # Remove search-related keywords to get clean query
        for keyword in keywords:
            query = re.sub(
                rf'\b{re.escape(keyword)}\b',
                '',
                query,
                flags=re.IGNORECASE
            )

        # Remove common connecting words
        query = re.sub(r'^(?:for|about|on|regarding|concerning)\s+', '', query, flags=re.IGNORECASE)
        query = query.strip()

        # If query is too short, return original message
        if len(query) < 3:
            return message

        return query

    # ===== BACKWARD COMPATIBILITY METHODS =====

    def detect_image_intent(self, message: str) -> tuple[bool, Optional[str]]:
        """
        Legacy method for backward compatibility.
        Detect if the message is requesting image generation.

        Args:
            message: User message text

        Returns:
            Tuple of (is_image_request, extracted_prompt)
        """
        intents = self.detect_intents(message)
        image_intents = [i for i in intents if i.intent_type == IntentType.IMAGE_GENERATION]

        if image_intents:
            intent = image_intents[0]
            return True, intent.extracted_query

        return False, None

    def should_generate_image(
        self,
        message: str,
        explicit_request: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Legacy method for backward compatibility.
        Determine if an image should be generated.

        Args:
            message: User message
            explicit_request: If True, user explicitly requested via button

        Returns:
            Tuple of (should_generate, image_prompt)
        """
        if explicit_request:
            return True, message

        return self.detect_image_intent(message)


# Global intent detector instance
intent_detector = IntentDetector()
