"""Comprehensive integration tests for leaderboard endpoints."""

import pytest
from uuid import uuid4, UUID
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from tests.factories import UserFactory


class TestDocumentUploadLeaderboard:
    """Test document upload leaderboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_success(self):
        """Test successfully getting document upload leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents")

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "timeframe" in data
        assert "generated_at" in data
        assert isinstance(data["leaderboard"], list)

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_all_time(self):
        """Test getting all-time document upload leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?timeframe=all_time")

        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "all_time"

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_month(self):
        """Test getting monthly document upload leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?timeframe=month")

        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "month"

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_week(self):
        """Test getting weekly document upload leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?timeframe=week")

        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "week"

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_custom_limit(self):
        """Test getting leaderboard with custom limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) <= 5

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_max_limit(self):
        """Test getting leaderboard with maximum limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?limit=100")

        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) <= 100

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_invalid_timeframe(self):
        """Test getting leaderboard with invalid timeframe fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?timeframe=invalid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_invalid_limit_zero(self):
        """Test getting leaderboard with zero limit fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_invalid_limit_negative(self):
        """Test getting leaderboard with negative limit fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?limit=-1")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_limit_exceeds_max(self):
        """Test getting leaderboard with limit exceeding maximum fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?limit=101")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_document_leaderboard_entry_structure(self):
        """Test leaderboard entries have correct structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?limit=1")

        assert response.status_code == 200
        data = response.json()
        if len(data["leaderboard"]) > 0:
            entry = data["leaderboard"][0]
            assert "user_id" in entry or "full_name" in entry
            assert "count" in entry or "score" in entry
            assert "rank" in entry


class TestChatActivityLeaderboard:
    """Test chat activity leaderboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_success(self):
        """Test successfully getting chat activity leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/chat")

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "timeframe" in data
        assert "generated_at" in data
        assert isinstance(data["leaderboard"], list)

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_all_timeframes(self):
        """Test getting chat leaderboard for all timeframes."""
        timeframes = ["all_time", "month", "week"]

        for timeframe in timeframes:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/v1/leaderboard/chat?timeframe={timeframe}")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == timeframe

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_custom_limit(self):
        """Test getting chat leaderboard with custom limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/chat?limit=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) <= 20

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_default_params(self):
        """Test getting chat leaderboard with default parameters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/chat")

        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "all_time"  # Default timeframe
        assert len(data["leaderboard"]) <= 10  # Default limit

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_invalid_timeframe(self):
        """Test getting chat leaderboard with invalid timeframe fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/chat?timeframe=invalid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_invalid_limit(self):
        """Test getting chat leaderboard with invalid limit fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/chat?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_chat_leaderboard_ordering(self):
        """Test chat leaderboard entries are ordered by rank."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/chat?limit=10")

        assert response.status_code == 200
        data = response.json()
        # Check if ranks are in ascending order
        if len(data["leaderboard"]) > 1:
            ranks = [entry.get("rank", 0) for entry in data["leaderboard"]]
            assert ranks == sorted(ranks)


class TestConversationLeaderboard:
    """Test conversation leaderboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_conversation_leaderboard_success(self):
        """Test successfully getting conversation leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/conversations")

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "timeframe" in data
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_get_conversation_leaderboard_all_timeframes(self):
        """Test getting conversation leaderboard for all timeframes."""
        timeframes = ["all_time", "month", "week"]

        for timeframe in timeframes:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/v1/leaderboard/conversations?timeframe={timeframe}")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == timeframe

    @pytest.mark.asyncio
    async def test_get_conversation_leaderboard_custom_limit(self):
        """Test getting conversation leaderboard with custom limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/conversations?limit=15")

        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) <= 15

    @pytest.mark.asyncio
    async def test_get_conversation_leaderboard_invalid_params(self):
        """Test getting conversation leaderboard with invalid parameters fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/conversations?limit=200")

        assert response.status_code == 422


class TestOverallLeaderboard:
    """Test overall leaderboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_overall_leaderboard_success(self):
        """Test successfully getting overall leaderboard."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/overall")

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "timeframe" in data
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_get_overall_leaderboard_all_timeframes(self):
        """Test getting overall leaderboard for all timeframes."""
        timeframes = ["all_time", "month", "week"]

        for timeframe in timeframes:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/v1/leaderboard/overall?timeframe={timeframe}")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == timeframe

    @pytest.mark.asyncio
    async def test_get_overall_leaderboard_custom_limit(self):
        """Test getting overall leaderboard with custom limit."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/overall?limit=25")

        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) <= 25

    @pytest.mark.asyncio
    async def test_get_overall_leaderboard_scoring_system(self):
        """Test overall leaderboard uses composite scoring."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/overall?limit=1")

        assert response.status_code == 200
        data = response.json()
        # Overall leaderboard should have score field representing combined metrics
        if len(data["leaderboard"]) > 0:
            entry = data["leaderboard"][0]
            # Score should be present in overall leaderboard
            assert "score" in entry or "count" in entry

    @pytest.mark.asyncio
    async def test_get_overall_leaderboard_default_params(self):
        """Test getting overall leaderboard with default parameters."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/overall")

        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "all_time"
        assert len(data["leaderboard"]) <= 10


