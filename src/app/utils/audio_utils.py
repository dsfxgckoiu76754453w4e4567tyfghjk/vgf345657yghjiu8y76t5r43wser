"""Audio processing utilities for metadata extraction and validation.

Provides utilities for extracting metadata from audio files including:
- Duration
- Format/codec
- Bitrate
- Sample rate
- Quality estimation
- File validation
"""

import io
import mimetypes
from pathlib import Path
from typing import BinaryIO, Literal, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_audio_duration(audio_data: bytes | BinaryIO, audio_format: str = "mp3") -> Optional[float]:
    """
    Extract audio duration in seconds.

    Args:
        audio_data: Audio file data (bytes or file-like object)
        audio_format: Audio format (mp3, wav, ogg, flac, etc.)

    Returns:
        Duration in seconds, or None if extraction fails
    """
    try:
        # Try using mutagen for accurate duration
        try:
            from mutagen import File as MutagenFile

            # Convert to file-like object if needed
            if isinstance(audio_data, bytes):
                audio_file = io.BytesIO(audio_data)
            else:
                audio_file = audio_data

            # Add fake filename for mutagen
            audio_file.name = f"audio.{audio_format}"

            # Extract metadata
            audio = MutagenFile(audio_file)
            if audio and audio.info:
                duration = audio.info.length
                logger.debug(
                    "audio_duration_extracted",
                    format=audio_format,
                    duration=duration,
                )
                return duration

        except ImportError:
            logger.warning("mutagen_not_installed", message="Install mutagen for accurate audio metadata")

        # Fallback: Estimate based on file size (rough approximation)
        if isinstance(audio_data, bytes):
            file_size = len(audio_data)
        else:
            audio_data.seek(0, 2)  # Seek to end
            file_size = audio_data.tell()
            audio_data.seek(0)  # Seek back to start

        # Rough estimation (assumes 128 kbps bitrate)
        estimated_duration = (file_size * 8) / (128 * 1024)  # Convert to seconds

        logger.debug(
            "audio_duration_estimated",
            format=audio_format,
            file_size=file_size,
            estimated_duration=estimated_duration,
        )

        return estimated_duration

    except Exception as e:
        logger.error("audio_duration_extraction_failed", error=str(e))
        return None


def extract_audio_metadata(audio_data: bytes | BinaryIO, audio_format: str = "mp3") -> dict:
    """
    Extract comprehensive audio metadata.

    Args:
        audio_data: Audio file data (bytes or file-like object)
        audio_format: Audio format (mp3, wav, ogg, flac, etc.)

    Returns:
        Dictionary with metadata:
        {
            "duration_seconds": float,
            "format": str,
            "bitrate": int (in kbps),
            "sample_rate": int (in Hz),
            "channels": int,
            "quality": str (low, medium, high, hd),
            "codec": str,
        }
    """
    metadata = {
        "duration_seconds": None,
        "format": audio_format,
        "bitrate": None,
        "sample_rate": None,
        "channels": None,
        "quality": "medium",  # Default
        "codec": None,
    }

    try:
        from mutagen import File as MutagenFile

        # Convert to file-like object if needed
        if isinstance(audio_data, bytes):
            audio_file = io.BytesIO(audio_data)
        else:
            audio_file = audio_data

        # Add fake filename for mutagen
        audio_file.name = f"audio.{audio_format}"

        # Extract metadata
        audio = MutagenFile(audio_file)

        if audio and audio.info:
            # Duration
            metadata["duration_seconds"] = audio.info.length

            # Bitrate (in kbps)
            if hasattr(audio.info, "bitrate"):
                metadata["bitrate"] = int(audio.info.bitrate / 1000)  # Convert to kbps

            # Sample rate
            if hasattr(audio.info, "sample_rate"):
                metadata["sample_rate"] = audio.info.sample_rate

            # Channels
            if hasattr(audio.info, "channels"):
                metadata["channels"] = audio.info.channels

            # Codec
            if hasattr(audio.info, "codec"):
                metadata["codec"] = audio.info.codec
            elif audio_format == "mp3":
                metadata["codec"] = "mp3"
            elif audio_format in ["ogg", "opus"]:
                metadata["codec"] = "opus"

            # Determine quality based on bitrate
            if metadata["bitrate"]:
                if metadata["bitrate"] < 96:
                    metadata["quality"] = "low"
                elif metadata["bitrate"] < 192:
                    metadata["quality"] = "medium"
                elif metadata["bitrate"] < 320:
                    metadata["quality"] = "high"
                else:
                    metadata["quality"] = "hd"

            logger.info(
                "audio_metadata_extracted",
                format=audio_format,
                duration=metadata["duration_seconds"],
                bitrate=metadata["bitrate"],
                quality=metadata["quality"],
            )

    except ImportError:
        logger.warning(
            "mutagen_not_available",
            message="Install mutagen for audio metadata: pip install mutagen"
        )
        # Fallback to basic duration extraction
        metadata["duration_seconds"] = get_audio_duration(audio_data, audio_format)

    except Exception as e:
        logger.error("audio_metadata_extraction_failed", error=str(e))

    return metadata


