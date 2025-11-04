"""Automatic Speech Recognition (ASR) service."""

import io
from typing import Literal, Optional

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ASRService:
    """Service for speech-to-text conversion using multiple providers."""

    def __init__(self):
        """Initialize ASR service."""
        # Get provider from settings
        self.provider: Literal["google", "whisper"] = getattr(
            settings, "asr_provider", "whisper"
        )

        # Initialize clients based on provider
        if self.provider == "whisper":
            openai_api_key = getattr(settings, "openai_api_key", None)
            self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        elif self.provider == "google":
            # Google Speech-to-Text client would be initialized here
            self.google_credentials = getattr(settings, "google_credentials_path", None)

    # ========================================================================
    # Speech-to-Text Transcription
    # ========================================================================

    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: str = "ar",  # Arabic by default
        model: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format (wav, mp3, m4a, etc.)
            language: Language code (ar, en, fa, ur)
            model: Specific model to use (optional)

        Returns:
            Transcription result with text and metadata
        """
        if self.provider == "whisper":
            return await self._transcribe_with_whisper(audio_data, audio_format, language, model)
        elif self.provider == "google":
            return await self._transcribe_with_google(audio_data, audio_format, language)
        else:
            raise ValueError(f"Unsupported ASR provider: {self.provider}")

    # ========================================================================
    # OpenAI Whisper Implementation
    # ========================================================================

    async def _transcribe_with_whisper(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str,
        model: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio using OpenAI Whisper.

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format
            language: Language code
            model: Model to use (whisper-1 by default)

        Returns:
            Transcription result
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"

            # Call Whisper API
            transcription = await self.openai_client.audio.transcriptions.create(
                model=model or "whisper-1",
                file=audio_file,
                language=language,  # ISO-639-1 code
                response_format="verbose_json",  # Get detailed response
            )

            logger.info(
                "whisper_transcription_success",
                language=language,
                duration=getattr(transcription, "duration", None),
            )

            return {
                "text": transcription.text,
                "language": language,
                "duration": getattr(transcription, "duration", None),
                "provider": "whisper",
                "model": model or "whisper-1",
            }

        except Exception as e:
            logger.error("whisper_transcription_failed", error=str(e))
            raise ValueError(f"Whisper transcription failed: {str(e)}")

    # ========================================================================
    # Google Speech-to-Text Implementation
    # ========================================================================

    async def _transcribe_with_google(
        self, audio_data: bytes, audio_format: str, language: str
    ) -> dict:
        """
        Transcribe audio using Google Speech-to-Text.

        This is a placeholder implementation. In production, you would:
        1. Install google-cloud-speech
        2. Set up credentials
        3. Use the Speech-to-Text API

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format
            language: Language code

        Returns:
            Transcription result
        """
        try:
            # PLACEHOLDER: This is where you would implement Google Speech-to-Text
            # from google.cloud import speech
            #
            # client = speech.SpeechClient()
            # audio = speech.RecognitionAudio(content=audio_data)
            # config = speech.RecognitionConfig(
            #     encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            #     language_code=language,
            #     enable_automatic_punctuation=True,
            # )
            #
            # response = client.recognize(config=config, audio=audio)
            #
            # text = " ".join([result.alternatives[0].transcript for result in response.results])

            # For now, return placeholder
            logger.warn(
                "google_speech_placeholder",
                message="Google Speech-to-Text not fully implemented",
            )

            return {
                "text": "[Google Speech-to-Text transcription would appear here]",
                "language": language,
                "provider": "google",
                "note": "This is a placeholder implementation",
            }

        except Exception as e:
            logger.error("google_speech_transcription_failed", error=str(e))
            raise ValueError(f"Google Speech transcription failed: {str(e)}")

    # ========================================================================
    # Language Support
    # ========================================================================

    def get_supported_languages(self) -> list[dict]:
        """
        Get list of supported languages for ASR.

        Returns:
            List of supported languages with codes
        """
        # Common languages for Islamic content
        languages = [
            {"code": "ar", "name": "Arabic", "native_name": "العربية"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "fa", "name": "Persian", "native_name": "فارسی"},
            {"code": "ur", "name": "Urdu", "native_name": "اردو"},
            {"code": "tr", "name": "Turkish", "native_name": "Türkçe"},
            {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia"},
            {"code": "ms", "name": "Malay", "native_name": "Bahasa Melayu"},
        ]

        return languages

    # ========================================================================
    # Audio Validation
    # ========================================================================

    def validate_audio(
        self,
        audio_data: bytes,
        max_size_mb: int = 25,  # Whisper max is 25MB
        allowed_formats: Optional[list[str]] = None,
    ) -> dict:
        """
        Validate audio file before transcription.

        Args:
            audio_data: Audio file bytes
            max_size_mb: Maximum file size in MB
            allowed_formats: List of allowed audio formats

        Returns:
            Validation result
        """
        if allowed_formats is None:
            allowed_formats = ["wav", "mp3", "m4a", "flac", "ogg", "webm"]

        # Check file size
        size_mb = len(audio_data) / (1024 * 1024)

        is_valid = size_mb <= max_size_mb

        return {
            "is_valid": is_valid,
            "size_mb": round(size_mb, 2),
            "max_size_mb": max_size_mb,
            "allowed_formats": allowed_formats,
            "error": f"File too large ({size_mb:.2f}MB > {max_size_mb}MB)"
            if not is_valid
            else None,
        }

    # ========================================================================
    # Translation (Speech-to-Text in Different Language)
    # ========================================================================

    async def translate_audio_to_english(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
    ) -> dict:
        """
        Transcribe and translate audio to English.

        CRITICAL: This translates the audio to English regardless of source language.

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format

        Returns:
            Translated transcription result
        """
        if self.provider != "whisper":
            raise ValueError("Translation is only supported with Whisper")

        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"

            # Call Whisper translation API
            translation = await self.openai_client.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )

            logger.info(
                "whisper_translation_success",
                duration=getattr(translation, "duration", None),
            )

            return {
                "text": translation.text,
                "language": "en",  # Always English
                "duration": getattr(translation, "duration", None),
                "provider": "whisper",
                "model": "whisper-1",
                "is_translation": True,
            }

        except Exception as e:
            logger.error("whisper_translation_failed", error=str(e))
            raise ValueError(f"Whisper translation failed: {str(e)}")
