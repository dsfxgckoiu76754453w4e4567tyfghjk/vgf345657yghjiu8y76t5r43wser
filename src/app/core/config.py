"""Application configuration management."""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["dev", "test", "prod"] = Field(default="dev")

    # Application
    app_name: str = Field(default="Shia Islamic Chatbot")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=True)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/shia_chatbot"
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_db: int = Field(default=1)
    redis_queue_db: int = Field(default=2)

    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection_name: str = Field(default="islamic_knowledge")

    # JWT & Security
    jwt_secret_key: str = Field(default="change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # Google OAuth
    google_client_id: str | None = Field(default=None)
    google_client_secret: str | None = Field(default=None)
    google_redirect_uri: str = Field(default="http://localhost:8000/auth/google/callback")

    # LLM Providers
    openai_api_key: str | None = Field(default=None)
    openai_org_id: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)
    google_api_key: str | None = Field(default=None)
    google_project_id: str | None = Field(default=None)
    google_location: str = Field(default="us-central1")
    cohere_api_key: str | None = Field(default=None)

    # Embeddings
    embedding_provider: Literal["gemini", "cohere"] = Field(default="gemini")
    embedding_model: str = Field(default="gemini-embedding-001")
    embedding_dimension: int = Field(default=3072)

    # Reranker
    reranker_provider: Literal["cohere", "vertex"] = Field(default="cohere")
    reranker_model: str = Field(default="rerank-3.5")

    # ASR
    asr_provider: Literal["google", "whisper"] = Field(default="google")
    google_speech_api_key: str | None = Field(default=None)

    # Chonkie
    chunking_strategy: Literal["semantic", "token", "sentence", "adaptive"] = Field(
        default="semantic"
    )
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)

    # mem0
    mem0_enabled: bool = Field(default=True)
    mem0_compression_enabled: bool = Field(default=True)

    # Guardrails
    guardrails_enabled: bool = Field(default=True)
    guardrails_llm_provider: str = Field(default="openai")
    guardrails_llm_model: str = Field(default="gpt-4o-mini")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="DEBUG")
    log_format: Literal["colored", "json"] = Field(default="colored")
    langfuse_enabled: bool = Field(default=False)
    langfuse_public_key: str | None = Field(default=None)
    langfuse_secret_key: str | None = Field(default=None)
    langfuse_host: str = Field(default="http://localhost:3000")

    # Rate Limiting
    rate_limit_anonymous: int = Field(default=5)
    rate_limit_free: int = Field(default=10)
    rate_limit_premium: int = Field(default=50)
    rate_limit_unlimited: int = Field(default=1000)
    rate_limit_test: int = Field(default=10000)

    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000")
    cors_allow_credentials: bool = Field(default=True)

    # External API
    external_api_enabled: bool = Field(default=True)
    external_api_default_rate_limit: int = Field(default=100)

    # Ahkam Tool
    ahkam_cache_ttl_hours: int = Field(default=24)
    ahkam_fetch_timeout_seconds: int = Field(default=30)
    ahkam_max_retries: int = Field(default=3)

    # HuggingFace
    huggingface_token: str | None = Field(default=None)
    huggingface_repo_id: str | None = Field(default=None)

    # Email
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str | None = Field(default=None)
    smtp_password: str | None = Field(default=None)
    smtp_from_email: str = Field(default="noreply@example.com")

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "prod"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "dev"

    @property
    def is_test(self) -> bool:
        """Check if running in test."""
        return self.environment == "test"


# Global settings instance
settings = Settings()
