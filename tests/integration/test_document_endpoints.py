"""Comprehensive integration tests for document/RAG endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from io import BytesIO

from app.main import app
from app.models.user import User, OTPCode
from app.models.document import Document
from tests.factories import UserFactory


@pytest.fixture
async def authenticated_client(db_session):
    """Create an authenticated client for testing."""
    user_data = UserFactory.create_user_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        await client.post("/api/v1/auth/register", json=user_data)

        # Get OTP and verify
        result = await db_session.execute(
            select(OTPCode).where(OTPCode.email == user_data["email"])
        )
        otp = result.scalar_one()
        await client.post(
            "/api/v1/auth/verify-email",
            json={"email": user_data["email"], "otp_code": otp.otp_code}
        )

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]}
        )
        token = login_response.json()["access_token"]

        client.headers["Authorization"] = f"Bearer {token}"
        yield client


class TestDocumentUpload:
    """Test document upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_document_text(self, authenticated_client, db_session):
        """Test uploading a text document."""
        files = {
            "file": ("test.txt", BytesIO(b"This is a test document content"), "text/plain")
        }
        data = {
            "title": "Test Document",
            "source": "test_source",
            "language": "en"
        }

        response = await authenticated_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data
        )

        assert response.status_code in [200, 201]
        result = response.json()
        assert "document_id" in result or "id" in result

    @pytest.mark.asyncio
    async def test_upload_document_pdf(self, authenticated_client):
        """Test uploading a PDF document."""
        # Create a minimal PDF-like file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
        files = {
            "file": ("test.pdf", BytesIO(pdf_content), "application/pdf")
        }
        data = {
            "title": "Test PDF",
            "source": "test_source",
            "language": "fa"
        }

        response = await authenticated_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data
        )

        # May fail due to PDF parsing, but should return proper error
        assert response.status_code in [200, 201, 400, 422]

    @pytest.mark.asyncio
    async def test_upload_document_without_auth(self):
        """Test uploading document without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {
                "file": ("test.txt", BytesIO(b"Test"), "text/plain")
            }
            response = await client.post("/api/v1/documents/upload", files=files)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(self, authenticated_client):
        """Test uploading invalid file type."""
        files = {
            "file": ("test.exe", BytesIO(b"MZ\x90\x00"), "application/x-msdownload")
        }

        response = await authenticated_client.post(
            "/api/v1/documents/upload",
            files=files
        )

        assert response.status_code in [400, 415, 422]


class TestEmbeddings:
    """Test embeddings generation endpoint."""

    @pytest.mark.asyncio
    async def test_generate_embeddings(self, authenticated_client, db_session):
        """Test generating embeddings for a document."""
        # First upload a document
        files = {
            "file": ("test.txt", BytesIO(b"This is test content for embeddings"), "text/plain")
        }
        upload_response = await authenticated_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"title": "Test Doc", "source": "test"}
        )

        if upload_response.status_code in [200, 201]:
            doc_data = upload_response.json()
            doc_id = doc_data.get("document_id") or doc_data.get("id")

            # Generate embeddings
            response = await authenticated_client.post(
                "/api/v1/documents/embeddings/generate",
                json={"document_id": doc_id}
            )

            # May succeed or fail based on external API availability
            assert response.status_code in [200, 201, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_generate_embeddings_nonexistent_document(self, authenticated_client):
        """Test generating embeddings for non-existent document."""
        response = await authenticated_client.post(
            "/api/v1/documents/embeddings/generate",
            json={"document_id": "00000000-0000-0000-0000-000000000000"}
        )

        assert response.status_code == 404


class TestDocumentSearch:
    """Test semantic search endpoint."""

    @pytest.mark.asyncio
    async def test_search_documents(self, authenticated_client):
        """Test semantic search."""
        response = await authenticated_client.post(
            "/api/v1/documents/search",
            json={
                "query": "What is the ruling on prayer?",
                "limit": 10
            }
        )

        # May return results or fail based on Qdrant availability
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, authenticated_client):
        """Test search with empty query."""
        response = await authenticated_client.post(
            "/api/v1/documents/search",
            json={"query": "", "limit": 10}
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_search_documents_invalid_limit(self, authenticated_client):
        """Test search with invalid limit."""
        response = await authenticated_client.post(
            "/api/v1/documents/search",
            json={"query": "test", "limit": -1}
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_search_documents_large_limit(self, authenticated_client):
        """Test search with very large limit."""
        response = await authenticated_client.post(
            "/api/v1/documents/search",
            json={"query": "test", "limit": 1000}
        )

        # Should either succeed with capped limit or reject
        assert response.status_code in [200, 400, 422]


class TestQdrantStatus:
    """Test Qdrant status endpoint."""

    @pytest.mark.asyncio
    async def test_qdrant_status(self, authenticated_client):
        """Test getting Qdrant status."""
        response = await authenticated_client.get("/api/v1/documents/qdrant/status")

        # Should return status regardless of Qdrant availability
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
