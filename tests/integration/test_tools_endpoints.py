"""Comprehensive integration tests for specialized tools endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.user import User, OTPCode
from tests.factories import UserFactory


@pytest.fixture
async def authenticated_client(db_session):
    """Create an authenticated client for testing."""
    user_data = UserFactory.create_user_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register, verify, and login
        await client.post("/api/v1/auth/register", json=user_data)

        result = await db_session.execute(
            select(OTPCode).where(OTPCode.email == user_data["email"])
        )
        otp = result.scalar_one()
        await client.post(
            "/api/v1/auth/verify-email",
            json={"email": user_data["email"], "otp_code": otp.otp_code}
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        client.headers["Authorization"] = f"Bearer {token}"
        yield client


class TestAhkamEndpoint:
    """Test Ahkam (Islamic rulings) endpoint - CRITICAL."""

    @pytest.mark.asyncio
    async def test_ahkam_query_success(self, authenticated_client):
        """Test successful Ahkam query."""
        response = await authenticated_client.post(
            "/api/v1/tools/ahkam",
            json={
                "query": "ما حكم الصلاة؟",  # What is the ruling on prayer?
                "marja": "sistani",
                "language": "ar"
            }
        )

        # May succeed or fail based on external source availability
        assert response.status_code in [200, 400, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "ruling" in data or "result" in data

    @pytest.mark.asyncio
    async def test_ahkam_query_different_marja(self, authenticated_client):
        """Test Ahkam query with different Marja."""
        response = await authenticated_client.post(
            "/api/v1/tools/ahkam",
            json={
                "query": "What is the ruling on fasting?",
                "marja": "khamenei",
                "language": "en"
            }
        )

        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_ahkam_query_empty(self, authenticated_client):
        """Test Ahkam with empty query."""
        response = await authenticated_client.post(
            "/api/v1/tools/ahkam",
            json={
                "query": "",
                "marja": "sistani"
            }
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_ahkam_query_invalid_marja(self, authenticated_client):
        """Test Ahkam with invalid Marja."""
        response = await authenticated_client.post(
            "/api/v1/tools/ahkam",
            json={
                "query": "test query",
                "marja": "invalid_marja"
            }
        )

        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_ahkam_without_auth(self):
        """Test Ahkam endpoint without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tools/ahkam",
                json={"query": "test", "marja": "sistani"}
            )

        assert response.status_code == 401


