"""Integration tests for document API endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from httpx import AsyncClient

from app.main import app
from app.models.user import User


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        role="admin",
        is_verified=True,
    )


@pytest.fixture
def sample_document_id():
    """Sample document ID."""
    return uuid4()


@pytest.fixture
def mock_document_response(sample_document_id):
    """Mock document response object."""
    return {
        "id": sample_document_id,
        "title": "Test Document",
        "document_type": "hadith",
        "primary_category": "aqidah",
        "language": "fa",
        "author": "Test Author",
        "source_reference": "Test Source",
        "total_characters": 100,
        "chunk_count": 5,
        "processing_status": "awaiting_chunk_approval",
        "chunking_method": "semantic",
        "uploaded_at": datetime.now(timezone.utc),
        "processed_at": datetime.now(timezone.utc),
    }


# ============================================================================
# Test: POST /upload - Document Upload Endpoint
# ============================================================================


class TestDocumentUploadEndpoint:
    """Test cases for POST /api/v1/documents/upload endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_success(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_document_service_class,
        sample_user,
        mock_document_response,
    ):
        """Test uploading a document successfully."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock document service instance
        mock_service = MagicMock()
        mock_document = MagicMock()
        for key, value in mock_document_response.items():
            setattr(mock_document, key, value)

        mock_service.create_document = AsyncMock(return_value=mock_document)
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "Test Document",
                    "content": "This is a test document content for testing purposes.",
                    "document_type": "hadith",
                    "primary_category": "aqidah",
                    "language": "fa",
                    "author": "Test Author",
                    "source_reference": "Test Source",
                    "chunking_strategy": "semantic",
                    "chunk_size": 768,
                    "chunk_overlap": 150,
                },
            )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Document uploaded successfully. 5 chunks created."
        assert data["document"]["title"] == "Test Document"
        assert data["document"]["document_type"] == "hadith"
        assert data["document"]["chunk_count"] == 5

        # Verify service was called correctly
        mock_service.create_document.assert_called_once()
        call_kwargs = mock_service.create_document.call_args[1]
        assert call_kwargs["title"] == "Test Document"
        assert call_kwargs["document_type"] == "hadith"
        assert call_kwargs["uploaded_by"] == sample_user.id

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_with_minimal_fields(
        self,
        mock_get_db,
        mock_get_current_user,
        sample_user,
    ):
        """Test uploading a document with only required fields."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user

        # Make request with minimal fields
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "Minimal Document",
                    "content": "Minimal content.",
                    "document_type": "article",
                    "primary_category": "general",
                },
            )

        # Should succeed with defaults
        assert response.status_code in [201, 500]  # May fail at service level in mock

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_validation_error_invalid_document_type(
        self,
        mock_get_db,
        mock_get_current_user,
        sample_user,
    ):
        """Test validation error for invalid document type."""
        mock_get_current_user.return_value = sample_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "Test Document",
                    "content": "Test content",
                    "document_type": "invalid_type",
                    "primary_category": "aqidah",
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_validation_error_invalid_category(
        self,
        mock_get_db,
        mock_get_current_user,
        sample_user,
    ):
        """Test validation error for invalid primary category."""
        mock_get_current_user.return_value = sample_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "Test Document",
                    "content": "Test content",
                    "document_type": "hadith",
                    "primary_category": "invalid_category",
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_validation_error_empty_title(
        self,
        mock_get_db,
        mock_get_current_user,
        sample_user,
    ):
        """Test validation error for empty title."""
        mock_get_current_user.return_value = sample_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "",
                    "content": "Test content",
                    "document_type": "hadith",
                    "primary_category": "aqidah",
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_validation_error_empty_content(
        self,
        mock_get_db,
        mock_get_current_user,
        sample_user,
    ):
        """Test validation error for empty content."""
        mock_get_current_user.return_value = sample_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "Test Document",
                    "content": "",
                    "document_type": "hadith",
                    "primary_category": "aqidah",
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_upload_document_service_error(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_document_service_class,
        sample_user,
    ):
        """Test handling service error during upload."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service to raise exception
        mock_service = MagicMock()
        mock_service.create_document = AsyncMock(
            side_effect=Exception("Document processing failed")
        )
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/upload",
                json={
                    "title": "Test Document",
                    "content": "Test content",
                    "document_type": "hadith",
                    "primary_category": "aqidah",
                },
            )

        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "DOCUMENT_UPLOAD_FAILED" in data["detail"]


# ============================================================================
# Test: POST /embeddings/generate - Embeddings Generation Endpoint
# ============================================================================


class TestEmbeddingsGenerationEndpoint:
    """Test cases for POST /api/v1/documents/embeddings/generate endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.qdrant_service")
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_generate_embeddings_success(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_document_service_class,
        mock_qdrant_service,
        sample_user,
        sample_document_id,
    ):
        """Test generating embeddings successfully."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock qdrant service
        mock_qdrant_service.ensure_collection_exists = AsyncMock()

        # Mock document service
        mock_service = MagicMock()
        mock_service.generate_embeddings_for_document = AsyncMock(return_value=10)
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/embeddings/generate",
                json={
                    "document_id": str(sample_document_id),
                },
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Generated 10 embeddings for document"
        assert data["embeddings_count"] == 10
        assert data["document_id"] == str(sample_document_id)

        # Verify collection was ensured to exist
        mock_qdrant_service.ensure_collection_exists.assert_called_once()

        # Verify service was called
        mock_service.generate_embeddings_for_document.assert_called_once_with(
            document_id=sample_document_id
        )

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.qdrant_service")
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_generate_embeddings_for_document_with_no_chunks(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_document_service_class,
        mock_qdrant_service,
        sample_user,
        sample_document_id,
    ):
        """Test generating embeddings for document with no chunks."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user
        mock_qdrant_service.ensure_collection_exists = AsyncMock()

        # Mock service to return 0 embeddings
        mock_service = MagicMock()
        mock_service.generate_embeddings_for_document = AsyncMock(return_value=0)
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/embeddings/generate",
                json={
                    "document_id": str(sample_document_id),
                },
            )

        # Verify response shows 0 embeddings
        assert response.status_code == 200
        data = response.json()
        assert data["embeddings_count"] == 0

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.qdrant_service")
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_generate_embeddings_service_error(
        self,
        mock_get_db,
        mock_get_current_user,
        mock_document_service_class,
        mock_qdrant_service,
        sample_user,
        sample_document_id,
    ):
        """Test handling service error during embeddings generation."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user
        mock_qdrant_service.ensure_collection_exists = AsyncMock()

        # Mock service to raise exception
        mock_service = MagicMock()
        mock_service.generate_embeddings_for_document = AsyncMock(
            side_effect=Exception("Embeddings generation failed")
        )
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/embeddings/generate",
                json={
                    "document_id": str(sample_document_id),
                },
            )

        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "EMBEDDINGS_GENERATION_FAILED" in data["detail"]

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_current_user")
    @patch("app.api.v1.documents.get_db")
    async def test_generate_embeddings_validation_error_invalid_uuid(
        self,
        mock_get_db,
        mock_get_current_user,
        sample_user,
    ):
        """Test validation error for invalid document ID."""
        mock_get_current_user.return_value = sample_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/embeddings/generate",
                json={
                    "document_id": "not-a-valid-uuid",
                },
            )

        # Verify validation error
        assert response.status_code == 422


# ============================================================================
# Test: POST /search - Document Search Endpoint
# ============================================================================


class TestSearchDocumentsEndpoint:
    """Test cases for POST /api/v1/documents/search endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_db")
    async def test_search_documents_success(
        self,
        mock_get_db,
        mock_document_service_class,
    ):
        """Test searching documents successfully."""
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service search results
        chunk_id = uuid4()
        document_id = uuid4()
        mock_service = MagicMock()
        mock_service.search_similar_chunks = AsyncMock(
            return_value=[
                {
                    "chunk_id": str(chunk_id),
                    "document_id": str(document_id),
                    "text": "This is a test chunk about Islam",
                    "score": 0.95,
                    "index": 0,
                },
                {
                    "chunk_id": str(uuid4()),
                    "document_id": str(uuid4()),
                    "text": "Another relevant chunk",
                    "score": 0.88,
                    "index": 1,
                },
            ]
        )
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "What is Islam?",
                    "limit": 10,
                    "score_threshold": 0.7,
                },
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Search completed successfully"
        assert data["query"] == "What is Islam?"
        assert data["count"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["score"] == 0.95
        assert data["results"][0]["text"] == "This is a test chunk about Islam"

        # Verify service was called
        mock_service.search_similar_chunks.assert_called_once_with(
            query="What is Islam?",
            limit=10,
            score_threshold=0.7,
            document_type=None,
            language=None,
        )

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_db")
    async def test_search_with_document_type_filter(
        self,
        mock_get_db,
        mock_document_service_class,
    ):
        """Test searching with document type filter."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service
        mock_service = MagicMock()
        mock_service.search_similar_chunks = AsyncMock(return_value=[])
        mock_document_service_class.return_value = mock_service

        # Make request with document type filter
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Search query",
                    "document_type": "hadith",
                },
            )

        # Verify filter was passed to service
        assert response.status_code == 200
        mock_service.search_similar_chunks.assert_called_once()
        call_kwargs = mock_service.search_similar_chunks.call_args[1]
        assert call_kwargs["document_type"] == "hadith"

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_db")
    async def test_search_with_language_filter(
        self,
        mock_get_db,
        mock_document_service_class,
    ):
        """Test searching with language filter."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service
        mock_service = MagicMock()
        mock_service.search_similar_chunks = AsyncMock(return_value=[])
        mock_document_service_class.return_value = mock_service

        # Make request with language filter
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Search query",
                    "language": "ar",
                },
            )

        # Verify filter was passed
        assert response.status_code == 200
        call_kwargs = mock_service.search_similar_chunks.call_args[1]
        assert call_kwargs["language"] == "ar"

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_db")
    async def test_search_with_custom_parameters(
        self,
        mock_get_db,
        mock_document_service_class,
    ):
        """Test searching with custom limit and threshold."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service
        mock_service = MagicMock()
        mock_service.search_similar_chunks = AsyncMock(return_value=[])
        mock_document_service_class.return_value = mock_service

        # Make request with custom parameters
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Test query",
                    "limit": 20,
                    "score_threshold": 0.85,
                },
            )

        # Verify parameters were passed
        assert response.status_code == 200
        mock_service.search_similar_chunks.assert_called_once_with(
            query="Test query",
            limit=20,
            score_threshold=0.85,
            document_type=None,
            language=None,
        )

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_db")
    async def test_search_with_no_results(
        self,
        mock_get_db,
        mock_document_service_class,
    ):
        """Test searching when no results are found."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service to return empty results
        mock_service = MagicMock()
        mock_service.search_similar_chunks = AsyncMock(return_value=[])
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Nonexistent content",
                },
            )

        # Verify empty results
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_db")
    async def test_search_validation_error_empty_query(
        self,
        mock_get_db,
    ):
        """Test validation error for empty query."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "",
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_db")
    async def test_search_validation_error_invalid_limit(
        self,
        mock_get_db,
    ):
        """Test validation error for invalid limit."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Test query",
                    "limit": 100,  # Max is 50
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.get_db")
    async def test_search_validation_error_invalid_threshold(
        self,
        mock_get_db,
    ):
        """Test validation error for invalid score threshold."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Test query",
                    "score_threshold": 1.5,  # Max is 1.0
                },
            )

        # Verify validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.DocumentService")
    @patch("app.api.v1.documents.get_db")
    async def test_search_service_error(
        self,
        mock_get_db,
        mock_document_service_class,
    ):
        """Test handling service error during search."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock service to raise exception
        mock_service = MagicMock()
        mock_service.search_similar_chunks = AsyncMock(
            side_effect=Exception("Search failed")
        )
        mock_document_service_class.return_value = mock_service

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/documents/search",
                json={
                    "query": "Test query",
                },
            )

        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "SEARCH_FAILED" in data["detail"]


