"""Unit tests for database configuration."""

import pytest
from app.core.config import Settings


class TestDatabaseConfiguration:
    """Test suite for database configuration with separate parameters."""

    def test_database_url_construction(self):
        """Test database URL is constructed from individual parameters."""
        settings = Settings(
            database_host="testhost",
            database_port=5555,
            database_user="testuser",
            database_password="testpass",
            database_name="testdb",
            database_driver="postgresql+asyncpg",
        )

        expected_url = "postgresql+asyncpg://testuser:testpass@testhost:5555/testdb"
        assert settings.database_url == expected_url

    def test_get_database_url_with_custom_database(self):
        """Test get_database_url with custom database name."""
        settings = Settings(
            database_host="localhost",
            database_port=5433,
            database_user="postgres",
            database_password="postgres",
            database_name="shia_chatbot",
        )

        # Get URL for different database
        postgres_url = settings.get_database_url("postgres")
        expected = "postgresql+asyncpg://postgres:postgres@localhost:5433/postgres"
        assert postgres_url == expected

    def test_database_url_with_special_characters(self):
        """Test database URL construction with special characters in password."""
        settings = Settings(
            database_host="localhost",
            database_port=5432,
            database_user="user",
            database_password="p@ss!w0rd#123",
            database_name="testdb",
        )

        # URL should contain special characters
        assert "p@ss!w0rd#123" in settings.database_url

    def test_default_database_parameters(self):
        """Test default database parameters are set correctly."""
        settings = Settings()

        assert settings.database_host == "localhost"
        assert settings.database_port == 5433
        assert settings.database_user == "postgres"
        assert settings.database_name == "shia_chatbot"
        assert settings.database_driver == "postgresql+asyncpg"

    def test_database_pool_settings(self):
        """Test database pool configuration."""
        settings = Settings(
            database_pool_size=50,
            database_max_overflow=20,
        )

        assert settings.database_pool_size == 50
        assert settings.database_max_overflow == 20

    def test_environment_parameter_override(self, monkeypatch):
        """Test individual parameters can be overridden by environment variables."""
        monkeypatch.setenv("DATABASE_HOST", "prodhost")
        monkeypatch.setenv("DATABASE_PORT", "5432")
        monkeypatch.setenv("DATABASE_USER", "produser")
        monkeypatch.setenv("DATABASE_PASSWORD", "prodpass")
        monkeypatch.setenv("DATABASE_NAME", "proddb")

        settings = Settings()

        assert settings.database_host == "prodhost"
        assert settings.database_port == 5432
        assert settings.database_user == "produser"
        assert settings.database_password == "prodpass"
        assert settings.database_name == "proddb"

        # URL should reflect the overridden values
        expected = "postgresql+asyncpg://produser:prodpass@prodhost:5432/proddb"
        assert settings.database_url == expected

    def test_database_url_immutable(self):
        """Test database_url property returns consistent values."""
        settings = Settings(
            database_host="localhost",
            database_port=5433,
            database_user="postgres",
            database_password="postgres",
            database_name="testdb",
        )

        url1 = settings.database_url
        url2 = settings.database_url

        # Should return the same value
        assert url1 == url2

    def test_get_database_url_none_parameter(self):
        """Test get_database_url with None uses default database name."""
        settings = Settings(database_name="default_db")

        # None should use default database name
        url_none = settings.get_database_url(None)
        url_default = settings.database_url

        assert url_none == url_default

    def test_database_driver_customization(self):
        """Test custom database driver."""
        settings = Settings(
            database_driver="postgresql+psycopg",
            database_user="user",
            database_password="pass",
            database_host="host",
            database_port=5432,
            database_name="db",
        )

        assert "postgresql+psycopg://" in settings.database_url


class TestSettingsProperties:
    """Test suite for settings properties."""

    def test_is_development(self):
        """Test is_development property."""
        settings = Settings(environment="dev")
        assert settings.is_development is True

        settings = Settings(environment="prod")
        assert settings.is_development is False

    def test_is_production(self):
        """Test is_production property."""
        settings = Settings(environment="prod")
        assert settings.is_production is True

        settings = Settings(environment="dev")
        assert settings.is_production is False

    def test_is_test(self):
        """Test is_test property."""
        settings = Settings(environment="test")
        assert settings.is_test is True

        settings = Settings(environment="dev")
        assert settings.is_test is False

    def test_show_docs(self):
        """Test show_docs property."""
        # Debug mode should show docs
        settings = Settings(debug=True)
        assert settings.show_docs is True

        # Production without debug should not show docs
        settings = Settings(environment="prod", debug=False)
        assert settings.show_docs is False

        # Dev environment always shows docs
        settings = Settings(environment="dev", debug=False)
        assert settings.show_docs is True
