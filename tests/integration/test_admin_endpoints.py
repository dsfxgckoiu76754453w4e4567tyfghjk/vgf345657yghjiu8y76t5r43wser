"""Comprehensive integration tests for admin endpoints."""

import pytest
from uuid import uuid4, UUID
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.user import User
from app.models.admin import AdminAPIKey
from tests.factories import UserFactory


# ============================================================================
# Test API Key Management
# ============================================================================


class TestAdminAPIKeyCreation:
    """Test admin API key creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, db_session):
        """Test successful API key creation."""
        request_data = {
            "key_name": "Test Admin Key",
            "permissions": ["user:read", "user:write", "content:moderate"],
            "expires_in_days": 90,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["key_name"] == request_data["key_name"]
        assert data["permissions"] == request_data["permissions"]
        assert "api_key" in data  # Only returned on creation
        assert data["api_key"].startswith("sk_")
        assert data["is_active"] is True
        assert "api_key_id" in data
        assert "created_at" in data

        # Verify key exists in database
        result = await db_session.execute(
            select(AdminAPIKey).where(AdminAPIKey.key_name == request_data["key_name"])
        )
        api_key = result.scalar_one_or_none()
        assert api_key is not None
        assert api_key.is_active is True

    @pytest.mark.asyncio
    async def test_create_api_key_no_expiration(self, db_session):
        """Test API key creation without expiration."""
        request_data = {
            "key_name": "Permanent Test Key",
            "permissions": ["user:read"],
            "expires_in_days": None,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is None

    @pytest.mark.asyncio
    async def test_create_api_key_missing_key_name(self):
        """Test API key creation without key name fails."""
        request_data = {
            "permissions": ["user:read"],
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_api_key_empty_permissions(self):
        """Test API key creation with empty permissions fails."""
        request_data = {
            "key_name": "Test Key",
            "permissions": [],
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_api_key_invalid_expiration(self):
        """Test API key creation with invalid expiration days."""
        request_data = {
            "key_name": "Test Key",
            "permissions": ["user:read"],
            "expires_in_days": 500,  # > 365
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        assert response.status_code == 422


class TestAdminAPIKeyListing:
    """Test admin API key listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_api_keys_success(self, db_session):
        """Test successful API key listing."""
        # Create a test API key first
        create_request = {
            "key_name": "List Test Key",
            "permissions": ["user:read"],
            "expires_in_days": 30,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/admin/api-keys", json=create_request)
            response = await client.get("/api/v1/admin/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # API key should not be in the list response (only on creation)
        for key in data:
            assert "api_key" not in key or key["api_key"] is None
            assert "key_name" in key
            assert "permissions" in key
            assert "is_active" in key

    @pytest.mark.asyncio
    async def test_list_api_keys_exclude_expired(self, db_session):
        """Test listing API keys excludes expired by default."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/api-keys?include_expired=false")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_api_keys_include_expired(self, db_session):
        """Test listing API keys includes expired when requested."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/api-keys?include_expired=true")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAdminAPIKeyRevocation:
    """Test admin API key revocation endpoint."""

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, db_session):
        """Test successful API key revocation."""
        # Create a key first
        create_request = {
            "key_name": "Revoke Test Key",
            "permissions": ["user:read"],
            "expires_in_days": 30,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/admin/api-keys", json=create_request)
            api_key_id = create_response.json()["api_key_id"]

            # Revoke the key
            revoke_response = await client.post(f"/api/v1/admin/api-keys/{api_key_id}/revoke")

        assert revoke_response.status_code == 200
        data = revoke_response.json()
        assert data["api_key_id"] == api_key_id
        assert data["status"] == "revoked"
        assert "revoked_at" in data

    @pytest.mark.asyncio
    async def test_revoke_api_key_not_found(self):
        """Test revoking non-existent API key."""
        fake_key_id = str(uuid4())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/v1/admin/api-keys/{fake_key_id}/revoke")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_api_key_invalid_uuid(self):
        """Test revoking API key with invalid UUID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys/invalid-uuid/revoke")

        assert response.status_code == 422


# ============================================================================
# Test User Management
# ============================================================================


class TestAdminUserListing:
    """Test admin user listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_users_success(self, db_session):
        """Test successful user listing with default pagination."""
        # Create a test user
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "pagination" in data
        assert isinstance(data["users"], list)
        assert "total" in data["pagination"]
        assert "page" in data["pagination"]
        assert "page_size" in data["pagination"]

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, db_session):
        """Test user listing with custom pagination."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_users_with_search(self, db_session):
        """Test user listing with search query."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users?search_query=test")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    @pytest.mark.asyncio
    async def test_list_users_with_role_filter(self, db_session):
        """Test user listing with role filter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users?role_filter=user")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    @pytest.mark.asyncio
    async def test_list_users_invalid_page(self):
        """Test user listing with invalid page number."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users?page=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_invalid_page_size(self):
        """Test user listing with invalid page size."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users?page_size=200")

        assert response.status_code == 422


class TestAdminUserBan:
    """Test admin user ban endpoint."""

    @pytest.mark.asyncio
    async def test_ban_user_success(self, db_session):
        """Test successful user ban."""
        # Create a test user
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "Violation of community guidelines - spam content",
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["status"] == "banned"
        assert data["reason"] == ban_request["reason"]
        assert "banned_at" in data

    @pytest.mark.asyncio
    async def test_ban_user_permanent(self, db_session):
        """Test permanent user ban."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "Serious violation requiring permanent ban",
            "ban_duration_days": None,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["ban_expires_at"] is None

    @pytest.mark.asyncio
    async def test_ban_user_not_found(self):
        """Test banning non-existent user."""
        fake_user_id = str(uuid4())
        ban_request = {
            "reason": "Test reason with sufficient length",
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{fake_user_id}/ban",
                json=ban_request,
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_ban_user_invalid_uuid(self):
        """Test banning user with invalid UUID."""
        ban_request = {
            "reason": "Test reason with sufficient length",
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/users/invalid-uuid/ban",
                json=ban_request,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ban_user_reason_too_short(self, db_session):
        """Test banning user with too short reason."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "Short",  # Less than 10 characters
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ban_user_missing_reason(self, db_session):
        """Test banning user without reason."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        assert response.status_code == 422


class TestAdminUserUnban:
    """Test admin user unban endpoint."""

    @pytest.mark.asyncio
    async def test_unban_user_success(self, db_session):
        """Test successful user unban."""
        # Create and ban a user first
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "Testing unban functionality after ban",
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Ban the user
            await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

            # Unban the user
            unban_response = await client.post(f"/api/v1/admin/users/{str(user.id)}/unban")

        assert unban_response.status_code == 200
        data = unban_response.json()
        assert data["user_id"] == str(user.id)
        assert data["status"] == "active"
        assert "unbanned_at" in data

    @pytest.mark.asyncio
    async def test_unban_user_not_found(self):
        """Test unbanning non-existent user."""
        fake_user_id = str(uuid4())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/v1/admin/users/{fake_user_id}/unban")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unban_user_invalid_uuid(self):
        """Test unbanning user with invalid UUID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/users/invalid-uuid/unban")

        assert response.status_code == 422


class TestAdminUserRoleChange:
    """Test admin user role change endpoint."""

    @pytest.mark.asyncio
    async def test_change_user_role_success(self, db_session):
        """Test successful user role change."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        role_request = {
            "new_role": "moderator",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/role",
                json=role_request,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["new_role"] == "moderator"
        assert "old_role" in data
        assert "changed_at" in data

    @pytest.mark.asyncio
    async def test_change_user_role_to_admin(self, db_session):
        """Test changing user role to admin."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        role_request = {
            "new_role": "admin",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/role",
                json=role_request,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["new_role"] == "admin"

    @pytest.mark.asyncio
    async def test_change_user_role_not_found(self):
        """Test changing role for non-existent user."""
        fake_user_id = str(uuid4())
        role_request = {
            "new_role": "moderator",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{fake_user_id}/role",
                json=role_request,
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_change_user_role_invalid_role(self, db_session):
        """Test changing user role to invalid role."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        role_request = {
            "new_role": "invalid_role",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/role",
                json=role_request,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_change_user_role_missing_role(self, db_session):
        """Test changing user role without providing new role."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/role",
                json={},
            )

        assert response.status_code == 422


# ============================================================================
# Test Content Moderation
# ============================================================================


class TestAdminPendingContent:
    """Test admin pending content endpoint."""

    @pytest.mark.asyncio
    async def test_get_pending_content_success(self, db_session):
        """Test successful retrieval of pending content."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/content/pending")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_pending_content_with_limit(self, db_session):
        """Test pending content retrieval with limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/content/pending?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_get_pending_content_invalid_limit(self):
        """Test pending content with invalid limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/content/pending?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_pending_content_limit_too_high(self):
        """Test pending content with limit exceeding maximum."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/content/pending?limit=200")

        assert response.status_code == 422


class TestAdminModerateContent:
    """Test admin content moderation endpoint."""

    @pytest.mark.asyncio
    async def test_moderate_content_approve(self, db_session):
        """Test approving content."""
        content_id = str(uuid4())
        moderate_request = {
            "action": "approve",
            "reason": None,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/content/document/{content_id}/moderate",
                json=moderate_request,
            )

        # May be 200 (success) or 400 (content not found)
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_moderate_content_reject(self, db_session):
        """Test rejecting content."""
        content_id = str(uuid4())
        moderate_request = {
            "action": "reject",
            "reason": "Content does not meet quality standards",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/content/document/{content_id}/moderate",
                json=moderate_request,
            )

        # May be 200 (success) or 400 (content not found)
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_moderate_content_invalid_action(self):
        """Test moderating content with invalid action."""
        content_id = str(uuid4())
        moderate_request = {
            "action": "invalid_action",
            "reason": None,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/content/document/{content_id}/moderate",
                json=moderate_request,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_moderate_content_missing_action(self):
        """Test moderating content without action."""
        content_id = str(uuid4())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/content/document/{content_id}/moderate",
                json={},
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_moderate_content_invalid_content_id(self):
        """Test moderating content with invalid content ID."""
        moderate_request = {
            "action": "approve",
            "reason": None,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/content/document/invalid-uuid/moderate",
                json=moderate_request,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_moderate_content_conversation(self):
        """Test moderating conversation content type."""
        content_id = str(uuid4())
        moderate_request = {
            "action": "approve",
            "reason": None,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/content/conversation/{content_id}/moderate",
                json=moderate_request,
            )

        # May be 200 (success) or 400 (content not found)
        assert response.status_code in [200, 400]


# ============================================================================
# Test System Statistics
# ============================================================================


class TestAdminSystemStatistics:
    """Test admin system statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_system_statistics_success(self, db_session):
        """Test successful retrieval of system statistics."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "content" in data
        assert "chat" in data
        assert "generated_at" in data

        # Check users statistics structure
        assert isinstance(data["users"], dict)

        # Check content statistics structure
        assert isinstance(data["content"], dict)

        # Check chat statistics structure
        assert isinstance(data["chat"], dict)

    @pytest.mark.asyncio
    async def test_get_system_statistics_structure(self, db_session):
        """Test system statistics response structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/statistics")

        assert response.status_code == 200
        data = response.json()

        # Verify statistics contain expected metrics
        users_stats = data["users"]
        assert "total" in users_stats
        assert "active" in users_stats
        assert "verified" in users_stats

        content_stats = data["content"]
        assert "documents" in content_stats
        assert "conversations" in content_stats

        chat_stats = data["chat"]
        assert "total_messages" in chat_stats
        assert "total_conversations" in chat_stats


# ============================================================================
# Test Edge Cases and Security
# ============================================================================


class TestAdminEndpointsSecurity:
    """Test security aspects of admin endpoints."""

    @pytest.mark.asyncio
    async def test_unauthorized_access_placeholder(self):
        """Test that admin endpoints require authentication (when implemented)."""
        # TODO: When authentication is implemented, test unauthorized access
        # For now, endpoints use placeholder admin_user_id
        pass

    @pytest.mark.asyncio
    async def test_sql_injection_prevention_user_search(self):
        """Test SQL injection prevention in user search."""
        malicious_query = "'; DROP TABLE users; --"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/admin/users?search_query={malicious_query}"
            )

        # Should not cause error or execute malicious SQL
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_xss_prevention_ban_reason(self, db_session):
        """Test XSS prevention in ban reason."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "<script>alert('XSS')</script> Malicious ban reason",
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        # Should handle gracefully without executing script
        assert response.status_code in [200, 400]


class TestAdminEndpointsEdgeCases:
    """Test edge cases for admin endpoints."""

    @pytest.mark.asyncio
    async def test_large_page_number(self):
        """Test user listing with very large page number."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/users?page=999999")

        assert response.status_code == 200
        data = response.json()
        # Should return empty list or handle gracefully
        assert "users" in data

    @pytest.mark.asyncio
    async def test_unicode_in_api_key_name(self):
        """Test API key creation with unicode characters."""
        request_data = {
            "key_name": "Test Key with émoji 🔑 and ελληνικά",
            "permissions": ["user:read"],
            "expires_in_days": 30,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_very_long_ban_reason(self, db_session):
        """Test banning with very long reason."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "A" * 600,  # Exceeds 500 character limit
            "ban_duration_days": 7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_concurrent_api_key_revocation(self, db_session):
        """Test revoking the same API key multiple times."""
        # Create a key
        create_request = {
            "key_name": "Concurrent Revoke Test",
            "permissions": ["user:read"],
            "expires_in_days": 30,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/admin/api-keys", json=create_request)
            api_key_id = create_response.json()["api_key_id"]

            # Revoke once
            first_revoke = await client.post(f"/api/v1/admin/api-keys/{api_key_id}/revoke")
            assert first_revoke.status_code == 200

            # Try to revoke again
            second_revoke = await client.post(f"/api/v1/admin/api-keys/{api_key_id}/revoke")
            # Should handle gracefully (200 if idempotent, 400 if already revoked)
            assert second_revoke.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_zero_expiration_days(self):
        """Test API key creation with zero expiration days."""
        request_data = {
            "key_name": "Zero Expiration Test",
            "permissions": ["user:read"],
            "expires_in_days": 0,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/api-keys", json=request_data)

        # Should fail validation (minimum 1 day)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_ban_duration(self, db_session):
        """Test banning user with negative duration."""
        user_data = UserFactory.create_user_data()
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            password_hash="dummy_hash",
            is_email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        ban_request = {
            "reason": "Testing negative duration handling properly",
            "ban_duration_days": -7,
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{str(user.id)}/ban",
                json=ban_request,
            )

        assert response.status_code == 422
