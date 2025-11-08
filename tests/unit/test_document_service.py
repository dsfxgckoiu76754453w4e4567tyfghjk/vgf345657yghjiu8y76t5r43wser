"""Unit tests for document service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.services.document_service import DocumentService


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def document_service(mock_db):
    """Create document service instance."""
    return DocumentService(db=mock_db)


@pytest.fixture
def sample_document_id():
    """Sample document ID."""
    return uuid4()


@pytest.fixture
def sample_chunk_id():
    """Sample chunk ID."""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return uuid4()


# ============================================================================
# Test: Document Service Initialization
# ============================================================================


class TestDocumentServiceInitialization:
    """Test cases for DocumentService initialization."""

    def test_initialization(self, mock_db):
        """Test that service initializes with database session."""
        service = DocumentService(db=mock_db)
        assert service.db == mock_db


# ============================================================================
# Test: Create Document
# ============================================================================


class TestDocumentServiceCreateDocument:
    """Test cases for document creation."""

    @pytest.mark.asyncio
    @patch("app.services.document_service.chonkie_service")
    async def test_create_document_success(
        self,
        mock_chonkie_service,
        document_service,
        mock_db,
        sample_user_id,
    ):
        """Test creating a document successfully."""
        # Mock chonkie service
        mock_chunks = [
            {
                "text": "Chunk 1 text content",
                "index": 0,
                "char_count": 20,
                "word_count": 3,
                "method": "semantic",
                "metadata": {},
            },
            {
                "text": "Chunk 2 text content",
                "index": 1,
                "char_count": 20,
                "word_count": 3,
                "method": "semantic",
                "metadata": {},
            },
        ]
        mock_chonkie_service.chunk_text.return_value = mock_chunks
        mock_chonkie_service.estimate_token_count.side_effect = [25, 25]

        # Call create_document
        result = await document_service.create_document(
            title="Test Document",
            content="This is a test document content for testing purposes.",
            document_type="hadith",
            primary_category="aqidah",
            language="fa",
            author="Test Author",
            source_reference="Test Source",
            uploaded_by=sample_user_id,
            chunking_strategy="semantic",
            chunk_size=768,
            chunk_overlap=150,
        )

        # Verify document was created
        assert mock_db.add.call_count == 1  # Document added
        document_arg = mock_db.add.call_args_list[0][0][0]
        assert isinstance(document_arg, Document)
        assert document_arg.title == "Test Document"
        assert document_arg.document_type == "hadith"
        assert document_arg.primary_category == "aqidah"
        assert document_arg.language == "fa"
        assert document_arg.processing_status == "processing"

        # Verify chunks were created
        assert mock_db.add_all.call_count == 1
        chunk_args = mock_db.add_all.call_args[0][0]
        assert len(chunk_args) == 2
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunk_args)

        # Verify database operations
        assert mock_db.flush.call_count == 2  # After document and after chunks
        assert mock_db.commit.called
        assert mock_db.refresh.called

        # Verify chonkie was called
        mock_chonkie_service.chunk_text.assert_called_once_with(
            text="This is a test document content for testing purposes.",
            strategy="semantic",
            chunk_size=768,
            overlap=150,
            language="fa",
        )

    @pytest.mark.asyncio
    @patch("app.services.document_service.chonkie_service")
    async def test_create_document_with_defaults(
        self,
        mock_chonkie_service,
        document_service,
        mock_db,
    ):
        """Test creating a document with default parameters."""
        # Mock chonkie service
        mock_chunks = [
            {
                "text": "Single chunk",
                "index": 0,
                "char_count": 12,
                "word_count": 2,
                "method": "semantic",
                "metadata": {},
            }
        ]
        mock_chonkie_service.chunk_text.return_value = mock_chunks
        mock_chonkie_service.estimate_token_count.return_value = 15

        # Call create_document with minimal params
        await document_service.create_document(
            title="Minimal Document",
            content="Minimal content.",
            document_type="article",
            primary_category="general",
        )

        # Verify defaults were used
        mock_chonkie_service.chunk_text.assert_called_once_with(
            text="Minimal content.",
            strategy="semantic",  # default
            chunk_size=768,  # default
            overlap=150,  # default
            language="fa",  # default
        )

    @pytest.mark.asyncio
    @patch("app.services.document_service.chonkie_service")
    async def test_create_document_chunking_failure(
        self,
        mock_chonkie_service,
        document_service,
        mock_db,
    ):
        """Test handling chunking failure."""
        # Mock chonkie service to raise exception
        mock_chonkie_service.chunk_text.side_effect = Exception("Chunking failed")

        # Call create_document - should raise exception
        with pytest.raises(Exception, match="Chunking failed"):
            await document_service.create_document(
                title="Failing Document",
                content="Content that will fail to chunk.",
                document_type="book",
                primary_category="fiqh",
            )

        # Verify document status was set to failed
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch("app.services.document_service.chonkie_service")
    async def test_create_document_with_all_parameters(
        self,
        mock_chonkie_service,
        document_service,
        mock_db,
        sample_user_id,
    ):
        """Test creating document with all optional parameters."""
        # Mock chonkie service
        mock_chunks = [
            {
                "text": "Test chunk",
                "index": 0,
                "char_count": 10,
                "word_count": 2,
                "method": "token",
                "metadata": {"key": "value"},
            }
        ]
        mock_chonkie_service.chunk_text.return_value = mock_chunks
        mock_chonkie_service.estimate_token_count.return_value = 12

        # Call with all parameters
        await document_service.create_document(
            title="Complete Document",
            content="Complete content.",
            document_type="tafsir",
            primary_category="tafsir",
            language="ar",
            author="Scholar Name",
            source_reference="Volume 1, Page 50",
            uploaded_by=sample_user_id,
            chunking_strategy="token",
            chunk_size=1024,
            chunk_overlap=200,
        )

        # Verify all parameters were used
        document_arg = mock_db.add.call_args_list[0][0][0]
        assert document_arg.title == "Complete Document"
        assert document_arg.language == "ar"
        assert document_arg.author == "Scholar Name"
        assert document_arg.source_reference == "Volume 1, Page 50"
        assert document_arg.chunk_size == 1024
        assert document_arg.chunk_overlap == 200


# ============================================================================
# Test: Generate Embeddings for Document
# ============================================================================


class TestDocumentServiceGenerateEmbeddings:
    """Test cases for embeddings generation."""

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_generate_embeddings_success(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
        mock_db,
        sample_document_id,
        sample_chunk_id,
    ):
        """Test generating embeddings successfully."""
        # Create mock chunks
        chunk1 = DocumentChunk(
            id=sample_chunk_id,
            document_id=sample_document_id,
            chunk_text="First chunk text",
            chunk_index=0,
            char_count=16,
            word_count=3,
            token_count_estimated=20,
            chunking_method="semantic",
        )
        chunk2 = DocumentChunk(
            id=uuid4(),
            document_id=sample_document_id,
            chunk_text="Second chunk text",
            chunk_index=1,
            char_count=17,
            word_count=3,
            token_count_estimated=21,
            chunking_method="semantic",
        )

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [chunk1, chunk2]
        mock_db.execute.return_value = mock_result

        # Mock embeddings service
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_embeddings_service.embed_documents = AsyncMock(return_value=mock_embeddings)
        mock_embeddings_service.model = "text-embedding-004"
        mock_embeddings_service.estimate_cost.side_effect = [0.0001, 0.0001]

        # Mock qdrant service
        mock_qdrant_service.add_points = AsyncMock()
        mock_qdrant_service.collection_name = "documents"

        # Call generate_embeddings
        count = await document_service.generate_embeddings_for_document(
            document_id=sample_document_id,
        )

        # Verify results
        assert count == 2

        # Verify embeddings were generated
        mock_embeddings_service.embed_documents.assert_called_once_with(
            ["First chunk text", "Second chunk text"]
        )

        # Verify points were added to Qdrant
        mock_qdrant_service.add_points.assert_called_once()
        points_arg = mock_qdrant_service.add_points.call_args[0][0]
        assert len(points_arg) == 2

        # Verify embedding records were created
        assert mock_db.add_all.called
        embedding_records = mock_db.add_all.call_args[0][0]
        assert len(embedding_records) == 2
        assert all(isinstance(rec, DocumentEmbedding) for rec in embedding_records)

        # Verify database operations
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_generate_embeddings_no_chunks(
        self,
        document_service,
        mock_db,
        sample_document_id,
    ):
        """Test generating embeddings when document has no chunks."""
        # Mock database query to return no chunks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Call generate_embeddings
        count = await document_service.generate_embeddings_for_document(
            document_id=sample_document_id,
        )

        # Verify count is 0
        assert count == 0

        # Verify no database writes occurred
        assert not mock_db.add_all.called
        assert not mock_db.commit.called

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_generate_embeddings_with_custom_collection(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
        mock_db,
        sample_document_id,
    ):
        """Test generating embeddings with custom collection name."""
        # Create mock chunk
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=sample_document_id,
            chunk_text="Test chunk",
            chunk_index=0,
            char_count=10,
            word_count=2,
            token_count_estimated=12,
            chunking_method="semantic",
        )

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [chunk]
        mock_db.execute.return_value = mock_result

        # Mock embeddings service
        mock_embeddings_service.embed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        mock_embeddings_service.model = "text-embedding-004"
        mock_embeddings_service.estimate_cost.return_value = 0.0001

        # Mock qdrant service
        mock_qdrant_service.add_points = AsyncMock()

        # Call with custom collection
        await document_service.generate_embeddings_for_document(
            document_id=sample_document_id,
            collection_name="custom_collection",
        )

        # Verify custom collection was used
        mock_qdrant_service.add_points.assert_called_once()
        collection_arg = mock_qdrant_service.add_points.call_args[0][1]
        assert collection_arg == "custom_collection"

    @pytest.mark.asyncio
    @patch("app.services.document_service.embeddings_service")
    async def test_generate_embeddings_with_multiple_chunks(
        self,
        mock_embeddings_service,
        document_service,
        mock_db,
        sample_document_id,
    ):
        """Test generating embeddings for multiple chunks."""
        # Create 5 mock chunks
        chunks = [
            DocumentChunk(
                id=uuid4(),
                document_id=sample_document_id,
                chunk_text=f"Chunk {i} text",
                chunk_index=i,
                char_count=13,
                word_count=3,
                token_count_estimated=15,
                chunking_method="semantic",
            )
            for i in range(5)
        ]

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = chunks
        mock_db.execute.return_value = mock_result

        # Mock embeddings service
        mock_embeddings = [[0.1, 0.2, 0.3] for _ in range(5)]
        mock_embeddings_service.embed_documents = AsyncMock(return_value=mock_embeddings)
        mock_embeddings_service.model = "text-embedding-004"
        mock_embeddings_service.estimate_cost.side_effect = [0.0001] * 5

        # Call generate_embeddings
        count = await document_service.generate_embeddings_for_document(
            document_id=sample_document_id,
        )

        # Verify all chunks were processed
        assert count == 5
        expected_texts = [f"Chunk {i} text" for i in range(5)]
        mock_embeddings_service.embed_documents.assert_called_once_with(expected_texts)


# ============================================================================
# Test: Search Similar Chunks
# ============================================================================


class TestDocumentServiceSearchSimilarChunks:
    """Test cases for semantic search."""

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_search_similar_chunks_success(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
    ):
        """Test searching for similar chunks successfully."""
        # Mock embeddings service
        query_embedding = [0.1, 0.2, 0.3]
        mock_embeddings_service.embed_text = AsyncMock(return_value=query_embedding)

        # Mock qdrant search results
        mock_search_result_1 = MagicMock()
        mock_search_result_1.payload = {
            "chunk_id": str(uuid4()),
            "document_id": str(uuid4()),
            "chunk_text": "First result chunk text",
            "chunk_index": 0,
        }
        mock_search_result_1.score = 0.95

        mock_search_result_2 = MagicMock()
        mock_search_result_2.payload = {
            "chunk_id": str(uuid4()),
            "document_id": str(uuid4()),
            "chunk_text": "Second result chunk text",
            "chunk_index": 1,
        }
        mock_search_result_2.score = 0.88

        mock_qdrant_service.search = AsyncMock(
            return_value=[mock_search_result_1, mock_search_result_2]
        )

        # Call search
        results = await document_service.search_similar_chunks(
            query="What is Islam?",
            limit=10,
            score_threshold=0.7,
        )

        # Verify results
        assert len(results) == 2
        assert results[0]["text"] == "First result chunk text"
        assert results[0]["score"] == 0.95
        assert results[1]["text"] == "Second result chunk text"
        assert results[1]["score"] == 0.88

        # Verify embeddings were generated for query
        mock_embeddings_service.embed_text.assert_called_once_with("What is Islam?")

        # Verify qdrant search was called
        mock_qdrant_service.search.assert_called_once_with(
            query_vector=query_embedding,
            limit=10,
            score_threshold=0.7,
            filter_conditions={},
        )

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_search_with_document_type_filter(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
    ):
        """Test searching with document type filter."""
        # Mock embeddings service
        mock_embeddings_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock qdrant search
        mock_qdrant_service.search = AsyncMock(return_value=[])

        # Call search with document type filter
        await document_service.search_similar_chunks(
            query="Search query",
            limit=5,
            score_threshold=0.8,
            document_type="hadith",
        )

        # Verify filter was passed
        mock_qdrant_service.search.assert_called_once()
        filter_arg = mock_qdrant_service.search.call_args[1]["filter_conditions"]
        assert filter_arg == {"document_type": "hadith"}

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_search_with_language_filter(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
    ):
        """Test searching with language filter."""
        # Mock embeddings service
        mock_embeddings_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock qdrant search
        mock_qdrant_service.search = AsyncMock(return_value=[])

        # Call search with language filter
        await document_service.search_similar_chunks(
            query="Search query",
            language="ar",
        )

        # Verify filter was passed
        filter_arg = mock_qdrant_service.search.call_args[1]["filter_conditions"]
        assert filter_arg == {"language": "ar"}

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_search_with_multiple_filters(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
    ):
        """Test searching with multiple filters."""
        # Mock embeddings service
        mock_embeddings_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock qdrant search
        mock_qdrant_service.search = AsyncMock(return_value=[])

        # Call search with both filters
        await document_service.search_similar_chunks(
            query="Search query",
            document_type="quran",
            language="ar",
            limit=20,
            score_threshold=0.85,
        )

        # Verify all filters and parameters were passed
        mock_qdrant_service.search.assert_called_once_with(
            query_vector=[0.1, 0.2, 0.3],
            limit=20,
            score_threshold=0.85,
            filter_conditions={"document_type": "quran", "language": "ar"},
        )

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_search_with_no_results(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
    ):
        """Test searching when no results are found."""
        # Mock embeddings service
        mock_embeddings_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock qdrant search to return empty
        mock_qdrant_service.search = AsyncMock(return_value=[])

        # Call search
        results = await document_service.search_similar_chunks(
            query="Nonexistent content",
        )

        # Verify empty results
        assert results == []

    @pytest.mark.asyncio
    @patch("app.services.document_service.qdrant_service")
    @patch("app.services.document_service.embeddings_service")
    async def test_search_formats_results_correctly(
        self,
        mock_embeddings_service,
        mock_qdrant_service,
        document_service,
    ):
        """Test that search results are formatted correctly."""
        # Mock embeddings service
        mock_embeddings_service.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Create mock result with all fields
        chunk_id = uuid4()
        document_id = uuid4()
        mock_result = MagicMock()
        mock_result.payload = {
            "chunk_id": str(chunk_id),
            "document_id": str(document_id),
            "chunk_text": "Test chunk text",
            "chunk_index": 5,
        }
        mock_result.score = 0.92

        mock_qdrant_service.search = AsyncMock(return_value=[mock_result])

        # Call search
        results = await document_service.search_similar_chunks(query="Test query")

        # Verify result format
        assert len(results) == 1
        result = results[0]
        assert result["chunk_id"] == str(chunk_id)
        assert result["document_id"] == str(document_id)
        assert result["text"] == "Test chunk text"
        assert result["score"] == 0.92
        assert result["index"] == 5
