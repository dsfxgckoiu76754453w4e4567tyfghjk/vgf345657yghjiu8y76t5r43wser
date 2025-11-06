"""API endpoints for speech-to-text (ASR)."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.logging import get_logger
from app.schemas.external_api import (
    SupportedLanguage,
    SupportedLanguagesResponse,
    TranscribeAudioResponse,
)
from app.services.asr_service import ASRService

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Audio Transcription
# ============================================================================


@router.post(
    "/transcribe",
    response_model=TranscribeAudioResponse,
    summary="Transcribe Audio to Text",
    description="""
    Transcribe audio files to text using ASR (Automatic Speech Recognition).

    **Supported Providers:**
    - OpenAI Whisper (default) - Highly accurate, multi-language
    - Google Speech-to-Text - Enterprise-grade (placeholder)

    **Supported Languages:**
    - Arabic (ar) - Default
    - English (en)
    - Persian/Farsi (fa)
    - Urdu (ur)
    - Turkish (tr)
    - Indonesian (id)
    - Malay (ms)

    **Supported Formats:**
    - WAV, MP3, M4A, FLAC, OGG, WEBM

    **File Size Limit:**
    - Maximum: 25 MB (Whisper limit)

    **Use Cases:**
    - Voice questions to the chatbot
    - Audio document transcription
    - Lecture/sermon transcription
    - Accessibility features
    """,
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form(default="ar", description="Language code"),
    model: str = Form(default=None, description="Specific model (optional)"),
) -> TranscribeAudioResponse:
    """
    Transcribe audio file to text.

    Args:
        file: Audio file
        language: Language code
        model: Specific model to use

    Returns:
        Transcription result
    """
    try:
        # Read audio data
        audio_data = await file.read()

        # Get file extension
        filename = file.filename or "audio.wav"
        audio_format = filename.split(".")[-1].lower()

        # Validate audio
        asr_service = ASRService()
        validation = asr_service.validate_audio(audio_data)

        if not validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["error"],
            )

        # Transcribe
        result = await asr_service.transcribe_audio(
            audio_data=audio_data,
            audio_format=audio_format,
            language=language,
            model=model,
        )

        logger.info(
            "audio_transcribed",
            language=language,
            format=audio_format,
            size_mb=validation["size_mb"],
        )

        return TranscribeAudioResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error("transcription_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("transcription_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio",
        )


# ============================================================================
# Audio Translation
# ============================================================================


@router.post(
    "/translate",
    response_model=TranscribeAudioResponse,
    summary="Translate Audio to English",
    description="""
    Transcribe and translate audio to English (regardless of source language).

    **CRITICAL**: This endpoint automatically detects the source language
    and translates the audio content to English.

    **Differences from /transcribe:**
    - /transcribe: Returns text in the same language as the audio
    - /translate: Returns text translated to English

    **Example:**
    - Input: Arabic audio saying "السلام عليكم"
    - Output: English text "Peace be upon you"

    **Use Cases:**
    - Multi-language support
    - Translation of Islamic lectures
    - Cross-language communication
    - Content localization

    **Provider:**
    - OpenAI Whisper only (Google Speech-to-Text doesn't support translation)
    """,
)
async def translate_audio(
    file: UploadFile = File(..., description="Audio file to translate"),
) -> TranscribeAudioResponse:
    """
    Transcribe and translate audio to English.

    Args:
        file: Audio file

    Returns:
        Translated transcription in English
    """
    try:
        # Read audio data
        audio_data = await file.read()

        # Get file extension
        filename = file.filename or "audio.wav"
        audio_format = filename.split(".")[-1].lower()

        # Validate audio
        asr_service = ASRService()
        validation = asr_service.validate_audio(audio_data)

        if not validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["error"],
            )

        # Translate to English
        result = await asr_service.translate_audio_to_english(
            audio_data=audio_data,
            audio_format=audio_format,
        )

        logger.info(
            "audio_translated",
            format=audio_format,
            size_mb=validation["size_mb"],
        )

        return TranscribeAudioResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error("translation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("translation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to translate audio",
        )


# ============================================================================
# Language Support
# ============================================================================


@router.get(
    "/languages",
    response_model=SupportedLanguagesResponse,
    summary="Get Supported Languages",
    description="""
    Get list of languages supported for speech-to-text.

    Languages are prioritized for Islamic content:
    - Arabic (ar) - Primary language
    - English (en) - International
    - Persian/Farsi (fa) - Iran, Afghanistan
    - Urdu (ur) - Pakistan, India
    - Turkish (tr) - Turkey
    - Indonesian (id) - Indonesia
    - Malay (ms) - Malaysia, Brunei

    All languages use ISO 639-1 codes.
    """,
)
async def get_supported_languages() -> SupportedLanguagesResponse:
    """
    Get supported languages.

    Returns:
        List of supported languages
    """
    try:
        asr_service = ASRService()
        languages = asr_service.get_supported_languages()

        return SupportedLanguagesResponse(
            languages=[SupportedLanguage(**lang) for lang in languages],
            provider=asr_service.provider,
        )

    except Exception as e:
        logger.error("get_supported_languages_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported languages",
        )
