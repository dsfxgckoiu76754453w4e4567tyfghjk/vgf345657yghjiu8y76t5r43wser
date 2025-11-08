"""Unit tests for MinIO storage service."""

import io
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

from minio.error import S3Error

from app.services.minio_storage_service import MinIOStorageService


@pytest.fixture
def mock_minio_client():
    """Create mock MinIO client."""
    client = MagicMock()
    client.bucket_exists = MagicMock(return_value=True)
    client.make_bucket = MagicMock()
    client.put_object = MagicMock()
    client.get_object = MagicMock()
    client.remove_object = MagicMock()
    client.stat_object = MagicMock()
    client.list_objects = MagicMock()
    client.list_buckets = MagicMock(return_value=[])
    client.presigned_get_object = MagicMock(return_value="https://minio.example.com/presigned-url")
    client.presigned_put_object = MagicMock(return_value="https://minio.example.com/presigned-put-url")
    client.set_bucket_lifecycle = MagicMock()
    client.set_bucket_policy = MagicMock()
    return client


@pytest.fixture
def sample_file_data():
    """Sample file data for testing."""
    return b"Test file content for unit testing"


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return uuid4()


# ============================================================================
# Test: MinIO Service Initialization
# ============================================================================


class TestMinIOStorageServiceInitialization:
    """Test cases for MinIOStorageService initialization."""

    @patch("app.services.minio_storage_service.settings")
    @patch("app.services.minio_storage_service.Minio")
    def test_initialization_when_enabled(self, mock_minio_class, mock_settings):
        """Test initialization when MinIO is enabled."""
        # Setup mock settings
        mock_settings.minio_enabled = True
        mock_settings.minio_endpoint = "minio.example.com"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(side_effect=lambda x: f"dev-{x}")

        # Setup bucket names
        mock_settings.minio_bucket_images = "wisqu-images"
        mock_settings.minio_bucket_documents = "wisqu-documents"
        mock_settings.minio_bucket_audio_resources = "wisqu-audio-resources"
        mock_settings.minio_bucket_audio_user = "wisqu-audio-user"
        mock_settings.minio_bucket_audio_transcripts = "wisqu-audio-transcripts"
        mock_settings.minio_bucket_uploads = "wisqu-uploads"
        mock_settings.minio_bucket_temp = "wisqu-temp"
        mock_settings.minio_bucket_backups = "wisqu-backups"

        # Mock client instance
        mock_client = MagicMock()
        mock_client.bucket_exists = MagicMock(return_value=False)
        mock_minio_class.return_value = mock_client

        # Initialize service
        service = MinIOStorageService()

        # Verify client was created
        assert service.client is not None
        mock_minio_class.assert_called_once_with(
            "minio.example.com",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,
        )

    @patch("app.services.minio_storage_service.settings")
    def test_initialization_when_disabled(self, mock_settings):
        """Test initialization when MinIO is disabled."""
        mock_settings.minio_enabled = False

        service = MinIOStorageService()

        # Verify client is None
        assert service.client is None

    @patch("app.services.minio_storage_service.settings")
    @patch("app.services.minio_storage_service.Minio")
    def test_initialization_handles_connection_error(self, mock_minio_class, mock_settings):
        """Test initialization handles connection error."""
        mock_settings.minio_enabled = True
        mock_settings.minio_endpoint = "minio.example.com"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False

        # Mock Minio to raise exception
        mock_minio_class.side_effect = Exception("Connection failed")

        # Initialize should raise exception
        with pytest.raises(Exception, match="Connection failed"):
            MinIOStorageService()


# ============================================================================
# Test: Upload File
# ============================================================================