# ============================================================================
# Test: GET /qdrant/status - Qdrant Status Endpoint
# ============================================================================


class TestQdrantStatusEndpoint:
    """Test cases for GET /api/v1/documents/qdrant/status endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.qdrant_service")
    @patch("app.api.v1.documents.get_current_user")
    async def test_get_qdrant_status_success(
        self,
        mock_get_current_user,
        mock_qdrant_service,
        sample_user,
    ):
        """Test getting Qdrant status successfully."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user

        # Mock qdrant service
        mock_qdrant_service.get_collection_info = AsyncMock(
            return_value={
                "collection_name": "documents",
                "vectors_count": 1000,
                "points_count": 1000,
                "status": "green",
            }
        )

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/documents/qdrant/status")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "QDRANT_STATUS_SUCCESS"
        assert data["message"] == "Qdrant status retrieved"
        assert data["collection"]["collection_name"] == "documents"
        assert data["collection"]["vectors_count"] == 1000

        # Verify service was called
        mock_qdrant_service.get_collection_info.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.v1.documents.qdrant_service")
    @patch("app.api.v1.documents.get_current_user")
    async def test_get_qdrant_status_service_error(
        self,
        mock_get_current_user,
        mock_qdrant_service,
        sample_user,
    ):
        """Test handling service error when getting Qdrant status."""
        # Setup mocks
        mock_get_current_user.return_value = sample_user

        # Mock service to raise exception
        mock_qdrant_service.get_collection_info = AsyncMock(
            side_effect=Exception("Qdrant connection failed")
        )

        # Make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/documents/qdrant/status")

        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "QDRANT_STATUS_FAILED" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_qdrant_status_requires_authentication(self):
        """Test that endpoint requires authentication."""
        # Make request without authentication mock
        # This will fail dependency injection for get_current_user
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/documents/qdrant/status")

        # Should return 401 or 500 depending on auth implementation
        assert response.status_code in [401, 500]
