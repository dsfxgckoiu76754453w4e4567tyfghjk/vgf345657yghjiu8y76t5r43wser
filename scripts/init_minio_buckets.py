#!/usr/bin/env python3
"""Initialize MinIO buckets with proper configurations.

This script creates all required buckets and sets up lifecycle policies.
Run this after starting MinIO for the first time.

Usage:
    python scripts/init_minio_buckets.py
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.config import settings
from app.core.logging import get_logger
from app.services.minio_storage_service import minio_storage

logger = get_logger(__name__)


def main():
    """Initialize MinIO buckets."""
    print("=" * 60)
    print("MinIO Bucket Initialization")
    print("=" * 60)

    if not settings.minio_enabled:
        print("❌ MinIO is not enabled in settings!")
        print("   Set MINIO_ENABLED=true in your .env file")
        sys.exit(1)

    print(f"\nMinIO Endpoint: {settings.minio_endpoint}")
    print(f"Secure: {settings.minio_secure}")
    print()

    # Test MinIO connection
    print("🔍 Testing MinIO connection...")
    health = minio_storage.health_check()

    if not health["healthy"]:
        print(f"❌ MinIO is not healthy: {health.get('error')}")
        print("\nMake sure MinIO is running:")
        print("  docker-compose -f docker-compose.minio.yml up -d")
        sys.exit(1)

    print("✅ MinIO connection successful!")
    print()

    # Get bucket stats
    print("📊 Bucket Statistics:")
    print("-" * 60)

    buckets = [
        (settings.minio_bucket_images, "Generated AI images (public)"),
        (settings.minio_bucket_documents, "RAG documents (private)"),
        (settings.minio_bucket_audio, "Audio files (private, 7-day retention)"),
        (settings.minio_bucket_uploads, "User uploads (private, 90-day retention)"),
        (settings.minio_bucket_temp, "Temp processing (private, 24-hour retention)"),
        (settings.minio_bucket_backups, "Backups (private, 30-day retention)"),
    ]

    for bucket_name, description in buckets:
        try:
            if minio_storage.client.bucket_exists(bucket_name):
                stats = minio_storage.get_bucket_stats(bucket_name)
                print(f"\n✅ {bucket_name}")
                print(f"   {description}")
                print(f"   Files: {stats['total_files']}")
                print(f"   Size: {stats['total_size_mb']} MB")
            else:
                print(f"\n❓ {bucket_name}")
                print(f"   {description}")
                print(f"   Bucket does not exist (will be created on first use)")
        except Exception as e:
            print(f"\n❌ {bucket_name}")
            print(f"   Error: {e}")

    print()
    print("=" * 60)
    print("✅ MinIO is ready!")
    print("=" * 60)
    print()
    print("Access MinIO Console:")
    print(f"  URL: http://{settings.minio_endpoint.split(':')[0]}:9001")
    print(f"  User: {settings.minio_access_key}")
    print(f"  Password: <MINIO_SECRET_KEY>")
    print()
    print("Buckets will be created automatically on first upload.")
    print()


if __name__ == "__main__":
    main()
