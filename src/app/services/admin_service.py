"""Admin service for user and content management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.admin import AdminActivityLog, AdminAPIKey, ContentModerationLog
from app.models.chat import Conversation
from app.models.document import Document
from app.models.user import User

logger = get_logger(__name__)


class AdminService:
    """Service for administrative operations."""

    def __init__(self, db: AsyncSession):
        """Initialize admin service.

        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # Super-Admin API Key Management
    # ========================================================================

    async def create_api_key(
        self,
        admin_user_id: UUID,
        key_name: str,
        permissions: list[str],
        expires_in_days: Optional[int] = None,
    ) -> dict:
        """
        Create a new super-admin API key.

        CRITICAL: Only super-admins can create API keys.

        Args:
            admin_user_id: ID of admin creating the key
            key_name: Descriptive name for the key
            permissions: List of permissions (e.g., ["user:write", "content:moderate"])
            expires_in_days: Expiration in days (None = never expires)

        Returns:
            API key information with the generated key
        """
        # Generate secure random API key
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        api_key_hash = secrets.token_hex(16)  # In production, use proper hashing

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        admin_api_key = AdminAPIKey(
            created_by_user_id=admin_user_id,
            key_name=key_name,
            key_hash=api_key_hash,
            permissions=permissions,
            expires_at=expires_at,
            is_active=True,
        )

        self.db.add(admin_api_key)

        # Log activity
        await self._log_admin_activity(
            admin_user_id=admin_user_id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=admin_api_key.id,
            details={"key_name": key_name, "permissions": permissions},
        )

        await self.db.commit()
        await self.db.refresh(admin_api_key)

        logger.info(
            "admin_api_key_created",
            key_id=str(admin_api_key.id),
            key_name=key_name,
            admin_user_id=str(admin_user_id),
        )

        return {
            "api_key_id": str(admin_api_key.id),
            "key_name": key_name,
            "api_key": api_key,  # ONLY returned once during creation
            "permissions": permissions,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "created_at": admin_api_key.created_at.isoformat(),
            "warning": "SAVE THIS KEY NOW - It will not be shown again!",
        }

    async def list_api_keys(
        self, admin_user_id: UUID, include_expired: bool = False
    ) -> list[dict]:
        """
        List all API keys.

        Args:
            admin_user_id: ID of admin requesting the list
            include_expired: Include expired keys

        Returns:
            List of API keys (without the actual key values)
        """
        query = select(AdminAPIKey)

        if not include_expired:
            query = query.where(
                and_(
                    AdminAPIKey.is_active == True,
                    (AdminAPIKey.expires_at.is_(None)) | (AdminAPIKey.expires_at > datetime.utcnow()),
                )
            )

        result = await self.db.execute(query)
        api_keys = result.scalars().all()

        return [
            {
                "api_key_id": str(key.id),
                "key_name": key.key_name,
                "permissions": key.permissions,
                "created_by": str(key.created_by_user_id),
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "is_active": key.is_active,
            }
            for key in api_keys
        ]

    async def revoke_api_key(self, admin_user_id: UUID, api_key_id: UUID) -> dict:
        """
        Revoke an API key.

        Args:
            admin_user_id: ID of admin revoking the key
            api_key_id: ID of API key to revoke

        Returns:
            Revocation confirmation
        """
        result = await self.db.execute(select(AdminAPIKey).where(AdminAPIKey.id == api_key_id))
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise ValueError("API key not found")

        api_key.is_active = False

        # Log activity
        await self._log_admin_activity(
            admin_user_id=admin_user_id,
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=api_key_id,
            details={"key_name": api_key.key_name},
        )

        await self.db.commit()

        logger.info(
            "admin_api_key_revoked",
            key_id=str(api_key_id),
            admin_user_id=str(admin_user_id),
        )

        return {
            "api_key_id": str(api_key_id),
            "key_name": api_key.key_name,
            "status": "revoked",
            "revoked_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # User Management
    # ========================================================================

    async def list_users(
        self,
        admin_user_id: UUID,
        page: int = 1,
        page_size: int = 50,
        search_query: Optional[str] = None,
        role_filter: Optional[str] = None,
    ) -> dict:
        """
        List all users with filtering and pagination.

        Args:
            admin_user_id: ID of admin requesting the list
            page: Page number
            page_size: Items per page
            search_query: Search by email or display name
            role_filter: Filter by role

        Returns:
            Paginated user list
        """
        query = select(User)

        # Apply filters
        if search_query:
            query = query.where(
                (User.email.ilike(f"%{search_query}%"))
                | (User.display_name.ilike(f"%{search_query}%"))
            )

        if role_filter:
            query = query.where(User.role == role_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        users = result.scalars().all()

        return {
            "users": [
                {
                    "user_id": str(user.id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "role": user.role,
                    "is_verified": user.is_verified,
                    "is_banned": user.is_banned,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    async def ban_user(
        self, admin_user_id: UUID, user_id: UUID, reason: str, ban_duration_days: Optional[int] = None
    ) -> dict:
        """
        Ban a user.

        Args:
            admin_user_id: ID of admin banning the user
            user_id: ID of user to ban
            reason: Reason for ban
            ban_duration_days: Duration in days (None = permanent)

        Returns:
            Ban confirmation
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if user.role == "super_admin":
            raise ValueError("Cannot ban super-admin users")

        user.is_banned = True
        user.ban_reason = reason

        if ban_duration_days:
            user.ban_expires_at = datetime.utcnow() + timedelta(days=ban_duration_days)

        # Log activity
        await self._log_admin_activity(
            admin_user_id=admin_user_id,
            action="ban_user",
            resource_type="user",
            resource_id=user_id,
            details={"reason": reason, "duration_days": ban_duration_days},
        )

        await self.db.commit()

        logger.warn(
            "user_banned",
            user_id=str(user_id),
            admin_user_id=str(admin_user_id),
            reason=reason,
        )

        return {
            "user_id": str(user_id),
            "email": user.email,
            "status": "banned",
            "reason": reason,
            "ban_expires_at": user.ban_expires_at.isoformat() if user.ban_expires_at else None,
            "banned_at": datetime.utcnow().isoformat(),
        }

    async def unban_user(self, admin_user_id: UUID, user_id: UUID) -> dict:
        """
        Unban a user.

        Args:
            admin_user_id: ID of admin unbanning the user
            user_id: ID of user to unban

        Returns:
            Unban confirmation
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        user.is_banned = False
        user.ban_reason = None
        user.ban_expires_at = None

        # Log activity
        await self._log_admin_activity(
            admin_user_id=admin_user_id,
            action="unban_user",
            resource_type="user",
            resource_id=user_id,
            details={},
        )

        await self.db.commit()

        logger.info(
            "user_unbanned",
            user_id=str(user_id),
            admin_user_id=str(admin_user_id),
        )

        return {
            "user_id": str(user_id),
            "email": user.email,
            "status": "active",
            "unbanned_at": datetime.utcnow().isoformat(),
        }

    async def change_user_role(self, admin_user_id: UUID, user_id: UUID, new_role: str) -> dict:
        """
        Change a user's role.

        Args:
            admin_user_id: ID of admin changing the role
            user_id: ID of user
            new_role: New role (user, moderator, admin, super_admin)

        Returns:
            Role change confirmation
        """
        if new_role not in ["user", "moderator", "admin", "super_admin"]:
            raise ValueError("Invalid role")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        old_role = user.role
        user.role = new_role

        # Log activity
        await self._log_admin_activity(
            admin_user_id=admin_user_id,
            action="change_user_role",
            resource_type="user",
            resource_id=user_id,
            details={"old_role": old_role, "new_role": new_role},
        )

        await self.db.commit()

        logger.info(
            "user_role_changed",
            user_id=str(user_id),
            old_role=old_role,
            new_role=new_role,
            admin_user_id=str(admin_user_id),
        )

        return {
            "user_id": str(user_id),
            "email": user.email,
            "old_role": old_role,
            "new_role": new_role,
            "changed_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # Content Moderation
    # ========================================================================

    async def get_pending_content(self, admin_user_id: UUID, limit: int = 20) -> list[dict]:
        """
        Get content pending moderation.

        Args:
            admin_user_id: ID of admin requesting content
            limit: Maximum number of items

        Returns:
            List of pending content
        """
        # Get documents pending review
        query = (
            select(Document)
            .where(Document.moderation_status == "pending")
            .order_by(Document.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [
            {
                "content_id": str(doc.id),
                "content_type": "document",
                "title": doc.title,
                "uploaded_by": str(doc.uploaded_by_user_id) if doc.uploaded_by_user_id else None,
                "created_at": doc.created_at.isoformat(),
                "moderation_status": doc.moderation_status,
            }
            for doc in documents
        ]

    async def moderate_content(
        self,
        admin_user_id: UUID,
        content_id: UUID,
        content_type: str,
        action: str,
        reason: Optional[str] = None,
    ) -> dict:
        """
        Moderate content (approve/reject).

        Args:
            admin_user_id: ID of admin moderating
            content_id: ID of content to moderate
            content_type: Type of content (document, conversation, etc.)
            action: Action to take (approve, reject)
            reason: Reason for rejection

        Returns:
            Moderation confirmation
        """
        if action not in ["approve", "reject"]:
            raise ValueError("Invalid action")

        # Handle document moderation
        if content_type == "document":
            result = await self.db.execute(select(Document).where(Document.id == content_id))
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError("Document not found")

            document.moderation_status = "approved" if action == "approve" else "rejected"
            document.moderated_at = datetime.utcnow()
            document.moderated_by_user_id = admin_user_id

        # Create moderation log
        moderation_log = ContentModerationLog(
            moderator_user_id=admin_user_id,
            content_type=content_type,
            content_id=content_id,
            action=action,
            reason=reason,
        )

        self.db.add(moderation_log)

        # Log admin activity
        await self._log_admin_activity(
            admin_user_id=admin_user_id,
            action=f"moderate_content_{action}",
            resource_type=content_type,
            resource_id=content_id,
            details={"action": action, "reason": reason},
        )

        await self.db.commit()

        logger.info(
            "content_moderated",
            content_id=str(content_id),
            content_type=content_type,
            action=action,
            admin_user_id=str(admin_user_id),
        )

        return {
            "content_id": str(content_id),
            "content_type": content_type,
            "action": action,
            "reason": reason,
            "moderated_by": str(admin_user_id),
            "moderated_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # System Statistics
    # ========================================================================

    async def get_system_statistics(self, admin_user_id: UUID) -> dict:
        """
        Get system-wide statistics.

        Args:
            admin_user_id: ID of admin requesting statistics

        Returns:
            System statistics
        """
        # Total users
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()

        # Verified users
        verified_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_verified == True)
        )
        verified_users = verified_users_result.scalar()

        # Banned users
        banned_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_banned == True)
        )
        banned_users = banned_users_result.scalar()

        # Total documents
        total_documents_result = await self.db.execute(select(func.count(Document.id)))
        total_documents = total_documents_result.scalar()

        # Pending moderation
        pending_moderation_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.moderation_status == "pending")
        )
        pending_moderation = pending_moderation_result.scalar()

        # Total conversations
        total_conversations_result = await self.db.execute(select(func.count(Conversation.id)))
        total_conversations = total_conversations_result.scalar()

        return {
            "users": {
                "total": total_users,
                "verified": verified_users,
                "banned": banned_users,
                "unverified": total_users - verified_users,
            },
            "content": {
                "total_documents": total_documents,
                "pending_moderation": pending_moderation,
            },
            "chat": {
                "total_conversations": total_conversations,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _log_admin_activity(
        self,
        admin_user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        details: dict,
    ) -> None:
        """Log admin activity.

        Args:
            admin_user_id: ID of admin performing action
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource
            details: Additional details
        """
        activity_log = AdminActivityLog(
            admin_user_id=admin_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )

        self.db.add(activity_log)
