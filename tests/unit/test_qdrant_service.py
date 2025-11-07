"""Unit tests for Qdrant vector database service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from qdrant_client.http import models
from qdrant_client.http.models import Distance, PointStruct

from app.services.qdrant_service import QdrantService


@pytest.fixture
def mock_qdrant_client():
    """Create mock Qdrant client."""
    client = AsyncMock()
    client.get_collections = AsyncMock()
    client.create_collection = AsyncMock()
    client.upsert = AsyncMock()
    client.search = AsyncMock()
    client.delete = AsyncMock()
    client.get_collection = AsyncMock()
    client.retrieve = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def qdrant_service(mock_qdrant_client):
    """Create Qdrant service with mocked client."""
    with patch("app.services.qdrant_service.AsyncQdrantClient", return_value=mock_qdrant_client):
        with patch("app.services.qdrant_service.settings") as mock_settings:
            mock_settings.qdrant_url = "http://qdrant.example.com"
            mock_settings.qdrant_api_key = "test-api-key"
            mock_settings.qdrant_collection_name = "islamic_knowledge"
            mock_settings.get_collection_name = MagicMock(return_value="islamic_knowledge_dev")

            service = QdrantService()
            service.client = mock_qdrant_client
            return service


# ============================================================================
# Test: Qdrant Service Initialization
# ============================================================================


class TestQdrantServiceInitialization:
    """Test cases for QdrantService initialization."""

    @patch("app.services.qdrant_service.AsyncQdrantClient")
    @patch("app.services.qdrant_service.settings")
    def test_initialization(self, mock_settings, mock_client_class):
        """Test that service initializes with client."""
        mock_settings.qdrant_url = "http://qdrant.example.com"
        mock_settings.qdrant_api_key = "test-api-key"
        mock_settings.qdrant_collection_name = "islamic_knowledge"
        mock_settings.get_collection_name = MagicMock(return_value="islamic_knowledge_dev")

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        service = QdrantService()

        # Verify client was created
        mock_client_class.assert_called_once_with(
            url="http://qdrant.example.com",
            api_key="test-api-key",
        )
        assert service.collection_name == "islamic_knowledge_dev"


# ============================================================================
# Test: Ensure Collection Exists
# ============================================================================


class TestQdrantServiceEnsureCollectionExists:
    """Test cases for collection creation."""

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_creates_when_not_exists(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test creating collection when it doesn't exist."""
        # Mock get_collections to return empty list
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Call ensure_collection_exists
        await qdrant_service.ensure_collection_exists(
            collection_name="test_collection",
            vector_size=1536,
            distance=Distance.COSINE,
        )

        # Verify collection was created
        mock_qdrant_client.create_collection.assert_called_once()
        call_kwargs = mock_qdrant_client.create_collection.call_args[1]
        assert call_kwargs["collection_name"] == "test_collection"
        assert call_kwargs["vectors_config"].size == 1536
        assert call_kwargs["vectors_config"].distance == Distance.COSINE

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_skips_when_exists(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test skipping creation when collection already exists."""
        # Mock get_collections to return existing collection
        mock_collection = MagicMock()
        mock_collection.name = "existing_collection"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Call ensure_collection_exists
        await qdrant_service.ensure_collection_exists(
            collection_name="existing_collection",
        )

        # Verify collection was NOT created
        mock_qdrant_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_uses_default_collection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test using default collection name when not specified."""
        # Mock get_collections to return empty list
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Call without collection_name
        await qdrant_service.ensure_collection_exists()

        # Verify default collection was used
        mock_qdrant_client.create_collection.assert_called_once()
        call_kwargs = mock_qdrant_client.create_collection.call_args[1]
        assert call_kwargs["collection_name"] == "islamic_knowledge_dev"

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error during collection creation."""
        # Mock get_collections to raise exception
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")

        # Call should raise exception
        with pytest.raises(Exception, match="Connection failed"):
            await qdrant_service.ensure_collection_exists()


# ============================================================================
# Test: Add Points
# ============================================================================


class TestQdrantServiceAddPoints:
    """Test cases for adding points."""

    @pytest.mark.asyncio
    async def test_add_points_success(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test adding points successfully."""
        # Create sample points
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=[0.1, 0.2, 0.3],
                payload={"text": "Test 1"},
            ),
            PointStruct(
                id=str(uuid4()),
                vector=[0.4, 0.5, 0.6],
                payload={"text": "Test 2"},
            ),
        ]

        # Add points
        await qdrant_service.add_points(points)

        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once_with(
            collection_name="islamic_knowledge_dev",
            points=points,
        )

    @pytest.mark.asyncio
    async def test_add_points_with_custom_collection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test adding points to custom collection."""
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=[0.1, 0.2, 0.3],
                payload={"text": "Test"},
            ),
        ]

        # Add points to custom collection
        await qdrant_service.add_points(
            points=points,
            collection_name="custom_collection",
        )

        # Verify custom collection was used
        mock_qdrant_client.upsert.assert_called_once()
        call_kwargs = mock_qdrant_client.upsert.call_args[1]
        assert call_kwargs["collection_name"] == "custom_collection"

    @pytest.mark.asyncio
    async def test_add_points_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error during point addition."""
        points = [PointStruct(id="1", vector=[0.1], payload={})]

        # Mock upsert to raise exception
        mock_qdrant_client.upsert.side_effect = Exception("Upsert failed")

        # Call should raise exception
        with pytest.raises(Exception, match="Upsert failed"):
            await qdrant_service.add_points(points)


