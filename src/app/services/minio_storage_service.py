"""MinIO object storage service for file management."""

import io
from datetime import timedelta
from typing import BinaryIO, Literal, Optional
from uuid import UUID

from minio import Minio
from minio.error import S3Error
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MinIOStorageService:
    """
    MinIO object storage service.

    Provides file upload, download, delete, and management operations
    with automatic bucket creation, lifecycle policies, and quota management.

    Features:
    - Multi-bucket support (images, documents, audio, uploads, temp, backups)
    - Pre-signed URLs for secure temporary access
    - Automatic lifecycle policies (auto-delete temp files)
    - User quota tracking
    - File type validation
    - Public/private bucket management
    """

    def __init__(self):
        """Initialize MinIO client and buckets."""
        if not settings.minio_enabled:
            logger.warning("minio_disabled")
            self.client = None
            return

        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )

            # Initialize buckets
            self._initialize_buckets()

            logger.info(
                "minio_service_initialized",
                endpoint=settings.minio_endpoint,
                secure=settings.minio_secure,
            )

        except Exception as e:
            logger.error("minio_initialization_failed", error=str(e))
            raise

    def _get_env_bucket_name(self, base_bucket: str) -> str:
        """
        Get environment-prefixed bucket name.

        Examples:
            dev:   wisqu-images  → dev-wisqu-images
            stage: wisqu-images  → stage-wisqu-images
            prod:  wisqu-images  → prod-wisqu-images
        """
        return settings.get_bucket_name(base_bucket)

    def _initialize_buckets(self):
        """Create buckets if they don't exist and set policies."""
        # Base bucket configurations (without environment prefix)
        base_buckets = {
            settings.minio_bucket_images: {
                "public": True,
                "lifecycle_days": None,  # AI-generated images (keep forever)
            },
            settings.minio_bucket_documents: {
                "public": False,
                "lifecycle_days": None,  # RAG corpus, user PDFs (keep forever)
            },
            settings.minio_bucket_audio_resources: {
                "public": True,
                "lifecycle_days": None,  # Quran, Mafatih, Duas (keep forever, public)
            },
            settings.minio_bucket_audio_user: {
                "public": False,
                "lifecycle_days": 30,  # User voice messages (30-day retention)
            },
            settings.minio_bucket_audio_transcripts: {
                "public": False,
                "lifecycle_days": 7,  # ASR processed audio (7-day retention)
            },
            settings.minio_bucket_uploads: {
                "public": False,
                "lifecycle_days": 90,  # General uploads, ticket attachments (90-day retention)
            },
            settings.minio_bucket_temp: {
                "public": False,
                "lifecycle_days": 1,  # Temporary processing (24-hour retention)
            },
            settings.minio_bucket_backups: {
                "public": False,
                "lifecycle_days": 30,  # System backups (30-day retention)
            },
        }

        # Create environment-prefixed buckets
        for base_bucket, config in base_buckets.items():
            # Add environment prefix
            bucket_name = self._get_env_bucket_name(base_bucket)

            try:
                # Create bucket if it doesn't exist
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(
                        "bucket_created",
                        bucket_name=bucket_name,
                        base_bucket=base_bucket,
                        environment=settings.environment
                    )

                # Set lifecycle policy if specified
                if config["lifecycle_days"]:
                    self._set_lifecycle_policy(bucket_name, config["lifecycle_days"])

                # Set public policy if needed
                if config["public"]:
                    self._set_public_policy(bucket_name)

            except S3Error as e:
                logger.error(
                    "bucket_initialization_failed",
                    bucket_name=bucket_name,
                    error=str(e),
                )

    def _set_lifecycle_policy(self, bucket_name: str, days: int):
        """Set lifecycle policy to auto-delete files after N days."""
        try:
            lifecycle_config = LifecycleConfig(
                [
                    Rule(
                        rule_id=f"delete-after-{days}-days",
                        rule_filter=Filter(),
                        expiration=Expiration(days=days),
                        rule_status="Enabled",
                    )
                ]
            )
            self.client.set_bucket_lifecycle(bucket_name, lifecycle_config)
            logger.info(
                "lifecycle_policy_set",
                bucket_name=bucket_name,
                days=days,
            )
        except S3Error as e:
            logger.warning(
                "lifecycle_policy_failed",
                bucket_name=bucket_name,
                error=str(e),
            )

    def _set_public_policy(self, bucket_name: str):
        """Set bucket policy to allow public read access."""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                }
            ],
        }

        try:
            import json
            self.client.set_bucket_policy(bucket_name, json.dumps(policy))
            logger.info("public_policy_set", bucket_name=bucket_name)
        except S3Error as e:
            logger.warning(
                "public_policy_failed",
                bucket_name=bucket_name,
                error=str(e),
            )

    async def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
        user_id: Optional[UUID] = None,
    ) -> dict[str, str]:
        """
        Upload file to MinIO with environment-specific bucket.

        Args:
            bucket: Base bucket name (use settings.minio_bucket_*)
                   Will be automatically prefixed with environment
            object_name: Object path/name in bucket
            file_data: File data as bytes or file-like object
            content_type: MIME type
            metadata: Optional metadata dict
            user_id: Optional user ID for tracking

        Returns:
            dict with url, bucket, object_name, size

        Raises:
            ValueError: If MinIO is disabled or file size exceeds limit
            S3Error: If upload fails

        Note:
            Bucket name is automatically prefixed with environment.
            Example: "wisqu-images" becomes "dev-wisqu-images" in dev env
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        # Add environment prefix to bucket name
        env_bucket = self._get_env_bucket_name(bucket)

        try:
            # Convert bytes to BytesIO if needed
            if isinstance(file_data, bytes):
                file_obj = io.BytesIO(file_data)
                file_size = len(file_data)
            else:
                file_obj = file_data
                file_obj.seek(0, 2)  # Seek to end
                file_size = file_obj.tell()
                file_obj.seek(0)  # Seek back to start

            # Check file size limits
            max_size_mb = settings.storage_max_file_size_mb
            if bucket == settings.minio_bucket_images:
                max_size_mb = settings.storage_max_image_size_mb
            elif bucket == settings.minio_bucket_audio:
                max_size_mb = settings.storage_max_audio_size_mb
            elif bucket == settings.minio_bucket_documents:
                max_size_mb = settings.storage_max_document_size_mb

            if file_size > max_size_mb * 1024 * 1024:
                raise ValueError(
                    f"File size {file_size / (1024 * 1024):.2f}MB exceeds limit of {max_size_mb}MB"
                )

            # Add user_id to metadata if provided
            final_metadata = metadata or {}
            if user_id:
                final_metadata["user_id"] = str(user_id)

            # Add environment tag to metadata
            final_metadata["environment"] = settings.environment

            # Upload to MinIO (using environment-prefixed bucket)
            result = self.client.put_object(
                env_bucket,
                object_name,
                file_obj,
                length=file_size,
                content_type=content_type,
                metadata=final_metadata,
            )

            # Generate URL
            if bucket == settings.minio_bucket_images:
                # Public URL for images (use env bucket)
                url = f"{settings.minio_public_url}/{env_bucket}/{object_name}"
            else:
                # Pre-signed URL for private files (1 hour expiry)
                url = self.get_presigned_url(bucket, object_name, expires=3600)

            logger.info(
                "file_uploaded",
                bucket=env_bucket,
                base_bucket=bucket,
                environment=settings.environment,
                object_name=object_name,
                size_bytes=file_size,
                user_id=str(user_id) if user_id else None,
            )

            return {
                "url": url,
                "bucket": bucket,  # Return base bucket name for consistency
                "env_bucket": env_bucket,  # Also return environment bucket
                "object_name": object_name,
                "size": file_size,
                "etag": result.etag,
                "environment": settings.environment,
            }

        except S3Error as e:
            logger.error(
                "file_upload_failed",
                bucket=env_bucket,
                base_bucket=bucket,
                object_name=object_name,
                error=str(e),
            )
            raise

    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires: int = 3600,
        method: Literal["GET", "PUT"] = "GET",
    ) -> str:
        """
        Generate pre-signed URL for temporary access.

        Args:
            bucket: Base bucket name (will be environment-prefixed)
            object_name: Object path/name
            expires: Expiration time in seconds (default 1 hour)
            method: HTTP method (GET for download, PUT for upload)

        Returns:
            Pre-signed URL string
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        # Add environment prefix
        env_bucket = self._get_env_bucket_name(bucket)

        try:
            if method == "GET":
                url = self.client.presigned_get_object(
                    env_bucket,
                    object_name,
                    expires=timedelta(seconds=expires),
                )
            else:  # PUT
                url = self.client.presigned_put_object(
                    bucket,
                    object_name,
                    expires=timedelta(seconds=expires),
                )

            return url

        except S3Error as e:
            logger.error(
                "presigned_url_generation_failed",
                bucket=bucket,
                object_name=object_name,
                error=str(e),
            )
            raise

    async def download_file(self, bucket: str, object_name: str) -> bytes:
        """
        Download file from MinIO.

        Args:
            bucket: Base bucket name (will be environment-prefixed)
            object_name: Object path/name

        Returns:
            File data as bytes
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        # Add environment prefix
        env_bucket = self._get_env_bucket_name(bucket)

        try:
            response = self.client.get_object(env_bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()

            logger.info(
                "file_downloaded",
                bucket=env_bucket,
                base_bucket=bucket,
                object_name=object_name,
                size_bytes=len(data),
            )

            return data

        except S3Error as e:
            logger.error(
                "file_download_failed",
                bucket=env_bucket,
                base_bucket=bucket,
                object_name=object_name,
                error=str(e),
            )
            raise

    async def delete_file(self, bucket: str, object_name: str) -> bool:
        """
        Delete file from MinIO.

        Args:
            bucket: Base bucket name (will be environment-prefixed)
            object_name: Object path/name

        Returns:
            True if deleted successfully
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        # Add environment prefix
        env_bucket = self._get_env_bucket_name(bucket)

        try:
            self.client.remove_object(env_bucket, object_name)

            logger.info(
                "file_deleted",
                bucket=env_bucket,
                base_bucket=bucket,
                object_name=object_name,
            )

            return True

        except S3Error as e:
            logger.error(
                "file_deletion_failed",
                bucket=env_bucket,
                base_bucket=bucket,
                object_name=object_name,
                error=str(e),
            )
            return False

    def file_exists(self, bucket: str, object_name: str) -> bool:
        """
        Check if file exists in MinIO.

        Args:
            bucket: Bucket name
            object_name: Object path/name

        Returns:
            True if file exists
        """
        if not self.client:
            return False

        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False

    def get_file_metadata(self, bucket: str, object_name: str) -> dict:
        """
        Get file metadata from MinIO.

        Args:
            bucket: Bucket name
            object_name: Object path/name

        Returns:
            Metadata dictionary
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        try:
            stat = self.client.stat_object(bucket, object_name)

            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
            }

        except S3Error as e:
            logger.error(
                "get_metadata_failed",
                bucket=bucket,
                object_name=object_name,
                error=str(e),
            )
            raise

    def list_files(
        self,
        bucket: str,
        prefix: str = "",
        recursive: bool = False,
    ) -> list[dict]:
        """
        List files in bucket.

        Args:
            bucket: Bucket name
            prefix: Filter by prefix (folder path)
            recursive: List recursively

        Returns:
            List of file info dicts
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        try:
            objects = self.client.list_objects(
                bucket,
                prefix=prefix,
                recursive=recursive,
            )

            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                })

            return files

        except S3Error as e:
            logger.error(
                "list_files_failed",
                bucket=bucket,
                prefix=prefix,
                error=str(e),
            )
            raise

    def get_bucket_stats(self, bucket: str) -> dict:
        """
        Get bucket statistics.

        Args:
            bucket: Bucket name

        Returns:
            Statistics dictionary
        """
        if not self.client:
            raise ValueError("MinIO is not enabled")

        try:
            total_size = 0
            total_files = 0

            objects = self.client.list_objects(bucket, recursive=True)
            for obj in objects:
                total_size += obj.size
                total_files += 1

            return {
                "bucket": bucket,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }

        except S3Error as e:
            logger.error(
                "get_bucket_stats_failed",
                bucket=bucket,
                error=str(e),
            )
            raise

    # ========================================================================
    # Helper Methods for Common Storage Patterns
    # ========================================================================

    async def upload_rag_document(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str = "application/pdf",
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Upload document to RAG corpus.

        Args:
            file_data: File data (bytes or file-like object)
            filename: Original filename
            content_type: MIME type
            metadata: Optional metadata (e.g., document category, tags)

        Returns:
            Upload result with URL and object info
        """
        final_metadata = metadata or {}
        final_metadata.update({
            "purpose": "rag_corpus",
            "original_filename": filename,
        })

        return await self.upload_file(
            bucket=settings.minio_bucket_documents,
            object_name=f"rag/{filename}",
            file_data=file_data,
            content_type=content_type,
            metadata=final_metadata,
        )

    async def upload_islamic_audio(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        audio_category: Literal["quran", "hadith", "dua", "mafatih", "ziyarat", "lecture"],
        reciter_name: Optional[str] = None,
        language: str = "ar",
        surah: Optional[int] = None,
        ayah_start: Optional[int] = None,
        ayah_end: Optional[int] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Upload Islamic audio resource (Quran, Duas, Mafatih, etc.).

        Args:
            file_data: Audio file data
            filename: Original filename
            audio_category: Type of audio (quran, dua, mafatih, etc.)
            reciter_name: Name of reciter/speaker
            language: Audio language (ar, fa, en, etc.)
            surah: Quran chapter number (1-114) if applicable
            ayah_start: Starting verse number if applicable
            ayah_end: Ending verse number if applicable
            metadata: Additional metadata

        Returns:
            Upload result with public URL
        """
        final_metadata = metadata or {}
        final_metadata.update({
            "purpose": "islamic_resource",
            "audio_category": audio_category,
            "language": language,
        })

        if reciter_name:
            final_metadata["reciter_name"] = reciter_name
        if surah:
            final_metadata["quran_surah"] = str(surah)
        if ayah_start:
            final_metadata["quran_ayah_start"] = str(ayah_start)
        if ayah_end:
            final_metadata["quran_ayah_end"] = str(ayah_end)

        # Organize by category
        object_name = f"{audio_category}/{filename}"

        result = await self.upload_file(
            bucket=settings.minio_bucket_audio_resources,
            object_name=object_name,
            file_data=file_data,
            content_type="audio/mpeg",  # Default to MP3
            metadata=final_metadata,
        )

        # Generate public URL (bucket is public)
        result["public_url"] = f"{settings.minio_public_url}/{settings.minio_bucket_audio_resources}/{object_name}"

        return result

    async def upload_user_voice_message(
        self,
        file_data: bytes | BinaryIO,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        should_transcribe: bool = True,
    ) -> dict[str, any]:
        """
        Upload user voice message and optionally transcribe it.

        Args:
            file_data: Audio file data
            user_id: User ID
            conversation_id: Optional conversation ID
            should_transcribe: Whether to transcribe the audio

        Returns:
            Upload result with optional transcript
        """
        import uuid
        from datetime import datetime

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_name = f"user_{user_id}/{timestamp}_{uuid.uuid4().hex[:8]}.mp3"

        metadata = {
            "purpose": "user_voice_message",
            "user_id": str(user_id),
        }
        if conversation_id:
            metadata["conversation_id"] = str(conversation_id)

        # Upload audio file
        upload_result = await self.upload_file(
            bucket=settings.minio_bucket_audio_user,
            object_name=object_name,
            file_data=file_data,
            content_type="audio/mpeg",
            metadata=metadata,
            user_id=user_id,
        )

        result = {**upload_result}

        # Optionally transcribe
        if should_transcribe:
            try:
                from app.services.asr_service import asr_service

                # Get audio data if we uploaded bytes
                if isinstance(file_data, bytes):
                    audio_data = file_data
                else:
                    file_data.seek(0)
                    audio_data = file_data.read()

                # Transcribe
                transcript_result = await asr_service.transcribe_audio(
                    audio_data=audio_data,
                    audio_format="mp3",
                    language="fa",  # Default to Persian, can be detected
                )

                result["transcript"] = transcript_result

                logger.info(
                    "user_voice_transcribed",
                    user_id=str(user_id),
                    text_length=len(transcript_result["text"]),
                )

            except Exception as e:
                logger.error(
                    "voice_transcription_failed",
                    user_id=str(user_id),
                    error=str(e),
                )
                result["transcript_error"] = str(e)

        return result

    async def upload_ticket_attachment(
        self,
        file_data: bytes | BinaryIO,
        ticket_id: UUID,
        user_id: UUID,
        filename: str,
        content_type: str,
    ) -> dict[str, str]:
        """
        Upload ticket attachment file.

        Args:
            file_data: File data
            ticket_id: Ticket ID
            user_id: User ID who uploaded
            filename: Original filename
            content_type: MIME type

        Returns:
            Upload result with access URL
        """
        object_name = f"tickets/{ticket_id}/{filename}"

        metadata = {
            "purpose": "ticket_attachment",
            "ticket_id": str(ticket_id),
            "user_id": str(user_id),
            "original_filename": filename,
        }

        return await self.upload_file(
            bucket=settings.minio_bucket_uploads,
            object_name=object_name,
            file_data=file_data,
            content_type=content_type,
            metadata=metadata,
            user_id=user_id,
        )

    async def upload_generated_image(
        self,
        file_data: bytes | BinaryIO,
        prompt: str,
        model: str,
        user_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
    ) -> dict[str, str]:
        """
        Upload AI-generated image (from DALL-E, Flux, Gemini, etc.).

        Args:
            file_data: Image file data
            prompt: Generation prompt
            model: Model used for generation
            user_id: Optional user ID
            conversation_id: Optional conversation ID

        Returns:
            Upload result with public URL
        """
        import uuid
        from datetime import datetime

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        image_id = uuid.uuid4().hex[:12]
        object_name = f"generated/{timestamp}_{image_id}.png"

        metadata = {
            "purpose": "generated_image",
            "model": model,
            "prompt": prompt[:500],  # Truncate long prompts
        }
        if user_id:
            metadata["user_id"] = str(user_id)
        if conversation_id:
            metadata["conversation_id"] = str(conversation_id)

        result = await self.upload_file(
            bucket=settings.minio_bucket_images,
            object_name=object_name,
            file_data=file_data,
            content_type="image/png",
            metadata=metadata,
            user_id=user_id,
        )

        # Generate public URL (images bucket is public)
        result["public_url"] = f"{settings.minio_public_url}/{settings.minio_bucket_images}/{object_name}"

        return result

    def health_check(self) -> dict:
        """
        Check MinIO health.

        Returns:
            Health status dictionary
        """
        if not self.client:
            return {
                "healthy": False,
                "error": "MinIO is not enabled",
            }

        try:
            # Try to list buckets as health check
            self.client.list_buckets()

            return {
                "healthy": True,
                "endpoint": settings.minio_endpoint,
                "secure": settings.minio_secure,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "endpoint": settings.minio_endpoint,
            }


# Global MinIO service instance
minio_storage = MinIOStorageService()
