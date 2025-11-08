"""File storage API endpoints for MinIO operations."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.storage import StoredFile, UserStorageQuota
from app.models.user import User
from app.services.minio_storage_service import minio_storage

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Schemas
class FileUploadResponse(BaseModel):
    """File upload response."""

    file_id: UUID
    filename: str
    url: str
    bucket: str
    file_type: str
    file_size_bytes: int
    mime_type: str


class FileInfoResponse(BaseModel):
    """File information response."""

    file_id: UUID
    filename: str
    original_filename: str | None
    url: str
    bucket: str
    object_name: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    is_public: bool
    download_count: int
    created_at: str


class StorageQuotaResponse(BaseModel):
    """User storage quota response."""

    user_id: UUID
    quota_limit_mb: float
    total_used_mb: float
    remaining_mb: float
    usage_percentage: float
    is_quota_exceeded: bool
    total_files: int
    breakdown: dict


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    bucket_type: Literal["images", "documents", "audio", "uploads"] = "uploads",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file to MinIO storage.

    - **file**: File to upload
    - **bucket_type**: Bucket type (images, documents, audio, uploads)

    Returns file information including URL for access.
    """
    try:
        # Map bucket type to actual bucket name
        bucket_mapping = {
            "images": settings.minio_bucket_images,
            "documents": settings.minio_bucket_documents,
            "audio": settings.minio_bucket_audio,
            "uploads": settings.minio_bucket_uploads,
        }
        bucket = bucket_mapping[bucket_type]

        # Check user quota
        quota = await _get_or_create_user_quota(current_user.id, db)
        if quota.is_quota_exceeded:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Storage quota exceeded. Used: {quota.usage_percentage:.1f}%",
            )

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Check if this upload would exceed quota
        if quota.total_used_bytes + file_size > quota.quota_limit_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size / (1024 * 1024):.2f}MB would exceed storage quota",
            )

        # Determine file type
        file_type = _determine_file_type(file.content_type or "application/octet-stream")

        # Generate unique object name
        import uuid
        from pathlib import Path

        file_ext = Path(file.filename).suffix
        object_name = f"{current_user.id}/{uuid.uuid4()}{file_ext}"

        # Upload to MinIO
        upload_result = await minio_storage.upload_file(
            bucket=bucket,
            object_name=object_name,
            file_data=file_content,
            content_type=file.content_type or "application/octet-stream",
            metadata={
                "original_filename": file.filename,
                "user_id": str(current_user.id),
            },
            user_id=current_user.id,
        )

        # Save to database
        stored_file = StoredFile(
            user_id=current_user.id,
            filename=file.filename,
            original_filename=file.filename,
            bucket=bucket,
            object_name=object_name,
            file_type=file_type,
            mime_type=file.content_type or "application/octet-stream",
            file_size_bytes=file_size,
            is_public=(bucket == settings.minio_bucket_images),
            access_url=upload_result["url"],
        )

        db.add(stored_file)

        # Update user quota
        quota.total_used_bytes += file_size
        quota.total_files += 1

        # Update type-specific usage
        if file_type == "image":
            quota.images_used_bytes += file_size
        elif file_type == "document":
            quota.documents_used_bytes += file_size
        elif file_type == "audio":
            quota.audio_used_bytes += file_size
        else:
            quota.other_used_bytes += file_size

        await db.commit()
        await db.refresh(stored_file)

        logger.info(
            "file_uploaded",
            user_id=str(current_user.id),
            file_id=str(stored_file.id),
            bucket=bucket,
            file_type=file_type,
            size_bytes=file_size,
        )

        return FileUploadResponse(
            file_id=stored_file.id,
            filename=stored_file.filename,
            url=stored_file.access_url,
            bucket=bucket,
            file_type=file_type,
            file_size_bytes=file_size,
            mime_type=stored_file.mime_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "file_upload_error",
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get file information by ID.

    Returns file metadata and access URL.
    """
    try:
        result = await db.execute(
            select(StoredFile).where(
                StoredFile.id == file_id,
                StoredFile.user_id == current_user.id,
                StoredFile.deleted_at.is_(None),
            )
        )
        stored_file = result.scalar_one_or_none()

        if not stored_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        # Generate fresh pre-signed URL if not public
        if not stored_file.is_public:
            url = minio_storage.get_presigned_url(
                stored_file.bucket,
                stored_file.object_name,
                expires=3600,
            )
        else:
            url = stored_file.access_url

        return FileInfoResponse(
            file_id=stored_file.id,
            filename=stored_file.filename,
            original_filename=stored_file.original_filename,
            url=url,
            bucket=stored_file.bucket,
            object_name=stored_file.object_name,
            file_type=stored_file.file_type,
            mime_type=stored_file.mime_type,
            file_size_bytes=stored_file.file_size_bytes,
            is_public=stored_file.is_public,
            download_count=stored_file.download_count,
            created_at=stored_file.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_file_info_error",
            file_id=str(file_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file information",
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a file from storage.

    Soft deletes from database and removes from MinIO.
    """
    try:
        result = await db.execute(
            select(StoredFile).where(
                StoredFile.id == file_id,
                StoredFile.user_id == current_user.id,
                StoredFile.deleted_at.is_(None),
            )
        )
        stored_file = result.scalar_one_or_none()

        if not stored_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        # Delete from MinIO
        await minio_storage.delete_file(stored_file.bucket, stored_file.object_name)

        # Soft delete from database
        from datetime import datetime
        stored_file.deleted_at = datetime.utcnow()

        # Update user quota
        result = await db.execute(
            select(UserStorageQuota).where(UserStorageQuota.user_id == current_user.id)
        )
        quota = result.scalar_one_or_none()

        if quota:
            quota.total_used_bytes -= stored_file.file_size_bytes
            quota.total_files -= 1

            # Update type-specific usage
            if stored_file.file_type == "image":
                quota.images_used_bytes -= stored_file.file_size_bytes
            elif stored_file.file_type == "document":
                quota.documents_used_bytes -= stored_file.file_size_bytes
            elif stored_file.file_type == "audio":
                quota.audio_used_bytes -= stored_file.file_size_bytes
            else:
                quota.other_used_bytes -= stored_file.file_size_bytes

        await db.commit()

        logger.info(
            "file_deleted",
            user_id=str(current_user.id),
            file_id=str(file_id),
        )

        return {"success": True, "message": "File deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "file_deletion_error",
            file_id=str(file_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )


@router.get("/quota/me", response_model=StorageQuotaResponse)
async def get_my_storage_quota(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's storage quota and usage.

    Returns quota limits, current usage, and breakdown by file type.
    """
    try:
        quota = await _get_or_create_user_quota(current_user.id, db)

        return StorageQuotaResponse(
            user_id=current_user.id,
            quota_limit_mb=round(quota.quota_limit_bytes / (1024 * 1024), 2),
            total_used_mb=round(quota.total_used_bytes / (1024 * 1024), 2),
            remaining_mb=round(quota.remaining_bytes / (1024 * 1024), 2),
            usage_percentage=round(quota.usage_percentage, 2),
            is_quota_exceeded=quota.is_quota_exceeded,
            total_files=quota.total_files,
            breakdown={
                "images_mb": round(quota.images_used_bytes / (1024 * 1024), 2),
                "documents_mb": round(quota.documents_used_bytes / (1024 * 1024), 2),
                "audio_mb": round(quota.audio_used_bytes / (1024 * 1024), 2),
                "other_mb": round(quota.other_used_bytes / (1024 * 1024), 2),
            },
        )

    except Exception as e:
        logger.error(
            "get_quota_error",
            user_id=str(current_user.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage quota",
        )


# Helper functions
async def _get_or_create_user_quota(user_id: UUID, db: AsyncSession) -> UserStorageQuota:
    """Get or create user storage quota."""
    result = await db.execute(
        select(UserStorageQuota).where(UserStorageQuota.user_id == user_id)
    )
    quota = result.scalar_one_or_none()

    if not quota:
        # Determine quota based on user subscription (placeholder logic)
        # TODO: Get actual subscription tier from user
        quota_limit = settings.storage_quota_free * 1024 * 1024  # Convert MB to bytes

        quota = UserStorageQuota(
            user_id=user_id,
            quota_limit_bytes=quota_limit,
        )
        db.add(quota)
        await db.commit()
        await db.refresh(quota)

    return quota


def _determine_file_type(mime_type: str) -> str:
    """Determine file type from MIME type."""
    if mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("audio/"):
        return "audio"
    elif mime_type.startswith("video/"):
        return "video"
    elif mime_type in ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        return "document"
    else:
        return "other"