def validate_audio_file(
    audio_data: bytes | BinaryIO,
    max_size_mb: int = 25,
    allowed_formats: Optional[list[str]] = None,
    min_duration_seconds: Optional[float] = None,
    max_duration_seconds: Optional[float] = None,
) -> dict:
    """
    Validate audio file against constraints.

    Args:
        audio_data: Audio file data
        max_size_mb: Maximum file size in MB
        allowed_formats: List of allowed audio formats (e.g., ['mp3', 'wav', 'ogg'])
        min_duration_seconds: Minimum audio duration
        max_duration_seconds: Maximum audio duration

    Returns:
        Validation result:
        {
            "is_valid": bool,
            "size_mb": float,
            "duration_seconds": float | None,
            "format": str,
            "errors": list[str],
        }
    """
    if allowed_formats is None:
        allowed_formats = ["mp3", "wav", "ogg", "opus", "flac", "m4a", "webm"]

    errors = []

    # Check file size
    if isinstance(audio_data, bytes):
        file_size = len(audio_data)
    else:
        audio_data.seek(0, 2)  # Seek to end
        file_size = audio_data.tell()
        audio_data.seek(0)  # Seek back to start

    size_mb = file_size / (1024 * 1024)

    if size_mb > max_size_mb:
        errors.append(f"File too large: {size_mb:.2f}MB (max {max_size_mb}MB)")

    # Try to detect format from content
    audio_format = "unknown"
    try:
        if isinstance(audio_data, bytes):
            # Check magic bytes for common formats
            if audio_data.startswith(b"ID3") or audio_data.startswith(b"\xFF\xFB"):
                audio_format = "mp3"
            elif audio_data.startswith(b"RIFF"):
                audio_format = "wav"
            elif audio_data.startswith(b"OggS"):
                audio_format = "ogg"
            elif audio_data.startswith(b"fLaC"):
                audio_format = "flac"
    except Exception:
        pass

    # Check if format is allowed
    if audio_format not in allowed_formats and audio_format != "unknown":
        errors.append(f"Format not allowed: {audio_format} (allowed: {', '.join(allowed_formats)})")

    # Check duration if constraints provided
    duration = None
    if min_duration_seconds or max_duration_seconds:
        duration = get_audio_duration(audio_data, audio_format)

        if duration:
            if min_duration_seconds and duration < min_duration_seconds:
                errors.append(
                    f"Audio too short: {duration:.1f}s (min {min_duration_seconds}s)"
                )
            if max_duration_seconds and duration > max_duration_seconds:
                errors.append(
                    f"Audio too long: {duration:.1f}s (max {max_duration_seconds}s)"
                )

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "size_mb": round(size_mb, 2),
        "duration_seconds": duration,
        "format": audio_format,
        "errors": errors,
    }


def get_audio_mime_type(file_extension: str) -> str:
    """
    Get MIME type for audio file extension.

    Args:
        file_extension: File extension (e.g., 'mp3', 'wav', 'ogg')

    Returns:
        MIME type string
    """
    # Common audio MIME types
    mime_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "opus": "audio/opus",
        "flac": "audio/flac",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "webm": "audio/webm",
        "weba": "audio/webm",
    }

    # Try custom map first
    ext = file_extension.lower().lstrip(".")
    if ext in mime_map:
        return mime_map[ext]

    # Fallback to mimetypes module
    mime_type, _ = mimetypes.guess_type(f"file.{ext}")
    return mime_type or "audio/mpeg"  # Default to MP3


def estimate_audio_quality(
    bitrate_kbps: Optional[int] = None,
    sample_rate_hz: Optional[int] = None,
) -> Literal["low", "medium", "high", "hd"]:
    """
    Estimate audio quality based on bitrate and sample rate.

    Args:
        bitrate_kbps: Bitrate in kbps
        sample_rate_hz: Sample rate in Hz

    Returns:
        Quality level: low, medium, high, or hd
    """
    if bitrate_kbps is None and sample_rate_hz is None:
        return "medium"

    # Primarily use bitrate
    if bitrate_kbps:
        if bitrate_kbps < 96:
            return "low"
        elif bitrate_kbps < 192:
            return "medium"
        elif bitrate_kbps < 320:
            return "high"
        else:
            return "hd"

    # Fallback to sample rate
    if sample_rate_hz:
        if sample_rate_hz < 32000:
            return "low"
        elif sample_rate_hz < 44100:
            return "medium"
        elif sample_rate_hz < 96000:
            return "high"
        else:
            return "hd"

    return "medium"
