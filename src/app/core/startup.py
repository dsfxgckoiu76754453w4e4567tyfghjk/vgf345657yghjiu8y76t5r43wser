"""Application startup checks and initialization."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_database_exists() -> bool:
    """
    Check if the database exists.

    Returns:
        bool: True if database exists, False otherwise
    """
    try:
        # Connect to postgres database to check if our database exists
        postgres_url = settings.get_database_url(database_name="postgres")
        engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")

        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT 1 FROM pg_database WHERE datname = :db_name"
                ),
                {"db_name": settings.database_name}
            )
            exists = result.scalar() is not None

        await engine.dispose()
        return exists
    except Exception as e:
        logger.error("failed_to_check_database_exists", error=str(e))
        return False


async def create_database() -> bool:
    """
    Create the database if it doesn't exist.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("creating_database", database=settings.database_name)

        # Connect to postgres database to create our database
        postgres_url = settings.get_database_url(database_name="postgres")
        engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")

        async with engine.connect() as conn:
            await conn.execute(
                text(f'CREATE DATABASE "{settings.database_name}"')
            )

        await engine.dispose()

        logger.info("database_created_successfully", database=settings.database_name)
        return True
    except Exception as e:
        logger.error("failed_to_create_database", error=str(e))
        return False


async def check_migrations_status() -> dict[str, any]:
    """
    Check the current migration status.

    Returns:
        dict: Migration status information
    """
    try:
        engine = create_async_engine(settings.database_url)

        async with engine.connect() as conn:
            # Check if alembic_version table exists
            result = await conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'alembic_version'
                    )
                    """
                )
            )
            alembic_table_exists = result.scalar()

            if not alembic_table_exists:
                await engine.dispose()
                return {
                    "has_migrations": False,
                    "current_revision": None,
                    "needs_migration": True,
                }

            # Get current revision
            result = await conn.execute(
                text("SELECT version_num FROM alembic_version")
            )
            current_revision = result.scalar()

        await engine.dispose()

        return {
            "has_migrations": True,
            "current_revision": current_revision,
            "needs_migration": False,  # Would need to check against head
        }
    except Exception as e:
        logger.error("failed_to_check_migrations", error=str(e))
        return {
            "has_migrations": False,
            "current_revision": None,
            "needs_migration": True,
            "error": str(e),
        }


async def run_migrations() -> bool:
    """
    Run database migrations using Alembic.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("running_database_migrations")

        # Import alembic here to avoid circular imports
        from alembic import command
        from alembic.config import Config

        # Get alembic config
        alembic_cfg = Config("alembic.ini")

        # Run migrations
        command.upgrade(alembic_cfg, "head")

        logger.info("migrations_completed_successfully")
        return True
    except Exception as e:
        logger.error("migrations_failed", error=str(e), exc_info=e)
        return False


async def initialize_database(auto_migrate: bool = False, confirm: bool = True) -> bool:
    """
    Initialize database with proper checks and migrations.

    Args:
        auto_migrate: Whether to automatically run migrations
        confirm: Whether to ask for confirmation (only in dev mode)

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(
        "checking_database_status",
        database=settings.database_name,
        host=settings.database_host,
        port=settings.database_port,
    )

    # Check if database exists
    db_exists = await check_database_exists()

    if not db_exists:
        logger.warning("database_does_not_exist", database=settings.database_name)

        # In development, we can create it automatically
        if settings.is_development:
            if confirm:
                logger.info("creating_database_automatically_in_dev_mode")
            created = await create_database()
            if not created:
                logger.error("failed_to_create_database")
                return False
        else:
            # In production/test, require manual intervention
            logger.error(
                "database_not_found_in_production",
                message="Please create the database manually or set ENVIRONMENT=dev"
            )
            return False

    # Check migration status
    migration_status = await check_migrations_status()
    logger.info("migration_status", **migration_status)

    if migration_status["needs_migration"]:
        if auto_migrate:
            logger.info("auto_migration_enabled_running_migrations")
            success = await run_migrations()
            if not success:
                logger.error("auto_migration_failed")
                return False
        elif settings.is_development:
            logger.warning(
                "migrations_needed",
                message="Run 'make db-upgrade' or set auto_migrate=True"
            )
            # In development, we can continue without migrations for testing
            return True
        else:
            logger.error(
                "migrations_required_in_production",
                message="Run migrations before starting the application"
            )
            return False

    logger.info("database_initialization_complete")
    return True


async def startup_checks() -> None:
    """
    Perform all startup checks.

    Raises:
        SystemExit: If critical checks fail
    """
    logger.info("performing_startup_checks")

    try:
        # Check database
        db_initialized = await initialize_database(
            auto_migrate=settings.is_development,  # Only auto-migrate in dev
            confirm=settings.is_development,
        )

        if not db_initialized:
            logger.error("database_initialization_failed")
            if settings.is_production:
                sys.exit(1)
            else:
                logger.warning("continuing_despite_database_initialization_failure_in_dev")

        # Log configuration
        logger.info(
            "application_configuration",
            environment=settings.environment,
            debug=settings.debug,
            database_host=settings.database_host,
            database_port=settings.database_port,
            database_name=settings.database_name,
        )

        logger.info("startup_checks_completed")

    except Exception as e:
        logger.error("startup_checks_failed", error=str(e), exc_info=e)
        if settings.is_production:
            sys.exit(1)
        raise
