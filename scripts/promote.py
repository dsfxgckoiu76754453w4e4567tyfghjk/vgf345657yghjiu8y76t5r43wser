#!/usr/bin/env python3
"""
Environment Promotion CLI Tool.

Manage data promotions between dev, stage, and prod environments.

Usage:
    python scripts/promote.py preview stored_files dev stage
    python scripts/promote.py execute stored_files dev stage --user-id <uuid>
    python scripts/promote.py rollback <promotion-id> --user-id <uuid>
    python scripts/promote.py scan-test-data dev stored_files
    python scripts/promote.py approve stored_files <item-id>
"""

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.storage import StoredFile
from app.services.promotion_service import EnvironmentPromotionService
from app.utils.test_data_detector import TestDataDetector

settings = get_settings()
logger = get_logger(__name__)

# Model mapping
MODEL_MAP = {
    "stored_files": StoredFile,
    # Add more models as they're updated with EnvironmentPromotionMixin
    # "users": User,
    # "conversations": Conversation,
}


def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}", file=sys.stderr)


def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


async def get_db_session() -> AsyncSession:
    """Create async database session."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


async def preview_promotion(
    model_name: str,
    source_env: str,
    target_env: str,
):
    """Preview promotion."""
    print_info(f"Previewing promotion: {model_name} from {source_env} to {target_env}")

    # Get model
    model_class = MODEL_MAP.get(model_name)
    if not model_class:
        print_error(f"Unknown model: {model_name}. Available: {list(MODEL_MAP.keys())}")
        return

    # Create service and preview
    async for db in get_db_session():
        service = EnvironmentPromotionService(db)

        preview = await service.preview_promotion(
            model_class=model_class,
            source_env=source_env,
            target_env=target_env,
        )

        # Display results
        print("\n" + "=" * 60)
        print(f"PROMOTION PREVIEW")
        print("=" * 60)
        print(f"Source: {preview.source_env}")
        print(f"Target: {preview.target_env}")
        print(f"Items: {preview.total_count}")

        if preview.total_size_bytes > 0:
            size_mb = preview.total_size_bytes / (1024 * 1024)
            print(f"Total Size: {size_mb:.2f} MB")

        print()

        # Errors
        if preview.errors:
            print_error("Errors:")
            for error in preview.errors:
                print(f"  - {error}")
            print()

        # Warnings
        if preview.warnings:
            print_warning("Warnings:")
            for warning in preview.warnings:
                print(f"  - {warning}")
            print()

        # Items
        if preview.items_to_promote:
            print_info("Items to promote:")
            for i, item in enumerate(preview.items_to_promote[:10], 1):
                print(f"  {i}. ID: {item['id']}")
                if "filename" in item:
                    print(f"     File: {item['filename']}")
                if "size_bytes" in item:
                    size_kb = item["size_bytes"] / 1024
                    print(f"     Size: {size_kb:.2f} KB")

            if len(preview.items_to_promote) > 10:
                print(f"  ... and {len(preview.items_to_promote) - 10} more")
            print()

        # Status
        if preview.to_dict()["is_valid"]:
            print_success("Preview is valid. Ready to execute.")
        else:
            print_error("Preview has errors. Fix them before executing.")

        print("=" * 60)


async def execute_promotion(
    model_name: str,
    source_env: str,
    target_env: str,
    user_id: str,
    reason: str = None,
    item_ids: list[str] = None,
):
    """Execute promotion."""
    print_info(f"Executing promotion: {model_name} from {source_env} to {target_env}")

    # Get model
    model_class = MODEL_MAP.get(model_name)
    if not model_class:
        print_error(f"Unknown model: {model_name}. Available: {list(MODEL_MAP.keys())}")
        return

    # Parse user ID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        print_error(f"Invalid user ID: {user_id}")
        return

    # Parse item IDs
    item_uuids = None
    if item_ids:
        try:
            item_uuids = [UUID(id) for id in item_ids]
        except ValueError as e:
            print_error(f"Invalid item ID: {e}")
            return

    # Create service and execute
    async for db in get_db_session():
        service = EnvironmentPromotionService(db)

        try:
            result = await service.execute_promotion(
                model_class=model_class,
                source_env=source_env,
                target_env=target_env,
                promoted_by_user_id=user_uuid,
                reason=reason,
                item_ids=item_uuids,
            )

            # Display results
            print("\n" + "=" * 60)
            print(f"PROMOTION RESULT")
            print("=" * 60)
            print(f"Promotion ID: {result.promotion_id}")
            print(f"Success Count: {result.success_count}")
            print(f"Error Count: {result.error_count}")
            print(f"Duration: {result.duration_seconds}s")
            print()

            if result.errors:
                print_error("Errors:")
                for item_id, error in result.errors.items():
                    print(f"  - {item_id}: {error}")
                print()

            if result.error_count == 0:
                print_success("Promotion completed successfully!")
            else:
                print_warning("Promotion completed with errors.")

            print("=" * 60)

        except Exception as e:
            print_error(f"Promotion failed: {e}")


async def rollback_promotion(
    promotion_id: str,
    user_id: str,
):
    """Rollback promotion."""
    print_info(f"Rolling back promotion: {promotion_id}")

    # Parse IDs
    try:
        promotion_uuid = UUID(promotion_id)
        user_uuid = UUID(user_id)
    except ValueError as e:
        print_error(f"Invalid UUID: {e}")
        return

    # Create service and rollback
    async for db in get_db_session():
        service = EnvironmentPromotionService(db)

        try:
            success = await service.rollback_promotion(
                promotion_id=promotion_uuid,
                rolled_back_by_user_id=user_uuid,
            )

            if success:
                print_success("Promotion rolled back successfully!")
            else:
                print_error("Rollback failed")

        except Exception as e:
            print_error(f"Rollback failed: {e}")


async def scan_test_data(
    environment: str,
    model_name: str,
):
    """Scan for test data."""
    print_info(f"Scanning for test data: {model_name} in {environment}")

    # Get model
    model_class = MODEL_MAP.get(model_name)
    if not model_class:
        print_error(f"Unknown model: {model_name}. Available: {list(MODEL_MAP.keys())}")
        return

    # Create session and scan
    async for db in get_db_session():
        result = await TestDataDetector.scan_and_mark_test_data(
            db=db,
            model_class=model_class,
            environment=environment,
        )

        # Display results
        print("\n" + "=" * 60)
        print(f"TEST DATA SCAN RESULTS")
        print("=" * 60)
        print(f"Model: {result['model']}")
        print(f"Environment: {result['environment']}")
        print(f"Scanned: {result['scanned']}")
        print(f"Marked as Test: {result['marked_as_test']}")
        print(f"Already Marked: {result['already_marked']}")
        print(f"Errors: {result['errors']}")
        print("=" * 60)

        if result['marked_as_test'] > 0:
            print_success(f"Marked {result['marked_as_test']} items as test data")


async def approve_item(
    model_name: str,
    item_id: str,
):
    """Approve item for promotion."""
    print_info(f"Approving item: {item_id}")

    # Get model
    model_class = MODEL_MAP.get(model_name)
    if not model_class:
        print_error(f"Unknown model: {model_name}. Available: {list(MODEL_MAP.keys())}")
        return

    # Parse item ID
    try:
        item_uuid = UUID(item_id)
    except ValueError:
        print_error(f"Invalid item ID: {item_id}")
        return

    # Create repository and approve
    async for db in get_db_session():
        from app.repositories.base import EnvironmentAwareRepository

        repo = EnvironmentAwareRepository(db, model_class)
        item = await repo.approve_for_promotion(item_uuid)

        if item:
            print_success(f"Item {item_id} approved for promotion")
        else:
            print_error(f"Failed to approve item {item_id}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Environment Promotion CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview promotion
  python scripts/promote.py preview stored_files dev stage

  # Execute promotion
  python scripts/promote.py execute stored_files dev stage \\
      --user-id 12345678-1234-1234-1234-123456789abc \\
      --reason "Deploy approved RAG documents"

  # Rollback promotion
  python scripts/promote.py rollback 87654321-4321-4321-4321-cba987654321 \\
      --user-id 12345678-1234-1234-1234-123456789abc

  # Scan for test data
  python scripts/promote.py scan-test-data dev stored_files

  # Approve item for promotion
  python scripts/promote.py approve stored_files 11111111-2222-3333-4444-555555555555
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Preview command
    preview_parser = subparsers.add_parser("preview", help="Preview promotion")
    preview_parser.add_argument("model", choices=list(MODEL_MAP.keys()), help="Model to promote")
    preview_parser.add_argument("source_env", help="Source environment")
    preview_parser.add_argument("target_env", help="Target environment")

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute promotion")
    execute_parser.add_argument("model", choices=list(MODEL_MAP.keys()), help="Model to promote")
    execute_parser.add_argument("source_env", help="Source environment")
    execute_parser.add_argument("target_env", help="Target environment")
    execute_parser.add_argument("--user-id", required=True, help="User ID executing promotion")
    execute_parser.add_argument("--reason", help="Reason for promotion")
    execute_parser.add_argument("--item-ids", nargs="+", help="Specific item IDs to promote")

    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback promotion")
    rollback_parser.add_argument("promotion_id", help="Promotion ID to rollback")
    rollback_parser.add_argument("--user-id", required=True, help="User ID executing rollback")

    # Scan test data command
    scan_parser = subparsers.add_parser("scan-test-data", help="Scan for test data")
    scan_parser.add_argument("environment", help="Environment to scan")
    scan_parser.add_argument("model", choices=list(MODEL_MAP.keys()), help="Model to scan")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve item for promotion")
    approve_parser.add_argument("model", choices=list(MODEL_MAP.keys()), help="Model type")
    approve_parser.add_argument("item_id", help="Item ID to approve")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    try:
        if args.command == "preview":
            asyncio.run(preview_promotion(args.model, args.source_env, args.target_env))
        elif args.command == "execute":
            asyncio.run(
                execute_promotion(
                    args.model,
                    args.source_env,
                    args.target_env,
                    args.user_id,
                    args.reason,
                    args.item_ids,
                )
            )
        elif args.command == "rollback":
            asyncio.run(rollback_promotion(args.promotion_id, args.user_id))
        elif args.command == "scan-test-data":
            asyncio.run(scan_test_data(args.environment, args.model))
        elif args.command == "approve":
            asyncio.run(approve_item(args.model, args.item_id))
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
