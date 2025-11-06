"""Create super admin user for production."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User, UserSettings, LinkedAuthProvider

settings = get_settings()


async def create_super_admin():
    """Create super admin user if it doesn't exist."""
    print("🔧 Creating Super Admin User...")
    print("=" * 50)

    # Create database engine
    engine = create_async_engine(settings.get_database_url())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if super admin exists
            result = await session.execute(
                select(User).where(User.email == settings.super_admin_email)
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⚠️  Super admin already exists: {settings.super_admin_email}")
                print(f"   User ID: {existing.id}")
                print(f"   Role: {existing.role if hasattr(existing, 'role') else 'N/A'}")
                return

            # Create super admin user
            admin = User(
                email=settings.super_admin_email,
                password_hash=hash_password(settings.super_admin_password),
                full_name="Super Administrator",
                role="super_admin",
                is_email_verified=True,
                is_active=True,
                account_type="unlimited",
                preferred_language="en"
            )

            session.add(admin)
            await session.flush()

            # Create linked auth provider
            linked_provider = LinkedAuthProvider(
                user_id=admin.id,
                provider_type="email",
                provider_email=admin.email,
                is_primary=True,
                is_verified=True,
            )
            session.add(linked_provider)

            # Create user settings
            user_settings = UserSettings(
                user_id=admin.id,
                theme="dark",
                rate_limit_tier="unlimited"
            )
            session.add(user_settings)

            await session.commit()

            print(f"✅ Super admin created successfully!")
            print(f"   Email: {settings.super_admin_email}")
            print(f"   User ID: {admin.id}")
            print(f"   Role: super_admin")
            print()
            print("⚠️  IMPORTANT: Change the password immediately after first login!")

        except Exception as e:
            print(f"❌ Error creating super admin: {e}")
            await session.rollback()
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_super_admin())
