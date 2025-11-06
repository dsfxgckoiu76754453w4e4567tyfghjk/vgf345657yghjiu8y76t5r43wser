"""Unit tests for health check functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.health import HealthChecker, get_health_status
from app.core.constants import ServiceStatus


class TestHealthChecker:
    """Test suite for HealthChecker."""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance."""
        return HealthChecker()

    @pytest.mark.asyncio
    async def test_check_database_healthy(self, health_checker):
        """Test database health check when healthy."""
        with patch("app.core.health.create_async_engine") as mock_engine:
            # Mock engine and connection
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_engine.return_value.connect = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
            )

            result = await health_checker.check_database()

            assert result["status"] == ServiceStatus.HEALTHY
            assert "latency_ms" in result
            assert result["message"] == "Database connection successful"

    @pytest.mark.asyncio
    async def test_check_database_unhealthy(self, health_checker):
        """Test database health check when unhealthy."""
        with patch("app.core.health.create_async_engine") as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")

            result = await health_checker.check_database()

            assert result["status"] == ServiceStatus.UNHEALTHY
            assert "error" in result

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self, health_checker):
        """Test Redis health check when healthy."""
        with patch("app.core.health.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client

            result = await health_checker.check_redis()

            assert result["status"] == ServiceStatus.HEALTHY
            assert "latency_ms" in result
            assert result["message"] == "Redis connection successful"

    @pytest.mark.asyncio
    async def test_check_redis_unhealthy(self, health_checker):
        """Test Redis health check when unhealthy."""
        with patch("app.core.health.aioredis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")

            result = await health_checker.check_redis()

            assert result["status"] == ServiceStatus.UNHEALTHY
            assert "error" in result

    @pytest.mark.asyncio
    async def test_check_qdrant_healthy(self, health_checker):
        """Test Qdrant health check when healthy."""
        with patch("app.core.health.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=AsyncMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value = mock_ctx

            result = await health_checker.check_qdrant()

            assert result["status"] == ServiceStatus.HEALTHY
            assert "latency_ms" in result
            assert result["message"] == "Qdrant connection successful"

    @pytest.mark.asyncio
    async def test_check_qdrant_unhealthy(self, health_checker):
        """Test Qdrant health check when unhealthy."""
        with patch("app.core.health.httpx.AsyncClient") as mock_client:
            mock_client.side_effect = Exception("Connection failed")

            result = await health_checker.check_qdrant()

            assert result["status"] == ServiceStatus.UNHEALTHY
            assert "error" in result

    @pytest.mark.asyncio
    async def test_check_all_services_all_healthy(self, health_checker):
        """Test check_all_services when all services are healthy."""
        # Mock all checks to return healthy
        health_checker.check_database = AsyncMock(return_value={
            "status": ServiceStatus.HEALTHY,
            "latency_ms": 2.0
        })
        health_checker.check_redis = AsyncMock(return_value={
            "status": ServiceStatus.HEALTHY,
            "latency_ms": 1.0
        })
        health_checker.check_qdrant = AsyncMock(return_value={
            "status": ServiceStatus.HEALTHY,
            "latency_ms": 5.0
        })

        result = await health_checker.check_all_services()

        assert result["status"] == ServiceStatus.HEALTHY
        assert "database" in result["services"]
        assert "redis" in result["services"]
        assert "qdrant" in result["services"]

    @pytest.mark.asyncio
    async def test_check_all_services_one_degraded(self, health_checker):
        """Test check_all_services when one service is unhealthy."""
        health_checker.check_database = AsyncMock(return_value={
            "status": ServiceStatus.HEALTHY,
        })
        health_checker.check_redis = AsyncMock(return_value={
            "status": ServiceStatus.UNHEALTHY,
            "error": "Connection failed"
        })
        health_checker.check_qdrant = AsyncMock(return_value={
            "status": ServiceStatus.HEALTHY,
        })

        result = await health_checker.check_all_services()

        # Overall status should be degraded
        assert result["status"] == ServiceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_check_all_services_all_unhealthy(self, health_checker):
        """Test check_all_services when all services are unhealthy."""
        health_checker.check_database = AsyncMock(return_value={
            "status": ServiceStatus.UNHEALTHY,
        })
        health_checker.check_redis = AsyncMock(return_value={
            "status": ServiceStatus.UNHEALTHY,
        })
        health_checker.check_qdrant = AsyncMock(return_value={
            "status": ServiceStatus.UNHEALTHY,
        })

        result = await health_checker.check_all_services()

        # Overall status should be unhealthy
        assert result["status"] == ServiceStatus.UNHEALTHY


class TestGetHealthStatus:
    """Test suite for get_health_status function."""

    @pytest.mark.asyncio
    async def test_get_health_status_without_dependencies(self):
        """Test get_health_status without checking dependencies."""
        result = await get_health_status(check_dependencies=False)

        assert result["status"] == ServiceStatus.HEALTHY
        assert "timestamp" in result
        assert "environment" in result
        assert "version" in result
        assert "uptime_seconds" in result
        assert "services" not in result  # Dependencies not checked

    @pytest.mark.asyncio
    async def test_get_health_status_with_dependencies(self):
        """Test get_health_status with dependency checks."""
        with patch("app.core.health._health_checker.check_all_services") as mock_check:
            mock_check.return_value = {
                "status": ServiceStatus.HEALTHY,
                "services": {
                    "database": {"status": ServiceStatus.HEALTHY},
                    "redis": {"status": ServiceStatus.HEALTHY},
                    "qdrant": {"status": ServiceStatus.HEALTHY},
                }
            }

            result = await get_health_status(check_dependencies=True)

            assert result["status"] == ServiceStatus.HEALTHY
            assert "services" in result
            assert "database" in result["services"]
