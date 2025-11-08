#!/usr/bin/env python3
"""
Environment Cleanup Job.

Scheduled job to clean up old data in dev/stage environments
based on retention policies.

Features:
- Delete old test data based on retention days
- Delete expired test accounts
- Respect environment-specific cleanup settings
- Dry-run mode for safety
- Detailed logging and metrics

Usage:
    # Dry run (preview what will be deleted)
    python scripts/cleanup_environments.py --dry-run

    # Execute cleanup
    python scripts/cleanup_environments.py

    # Cleanup specific environment
    python scripts/cleanup_environments.py --environment dev

    # Cleanup specific model
    python scripts/cleanup_environments.py --model stored_files

Schedule with cron:
    # Run daily at 2 AM
    0 2 * * * cd /path/to/app && python scripts/cleanup_environments.py
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.storage import StoredFile, UserStorageQuota

settings = get_settings()
logger = get_logger(__name__)

# Models to cleanup (add more as they implement EnvironmentPromotionMixin)
CLEANABLE_MODELS = {
    "stored_files": StoredFile,
    "user_storage_quotas": UserStorageQuota,
}


class CleanupStats:
    """Track cleanup statistics."""

    def __init__(self):
        self.models_processed = 0
        self.items_deleted = 0
        self.items_skipped = 0
        self.errors = 0
        self.details: dict[str, dict] = {}

    def add_model_stats(self, model_name: str, deleted: int, skipped: int, errors: int):
        """Add stats for a model."""
        self.models_processed += 1
        self.items_deleted += deleted
        self.items_skipped += skipped
        self.errors += errors

        self.details[model_name] = {
            "deleted": deleted,
            "skipped": skipped,
            "errors": errors,
        }

    def print_summary(self):
        """Print cleanup summary."""
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60)
        print(f"Models Processed: {self.models_processed}")
        print(f"Total Items Deleted: {self.items_deleted}")
        print(f"Total Items Skipped: {self.items_skipped}")
        print(f"Total Errors: {self.errors}")
        print()

        if self.details:
            print("Details by Model:")
            for model_name, stats in self.details.items():
                print(f"  {model_name}:")
                print(f"    Deleted: {stats['deleted']}")
                print(f"    Skipped: {stats['skipped']}")
                print(f"    Errors: {stats['errors']}")
            print()

        print("=" * 60)


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


async def cleanup_model(
    db: AsyncSession,
    model_class: type,
    environment: str,
    retention_days: int,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """
    Clean up old records for a model.

    Args:
        db: Database session
        model_class: Model class to clean
        environment: Environment to clean
        retention_days: Number of days to retain
        dry_run: If True, only preview without deleting

    Returns:
        (deleted_count, skipped_count, error_count)
    """
    model_name = model_class.__name__

    # Check if model has environment support
    if not hasattr(model_class, "environment"):
        logger.warning(
            "model_without_environment_support",
            model=model_name,
        )
        return 0, 0, 1

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    try:
        # Build query for old test data
        query = select(model_class).where(
            model_class.environment == environment,
            model_class.created_at < cutoff_date,
        )

        # Get items to delete
        result = await db.execute(query)
        items = result.scalars().all()

        deleted_count = 0
        skipped_count = 0

        for item in items:
            # Safety checks - never delete production data or promoted items
            if hasattr(item, "is_production") and item.is_production:
                skipped_count += 1
                logger.info(
                    "skipped_production_item",
                    model=model_name,
                    id=str(item.id),
                    reason="Production data cannot be auto-deleted",
                )
                continue

            if hasattr(item, "promotion_status") and item.promotion_status == "promoted":
                skipped_count += 1
                logger.info(
                    "skipped_promoted_item",
                    model=model_name,
                    id=str(item.id),
                    reason="Promoted items should not be deleted",
                )
                continue

            # Preview mode
            if dry_run:
                logger.info(
                    "would_delete_item",
                    model=model_name,
                    id=str(item.id),
                    environment=environment,
                    age_days=(datetime.utcnow() - item.created_at).days,
                )
                deleted_count += 1
                continue

            # Actually delete
            try:
                # Use soft delete if available
                if hasattr(item, "soft_delete"):
                    item.soft_delete()
                else:
                    await db.delete(item)

                deleted_count += 1

                logger.info(
                    "deleted_old_item",
                    model=model_name,
                    id=str(item.id),
                    environment=environment,
                    age_days=(datetime.utcnow() - item.created_at).days,
                )

            except Exception as e:
                logger.error(
                    "delete_failed",
                    model=model_name,
                    id=str(item.id),
                    error=str(e),
                )
                continue

        # Commit if not dry run
        if not dry_run and deleted_count > 0:
            await db.commit()
            logger.info(
                "cleanup_committed",
                model=model_name,
                environment=environment,
                deleted=deleted_count,
            )

        return deleted_count, skipped_count, 0

    except Exception as e:
        logger.error(
            "cleanup_failed",
            model=model_name,
            environment=environment,
            error=str(e),
        )
        return 0, 0, 1


async def cleanup_test_data_only(
    db: AsyncSession,
    model_class: type,
    environment: str,
    min_age_days: int = 7,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """
    Clean up ONLY test data (regardless of retention policy).

    More aggressive cleanup for clearly marked test data.

    Args:
        db: Database session
        model_class: Model class to clean
        environment: Environment to clean
        min_age_days: Minimum age for test data deletion
        dry_run: If True, only preview without deleting

    Returns:
        (deleted_count, skipped_count, error_count)
    """
    model_name = model_class.__name__

    if not hasattr(model_class, "is_test_data"):
        return 0, 0, 0

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=min_age_days)

    try:
        # Build query for test data
        query = select(model_class).where(
            model_class.environment == environment,
            model_class.is_test_data == True,  # noqa: E712
            model_class.created_at < cutoff_date,
        )

        result = await db.execute(query)
        items = result.scalars().all()

        deleted_count = 0

        for item in items:
            if dry_run:
                logger.info(
                    "would_delete_test_data",
                    model=model_name,
                    id=str(item.id),
                    reason=getattr(item, "test_data_reason", "unknown"),
                )
                deleted_count += 1
                continue

            try:
                if hasattr(item, "soft_delete"):
                    item.soft_delete()
                else:
                    await db.delete(item)

                deleted_count += 1

                logger.info(
                    "deleted_test_data",
                    model=model_name,
                    id=str(item.id),
                    reason=getattr(item, "test_data_reason", "unknown"),
                )

            except Exception as e:
                logger.error(
                    "test_data_delete_failed",
                    model=model_name,
                    id=str(item.id),
                    error=str(e),
                )
                continue

        if not dry_run and deleted_count > 0:
            await db.commit()

        return deleted_count, 0, 0

    except Exception as e:
        logger.error(
            "test_data_cleanup_failed",
            model=model_name,
            error=str(e),
        )
        return 0, 0, 1


async def run_cleanup(
    environment: Optional[str] = None,
    model_name: Optional[str] = None,
    dry_run: bool = False,
    test_data_only: bool = False,
):
    """
    Run cleanup job.

    Args:
        environment: Specific environment to clean (default: all non-prod)
        model_name: Specific model to clean (default: all)
        dry_run: Preview mode
        test_data_only: Only delete test data
    """
    stats = CleanupStats()

    # Determine environments to clean
    environments_to_clean = []
    if environment:
        environments_to_clean = [environment]
    else:
        # Clean dev and stage by default, never prod
        environments_to_clean = ["dev", "test", "stage"]

    # Never auto-cleanup prod
    if "prod" in environments_to_clean:
        print("❌ ERROR: Cannot auto-cleanup production environment!")
        print("   Remove prod data manually if absolutely necessary.")
        return

    # Determine models to clean
    models_to_clean = {}
    if model_name:
        if model_name not in CLEANABLE_MODELS:
            print(f"❌ ERROR: Unknown model: {model_name}")
            print(f"   Available: {list(CLEANABLE_MODELS.keys())}")
            return
        models_to_clean = {model_name: CLEANABLE_MODELS[model_name]}
    else:
        models_to_clean = CLEANABLE_MODELS

    # Print header
    mode = "DRY RUN" if dry_run else "EXECUTING"
    print(f"\n{'=' * 60}")
    print(f"ENVIRONMENT CLEANUP - {mode}")
    print(f"{'=' * 60}")
    print(f"Environments: {', '.join(environments_to_clean)}")
    print(f"Models: {', '.join(models_to_clean.keys())}")
    if test_data_only:
        print("Mode: Test Data Only (7+ days old)")
    else:
        print(f"Mode: Full Cleanup (retention: {settings.environment_data_retention_days} days)")
    print(f"{'=' * 60}\n")

    # Run cleanup
    async for db in get_db_session():
        for env in environments_to_clean:
            # Check if cleanup is enabled for this environment
            if not settings.environment_auto_cleanup_enabled and env != "dev":
                print(f"⚠️  Skipping {env}: Auto-cleanup disabled in settings")
                continue

            print(f"\n🔍 Cleaning {env} environment...")

            for name, model_class in models_to_clean.items():
                print(f"  📦 Processing {name}...")

                try:
                    if test_data_only:
                        deleted, skipped, errors = await cleanup_test_data_only(
                            db, model_class, env, min_age_days=7, dry_run=dry_run
                        )
                    else:
                        deleted, skipped, errors = await cleanup_model(
                            db,
                            model_class,
                            env,
                            settings.environment_data_retention_days,
                            dry_run=dry_run,
                        )

                    stats.add_model_stats(f"{env}/{name}", deleted, skipped, errors)

                    print(f"     ✓ Deleted: {deleted}, Skipped: {skipped}, Errors: {errors}")

                except Exception as e:
                    logger.error(
                        "cleanup_error",
                        model=name,
                        environment=env,
                        error=str(e),
                    )
                    stats.add_model_stats(f"{env}/{name}", 0, 0, 1)
                    print(f"     ✗ Error: {e}")

    # Print summary
    stats.print_summary()

    if dry_run:
        print("\n💡 This was a dry run. No data was actually deleted.")
        print("   Run without --dry-run to execute cleanup.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Environment Cleanup Job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview)
  python scripts/cleanup_environments.py --dry-run

  # Execute cleanup
  python scripts/cleanup_environments.py

  # Cleanup specific environment
  python scripts/cleanup_environments.py --environment dev

  # Cleanup specific model
  python scripts/cleanup_environments.py --model stored_files

  # Delete only test data (7+ days old)
  python scripts/cleanup_environments.py --test-data-only

Schedule with cron:
  # Run daily at 2 AM
  0 2 * * * cd /path/to/app && python scripts/cleanup_environments.py
        """,
    )

    parser.add_argument(
        "--environment",
        choices=["dev", "test", "stage"],
        help="Specific environment to clean (default: all non-prod)",
    )
    parser.add_argument(
        "--model",
        choices=list(CLEANABLE_MODELS.keys()),
        help="Specific model to clean (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what will be deleted without actually deleting",
    )
    parser.add_argument(
        "--test-data-only",
        action="store_true",
        help="Only delete test data (7+ days old), ignore retention policy",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_cleanup(
                environment=args.environment,
                model_name=args.model,
                dry_run=args.dry_run,
                test_data_only=args.test_data_only,
            )
        )
    except KeyboardInterrupt:
        print("\n⚠️  Cleanup cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        logger.error("cleanup_job_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