# ============================================================================
# Test: Search
# ============================================================================


class TestQdrantServiceSearch:
    """Test cases for vector search."""

    @pytest.mark.asyncio
    async def test_search_success(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test searching for similar vectors successfully."""
        # Mock search results
        mock_result1 = MagicMock()
        mock_result1.id = str(uuid4())
        mock_result1.score = 0.95
        mock_result1.payload = {"text": "Result 1"}

        mock_result2 = MagicMock()
        mock_result2.id = str(uuid4())
        mock_result2.score = 0.88
        mock_result2.payload = {"text": "Result 2"}

        mock_qdrant_client.search.return_value = [mock_result1, mock_result2]

        # Perform search
        query_vector = [0.1, 0.2, 0.3]
        results = await qdrant_service.search(
            query_vector=query_vector,
            limit=10,
            score_threshold=0.7,
        )

        # Verify search was called
        mock_qdrant_client.search.assert_called_once()
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert call_kwargs["collection_name"] == "islamic_knowledge_dev"
        assert call_kwargs["query_vector"] == query_vector
        assert call_kwargs["limit"] == 10
        assert call_kwargs["score_threshold"] == 0.7
        assert call_kwargs["query_filter"] is None

        # Verify results
        assert len(results) == 2
        assert results[0].score == 0.95
        assert results[1].score == 0.88

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test searching with filter conditions."""
        mock_qdrant_client.search.return_value = []

        # Perform search with filters
        await qdrant_service.search(
            query_vector=[0.1, 0.2, 0.3],
            filter_conditions={
                "document_type": "hadith",
                "language": "ar",
            },
        )

        # Verify filter was passed
        mock_qdrant_client.search.assert_called_once()
        call_kwargs = mock_qdrant_client.search.call_args[1]
        query_filter = call_kwargs["query_filter"]
        assert query_filter is not None
        assert len(query_filter.must) == 2

    @pytest.mark.asyncio
    async def test_search_with_custom_collection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test searching in custom collection."""
        mock_qdrant_client.search.return_value = []

        await qdrant_service.search(
            query_vector=[0.1, 0.2, 0.3],
            collection_name="custom_collection",
        )

        # Verify custom collection was used
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert call_kwargs["collection_name"] == "custom_collection"

    @pytest.mark.asyncio
    async def test_search_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error during search."""
        mock_qdrant_client.search.side_effect = Exception("Search failed")

        with pytest.raises(Exception, match="Search failed"):
            await qdrant_service.search(query_vector=[0.1, 0.2, 0.3])


# ============================================================================
# Test: Delete Points
# ============================================================================


class TestQdrantServiceDeletePoints:
    """Test cases for deleting points."""

    @pytest.mark.asyncio
    async def test_delete_points_success(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test deleting points successfully."""
        point_ids = [uuid4(), uuid4(), uuid4()]

        # Delete points
        await qdrant_service.delete_points(point_ids)

        # Verify delete was called
        mock_qdrant_client.delete.assert_called_once()
        call_kwargs = mock_qdrant_client.delete.call_args[1]
        assert call_kwargs["collection_name"] == "islamic_knowledge_dev"
        assert len(call_kwargs["points_selector"].points) == 3

    @pytest.mark.asyncio
    async def test_delete_points_with_custom_collection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test deleting points from custom collection."""
        point_ids = [uuid4()]

        await qdrant_service.delete_points(
            point_ids=point_ids,
            collection_name="custom_collection",
        )

        # Verify custom collection was used
        call_kwargs = mock_qdrant_client.delete.call_args[1]
        assert call_kwargs["collection_name"] == "custom_collection"

    @pytest.mark.asyncio
    async def test_delete_points_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error during deletion."""
        point_ids = [uuid4()]
        mock_qdrant_client.delete.side_effect = Exception("Delete failed")

        with pytest.raises(Exception, match="Delete failed"):
            await qdrant_service.delete_points(point_ids)


# ============================================================================
# Test: Get Collection Info
# ============================================================================


class TestQdrantServiceGetCollectionInfo:
    """Test cases for getting collection information."""

    @pytest.mark.asyncio
    async def test_get_collection_info_success(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test getting collection info successfully."""
        # Mock collection info
        mock_info = MagicMock()
        mock_info.points_count = 1000
        mock_info.vectors_count = 1000
        mock_info.status = "green"
        mock_info.optimizer_status = "ok"
        mock_qdrant_client.get_collection.return_value = mock_info

        # Get collection info
        info = await qdrant_service.get_collection_info()

        # Verify info
        assert info["name"] == "islamic_knowledge_dev"
        assert info["points_count"] == 1000
        assert info["vectors_count"] == 1000
        assert info["status"] == "green"
        assert info["optimizer_status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_collection_info_with_custom_collection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test getting info for custom collection."""
        mock_info = MagicMock()
        mock_info.points_count = 500
        mock_info.vectors_count = 500
        mock_info.status = "green"
        mock_info.optimizer_status = "ok"
        mock_qdrant_client.get_collection.return_value = mock_info

        info = await qdrant_service.get_collection_info(
            collection_name="custom_collection"
        )

        # Verify custom collection was used
        assert info["name"] == "custom_collection"

    @pytest.mark.asyncio
    async def test_get_collection_info_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error when getting collection info."""
        mock_qdrant_client.get_collection.side_effect = Exception("Collection not found")

        with pytest.raises(Exception, match="Collection not found"):
            await qdrant_service.get_collection_info()


# ============================================================================
# Test: Get Points by IDs
# ============================================================================


class TestQdrantServiceGetPointsByIds:
    """Test cases for retrieving points by IDs."""

    @pytest.mark.asyncio
    async def test_get_points_by_ids_success(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test retrieving points by IDs successfully."""
        # Mock retrieved points
        point_id1 = uuid4()
        point_id2 = uuid4()

        mock_record1 = MagicMock()
        mock_record1.id = str(point_id1)
        mock_record1.vector = [0.1, 0.2, 0.3]
        mock_record1.payload = {"text": "Point 1"}

        mock_record2 = MagicMock()
        mock_record2.id = str(point_id2)
        mock_record2.vector = [0.4, 0.5, 0.6]
        mock_record2.payload = {"text": "Point 2"}

        mock_qdrant_client.retrieve.return_value = [mock_record1, mock_record2]

        # Retrieve points
        point_ids = [point_id1, point_id2]
        results = await qdrant_service.get_points_by_ids(point_ids)

        # Verify retrieve was called
        mock_qdrant_client.retrieve.assert_called_once()
        call_kwargs = mock_qdrant_client.retrieve.call_args[1]
        assert call_kwargs["collection_name"] == "islamic_knowledge_dev"
        assert len(call_kwargs["ids"]) == 2
        assert call_kwargs["with_vectors"] is True
        assert call_kwargs["with_payload"] is True

        # Verify results
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_points_by_ids_with_custom_collection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test retrieving points from custom collection."""
        mock_qdrant_client.retrieve.return_value = []

        await qdrant_service.get_points_by_ids(
            point_ids=[uuid4()],
            collection_name="custom_collection",
        )

        # Verify custom collection was used
        call_kwargs = mock_qdrant_client.retrieve.call_args[1]
        assert call_kwargs["collection_name"] == "custom_collection"

    @pytest.mark.asyncio
    async def test_get_points_by_ids_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error when retrieving points."""
        mock_qdrant_client.retrieve.side_effect = Exception("Retrieve failed")

        with pytest.raises(Exception, match="Retrieve failed"):
            await qdrant_service.get_points_by_ids([uuid4()])


# ============================================================================
# Test: Copy Points to Collection
# ============================================================================


class TestQdrantServiceCopyPointsToCollection:
    """Test cases for copying points between collections."""

    @pytest.mark.asyncio
    async def test_copy_points_to_collection_success(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test copying points to another collection successfully."""
        # Mock source points
        point_id1 = uuid4()
        point_id2 = uuid4()

        mock_record1 = MagicMock()
        mock_record1.id = str(point_id1)
        mock_record1.vector = [0.1, 0.2, 0.3]
        mock_record1.payload = {"text": "Point 1"}

        mock_record2 = MagicMock()
        mock_record2.id = str(point_id2)
        mock_record2.vector = [0.4, 0.5, 0.6]
        mock_record2.payload = {"text": "Point 2"}

        # First retrieve call returns source points
        mock_qdrant_client.retrieve.return_value = [mock_record1, mock_record2]

        # Mock ensure_collection_exists
        qdrant_service.ensure_collection_exists = AsyncMock()

        # Copy points
        point_ids = [point_id1, point_id2]
        count = await qdrant_service.copy_points_to_collection(
            point_ids=point_ids,
            source_collection="source_dev",
            target_collection="target_prod",
        )

        # Verify retrieve was called on source
        assert mock_qdrant_client.retrieve.called
        retrieve_kwargs = mock_qdrant_client.retrieve.call_args[1]
        assert retrieve_kwargs["collection_name"] == "source_dev"

        # Verify target collection was ensured
        qdrant_service.ensure_collection_exists.assert_called_once_with(
            collection_name="target_prod"
        )

        # Verify upsert was called on target
        assert mock_qdrant_client.upsert.called
        upsert_kwargs = mock_qdrant_client.upsert.call_args[1]
        assert upsert_kwargs["collection_name"] == "target_prod"
        assert len(upsert_kwargs["points"]) == 2

        # Verify count
        assert count == 2

    @pytest.mark.asyncio
    async def test_copy_points_to_collection_with_no_points(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test copying when no points are found."""
        # Mock retrieve to return empty list
        mock_qdrant_client.retrieve.return_value = []

        # Copy points
        count = await qdrant_service.copy_points_to_collection(
            point_ids=[uuid4()],
            source_collection="source_dev",
            target_collection="target_prod",
        )

        # Verify count is 0
        assert count == 0

        # Verify upsert was NOT called
        mock_qdrant_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_copy_points_to_collection_handles_error(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test handling error during point copying."""
        mock_qdrant_client.retrieve.side_effect = Exception("Copy failed")

        with pytest.raises(Exception, match="Copy failed"):
            await qdrant_service.copy_points_to_collection(
                point_ids=[uuid4()],
                source_collection="source_dev",
                target_collection="target_prod",
            )


# ============================================================================
# Test: Get Environment Collection Name
# ============================================================================


class TestQdrantServiceGetEnvCollectionName:
    """Test cases for environment-specific collection names."""

    def test_get_env_collection_name(self, qdrant_service):
        """Test generating environment-specific collection name."""
        name = qdrant_service.get_env_collection_name(
            base_collection="islamic_knowledge",
            environment="prod",
        )

        assert name == "islamic_knowledge_prod"

    def test_get_env_collection_name_for_different_environments(
        self,
        qdrant_service,
    ):
        """Test generating collection names for different environments."""
        dev_name = qdrant_service.get_env_collection_name(
            "documents",
            "dev",
        )
        stage_name = qdrant_service.get_env_collection_name(
            "documents",
            "stage",
        )
        prod_name = qdrant_service.get_env_collection_name(
            "documents",
            "prod",
        )

        assert dev_name == "documents_dev"
        assert stage_name == "documents_stage"
        assert prod_name == "documents_prod"


# ============================================================================
# Test: Close Connection
# ============================================================================


class TestQdrantServiceClose:
    """Test cases for closing connection."""

    @pytest.mark.asyncio
    async def test_close_connection(
        self,
        qdrant_service,
        mock_qdrant_client,
    ):
        """Test closing Qdrant connection."""
        await qdrant_service.close()

        # Verify close was called
        mock_qdrant_client.close.assert_called_once()
