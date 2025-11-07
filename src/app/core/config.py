"""Application configuration management."""

from typing import Literal
from pydantic import Field, field_validator, model_validator
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

    # Database - Separate Parameters (recommended for production)
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5433)
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="postgres")
    database_name: str = Field(default="shia_chatbot")
    database_driver: str = Field(default="postgresql+asyncpg")
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    # Database - Connection parameters (recommended for production)
    # Note: Individual parameters are always used to build the connection URL
    # This ensures better security and configuration management

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

    # OpenRouter (Unified LLM API - Recommended)
    openrouter_api_key: str | None = Field(default=None)
    openrouter_app_name: str = Field(default="WisQu Islamic Chatbot")
    openrouter_app_url: str = Field(default="https://wisqu.com")

    # LLM Configuration (Used by LangGraph)
    llm_provider: Literal["openrouter", "openai", "anthropic"] = Field(default="openrouter")
    llm_model: str = Field(default="anthropic/claude-3.5-sonnet")
    llm_temperature: float = Field(default=0.7)
    llm_max_tokens: int = Field(default=4096)

    # Embeddings
    embedding_provider: Literal["gemini", "cohere", "openrouter"] = Field(default="gemini")
    embedding_model: str = Field(default="gemini-embedding-001")
    embedding_dimension: int = Field(default=3072)

    # Web Search
    web_search_enabled: bool = Field(default=True)
    web_search_provider: Literal["tavily", "serper"] = Field(default="tavily")
    tavily_api_key: str | None = Field(default=None)
    serper_api_key: str | None = Field(default=None)

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

    # Logging (Standard v2.0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="DEBUG")
    log_format: Literal["colored", "json"] = Field(default="colored")
    log_timestamp: Literal["utc", "ir", "both"] = Field(default="both")
    log_timestamp_precision: Literal[3, 6] = Field(default=6)  # 3=ms, 6=μs
    log_color: Literal["auto", "true", "false"] = Field(default="auto")
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

    # Super Admin (for initial setup)
    super_admin_email: str = Field(default="admin@wisqu.com")
    super_admin_password: str = Field(default="ChangeMe123!")

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator("debug", mode="before")
    @classmethod
    def set_debug_from_environment(cls, v, info):
        """Automatically set debug based on environment if not explicitly set."""
        if v is None:
            environment = info.data.get("environment", "dev")
            return environment == "dev"
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def set_log_level_from_environment(cls, v, info):
        """Automatically set log level based on environment if not explicitly set."""
        if v is None:
            environment = info.data.get("environment", "dev")
            return {"dev": "DEBUG", "test": "INFO", "prod": "WARNING"}[environment]
        return v

    @field_validator("log_format", mode="before")
    @classmethod
    def set_log_format_from_environment(cls, v, info):
        """Automatically set log format based on environment if not explicitly set."""
        if v is None:
            environment = info.data.get("environment", "dev")
            return "colored" if environment == "dev" else "json"
        return v

    @field_validator("log_timestamp_precision", mode="before")
    @classmethod
    def convert_log_timestamp_precision(cls, v):
        """Convert string to int for log_timestamp_precision."""
        if isinstance(v, str):
            return int(v)
        return v

    @model_validator(mode="after")
    def validate_production_secrets(self):
        """Validate that production environments have secure secrets."""
        if self.environment == "prod":
            # Check JWT secret
            if self.jwt_secret_key == "change-in-production":
                raise ValueError(
                    "JWT_SECRET_KEY must be changed in production environment"
                )

            # Warn about debug mode in production
            if self.debug:
                import warnings
                warnings.warn(
                    "DEBUG mode is enabled in production. This is not recommended.",
                    UserWarning
                )

        return self

    def get_database_url(self, database_name: str | None = None) -> str:
        """
        Build database URL from individual parameters.

        Args:
            database_name: Optional database name override (useful for connecting to 'postgres' db)

        Returns:
            str: Complete database URL
        """
        db_name = database_name if database_name is not None else self.database_name
        return (
            f"{self.database_driver}://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{db_name}"
        )

    @property
    def database_url(self) -> str:
        """
        Get the database URL as a computed property.

        This ensures the URL is always constructed from individual parameters,
        preventing environment variable override issues.

        Returns:
            str: Complete database URL
        """
        return self.get_database_url()

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

    @property
    def show_docs(self) -> bool:
        """Whether to show API documentation endpoints."""
        return self.debug or self.environment != "prod"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    This function is used for dependency injection in FastAPI.

    Returns:
        Settings: The global settings instance
    """
    return settings