class TestMinIOStorageServiceUploadFile:
    """Test cases for file upload."""

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_file_success_with_bytes(
        self,
        mock_settings,
        mock_minio_client,
        sample_file_data,
        sample_user_id,
    ):
        """Test uploading file with bytes data."""
        # Setup settings
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")
        mock_settings.storage_max_file_size_mb = 100
        mock_settings.minio_bucket_uploads = "wisqu-uploads"
        mock_settings.minio_public_url = "https://cdn.example.com"

        # Setup service
        service = MinIOStorageService()
        service.client = mock_minio_client
        service.get_presigned_url = MagicMock(return_value="https://presigned-url.example.com")

        # Mock put_object result
        mock_result = MagicMock()
        mock_result.etag = "abc123etag"
        mock_minio_client.put_object.return_value = mock_result

        # Upload file
        result = await service.upload_file(
            bucket="wisqu-uploads",
            object_name="test/file.txt",
            file_data=sample_file_data,
            content_type="text/plain",
            metadata={"description": "Test file"},
            user_id=sample_user_id,
        )

        # Verify upload was called
        mock_minio_client.put_object.assert_called_once()
        call_args = mock_minio_client.put_object.call_args
        assert call_args[0][0] == "dev-wisqu-uploads"  # Environment bucket
        assert call_args[0][1] == "test/file.txt"
        assert call_args[1]["length"] == len(sample_file_data)
        assert call_args[1]["content_type"] == "text/plain"

        # Verify metadata includes user_id and environment
        metadata = call_args[1]["metadata"]
        assert metadata["user_id"] == str(sample_user_id)
        assert metadata["environment"] == "dev"
        assert metadata["description"] == "Test file"

        # Verify result
        assert result["bucket"] == "wisqu-uploads"
        assert result["env_bucket"] == "dev-wisqu-uploads"
        assert result["object_name"] == "test/file.txt"
        assert result["size"] == len(sample_file_data)
        assert result["etag"] == "abc123etag"
        assert result["environment"] == "dev"

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_file_success_with_file_object(
        self,
        mock_settings,
        mock_minio_client,
        sample_file_data,
    ):
        """Test uploading file with file-like object."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")
        mock_settings.storage_max_file_size_mb = 100
        mock_settings.minio_bucket_uploads = "wisqu-uploads"

        service = MinIOStorageService()
        service.client = mock_minio_client
        service.get_presigned_url = MagicMock(return_value="https://presigned-url.example.com")

        mock_result = MagicMock()
        mock_result.etag = "etag123"
        mock_minio_client.put_object.return_value = mock_result

        # Create file-like object
        file_obj = io.BytesIO(sample_file_data)

        # Upload file
        result = await service.upload_file(
            bucket="wisqu-uploads",
            object_name="test/file.txt",
            file_data=file_obj,
            content_type="text/plain",
        )

        # Verify result
        assert result["size"] == len(sample_file_data)

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_file_raises_error_when_disabled(self, mock_settings):
        """Test upload raises error when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        with pytest.raises(ValueError, match="MinIO is not enabled"):
            await service.upload_file(
                bucket="wisqu-uploads",
                object_name="file.txt",
                file_data=b"data",
            )

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_file_raises_error_when_exceeds_size_limit(
        self,
        mock_settings,
        mock_minio_client,
    ):
        """Test upload raises error when file exceeds size limit."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")
        mock_settings.storage_max_file_size_mb = 1  # 1 MB limit
        mock_settings.minio_bucket_uploads = "wisqu-uploads"

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Create 2 MB file
        large_file = b"x" * (2 * 1024 * 1024)

        with pytest.raises(ValueError, match="exceeds limit"):
            await service.upload_file(
                bucket="wisqu-uploads",
                object_name="large.txt",
                file_data=large_file,
            )

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_file_handles_s3_error(
        self,
        mock_settings,
        mock_minio_client,
        sample_file_data,
    ):
        """Test upload handles S3 error."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")
        mock_settings.storage_max_file_size_mb = 100
        mock_settings.minio_bucket_uploads = "wisqu-uploads"

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Mock S3Error
        mock_minio_client.put_object.side_effect = S3Error(
            code="NoSuchBucket",
            message="Bucket does not exist",
            resource="/test",
            request_id="123",
            host_id="456",
            response="error",
        )

        with pytest.raises(S3Error):
            await service.upload_file(
                bucket="wisqu-uploads",
                object_name="file.txt",
                file_data=sample_file_data,
            )


# ============================================================================
# Test: Get Presigned URL
# ============================================================================


