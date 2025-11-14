# ADR-005: Gemini Audio for ASR Transcription

**Status**: Accepted
**Date**: 2025-01-14
**Impact**: Medium

---

## Problem
Need a high-quality, simple audio transcription service that supports multiple languages (Persian, Arabic, English) with good accuracy for voice-to-text conversion in the chatbot interface.

---

## Decision
Add **Gemini** as a third ASR provider alongside Whisper and Google Speech-to-Text, using Gemini's native audio understanding capabilities.

**Implementation:**
- Support inline data for files <20MB (base64 encoding)
- Support file upload API for files >20MB (max 9.5 hours)
- Simple transcription prompt: "Generate a transcript of the speech in {language}."
- Focus on basic transcription flow: voice → text → display → edit → send

**Supported Formats:**
- WAV, MP3, AIFF, AAC, OGG, FLAC, M4A, WebM (8 formats)

---

## Why
- **Multimodal Native**: Gemini natively understands audio (not speech-to-text API wrapper)
- **Large Files**: Supports up to 9.5 hours of audio (vs 25MB Whisper limit)
- **High Quality**: Advanced audio understanding from Google's latest model
- **Simple Integration**: Same API as text generation with audio input
- **Cost Effective**: Competitive pricing with prompt caching support
- **Multi-Language**: Excellent support for Persian, Arabic, English, Urdu
- **No Preprocessing**: No need for audio format conversion
- **Already Available**: Gemini API already integrated for LLM services

---

## Alternatives Rejected
- **Keep Whisper Only**: Limited to 25MB files, separate API integration
- **Keep Google Speech Only**: Requires credentials setup, less flexible
- **OpenAI Whisper API**: Good but file size limits restrictive
- **Custom ASR Model**: High complexity, requires training/maintenance

---

## Impact

**Changed Components:**
- `src/app/services/asr_service.py` - Added `_transcribe_with_gemini()` method
- `src/app/core/config.py` - Added `gemini` to `asr_provider`, added `gemini_model` field
- `src/app/api/v1/asr.py` - Updated documentation for Gemini support
- `.env.example` - Added `GEMINI_MODEL` configuration

**Dependencies:**
- Already have: `google-generativeai>=0.8.0` (installed for LLM services)

**Breaking Changes:** No (backward compatible, opt-in via config)

**Migration Required:** No
- Existing deployments continue using current provider (Whisper/Google)
- To use Gemini: Set `ASR_PROVIDER=gemini` in environment variables

---

## Notes
- **File Size Handling:**
  - <20MB: Inline data (base64 encoding)
  - >20MB: File upload API with processing wait time
- **Transcription Flow:** User speaks → Audio captured → Gemini transcribes → Text displayed in text box → User can edit → Send message
- **Language Mapping:** ISO codes (fa, en, ar) mapped to full names (Persian, English, Arabic)
- **Model Default:** `gemini-2.0-flash-exp` (fast, cost-effective)
- **Token Cost:** ~32 tokens per second of audio
- **Use Case:** Primary use is simple voice input for chatbot, not complex audio analysis
- **Future Enhancements:** Can add timestamp queries, audio Q&A, translation if needed
- **Configuration:** Uses existing `GEMINI_API_KEY` from LLM services
