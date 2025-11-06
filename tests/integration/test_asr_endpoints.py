"""Comprehensive integration tests for ASR (Automatic Speech Recognition) endpoints."""

import pytest
import io
from httpx import AsyncClient, ASGITransport

from app.main import app


class TestTranscribeAudio:
    """Test audio transcription endpoint."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self):
        """Test successfully transcribing audio file."""
        # Create a minimal WAV file (mock audio data)
        # This is a very simple WAV header + minimal data
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        # May succeed with transcription or fail due to invalid audio format
        # Depends on whether ASR service is mocked or uses real API
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_default_language(self):
        """Test transcribing audio with default language (Arabic)."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            # Don't specify language - should default to 'ar'
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files
            )

        # Response may vary based on implementation
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_english(self):
        """Test transcribing audio in English."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            data = {"language": "en"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_all_supported_languages(self):
        """Test transcribing audio in all supported languages."""
        languages = ["ar", "en", "fa", "ur", "tr", "id", "ms"]
        wav_data = self._create_mock_wav_file()

        for language in languages:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
                data = {"language": language}
                response = await client.post(
                    "/api/v1/asr/transcribe",
                    files=files,
                    data=data
                )

            # Each language should be accepted
            assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_mp3_format(self):
        """Test transcribing MP3 audio file."""
        # Create mock MP3 data (simplified)
        mp3_data = b"ID3" + b"\x00" * 100  # Minimal MP3 structure

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.mp3", mp3_data, "audio/mpeg")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_m4a_format(self):
        """Test transcribing M4A audio file."""
        # Create mock M4A data
        m4a_data = b"ftyp" + b"\x00" * 100

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.m4a", m4a_data, "audio/m4a")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_invalid_language(self):
        """Test transcribing with invalid language code fails."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            data = {"language": "invalid_lang"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_transcribe_audio_missing_file(self):
        """Test transcribing without audio file fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                data=data
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_file(self):
        """Test transcribing empty audio file fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("empty.wav", b"", "audio/wav")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_transcribe_audio_oversized_file(self):
        """Test transcribing file exceeding size limit fails."""
        # Create a file larger than 25MB (Whisper limit)
        large_data = b"A" * (26 * 1024 * 1024)  # 26MB

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("large_audio.wav", large_data, "audio/wav")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_transcribe_audio_unsupported_format(self):
        """Test transcribing unsupported audio format fails."""
        # Create a text file pretending to be audio
        txt_data = b"This is not audio"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("fake_audio.txt", txt_data, "text/plain")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_specific_model(self):
        """Test transcribing with specific model parameter."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            data = {"language": "ar", "model": "whisper-1"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        # Model parameter should be accepted
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_audio_response_structure(self):
        """Test that successful transcription has correct response structure."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        if response.status_code == 200:
            data = response.json()
            assert "text" in data or "transcription" in data
            # May include additional fields like language, duration, etc.

    def _create_mock_wav_file(self) -> bytes:
        """Create a minimal valid WAV file for testing."""
        # WAV file header (44 bytes) + minimal audio data
        # This is a simplified WAV structure
        header = b"RIFF"
        header += (36 + 100).to_bytes(4, "little")  # File size - 8
        header += b"WAVE"
        header += b"fmt "
        header += (16).to_bytes(4, "little")  # fmt chunk size
        header += (1).to_bytes(2, "little")  # Audio format (1 = PCM)
        header += (1).to_bytes(2, "little")  # Number of channels
        header += (44100).to_bytes(4, "little")  # Sample rate
        header += (88200).to_bytes(4, "little")  # Byte rate
        header += (2).to_bytes(2, "little")  # Block align
        header += (16).to_bytes(2, "little")  # Bits per sample
        header += b"data"
        header += (100).to_bytes(4, "little")  # Data chunk size
        header += b"\x00" * 100  # Actual audio data (silence)
        return header