class TestMinIOStorageServiceGetPresignedURL:
    """Test cases for presigned URL generation."""

    @patch("app.services.minio_storage_service.settings")
    def test_get_presigned_url_for_download(
        self,
        mock_settings,
        mock_minio_client,
    ):
        """Test generating presigned URL for download."""
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-documents")

        service = MinIOStorageService()
        service.client = mock_minio_client

        url = service.get_presigned_url(
            bucket="wisqu-documents",
            object_name="test.pdf",
            expires=7200,
            method="GET",
        )

        # Verify presigned URL was generated
        assert url == "https://minio.example.com/presigned-url"
        mock_minio_client.presigned_get_object.assert_called_once()

    @patch("app.services.minio_storage_service.settings")
    def test_get_presigned_url_for_upload(
        self,
        mock_settings,
        mock_minio_client,
    ):
        """Test generating presigned URL for upload."""
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")

        service = MinIOStorageService()
        service.client = mock_minio_client

        url = service.get_presigned_url(
            bucket="wisqu-uploads",
            object_name="upload.txt",
            expires=3600,
            method="PUT",
        )

        # Verify presigned PUT URL was generated
        assert url == "https://minio.example.com/presigned-put-url"
        mock_minio_client.presigned_put_object.assert_called_once()

    def test_get_presigned_url_raises_error_when_disabled(self):
        """Test presigned URL raises error when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        with pytest.raises(ValueError, match="MinIO is not enabled"):
            service.get_presigned_url(
                bucket="wisqu-documents",
                object_name="test.pdf",
            )


# ============================================================================
# Test: Download File
# ============================================================================


class TestMinIOStorageServiceDownloadFile:
    """Test cases for file download."""

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_download_file_success(
        self,
        mock_settings,
        mock_minio_client,
        sample_file_data,
    ):
        """Test downloading file successfully."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")

        # Mock response object
        mock_response = MagicMock()
        mock_response.read.return_value = sample_file_data
        mock_response.close = MagicMock()
        mock_response.release_conn = MagicMock()
        mock_minio_client.get_object.return_value = mock_response

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Download file
        data = await service.download_file(
            bucket="wisqu-uploads",
            object_name="test/file.txt",
        )

        # Verify data was downloaded
        assert data == sample_file_data
        mock_minio_client.get_object.assert_called_once_with(
            "dev-wisqu-uploads",
            "test/file.txt",
        )
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file_raises_error_when_disabled(self):
        """Test download raises error when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        with pytest.raises(ValueError, match="MinIO is not enabled"):
            await service.download_file(
                bucket="wisqu-uploads",
                object_name="file.txt",
            )

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_download_file_handles_s3_error(
        self,
        mock_settings,
        mock_minio_client,
    ):
        """Test download handles S3 error."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")

        mock_minio_client.get_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Key does not exist",
            resource="/test",
            request_id="123",
            host_id="456",
            response="error",
        )

        service = MinIOStorageService()
        service.client = mock_minio_client

        with pytest.raises(S3Error):
            await service.download_file(
                bucket="wisqu-uploads",
                object_name="nonexistent.txt",
            )


# ============================================================================
# Test: Delete File
# ============================================================================


class TestMinIOStorageServiceDeleteFile:
    """Test cases for file deletion."""

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_delete_file_success(
        self,
        mock_settings,
        mock_minio_client,
    ):
        """Test deleting file successfully."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Delete file
        result = await service.delete_file(
            bucket="wisqu-uploads",
            object_name="test/file.txt",
        )

        # Verify deletion
        assert result is True
        mock_minio_client.remove_object.assert_called_once_with(
            "dev-wisqu-uploads",
            "test/file.txt",
        )

    @pytest.mark.asyncio
    async def test_delete_file_raises_error_when_disabled(self):
        """Test delete raises error when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        with pytest.raises(ValueError, match="MinIO is not enabled"):
            await service.delete_file(
                bucket="wisqu-uploads",
                object_name="file.txt",
            )

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_delete_file_handles_s3_error(
        self,
        mock_settings,
        mock_minio_client,
    ):
        """Test delete handles S3 error."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")

        mock_minio_client.remove_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Key does not exist",
            resource="/test",
            request_id="123",
            host_id="456",
            response="error",
        )

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Delete should return False on error
        result = await service.delete_file(
            bucket="wisqu-uploads",
            object_name="nonexistent.txt",
        )

        assert result is False


# ============================================================================
# Test: File Exists
# ============================================================================


class TestMinIOStorageServiceFileExists:
    """Test cases for file existence check."""

    def test_file_exists_returns_true_when_exists(
        self,
        mock_minio_client,
    ):
        """Test file_exists returns True when file exists."""
        mock_stat = MagicMock()
        mock_minio_client.stat_object.return_value = mock_stat

        service = MinIOStorageService()
        service.client = mock_minio_client

        exists = service.file_exists(
            bucket="wisqu-uploads",
            object_name="test/file.txt",
        )

        assert exists is True

    def test_file_exists_returns_false_when_not_exists(
        self,
        mock_minio_client,
    ):
        """Test file_exists returns False when file doesn't exist."""
        mock_minio_client.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Key does not exist",
            resource="/test",
            request_id="123",
            host_id="456",
            response="error",
        )

        service = MinIOStorageService()
        service.client = mock_minio_client

        exists = service.file_exists(
            bucket="wisqu-uploads",
            object_name="nonexistent.txt",
        )

        assert exists is False

    def test_file_exists_returns_false_when_disabled(self):
        """Test file_exists returns False when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        exists = service.file_exists(
            bucket="wisqu-uploads",
            object_name="file.txt",
        )

        assert exists is False


# ============================================================================
# Test: Get File Metadata
# ============================================================================


class TestMinIOStorageServiceGetFileMetadata:
    """Test cases for getting file metadata."""

    def test_get_file_metadata_success(
        self,
        mock_minio_client,
    ):
        """Test getting file metadata successfully."""
        # Mock stat object
        mock_stat = MagicMock()
        mock_stat.size = 1024
        mock_stat.content_type = "text/plain"
        mock_stat.etag = "abc123"
        mock_stat.last_modified = datetime(2025, 1, 1, 12, 0, 0)
        mock_stat.metadata = {"user_id": "123"}
        mock_minio_client.stat_object.return_value = mock_stat

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Get metadata
        metadata = service.get_file_metadata(
            bucket="wisqu-uploads",
            object_name="test/file.txt",
        )

        # Verify metadata
        assert metadata["size"] == 1024
        assert metadata["content_type"] == "text/plain"
        assert metadata["etag"] == "abc123"
        assert metadata["last_modified"] == datetime(2025, 1, 1, 12, 0, 0)
        assert metadata["metadata"] == {"user_id": "123"}

    def test_get_file_metadata_raises_error_when_disabled(self):
        """Test get_file_metadata raises error when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        with pytest.raises(ValueError, match="MinIO is not enabled"):
            service.get_file_metadata(
                bucket="wisqu-uploads",
                object_name="file.txt",
            )


