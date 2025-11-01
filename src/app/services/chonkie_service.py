"""Chonkie chunking service for intelligent text segmentation."""

from typing import Literal, Optional

from chonkie import SemanticChunker, SentenceChunker, TokenChunker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChonkieService:
    """
    Service for intelligent text chunking using Chonkie library.

    CRITICAL: Use Chonkie for chunking, NOT traditional LangChain text splitters.
    Chonkie provides semantic-aware, intelligent chunking optimized for RAG.
    """

    def __init__(self):
        """Initialize Chonkie service."""
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.default_strategy = settings.chunking_strategy

    def chunk_text(
        self,
        text: str,
        strategy: Optional[
            Literal["semantic", "token", "sentence", "adaptive"]
        ] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        language: str = "fa",
    ) -> list[dict[str, any]]:
        """
        Chunk text using specified strategy.

        Args:
            text: Text to chunk
            strategy: Chunking strategy (semantic, token, sentence, adaptive)
            chunk_size: Target chunk size
            overlap: Chunk overlap size
            language: Text language (fa, ar, en, ur)

        Returns:
            List of chunks with metadata
        """
        strategy = strategy or self.default_strategy
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap

        logger.info(
            "chonkie_chunking_started",
            strategy=strategy,
            chunk_size=chunk_size,
            language=language,
            text_length=len(text),
        )

        try:
            chunks = []

            if strategy == "semantic":
                chunks = self._semantic_chunk(text, chunk_size, overlap, language)
            elif strategy == "token":
                chunks = self._token_chunk(text, chunk_size, overlap)
            elif strategy == "sentence":
                chunks = self._sentence_chunk(text, chunk_size, overlap, language)
            elif strategy == "adaptive":
                # Adaptive: Use semantic for long texts, sentence for shorter ones
                if len(text) > 5000:
                    chunks = self._semantic_chunk(text, chunk_size, overlap, language)
                else:
                    chunks = self._sentence_chunk(text, chunk_size, overlap, language)
            else:
                raise ValueError(f"Unknown chunking strategy: {strategy}")

            logger.info(
                "chonkie_chunking_completed",
                strategy=strategy,
                chunks_count=len(chunks),
            )

            return chunks

        except Exception as e:
            logger.error(
                "chonkie_chunking_failed",
                strategy=strategy,
                error=str(e),
            )
            raise

    def _semantic_chunk(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        language: str,
    ) -> list[dict[str, any]]:
        """
        Semantic chunking - preserves meaning and context.

        Best for: Books, articles, long-form content
        """
        try:
            chunker = SemanticChunker(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                # Chonkie automatically detects language, but we can hint
                min_chunk_size=100,  # Minimum chunk size to avoid tiny chunks
            )

            raw_chunks = chunker.chunk(text)

            # Convert to our format
            chunks = []
            for idx, chunk_text in enumerate(raw_chunks):
                chunks.append(
                    {
                        "text": chunk_text,
                        "index": idx,
                        "method": "semantic",
                        "char_count": len(chunk_text),
                        "word_count": len(chunk_text.split()),
                        "metadata": {
                            "language": language,
                            "chunker": "chonkie_semantic",
                        },
                    }
                )

            return chunks

        except Exception as e:
            logger.error("semantic_chunking_failed", error=str(e))
            raise

    def _token_chunk(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> list[dict[str, any]]:
        """
        Token-based chunking - splits by token count.

        Best for: Precise token control, API limits
        """
        try:
            chunker = TokenChunker(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
            )

            raw_chunks = chunker.chunk(text)

            chunks = []
            for idx, chunk_text in enumerate(raw_chunks):
                chunks.append(
                    {
                        "text": chunk_text,
                        "index": idx,
                        "method": "token",
                        "char_count": len(chunk_text),
                        "word_count": len(chunk_text.split()),
                        "metadata": {
                            "chunker": "chonkie_token",
                        },
                    }
                )

            return chunks

        except Exception as e:
            logger.error("token_chunking_failed", error=str(e))
            raise

    def _sentence_chunk(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        language: str,
    ) -> list[dict[str, any]]:
        """
        Sentence-based chunking - preserves sentence boundaries.

        Best for: Short documents, maintaining readability
        """
        try:
            chunker = SentenceChunker(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
            )

            raw_chunks = chunker.chunk(text)

            chunks = []
            for idx, chunk_text in enumerate(raw_chunks):
                chunks.append(
                    {
                        "text": chunk_text,
                        "index": idx,
                        "method": "sentence",
                        "char_count": len(chunk_text),
                        "word_count": len(chunk_text.split()),
                        "metadata": {
                            "language": language,
                            "chunker": "chonkie_sentence",
                        },
                    }
                )

            return chunks

        except Exception as e:
            logger.error("sentence_chunking_failed", error=str(e))
            raise

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for a text.

        Approximate: 1 token ≈ 4 characters for English
        For Persian/Arabic: 1 token ≈ 2-3 characters (conservative)

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Conservative estimate for Persian/Arabic
        return len(text) // 2


# Global Chonkie service instance
chonkie_service = ChonkieService()
