"""Integration tests for health API endpoints."""

import pytest
from httpx import AsyncClient
from app.main import app


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_basic(self):
        """Test basic health endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # Check basic fields
            assert "status" in data
            assert "timestamp" in data
            assert "environment" in data
            assert "version" in data
            assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_with_services(self):
        """Test health endpoint includes service checks."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # Check services
            assert "services" in data
            assert "database" in data["services"]
            assert "redis" in data["services"]
            assert "qdrant" in data["services"]

            # Each service should have status
            for service_name, service_data in data["services"].items():
                assert "status" in service_data

    @pytest.mark.asyncio
    async def test_health_endpoint_response_structure(self):
        """Test health endpoint response structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

            data = response.json()

            # Check status is one of the expected values
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

            # Check uptime is positive
            assert data["uptime_seconds"] >= 0

            # Check environment
            assert data["environment"] in ["dev", "test", "prod"]


class TestRootEndpoint:
    """Test suite for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

            assert response.status_code == 200
            data = response.json()

            # Check basic API info
            assert "message" in data or "name" in data
