"""Automatic Speech Recognition (ASR) service."""

import base64
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
        self.provider: Literal["google", "whisper", "gemini"] = getattr(
            settings, "asr_provider", "whisper"
        )

        # Initialize clients based on provider
        if self.provider == "whisper":
            openai_api_key = getattr(settings, "openai_api_key", None)
            self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        elif self.provider == "google":
            # Google Speech-to-Text client would be initialized here
            self.google_credentials = getattr(settings, "google_credentials_path", None)
        elif self.provider == "gemini":
            # Gemini client will be initialized on-demand
            self.gemini_api_key = getattr(settings, "gemini_api_key", None)
            self.gemini_asr_model = getattr(settings, "gemini_asr_model", "gemini-2.0-flash-exp")

    # ========================================================================
    # Speech-to-Text Transcription
    # ========================================================================

    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: str = "fa",  # Persian by default
        model: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format (wav, mp3, m4a, etc.)
            language: Language code (fa, en, ar, ur)
            model: Specific model to use (optional)

        Returns:
            Transcription result with text and metadata
        """
        if self.provider == "whisper":
            return await self._transcribe_with_whisper(audio_data, audio_format, language, model)
        elif self.provider == "google":
            return await self._transcribe_with_google(audio_data, audio_format, language)
        elif self.provider == "gemini":
            return await self._transcribe_with_gemini(audio_data, audio_format, language, model)
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

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format
            language: Language code (e.g., 'ar', 'fa', 'en')

        Returns:
            Transcription result
        """
        try:
            from google.cloud import speech

            # Initialize Google Speech client
            client = speech.SpeechClient()

            # Map language codes to Google format (ISO-639-1 to BCP-47)
            language_map = {
                "fa": "fa-IR",  # Persian (Iran)
                "en": "en-US",  # English (US)
                "ar": "ar-SA",  # Arabic (Saudi Arabia)
                "ur": "ur-PK",  # Urdu (Pakistan)
            }
            google_language = language_map.get(language, f"{language}-IR")

            # Map audio format to Google encoding
            encoding_map = {
                "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
                "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
                "ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            }
            encoding = encoding_map.get(
                audio_format.lower(),
                speech.RecognitionConfig.AudioEncoding.MP3
            )

            # Prepare audio
            audio = speech.RecognitionAudio(content=audio_data)

            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=encoding,
                language_code=google_language,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False,
                model="default",  # or "phone_call" for phone audio
            )

            # Perform transcription
            response = client.recognize(config=config, audio=audio)

            # Extract text from results
            if not response.results:
                logger.warning("google_speech_no_results", language=google_language)
                return {
                    "text": "",
                    "language": language,
                    "provider": "google",
                    "confidence": 0.0,
                }

            # Combine all transcriptions
            text = " ".join([
                result.alternatives[0].transcript
                for result in response.results
            ])

            # Get confidence (average of all results)
            confidences = [
                result.alternatives[0].confidence
                for result in response.results
                if hasattr(result.alternatives[0], "confidence")
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.9

            logger.info(
                "google_speech_success",
                language=google_language,
                text_length=len(text),
                confidence=avg_confidence,
            )

            return {
                "text": text,
                "language": language,
                "provider": "google",
                "confidence": avg_confidence,
                "model": "default",
            }

        except ImportError:
            logger.error("google_speech_import_error")
            raise ValueError(
                "google-cloud-speech not installed. Install with: pip install google-cloud-speech"
            )
        except Exception as e:
            logger.error("google_speech_transcription_failed", error=str(e))
            raise ValueError(f"Google Speech transcription failed: {str(e)}")

    # ========================================================================
    # Gemini Audio Implementation
    # ========================================================================

    async def _transcribe_with_gemini(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str,
        model: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio using Gemini's audio understanding.

        Supports inline data (<20MB) and file upload (>20MB).

        Args:
            audio_data: Audio file bytes
            audio_format: Audio format
            language: Language code (e.g., 'fa', 'en', 'ar')
            model: Model to use (gemini-2.0-flash-exp by default)

        Returns:
            Transcription result
        """
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured")

        try:
            import google.generativeai as genai

            # Configure Gemini
            genai.configure(api_key=self.gemini_api_key)

            # Map language codes to full language names
            language_map = {
                "fa": "Persian",
                "en": "English",
                "ar": "Arabic",
                "ur": "Urdu",
                "tr": "Turkish",
                "id": "Indonesian",
                "ms": "Malay",
            }
            language_name = language_map.get(language, language)

            # Map audio format to MIME type
            mime_type_map = {
                "wav": "audio/wav",
                "mp3": "audio/mp3",
                "aiff": "audio/aiff",
                "aac": "audio/aac",
                "ogg": "audio/ogg",
                "flac": "audio/flac",
                "m4a": "audio/mp4",
                "webm": "audio/webm",
            }
            mime_type = mime_type_map.get(audio_format.lower(), "audio/wav")

            # Check file size (20MB threshold)
            size_mb = len(audio_data) / (1024 * 1024)

            # Simple transcription prompt
            prompt = f"Generate a transcript of the speech in {language_name}."

            # Use appropriate model
            model_name = model or self.gemini_asr_model

            if size_mb < 20:
                # Inline data for small files (<20MB)
                logger.info(
                    "gemini_transcribe_inline",
                    size_mb=round(size_mb, 2),
                    language=language_name,
                )

                # Create model instance
                model_instance = genai.GenerativeModel(model_name)

                # Encode audio to base64 for inline data
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")

                # Generate content with inline audio
                response = await model_instance.generate_content_async(
                    [
                        {
                            "mime_type": mime_type,
                            "data": audio_base64,
                        },
                        prompt,
                    ]
                )

            else:
                # File upload for large files (>20MB, max 9.5 hours)
                logger.info(
                    "gemini_transcribe_upload",
                    size_mb=round(size_mb, 2),
                    language=language_name,
                )

                # Upload file to Gemini
                audio_file = genai.upload_file(
                    io.BytesIO(audio_data),
                    mime_type=mime_type,
                )

                # Wait for file processing
                import time

                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)

                if audio_file.state.name == "FAILED":
                    raise ValueError("Gemini failed to process audio file")

                # Create model instance
                model_instance = genai.GenerativeModel(model_name)

                # Generate content with uploaded file
                response = await model_instance.generate_content_async([audio_file, prompt])

                # Delete uploaded file after processing
                genai.delete_file(audio_file.name)

            # Extract transcription text
            transcription_text = response.text

            logger.info(
                "gemini_transcription_success",
                language=language_name,
                text_length=len(transcription_text),
            )

            return {
                "text": transcription_text,
                "language": language,
                "provider": "gemini",
                "model": model_name,
            }

        except ImportError:
            logger.error("gemini_import_error")
            raise ValueError(
                "google-generativeai not installed. Install with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error("gemini_transcription_failed", error=str(e))
            raise ValueError(f"Gemini transcription failed: {str(e)}")

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
            {"code": "fa", "name": "Persian", "native_name": "فارسی"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "ar", "name": "Arabic", "native_name": "العربية"},
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

    # ========================================================================
    # Health Check
    # ========================================================================

    def health_check(self) -> dict:
        """
        Check ASR service health and configuration.

        Returns:
            Health status with provider information
        """
        try:
            # Check provider-specific dependencies
            if self.provider == "whisper":
                if not self.openai_client:
                    return {
                        "healthy": False,
                        "provider": "whisper",
                        "error": "OpenAI API key not configured",
                    }
                return {
                    "healthy": True,
                    "provider": "whisper",
                    "model": "whisper-1",
                }

            elif self.provider == "google":
                try:
                    from google.cloud import speech  # noqa: F401

                    return {
                        "healthy": True,
                        "provider": "google",
                        "credentials": "configured" if self.google_credentials else "not_configured",
                    }
                except ImportError:
                    return {
                        "healthy": False,
                        "provider": "google",
                        "error": "google-cloud-speech not installed",
                    }

            elif self.provider == "gemini":
                if not self.gemini_api_key:
                    return {
                        "healthy": False,
                        "provider": "gemini",
                        "error": "Gemini API key not configured",
                    }
                try:
                    import google.generativeai  # noqa: F401

                    return {
                        "healthy": True,
                        "provider": "gemini",
                        "model": self.gemini_asr_model,
                    }
                except ImportError:
                    return {
                        "healthy": False,
                        "provider": "gemini",
                        "error": "google-generativeai not installed",
                    }

            else:
                return {
                    "healthy": False,
                    "provider": self.provider,
                    "error": f"Unknown provider: {self.provider}",
                }

        except Exception as e:
            logger.error("asr_health_check_failed", error=str(e))
            return {
                "healthy": False,
                "provider": self.provider,
                "error": str(e),
            }


# Global ASR service instance
asr_service = ASRService()