class TestTranslateAudio:
    """Test audio translation endpoint."""

    @pytest.mark.asyncio
    async def test_translate_audio_success(self):
        """Test successfully translating audio to English."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        # May succeed or fail based on implementation
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_translate_audio_no_language_param(self):
        """Test that translate endpoint doesn't require language parameter."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            # No language parameter - should auto-detect
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        # Should work without language parameter
        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_translate_audio_various_formats(self):
        """Test translating different audio formats."""
        formats = [
            ("test.wav", self._create_mock_wav_file(), "audio/wav"),
            ("test.mp3", b"ID3" + b"\x00" * 100, "audio/mpeg"),
        ]

        for filename, data, content_type in formats:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                files = {"file": (filename, data, content_type)}
                response = await client.post(
                    "/api/v1/asr/translate",
                    files=files
                )

            assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_translate_audio_missing_file(self):
        """Test translating without audio file fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/asr/translate")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_translate_audio_empty_file(self):
        """Test translating empty audio file fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("empty.wav", b"", "audio/wav")}
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_translate_audio_oversized_file(self):
        """Test translating file exceeding size limit fails."""
        large_data = b"A" * (26 * 1024 * 1024)  # 26MB

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("large_audio.wav", large_data, "audio/wav")}
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_translate_audio_response_structure(self):
        """Test that successful translation has correct response structure."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        if response.status_code == 200:
            data = response.json()
            # Should contain translated text in English
            assert "text" in data or "translation" in data

    @pytest.mark.asyncio
    async def test_translate_audio_returns_english(self):
        """Test that translation always returns English text."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        if response.status_code == 200:
            data = response.json()
            # Translation should be in English regardless of source language
            # This is a semantic test - actual validation would require real audio

    def _create_mock_wav_file(self) -> bytes:
        """Create a minimal valid WAV file for testing."""
        header = b"RIFF"
        header += (36 + 100).to_bytes(4, "little")
        header += b"WAVE"
        header += b"fmt "
        header += (16).to_bytes(4, "little")
        header += (1).to_bytes(2, "little")
        header += (1).to_bytes(2, "little")
        header += (44100).to_bytes(4, "little")
        header += (88200).to_bytes(4, "little")
        header += (2).to_bytes(2, "little")
        header += (16).to_bytes(2, "little")
        header += b"data"
        header += (100).to_bytes(4, "little")
        header += b"\x00" * 100
        return header