# ============================================================================
# Test: List Files
# ============================================================================


class TestMinIOStorageServiceListFiles:
    """Test cases for listing files."""

    def test_list_files_success(
        self,
        mock_minio_client,
    ):
        """Test listing files successfully."""
        # Mock list objects
        mock_obj1 = MagicMock()
        mock_obj1.object_name = "file1.txt"
        mock_obj1.size = 100
        mock_obj1.last_modified = datetime(2025, 1, 1)
        mock_obj1.etag = "etag1"

        mock_obj2 = MagicMock()
        mock_obj2.object_name = "file2.txt"
        mock_obj2.size = 200
        mock_obj2.last_modified = datetime(2025, 1, 2)
        mock_obj2.etag = "etag2"

        mock_minio_client.list_objects.return_value = [mock_obj1, mock_obj2]

        service = MinIOStorageService()
        service.client = mock_minio_client

        # List files
        files = service.list_files(
            bucket="wisqu-uploads",
            prefix="test/",
            recursive=True,
        )

        # Verify files
        assert len(files) == 2
        assert files[0]["name"] == "file1.txt"
        assert files[0]["size"] == 100
        assert files[1]["name"] == "file2.txt"
        assert files[1]["size"] == 200

    def test_list_files_raises_error_when_disabled(self):
        """Test list_files raises error when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        with pytest.raises(ValueError, match="MinIO is not enabled"):
            service.list_files(bucket="wisqu-uploads")


# ============================================================================
# Test: Helper Methods
# ============================================================================


class TestMinIOStorageServiceHelperMethods:
    """Test cases for helper methods."""

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_rag_document(
        self,
        mock_settings,
        mock_minio_client,
        sample_file_data,
    ):
        """Test uploading RAG document."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-documents")
        mock_settings.storage_max_file_size_mb = 100
        mock_settings.minio_bucket_documents = "wisqu-documents"
        mock_settings.minio_bucket_uploads = "wisqu-uploads"

        service = MinIOStorageService()
        service.client = mock_minio_client
        service.get_presigned_url = MagicMock(return_value="https://presigned-url.example.com")

        mock_result = MagicMock()
        mock_result.etag = "etag123"
        mock_minio_client.put_object.return_value = mock_result

        # Upload RAG document
        result = await service.upload_rag_document(
            file_data=sample_file_data,
            filename="document.pdf",
            content_type="application/pdf",
            metadata={"category": "aqidah"},
        )

        # Verify upload was called with correct parameters
        call_args = mock_minio_client.put_object.call_args
        metadata = call_args[1]["metadata"]
        assert metadata["purpose"] == "rag_corpus"
        assert metadata["original_filename"] == "document.pdf"
        assert metadata["category"] == "aqidah"

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_generated_image(
        self,
        mock_settings,
        mock_minio_client,
        sample_user_id,
    ):
        """Test uploading AI-generated image."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-images")
        mock_settings.storage_max_file_size_mb = 100
        mock_settings.storage_max_image_size_mb = 10
        mock_settings.minio_bucket_images = "wisqu-images"
        mock_settings.minio_bucket_uploads = "wisqu-uploads"
        mock_settings.minio_public_url = "https://cdn.example.com"

        service = MinIOStorageService()
        service.client = mock_minio_client

        mock_result = MagicMock()
        mock_result.etag = "etag123"
        mock_minio_client.put_object.return_value = mock_result

        image_data = b"fake image data"

        # Upload generated image
        result = await service.upload_generated_image(
            file_data=image_data,
            prompt="A beautiful sunset",
            model="dall-e-3",
            user_id=sample_user_id,
            conversation_id=uuid4(),
        )

        # Verify metadata
        call_args = mock_minio_client.put_object.call_args
        metadata = call_args[1]["metadata"]
        assert metadata["purpose"] == "generated_image"
        assert metadata["model"] == "dall-e-3"
        assert metadata["prompt"] == "A beautiful sunset"
        assert "public_url" in result

    @pytest.mark.asyncio
    @patch("app.services.minio_storage_service.settings")
    async def test_upload_ticket_attachment(
        self,
        mock_settings,
        mock_minio_client,
        sample_file_data,
        sample_user_id,
    ):
        """Test uploading ticket attachment."""
        mock_settings.environment = "dev"
        mock_settings.get_bucket_name = MagicMock(return_value="dev-wisqu-uploads")
        mock_settings.storage_max_file_size_mb = 100
        mock_settings.minio_bucket_uploads = "wisqu-uploads"

        service = MinIOStorageService()
        service.client = mock_minio_client
        service.get_presigned_url = MagicMock(return_value="https://presigned-url.example.com")

        mock_result = MagicMock()
        mock_result.etag = "etag123"
        mock_minio_client.put_object.return_value = mock_result

        ticket_id = uuid4()

        # Upload ticket attachment
        result = await service.upload_ticket_attachment(
            file_data=sample_file_data,
            ticket_id=ticket_id,
            user_id=sample_user_id,
            filename="screenshot.png",
            content_type="image/png",
        )

        # Verify metadata
        call_args = mock_minio_client.put_object.call_args
        assert call_args[0][1].startswith(f"tickets/{ticket_id}/")
        metadata = call_args[1]["metadata"]
        assert metadata["purpose"] == "ticket_attachment"
        assert metadata["ticket_id"] == str(ticket_id)


# ============================================================================
# Test: Health Check
# ============================================================================


class TestMinIOStorageServiceHealthCheck:
    """Test cases for health check."""

    def test_health_check_healthy(
        self,
        mock_minio_client,
    ):
        """Test health check when service is healthy."""
        mock_minio_client.list_buckets.return_value = []

        service = MinIOStorageService()
        service.client = mock_minio_client

        # Patch settings for health check
        with patch("app.services.minio_storage_service.settings") as mock_settings:
            mock_settings.minio_endpoint = "minio.example.com"
            mock_settings.minio_secure = False

            health = service.health_check()

        # Verify health status
        assert health["healthy"] is True
        assert health["endpoint"] == "minio.example.com"
        assert health["secure"] is False

    def test_health_check_unhealthy_when_disabled(self):
        """Test health check when MinIO is disabled."""
        service = MinIOStorageService()
        service.client = None

        health = service.health_check()

        # Verify unhealthy status
        assert health["healthy"] is False
        assert health["error"] == "MinIO is not enabled"

    def test_health_check_unhealthy_on_error(
        self,
        mock_minio_client,
    ):
        """Test health check when connection fails."""
        mock_minio_client.list_buckets.side_effect = Exception("Connection failed")

        service = MinIOStorageService()
        service.client = mock_minio_client

        with patch("app.services.minio_storage_service.settings") as mock_settings:
            mock_settings.minio_endpoint = "minio.example.com"
            mock_settings.minio_secure = False

            health = service.health_check()

        # Verify unhealthy status
        assert health["healthy"] is False
        assert health["error"] == "Connection failed"