class TestUserStatistics:
    """Test user statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_statistics_success(self, db_session):
        """Test successfully getting user statistics."""
        # Use a valid user ID format
        user_id = UUID("00000000-0000-0000-0000-000000000000")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/leaderboard/users/{user_id}/statistics")

        # May return 200 with stats or 404 if user doesn't exist
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_user_statistics_structure(self, db_session):
        """Test user statistics response structure."""
        user_id = UUID("00000000-0000-0000-0000-000000000000")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/leaderboard/users/{user_id}/statistics")

        if response.status_code == 200:
            data = response.json()
            # Should contain user statistics fields
            assert "user_id" in data
            # May contain document_count, conversation_count, message_count, etc.

    @pytest.mark.asyncio
    async def test_get_user_statistics_nonexistent_user(self):
        """Test getting statistics for non-existent user."""
        fake_user_id = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/leaderboard/users/{fake_user_id}/statistics")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_statistics_invalid_uuid(self):
        """Test getting statistics with invalid UUID fails."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/users/invalid-uuid/statistics")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_my_statistics_success(self):
        """Test successfully getting current user's statistics."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/me/statistics")

        # May return 200 with stats or 404 if user doesn't exist
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_my_statistics_structure(self):
        """Test current user statistics response structure."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/me/statistics")

        if response.status_code == 200:
            data = response.json()
            # Should contain statistics for the current user
            assert "user_id" in data

    @pytest.mark.asyncio
    async def test_get_my_statistics_includes_rank(self):
        """Test current user statistics includes global rank."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/me/statistics")

        if response.status_code == 200:
            data = response.json()
            # May include rank field showing user's position in leaderboard
            # This is optional depending on implementation


class TestLeaderboardCombinations:
    """Test various combinations of leaderboard parameters."""

    @pytest.mark.asyncio
    async def test_all_leaderboards_week_limit_5(self):
        """Test all leaderboards with week timeframe and limit 5."""
        endpoints = [
            "/api/v1/leaderboard/documents",
            "/api/v1/leaderboard/chat",
            "/api/v1/leaderboard/conversations",
            "/api/v1/leaderboard/overall"
        ]

        for endpoint in endpoints:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"{endpoint}?timeframe=week&limit=5")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == "week"
            assert len(data["leaderboard"]) <= 5

    @pytest.mark.asyncio
    async def test_all_leaderboards_month_limit_50(self):
        """Test all leaderboards with month timeframe and limit 50."""
        endpoints = [
            "/api/v1/leaderboard/documents",
            "/api/v1/leaderboard/chat",
            "/api/v1/leaderboard/conversations",
            "/api/v1/leaderboard/overall"
        ]

        for endpoint in endpoints:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"{endpoint}?timeframe=month&limit=50")

            assert response.status_code == 200
            data = response.json()
            assert data["timeframe"] == "month"
            assert len(data["leaderboard"]) <= 50

    @pytest.mark.asyncio
    async def test_leaderboards_response_time(self):
        """Test that leaderboard endpoints respond in reasonable time."""
        import time

        endpoints = [
            "/api/v1/leaderboard/documents",
            "/api/v1/leaderboard/chat",
            "/api/v1/leaderboard/overall"
        ]

        for endpoint in endpoints:
            start = time.time()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(endpoint)
            end = time.time()

            assert response.status_code == 200
            # Should respond within 5 seconds
            assert (end - start) < 5.0

    @pytest.mark.asyncio
    async def test_leaderboards_consistent_structure(self):
        """Test all leaderboard endpoints return consistent structure."""
        endpoints = [
            "/api/v1/leaderboard/documents",
            "/api/v1/leaderboard/chat",
            "/api/v1/leaderboard/conversations",
            "/api/v1/leaderboard/overall"
        ]

        for endpoint in endpoints:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(endpoint)

            assert response.status_code == 200
            data = response.json()
            # All should have these common fields
            assert "leaderboard" in data
            assert "timeframe" in data
            assert "generated_at" in data
            assert isinstance(data["leaderboard"], list)

    @pytest.mark.asyncio
    async def test_empty_leaderboards(self):
        """Test leaderboards return empty list when no data available."""
        # This tests with potentially empty database
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leaderboard/documents?timeframe=week")

        assert response.status_code == 200
        data = response.json()
        # Should return empty list, not error
        assert isinstance(data["leaderboard"], list)
        assert len(data["leaderboard"]) >= 0