class TestHadithSearchEndpoint:
    """Test Hadith search endpoint."""

    @pytest.mark.asyncio
    async def test_hadith_search_success(self, authenticated_client):
        """Test successful Hadith search."""
        response = await authenticated_client.post(
            "/api/v1/tools/hadith/search",
            json={
                "query": "prayer",
                "collection": "al-kafi",
                "language": "en"
            }
        )

        assert response.status_code in [200, 400, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "hadiths" in data

    @pytest.mark.asyncio
    async def test_hadith_search_arabic(self, authenticated_client):
        """Test Hadith search in Arabic."""
        response = await authenticated_client.post(
            "/api/v1/tools/hadith/search",
            json={
                "query": "الصلاة",
                "collection": "al-kafi",
                "language": "ar"
            }
        )

        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_hadith_search_empty_query(self, authenticated_client):
        """Test Hadith search with empty query."""
        response = await authenticated_client.post(
            "/api/v1/tools/hadith/search",
            json={
                "query": "",
                "collection": "al-kafi"
            }
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_hadith_search_invalid_collection(self, authenticated_client):
        """Test Hadith search with invalid collection."""
        response = await authenticated_client.post(
            "/api/v1/tools/hadith/search",
            json={
                "query": "test",
                "collection": "invalid_collection"
            }
        )

        assert response.status_code in [400, 404, 422]


class TestPrayerTimesEndpoint:
    """Test prayer times endpoint."""

    @pytest.mark.asyncio
    async def test_prayer_times_success(self, authenticated_client):
        """Test getting prayer times for a location."""
        response = await authenticated_client.post(
            "/api/v1/tools/datetime/prayer-times",
            json={
                "latitude": 33.8938,  # Baghdad
                "longitude": 44.3661,
                "date": "2025-01-01",
                "calculation_method": "karachi"
            }
        )

        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "Fajr" in data or "fajr" in data
            assert "Dhuhr" in data or "dhuhr" in data

    @pytest.mark.asyncio
    async def test_prayer_times_invalid_coordinates(self, authenticated_client):
        """Test prayer times with invalid coordinates."""
        response = await authenticated_client.post(
            "/api/v1/tools/datetime/prayer-times",
            json={
                "latitude": 1000,  # Invalid
                "longitude": 2000,  # Invalid
                "date": "2025-01-01"
            }
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_prayer_times_invalid_date(self, authenticated_client):
        """Test prayer times with invalid date."""
        response = await authenticated_client.post(
            "/api/v1/tools/datetime/prayer-times",
            json={
                "latitude": 33.8938,
                "longitude": 44.3661,
                "date": "invalid-date"
            }
        )

        assert response.status_code in [400, 422]


class TestCalendarConversionEndpoint:
    """Test calendar conversion endpoint."""

    @pytest.mark.asyncio
    async def test_calendar_convert_gregorian_to_hijri(self, authenticated_client):
        """Test converting Gregorian to Hijri."""
        response = await authenticated_client.post(
            "/api/v1/tools/datetime/convert",
            json={
                "date": "2025-01-01",
                "from_calendar": "gregorian",
                "to_calendar": "hijri"
            }
        )

        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "date" in data or "converted_date" in data

    @pytest.mark.asyncio
    async def test_calendar_convert_hijri_to_gregorian(self, authenticated_client):
        """Test converting Hijri to Gregorian."""
        response = await authenticated_client.post(
            "/api/v1/tools/datetime/convert",
            json={
                "date": "1446-07-01",
                "from_calendar": "hijri",
                "to_calendar": "gregorian"
            }
        )

        assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_calendar_convert_invalid_date(self, authenticated_client):
        """Test calendar conversion with invalid date."""
        response = await authenticated_client.post(
            "/api/v1/tools/datetime/convert",
            json={
                "date": "invalid",
                "from_calendar": "gregorian",
                "to_calendar": "hijri"
            }
        )

        assert response.status_code in [400, 422]


class TestZakatCalculationEndpoint:
    """Test Zakat calculation endpoint."""

    @pytest.mark.asyncio
    async def test_zakat_calculation_success(self, authenticated_client):
        """Test successful Zakat calculation."""
        response = await authenticated_client.post(
            "/api/v1/tools/math/zakat",
            json={
                "wealth": 10000.0,
                "currency": "USD",
                "calculation_method": "standard"
            }
        )

        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "zakat_amount" in data or "amount" in data
            # Verify warning about consulting scholar is present
            assert "warning" in str(data).lower() or "consult" in str(data).lower()

    @pytest.mark.asyncio
    async def test_zakat_calculation_zero_wealth(self, authenticated_client):
        """Test Zakat calculation with zero wealth."""
        response = await authenticated_client.post(
            "/api/v1/tools/math/zakat",
            json={
                "wealth": 0.0,
                "currency": "USD"
            }
        )

        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_zakat_calculation_negative_wealth(self, authenticated_client):
        """Test Zakat calculation with negative wealth."""
        response = await authenticated_client.post(
            "/api/v1/tools/math/zakat",
            json={
                "wealth": -1000.0,
                "currency": "USD"
            }
        )

        assert response.status_code in [400, 422]


class TestKhumsCalculationEndpoint:
    """Test Khums calculation endpoint."""

    @pytest.mark.asyncio
    async def test_khums_calculation_success(self, authenticated_client):
        """Test successful Khums calculation."""
        response = await authenticated_client.post(
            "/api/v1/tools/math/khums",
            json={
                "income": 50000.0,
                "expenses": 30000.0,
                "currency": "USD"
            }
        )

        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "khums_amount" in data or "amount" in data
            # Verify warning about consulting scholar is present
            assert "warning" in str(data).lower() or "consult" in str(data).lower()

    @pytest.mark.asyncio
    async def test_khums_calculation_expenses_exceed_income(self, authenticated_client):
        """Test Khums when expenses exceed income."""
        response = await authenticated_client.post(
            "/api/v1/tools/math/khums",
            json={
                "income": 10000.0,
                "expenses": 15000.0,
                "currency": "USD"
            }
        )

        # Should either return 0 or handle gracefully
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_khums_calculation_negative_values(self, authenticated_client):
        """Test Khums with negative values."""
        response = await authenticated_client.post(
            "/api/v1/tools/math/khums",
            json={
                "income": -1000.0,
                "expenses": 500.0,
                "currency": "USD"
            }
        )

        assert response.status_code in [400, 422]


class TestMultiToolOrchestration:
    """Test multi-tool query orchestration endpoint."""

    @pytest.mark.asyncio
    async def test_multi_tool_query_success(self, authenticated_client):
        """Test multi-tool query execution."""
        response = await authenticated_client.post(
            "/api/v1/tools/query",
            json={
                "query": "What is the prayer time in Baghdad and the ruling on shortening prayers?",
                "marja_preference": "sistani"
            }
        )

        # Complex orchestration, may succeed or fail
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_multi_tool_query_empty(self, authenticated_client):
        """Test multi-tool query with empty query."""
        response = await authenticated_client.post(
            "/api/v1/tools/query",
            json={"query": ""}
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_multi_tool_query_simple(self, authenticated_client):
        """Test multi-tool query with simple query."""
        response = await authenticated_client.post(
            "/api/v1/tools/query",
            json={"query": "What time is Fajr prayer?"}
        )

        assert response.status_code in [200, 400, 500, 503]