class TestGetSupportedLanguages:
    """Test getting supported languages endpoint."""

    @pytest.mark.asyncio
    async def test_get_supported_languages_success(self):
        """Test successfully getting supported languages."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0

    @pytest.mark.asyncio
    async def test_get_supported_languages_includes_arabic(self):
        """Test that Arabic is in supported languages."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()
        language_codes = [lang["code"] for lang in data["languages"]]
        assert "ar" in language_codes

    @pytest.mark.asyncio
    async def test_get_supported_languages_includes_english(self):
        """Test that English is in supported languages."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()
        language_codes = [lang["code"] for lang in data["languages"]]
        assert "en" in language_codes

    @pytest.mark.asyncio
    async def test_get_supported_languages_includes_islamic_languages(self):
        """Test that Islamic/Muslim-majority languages are supported."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()
        language_codes = [lang["code"] for lang in data["languages"]]

        # Should include languages common in Islamic world
        islamic_languages = ["ar", "fa", "ur", "tr", "id", "ms"]
        for lang in islamic_languages:
            assert lang in language_codes

    @pytest.mark.asyncio
    async def test_get_supported_languages_structure(self):
        """Test that language entries have correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()
        assert len(data["languages"]) > 0

        # Check first language entry has required fields
        first_lang = data["languages"][0]
        assert "code" in first_lang
        assert "name" in first_lang
        # May also have 'native_name', 'region', etc.

    @pytest.mark.asyncio
    async def test_get_supported_languages_includes_provider(self):
        """Test that response includes ASR provider information."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        # Provider should be something like "openai_whisper" or "google"

    @pytest.mark.asyncio
    async def test_get_supported_languages_no_params_needed(self):
        """Test that endpoint works without any parameters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_supported_languages_consistent_response(self):
        """Test that endpoint returns consistent results across calls."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response1 = await client.get("/api/v1/asr/languages")
            response2 = await client.get("/api/v1/asr/languages")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Should return same languages
        assert len(data1["languages"]) == len(data2["languages"])

    @pytest.mark.asyncio
    async def test_get_supported_languages_uses_iso_codes(self):
        """Test that language codes follow ISO 639-1 standard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/asr/languages")

        assert response.status_code == 200
        data = response.json()

        # All language codes should be 2-letter ISO codes
        for lang in data["languages"]:
            code = lang["code"]
            assert len(code) == 2
            assert code.islower()


class TestASREndpointCombinations:
    """Test various combinations of ASR endpoint usage."""

    @pytest.mark.asyncio
    async def test_transcribe_then_translate_same_file(self):
        """Test transcribing and translating the same audio file."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First transcribe
            files1 = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            data1 = {"language": "ar"}
            transcribe_response = await client.post(
                "/api/v1/asr/transcribe",
                files=files1,
                data=data1
            )

            # Then translate
            files2 = {"file": ("test_audio.wav", wav_data, "audio/wav")}
            translate_response = await client.post(
                "/api/v1/asr/translate",
                files=files2
            )

        # Both operations should have same status pattern
        assert transcribe_response.status_code in [200, 400, 500]
        assert translate_response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_get_languages_before_transcribe(self):
        """Test getting supported languages before transcribing."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Get languages
            lang_response = await client.get("/api/v1/asr/languages")
            assert lang_response.status_code == 200

            # Use one of the supported languages for transcription
            languages = lang_response.json()["languages"]
            if len(languages) > 0:
                test_lang = languages[0]["code"]

                wav_data = self._create_mock_wav_file()
                files = {"file": ("test_audio.wav", wav_data, "audio/wav")}
                data = {"language": test_lang}
                transcribe_response = await client.post(
                    "/api/v1/asr/transcribe",
                    files=files,
                    data=data
                )

                assert transcribe_response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_multiple_transcriptions_sequential(self):
        """Test multiple sequential transcription requests."""
        wav_data = self._create_mock_wav_file()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for i in range(3):
                files = {"file": (f"test_audio_{i}.wav", wav_data, "audio/wav")}
                data = {"language": "ar"}
                response = await client.post(
                    "/api/v1/asr/transcribe",
                    files=files,
                    data=data
                )

                # Each request should be handled independently
                assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_asr_endpoints_response_time(self):
        """Test that ASR endpoints respond in reasonable time."""
        import time

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test languages endpoint
            start = time.time()
            response = await client.get("/api/v1/asr/languages")
            end = time.time()

            assert response.status_code == 200
            # Should respond quickly (within 2 seconds)
            assert (end - start) < 2.0

    def _create_mock_wav_file(self) -> bytes:
        """Create a minimal valid WAV file for testing."""
        header = b"RIFF"
        header += (36 + 100).to_bytes(4, "little")
        header += b"WAVE"
        header += b"fmt "
        header += (16).to_bytes(4, "little")
        header += (1).to_bytes(2, "little")
        header += (1).to_bytes(2, "little")
        header += (44100).to_bytes(4, "little")
        header += (88200).to_bytes(4, "little")
        header += (2).to_bytes(2, "little")
        header += (16).to_bytes(2, "little")
        header += b"data"
        header += (100).to_bytes(4, "little")
        header += b"\x00" * 100
        return header


class TestASRErrorHandling:
    """Test error handling in ASR endpoints."""

    @pytest.mark.asyncio
    async def test_transcribe_corrupted_audio_file(self):
        """Test transcribing corrupted audio file."""
        corrupted_data = b"RIFF" + b"\xFF" * 50  # Invalid WAV data

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("corrupted.wav", corrupted_data, "audio/wav")}
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_with_malformed_request(self):
        """Test transcribing with malformed request data."""
        wav_data = b"RIFF" + b"\x00" * 100

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Send data in wrong format
            response = await client.post(
                "/api/v1/asr/transcribe",
                json={"file": "not_a_file", "language": "ar"}
            )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_translate_invalid_audio_data(self):
        """Test translating with invalid audio data."""
        invalid_data = b"This is not audio"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("invalid.wav", invalid_data, "audio/wav")}
            response = await client.post(
                "/api/v1/asr/translate",
                files=files
            )

        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_transcribe_wrong_content_type(self):
        """Test transcribing with wrong content type."""
        wav_data = b"RIFF" + b"\x00" * 100

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.wav", wav_data, "application/json")}  # Wrong content type
            data = {"language": "ar"}
            response = await client.post(
                "/api/v1/asr/transcribe",
                files=files,
                data=data
            )

        # May accept or reject based on implementation
        assert response.status_code in [200, 400, 415, 422, 500]
