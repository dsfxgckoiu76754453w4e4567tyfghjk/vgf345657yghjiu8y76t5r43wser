"""Comprehensive integration tests for external API client endpoints."""

import pytest
from uuid import uuid4, UUID
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.external_api import ExternalAPIClient
from tests.factories import UserFactory


class TestRegisterExternalAPIClient:
    """Test registering external API clients."""

    @pytest.mark.asyncio
    async def test_register_client_success(self, db_session):
        """Test successfully registering an external API client."""
        client_data = {
            "app_name": "Test Mobile App",
            "app_description": "A test mobile application",
            "callback_url": "https://example.com/callback",
            "allowed_origins": ["https://example.com"],
            "rate_limit_per_minute": 60,
            "rate_limit_per_day": 10000
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == client_data["app_name"]
        assert "client_id" in data
        assert "api_key" in data  # Should be returned only once
        assert "api_secret" in data  # Should be returned only once
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_register_client_minimal_data(self, db_session):
        """Test registering client with minimal required data."""
        client_data = {
            "app_name": "Minimal App",
            "app_description": "Minimal description"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == client_data["app_name"]
        assert "client_id" in data

    @pytest.mark.asyncio
    async def test_register_client_with_cors_origins(self, db_session):
        """Test registering client with CORS origins."""
        client_data = {
            "app_name": "Web App",
            "app_description": "Web application with CORS",
            "allowed_origins": [
                "https://example.com",
                "https://app.example.com",
                "https://api.example.com"
            ]
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 200
        data = response.json()
        assert "allowed_origins" in data
        assert len(data["allowed_origins"]) == 3

    @pytest.mark.asyncio
    async def test_register_client_custom_rate_limits(self, db_session):
        """Test registering client with custom rate limits."""
        client_data = {
            "app_name": "Premium App",
            "app_description": "App with custom rate limits",
            "rate_limit_per_minute": 120,
            "rate_limit_per_day": 50000
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 200
        data = response.json()
        assert data["rate_limit_per_minute"] == 120
        assert data["rate_limit_per_day"] == 50000

    @pytest.mark.asyncio
    async def test_register_client_missing_app_name(self):
        """Test registering client without app name fails."""
        client_data = {
            "app_description": "Missing name"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_client_empty_app_name(self):
        """Test registering client with empty app name fails."""
        client_data = {
            "app_name": "",
            "app_description": "Empty name"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_client_invalid_callback_url(self):
        """Test registering client with invalid callback URL fails."""
        client_data = {
            "app_name": "Test App",
            "app_description": "Invalid callback",
            "callback_url": "not-a-valid-url"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_client_negative_rate_limit(self):
        """Test registering client with negative rate limit fails."""
        client_data = {
            "app_name": "Test App",
            "app_description": "Negative rate limit",
            "rate_limit_per_minute": -10
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_client_api_credentials_unique(self, db_session):
        """Test that each registered client gets unique API credentials."""
        client_data = {
            "app_name": "Unique Test App",
            "app_description": "Testing uniqueness"
        }

        api_keys = []
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for i in range(3):
                data = {**client_data, "app_name": f"App {i}"}
                response = await client.post("/api/v1/external-api/clients", json=data)
                assert response.status_code == 200
                api_keys.append(response.json()["api_key"])

        # All API keys should be unique
        assert len(api_keys) == len(set(api_keys))

    @pytest.mark.asyncio
    async def test_register_client_wildcard_cors(self, db_session):
        """Test registering client with wildcard CORS (development mode)."""
        client_data = {
            "app_name": "Dev App",
            "app_description": "Development app with wildcard CORS",
            "allowed_origins": ["*"]
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/external-api/clients", json=client_data)

        # Should succeed but may include warning
        assert response.status_code == 200


class TestListExternalAPIClients:
    """Test listing external API clients."""

    @pytest.mark.asyncio
    async def test_list_clients_success(self, db_session):
        """Test successfully listing API clients."""
        # Register a few clients first
        for i in range(3):
            client_data = {
                "app_name": f"Test App {i}",
                "app_description": f"Description {i}"
            }
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/v1/external-api/clients", json=client_data)

        # List clients
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/external-api/clients")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_list_clients_empty(self, db_session):
        """Test listing clients when none exist."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/external-api/clients")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_clients_exclude_secrets(self, db_session):
        """Test that listing clients does not expose secrets."""
        # Register a client
        client_data = {
            "app_name": "Secret Test App",
            "app_description": "Testing secret exposure"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/external-api/clients", json=client_data)

            # List clients
            response = await client.get("/api/v1/external-api/clients")

        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            # API secret should not be in the list response
            assert "api_secret" not in data[0]

    @pytest.mark.asyncio
    async def test_list_clients_include_inactive(self, db_session):
        """Test listing clients with include_inactive parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/external-api/clients?include_inactive=true")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_clients_only_active(self, db_session):
        """Test listing only active clients (default behavior)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/external-api/clients?include_inactive=false")

        assert response.status_code == 200
        data = response.json()
        # All returned clients should be active
        for client_item in data:
            assert client_item.get("is_active", True) is True


class TestGetClientDetails:
    """Test getting external API client details."""

    @pytest.mark.asyncio
    async def test_get_client_details_success(self, db_session):
        """Test successfully getting client details."""
        # Register a client
        client_data = {
            "app_name": "Detail Test App",
            "app_description": "Testing client details"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get client details
            response = await client.get(f"/api/v1/external-api/clients/{client_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == client_id
        assert data["app_name"] == client_data["app_name"]
        assert "usage_statistics" in data or "total_requests" in data

    @pytest.mark.asyncio
    async def test_get_client_details_includes_usage_stats(self, db_session):
        """Test that client details include usage statistics."""
        # Register a client
        client_data = {
            "app_name": "Stats Test App",
            "app_description": "Testing usage stats"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get client details
            response = await client.get(f"/api/v1/external-api/clients/{client_id}")

        assert response.status_code == 200
        data = response.json()
        # Should include some usage metrics
        assert "total_requests" in data or "request_count" in data

    @pytest.mark.asyncio
    async def test_get_client_details_nonexistent(self):
        """Test getting details of non-existent client fails."""
        fake_client_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/external-api/clients/{fake_client_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_client_details_invalid_uuid(self):
        """Test getting client details with invalid UUID fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/external-api/clients/invalid-uuid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_client_details_no_secret(self, db_session):
        """Test that client details do not expose API secret."""
        # Register a client
        client_data = {
            "app_name": "No Secret Test App",
            "app_description": "Testing secret exposure"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get client details
            response = await client.get(f"/api/v1/external-api/clients/{client_id}")

        assert response.status_code == 200
        data = response.json()
        # API secret should not be exposed
        assert "api_secret" not in data
        # May have api_key_prefix but not full key
        assert "api_key_prefix" in data or "api_key" not in data


class TestUpdateExternalAPIClient:
    """Test updating external API clients."""

    @pytest.mark.asyncio
    async def test_update_client_success(self, db_session):
        """Test successfully updating a client."""
        # Register a client
        client_data = {
            "app_name": "Original Name",
            "app_description": "Original description"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Update client
            update_data = {
                "app_name": "Updated Name",
                "app_description": "Updated description"
            }
            response = await client.put(
                f"/api/v1/external-api/clients/{client_id}",
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "Updated Name"
        assert data["app_description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_client_rate_limits(self, db_session):
        """Test updating client rate limits."""
        # Register a client
        client_data = {
            "app_name": "Rate Limit Test",
            "app_description": "Testing rate limit updates",
            "rate_limit_per_minute": 60
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Update rate limits
            update_data = {
                "rate_limit_per_minute": 120,
                "rate_limit_per_day": 20000
            }
            response = await client.put(
                f"/api/v1/external-api/clients/{client_id}",
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["rate_limit_per_minute"] == 120
        assert data["rate_limit_per_day"] == 20000

    @pytest.mark.asyncio
    async def test_update_client_cors_origins(self, db_session):
        """Test updating CORS origins."""
        # Register a client
        client_data = {
            "app_name": "CORS Test",
            "app_description": "Testing CORS updates",
            "allowed_origins": ["https://example.com"]
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Update CORS origins
            update_data = {
                "allowed_origins": [
                    "https://example.com",
                    "https://app.example.com"
                ]
            }
            response = await client.put(
                f"/api/v1/external-api/clients/{client_id}",
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["allowed_origins"]) == 2

    @pytest.mark.asyncio
    async def test_update_client_nonexistent(self):
        """Test updating non-existent client fails."""
        fake_client_id = uuid4()
        update_data = {
            "app_name": "Updated Name"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/external-api/clients/{fake_client_id}",
                json=update_data
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_client_partial_update(self, db_session):
        """Test partial update of client (only some fields)."""
        # Register a client
        client_data = {
            "app_name": "Partial Test",
            "app_description": "Original description",
            "rate_limit_per_minute": 60
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Update only app_name
            update_data = {
                "app_name": "New Name Only"
            }
            response = await client.put(
                f"/api/v1/external-api/clients/{client_id}",
                json=update_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "New Name Only"
        # Other fields should remain unchanged or have default values


class TestRegenerateAPISecret:
    """Test regenerating API secrets."""

    @pytest.mark.asyncio
    async def test_regenerate_secret_success(self, db_session):
        """Test successfully regenerating API secret."""
        # Register a client
        client_data = {
            "app_name": "Secret Regen Test",
            "app_description": "Testing secret regeneration"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]
            original_secret = create_response.json().get("api_secret")

            # Regenerate secret
            response = await client.post(
                f"/api/v1/external-api/clients/{client_id}/regenerate-secret"
            )

        assert response.status_code == 200
        data = response.json()
        assert "new_api_secret" in data
        # New secret should be different from original (if original was captured)
        if original_secret:
            assert data["new_api_secret"] != original_secret

    @pytest.mark.asyncio
    async def test_regenerate_secret_returns_once(self, db_session):
        """Test that regenerated secret is shown only once."""
        # Register a client
        client_data = {
            "app_name": "Once Test",
            "app_description": "Testing one-time secret display"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Regenerate secret
            regen_response = await client.post(
                f"/api/v1/external-api/clients/{client_id}/regenerate-secret"
            )
            assert "new_api_secret" in regen_response.json()

            # Get client details - should not show secret
            details_response = await client.get(f"/api/v1/external-api/clients/{client_id}")

        assert details_response.status_code == 200
        assert "api_secret" not in details_response.json()

    @pytest.mark.asyncio
    async def test_regenerate_secret_nonexistent_client(self):
        """Test regenerating secret for non-existent client fails."""
        fake_client_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/external-api/clients/{fake_client_id}/regenerate-secret"
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_regenerate_secret_multiple_times(self, db_session):
        """Test regenerating secret multiple times."""
        # Register a client
        client_data = {
            "app_name": "Multi Regen Test",
            "app_description": "Testing multiple regenerations"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Regenerate secret multiple times
            secrets = []
            for _ in range(3):
                response = await client.post(
                    f"/api/v1/external-api/clients/{client_id}/regenerate-secret"
                )
                assert response.status_code == 200
                secrets.append(response.json()["new_api_secret"])

        # All secrets should be unique
        assert len(secrets) == len(set(secrets))


class TestDeactivateActivateClient:
    """Test deactivating and activating clients."""

    @pytest.mark.asyncio
    async def test_deactivate_client_success(self, db_session):
        """Test successfully deactivating a client."""
        # Register a client
        client_data = {
            "app_name": "Deactivate Test",
            "app_description": "Testing deactivation"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Deactivate client
            response = await client.post(
                f"/api/v1/external-api/clients/{client_id}/deactivate"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False or data["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_activate_client_success(self, db_session):
        """Test successfully activating a client."""
        # Register and deactivate a client
        client_data = {
            "app_name": "Activate Test",
            "app_description": "Testing activation"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Deactivate first
            await client.post(f"/api/v1/external-api/clients/{client_id}/deactivate")

            # Now activate
            response = await client.post(
                f"/api/v1/external-api/clients/{client_id}/activate"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True or data["status"] == "active"

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_client(self):
        """Test deactivating non-existent client fails."""
        fake_client_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/external-api/clients/{fake_client_id}/deactivate"
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_activate_nonexistent_client(self):
        """Test activating non-existent client fails."""
        fake_client_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/external-api/clients/{fake_client_id}/activate"
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deactivate_already_inactive(self, db_session):
        """Test deactivating already inactive client."""
        # Register and deactivate a client
        client_data = {
            "app_name": "Double Deactivate Test",
            "app_description": "Testing double deactivation"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Deactivate twice
            first_response = await client.post(
                f"/api/v1/external-api/clients/{client_id}/deactivate"
            )
            second_response = await client.post(
                f"/api/v1/external-api/clients/{client_id}/deactivate"
            )

        # Both should succeed or second might return specific message
        assert first_response.status_code == 200
        assert second_response.status_code in [200, 400]


class TestGetUsageStatistics:
    """Test getting usage statistics for API clients."""

    @pytest.mark.asyncio
    async def test_get_usage_statistics_success(self, db_session):
        """Test successfully getting usage statistics."""
        # Register a client
        client_data = {
            "app_name": "Usage Stats Test",
            "app_description": "Testing usage statistics"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get usage statistics
            response = await client.get(
                f"/api/v1/external-api/clients/{client_id}/usage"
            )

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data or "request_count" in data
        # May include metrics like average_response_time, error_rate, etc.

    @pytest.mark.asyncio
    async def test_get_usage_statistics_custom_days(self, db_session):
        """Test getting usage statistics for custom number of days."""
        # Register a client
        client_data = {
            "app_name": "Custom Days Test",
            "app_description": "Testing custom days parameter"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get usage statistics for 30 days
            response = await client.get(
                f"/api/v1/external-api/clients/{client_id}/usage?days=30"
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_usage_statistics_max_days(self, db_session):
        """Test getting usage statistics for maximum allowed days."""
        # Register a client
        client_data = {
            "app_name": "Max Days Test",
            "app_description": "Testing max days"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get usage statistics for 90 days (max)
            response = await client.get(
                f"/api/v1/external-api/clients/{client_id}/usage?days=90"
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_usage_statistics_invalid_days(self, db_session):
        """Test getting usage statistics with invalid days fails."""
        # Register a client
        client_data = {
            "app_name": "Invalid Days Test",
            "app_description": "Testing invalid days"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Try with invalid days (exceeds max)
            response = await client.get(
                f"/api/v1/external-api/clients/{client_id}/usage?days=100"
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_usage_statistics_zero_days(self, db_session):
        """Test getting usage statistics with zero days fails."""
        # Register a client
        client_data = {
            "app_name": "Zero Days Test",
            "app_description": "Testing zero days"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Try with zero days
            response = await client.get(
                f"/api/v1/external-api/clients/{client_id}/usage?days=0"
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_usage_statistics_nonexistent_client(self):
        """Test getting usage statistics for non-existent client fails."""
        fake_client_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/external-api/clients/{fake_client_id}/usage"
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_usage_statistics_new_client(self, db_session):
        """Test getting usage statistics for newly created client (no usage yet)."""
        # Register a client
        client_data = {
            "app_name": "New Client Test",
            "app_description": "Testing new client with no usage"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_response = await client.post("/api/v1/external-api/clients", json=client_data)
            client_id = create_response.json()["client_id"]

            # Get usage statistics immediately
            response = await client.get(
                f"/api/v1/external-api/clients/{client_id}/usage"
            )

        assert response.status_code == 200
        data = response.json()
        # Should return zero or empty statistics
        total_requests = data.get("total_requests", 0)
        assert total_requests >= 0
