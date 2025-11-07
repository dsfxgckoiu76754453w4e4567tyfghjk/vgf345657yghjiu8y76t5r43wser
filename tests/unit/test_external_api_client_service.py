"""Comprehensive unit tests for External API Client Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.external_api_client_service import ExternalAPIClientService


class TestExternalAPIClientServiceRegistration:
    """Test cases for API client registration."""

    @pytest.mark.asyncio
    async def test_register_client_creates_client_with_credentials(self):
        """Test that registering a client creates credentials."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        owner_user_id = uuid4()

        # Act
        result = await service.register_client(
            owner_user_id=owner_user_id,
            app_name="Test App",
            app_description="Test Description",
            callback_url="https://example.com/callback",
            allowed_origins=["https://example.com"],
            rate_limit_per_minute=100,
            rate_limit_per_day=50000,
        )

        # Assert
        assert "client_id" in result
        assert "api_key" in result
        assert "api_secret" in result
        assert result["api_key"].startswith("pk_")
        assert result["api_secret"].startswith("sk_")
        assert result["app_name"] == "Test App"
        assert result["rate_limit_per_minute"] == 100
        assert result["rate_limit_per_day"] == 50000
        assert "warning" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_client_with_minimal_params(self):
        """Test registering client with minimal parameters."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        owner_user_id = uuid4()

        # Act
        result = await service.register_client(
            owner_user_id=owner_user_id,
            app_name="Minimal App",
            app_description="Minimal Description",
        )

        # Assert
        assert result is not None
        assert result["app_name"] == "Minimal App"
        # Should use default rate limits
        assert result["rate_limit_per_minute"] == 60
        assert result["rate_limit_per_day"] == 10000


class TestExternalAPIClientServiceListing:
    """Test cases for listing API clients."""

    @pytest.mark.asyncio
    async def test_list_clients_returns_active_clients_only(self):
        """Test that list_clients returns only active clients by default."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        owner_user_id = uuid4()

        # Mock active client
        active_client = MagicMock()
        active_client.id = uuid4()
        active_client.app_name = "Active App"
        active_client.app_description = "Active Description"
        active_client.callback_url = None
        active_client.allowed_origins = []
        active_client.rate_limit_per_minute = 60
        active_client.rate_limit_per_day = 10000
        active_client.is_active = True
        active_client.created_at = datetime.utcnow()
        active_client.last_used_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [active_client]
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.list_clients(owner_user_id=owner_user_id)

        # Assert
        assert len(result) == 1
        assert result[0]["app_name"] == "Active App"
        assert result[0]["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_clients_includes_inactive_when_requested(self):
        """Test that list_clients includes inactive clients when requested."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        owner_user_id = uuid4()

        # Mock active and inactive clients
        active_client = MagicMock()
        active_client.id = uuid4()
        active_client.app_name = "Active App"
        active_client.is_active = True
        active_client.created_at = datetime.utcnow()
        active_client.last_used_at = None

        inactive_client = MagicMock()
        inactive_client.id = uuid4()
        inactive_client.app_name = "Inactive App"
        inactive_client.is_active = False
        inactive_client.created_at = datetime.utcnow()
        inactive_client.last_used_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [active_client, inactive_client]
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.list_clients(
            owner_user_id=owner_user_id,
            include_inactive=True,
        )

        # Assert
        assert len(result) == 2
        assert any(c["app_name"] == "Active App" for c in result)
        assert any(c["app_name"] == "Inactive App" for c in result)


class TestExternalAPIClientServiceDetails:
    """Test cases for getting client details."""

    @pytest.mark.asyncio
    async def test_get_client_details_returns_full_information(self):
        """Test getting detailed client information with usage stats."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id
        mock_client.app_name = "Test App"
        mock_client.app_description = "Test Description"
        mock_client.callback_url = "https://example.com/callback"
        mock_client.allowed_origins = ["https://example.com"]
        mock_client.rate_limit_per_minute = 100
        mock_client.rate_limit_per_day = 50000
        mock_client.is_active = True
        mock_client.created_at = datetime.utcnow()
        mock_client.last_used_at = datetime.utcnow()

        # Mock database queries
        mock_client_result = MagicMock()
        mock_client_result.scalar_one_or_none.return_value = mock_client

        mock_usage_today_result = MagicMock()
        mock_usage_today_result.scalar.return_value = 150

        mock_total_usage_result = MagicMock()
        mock_total_usage_result.scalar.return_value = 5000

        mock_db.execute.side_effect = [
            mock_client_result,
            mock_usage_today_result,
            mock_total_usage_result,
        ]

        # Act
        result = await service.get_client_details(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        # Assert
        assert result["client_id"] == str(client_id)
        assert result["app_name"] == "Test App"
        assert "usage_statistics" in result
        assert result["usage_statistics"]["requests_today"] == 150
        assert result["usage_statistics"]["total_requests"] == 5000
        assert result["usage_statistics"]["remaining_today"] == 50000 - 150

    @pytest.mark.asyncio
    async def test_get_client_details_raises_error_for_nonexistent_client(self):
        """Test that getting details raises error for non-existent client."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        client_id = uuid4()
        owner_user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Client not found"):
            await service.get_client_details(client_id, owner_user_id)


class TestExternalAPIClientServiceUpdate:
    """Test cases for updating client information."""

    @pytest.mark.asyncio
    async def test_update_client_updates_specified_fields(self):
        """Test that update_client updates only specified fields."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id
        mock_client.app_name = "Old Name"
        mock_client.app_description = "Old Description"
        mock_client.rate_limit_per_minute = 60
        mock_client.rate_limit_per_day = 10000

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_client
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.update_client(
            client_id=client_id,
            owner_user_id=owner_user_id,
            app_name="New Name",
            rate_limit_per_minute=200,
        )

        # Assert
        assert mock_client.app_name == "New Name"
        assert mock_client.rate_limit_per_minute == 200
        # Description should remain unchanged
        assert mock_client.app_description == "Old Description"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_client_raises_error_for_nonexistent_client(self):
        """Test that updating raises error for non-existent client."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        client_id = uuid4()
        owner_user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Client not found"):
            await service.update_client(
                client_id=client_id,
                owner_user_id=owner_user_id,
                app_name="New Name",
            )


class TestExternalAPIClientServiceSecretRegeneration:
    """Test cases for regenerating API secrets."""

    @pytest.mark.asyncio
    async def test_regenerate_secret_generates_new_secret(self):
        """Test that regenerate_secret generates a new secret."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id
        old_secret_hash = "old_hash_123"
        mock_client.api_secret_hash = old_secret_hash

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_client
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.regenerate_secret(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        # Assert
        assert "api_secret" in result
        assert result["api_secret"].startswith("sk_")
        assert "warning" in result
        assert mock_client.api_secret_hash != old_secret_hash
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_secret_raises_error_for_nonexistent_client(self):
        """Test that regenerating secret raises error for non-existent client."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        client_id = uuid4()
        owner_user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Client not found"):
            await service.regenerate_secret(client_id, owner_user_id)


class TestExternalAPIClientServiceActivation:
    """Test cases for activating and deactivating clients."""

    @pytest.mark.asyncio
    async def test_deactivate_client_sets_inactive_status(self):
        """Test that deactivating a client sets it to inactive."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock active client
        mock_client = MagicMock()
        mock_client.id = client_id
        mock_client.app_name = "Test App"
        mock_client.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_client
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.deactivate_client(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        # Assert
        assert mock_client.is_active is False
        assert result["status"] == "inactive"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_client_sets_active_status(self):
        """Test that activating a client sets it to active."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock inactive client
        mock_client = MagicMock()
        mock_client.id = client_id
        mock_client.app_name = "Test App"
        mock_client.is_active = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_client
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.activate_client(
            client_id=client_id,
            owner_user_id=owner_user_id,
        )

        # Assert
        assert mock_client.is_active is True
        assert result["status"] == "active"
        mock_db.commit.assert_called_once()


class TestExternalAPIClientServiceUsageLogging:
    """Test cases for API usage logging."""

    @pytest.mark.asyncio
    async def test_log_api_usage_creates_usage_log(self):
        """Test that logging API usage creates a usage log entry."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id
        mock_client.last_used_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_client
        mock_db.execute.return_value = mock_result

        # Act
        await service.log_api_usage(
            client_id=client_id,
            endpoint="/api/v1/chat",
            method="POST",
            status_code=200,
            response_time_ms=150,
            ip_address="192.168.1.1",
            user_agent="Test Agent",
        )

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify usage log was created
        usage_log = mock_db.add.call_args[0][0]
        assert usage_log.client_id == client_id
        assert usage_log.endpoint == "/api/v1/chat"
        assert usage_log.method == "POST"
        assert usage_log.status_code == 200
        assert usage_log.response_time_ms == 150

    @pytest.mark.asyncio
    async def test_log_api_usage_updates_client_last_used_at(self):
        """Test that logging usage updates client's last_used_at timestamp."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id
        mock_client.last_used_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_client
        mock_db.execute.return_value = mock_result

        # Act
        await service.log_api_usage(
            client_id=client_id,
            endpoint="/api/v1/chat",
            method="POST",
            status_code=200,
            response_time_ms=150,
        )

        # Assert
        assert mock_client.last_used_at is not None


class TestExternalAPIClientServiceUsageStatistics:
    """Test cases for usage statistics."""

    @pytest.mark.asyncio
    async def test_get_usage_statistics_returns_correct_stats(self):
        """Test getting usage statistics returns correct data."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id

        # Mock queries
        mock_client_result = MagicMock()
        mock_client_result.scalar_one_or_none.return_value = mock_client

        mock_total_requests_result = MagicMock()
        mock_total_requests_result.scalar.return_value = 1000

        mock_avg_response_time_result = MagicMock()
        mock_avg_response_time_result.scalar.return_value = 125.5

        mock_error_count_result = MagicMock()
        mock_error_count_result.scalar.return_value = 50

        mock_db.execute.side_effect = [
            mock_client_result,
            mock_total_requests_result,
            mock_avg_response_time_result,
            mock_error_count_result,
        ]

        # Act
        result = await service.get_usage_statistics(
            client_id=client_id,
            owner_user_id=owner_user_id,
            days=7,
        )

        # Assert
        assert result["client_id"] == str(client_id)
        assert result["period_days"] == 7
        assert result["total_requests"] == 1000
        assert result["average_response_time_ms"] == 125.5
        assert result["error_count"] == 50
        assert result["error_rate_percent"] == 5.0  # 50/1000 * 100
        assert result["requests_per_day"] == pytest.approx(142.86, 0.01)  # 1000/7

    @pytest.mark.asyncio
    async def test_get_usage_statistics_handles_no_requests(self):
        """Test usage statistics with no requests."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        client_id = uuid4()
        owner_user_id = uuid4()

        # Mock client
        mock_client = MagicMock()
        mock_client.id = client_id

        # Mock queries - all return 0
        mock_client_result = MagicMock()
        mock_client_result.scalar_one_or_none.return_value = mock_client

        mock_total_requests_result = MagicMock()
        mock_total_requests_result.scalar.return_value = 0

        mock_avg_response_time_result = MagicMock()
        mock_avg_response_time_result.scalar.return_value = 0

        mock_error_count_result = MagicMock()
        mock_error_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [
            mock_client_result,
            mock_total_requests_result,
            mock_avg_response_time_result,
            mock_error_count_result,
        ]

        # Act
        result = await service.get_usage_statistics(
            client_id=client_id,
            owner_user_id=owner_user_id,
            days=7,
        )

        # Assert
        assert result["total_requests"] == 0
        assert result["error_rate_percent"] == 0  # Should handle division by zero
        assert result["requests_per_day"] == 0

    @pytest.mark.asyncio
    async def test_get_usage_statistics_raises_error_for_nonexistent_client(self):
        """Test that getting statistics raises error for non-existent client."""
        # Arrange
        mock_db = AsyncMock()
        service = ExternalAPIClientService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        client_id = uuid4()
        owner_user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Client not found"):
            await service.get_usage_statistics(client_id, owner_user_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
