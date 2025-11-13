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

    # Temporal Workflow Engine
    temporal_host: str = Field(default="localhost:7233")
    temporal_namespace: str = Field(default="default")
    temporal_task_queue: str = Field(default="chat-queue")
    temporal_enabled: bool = Field(default=False)  # Enable for hybrid mode
    

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

    # Database Read Replica (for read scaling)
    database_read_replica_host: str | None = Field(default=None)  # If None, uses primary
    database_read_replica_port: int | None = Field(default=None)
    database_read_replica_enabled: bool = Field(default=False)

    # Database - Connection parameters (recommended for production)
    # Note: Individual parameters are always used to build the connection URL
    # This ensures better security and configuration management

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_db: int = Field(default=1)
    redis_queue_db: int = Field(default=2)

    # Celery
    celery_broker_url: str | None = Field(default=None)  # Auto-configured from redis_url
    celery_result_backend: str | None = Field(default=None)  # Auto-configured from database_url
    celery_task_always_eager: bool = Field(default=False)  # Sync execution for testing
    celery_task_eager_propagates: bool = Field(default=True)  # Propagate exceptions in eager mode

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
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_app_name: str = Field(default="WisQu Islamic Chatbot")
    openrouter_app_url: str = Field(default="https://wisqu.com")
    openrouter_model: str = Field(default="anthropic/claude-3.5-sonnet")

    # LLM Configuration (Used by LangGraph)
    llm_provider: Literal["openrouter", "openai", "anthropic"] = Field(default="openrouter")
    llm_model: str = Field(default="anthropic/claude-3.5-sonnet")
    llm_temperature: float = Field(default=0.7)
    llm_max_tokens: int = Field(default=4096)

    # Embeddings
    embedding_provider: Literal["gemini", "cohere", "openrouter"] = Field(default="gemini")
    embedding_model: str = Field(default="gemini-embedding-001")
    embedding_dimension: int = Field(default=3072)

    # Reranker (for 2-stage retrieval)
    reranker_enabled: bool = Field(default=True)
    reranker_provider: Literal["cohere"] = Field(default="cohere")
    reranker_model: str = Field(default="rerank-3.5")

    # Web Search
    web_search_enabled: bool = Field(default=True)
    web_search_provider: Literal["serper", "openrouter"] = Field(default="openrouter")
    serper_api_key: str | None = Field(default=None)
    # OpenRouter Search Configuration (when WEB_SEARCH_PROVIDER=openrouter)
    web_search_model: str = Field(default="perplexity/sonar")
    web_search_temperature: float = Field(default=0.3)
    web_search_max_tokens: int = Field(default=4096)
    # Search context size for native search (low, medium, high)
    web_search_context_size: Literal["low", "medium", "high"] = Field(default="medium")
    # Web search engine (native, exa, or None for automatic)
    web_search_engine: Literal["native", "exa"] | None = Field(default=None)

    # Prompt Caching
    prompt_caching_enabled: bool = Field(default=True)
    cache_control_strategy: Literal["auto", "manual"] = Field(default="auto")
    cache_min_tokens: int = Field(default=1024)  # Minimum tokens for OpenAI caching

    # Model Routing & Fallbacks
    model_routing_enabled: bool = Field(default=True)
    default_fallback_models: list[str] = Field(
        default_factory=lambda: []
    )  # Fallback models for routing
    routing_strategy: Literal["auto", "price", "latency", "uptime"] = Field(default="auto")
    enable_auto_router: bool = Field(default=False)  # Use openrouter/auto

    # Usage Accounting
    usage_tracking_enabled: bool = Field(default=True)
    track_user_ids: bool = Field(default=True)  # Send user parameter to OpenRouter

    # Image Generation
    image_generation_enabled: bool = Field(default=False)
    image_generation_models: list[str] = Field(
        default_factory=lambda: ["google/gemini-2.5-flash-image-preview"]
    )
    image_storage_type: Literal["database", "s3", "local"] = Field(default="database")
    image_max_size_mb: int = Field(default=10)

    # Structured Outputs
    structured_outputs_enabled: bool = Field(default=True)

    # Multimodal Processing
    pdf_processing_enabled: bool = Field(default=True)
    audio_processing_enabled: bool = Field(default=True)
    pdf_skip_parsing: bool = Field(default=False)  # For cost control

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

    # Email - SMTP (Legacy/Fallback)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str | None = Field(default=None)
    smtp_password: str | None = Field(default=None)
    smtp_from_email: str = Field(default="noreply@example.com")
    smtp_from_name: str = Field(default="WisQu Islamic Chatbot")

    # Email - Mailgun (Recommended)
    mailgun_api_key: str | None = Field(default=None)
    mailgun_domain: str | None = Field(default=None)
    mailgun_from_email: str = Field(default="noreply@wisqu.com")
    mailgun_from_name: str = Field(default="WisQu Islamic Chatbot")

    # Email Provider Selection
    email_provider: Literal["smtp", "mailgun"] = Field(default="mailgun")

    # Super Admin (for initial setup)
    super_admin_email: str = Field(default="admin@wisqu.com")
    super_admin_password: str = Field(default="ChangeMe123!")

    # MinIO Object Storage
    minio_enabled: bool = Field(default=True)
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_secure: bool = Field(default=False)  # True for HTTPS
    minio_region: str = Field(default="us-east-1")
    minio_public_url: str = Field(default="http://localhost:9000")  # For public URLs

    # MinIO Bucket Names
    minio_bucket_images: str = Field(default="wisqu-images")  # AI-generated images (public)
    minio_bucket_documents: str = Field(default="wisqu-documents")  # RAG docs, user PDFs
    minio_bucket_audio_resources: str = Field(
        default="wisqu-audio-resources"
    )  # Quran, Mafatih, Duas (public)
    minio_bucket_audio_user: str = Field(
        default="wisqu-audio-user"
    )  # User voice messages (private)
    minio_bucket_audio_transcripts: str = Field(
        default="wisqu-audio-transcripts"
    )  # ASR processed audio
    minio_bucket_uploads: str = Field(
        default="wisqu-uploads"
    )  # General uploads, ticket attachments
    minio_bucket_temp: str = Field(default="wisqu-temp")  # Temporary processing
    minio_bucket_backups: str = Field(default="wisqu-backups")  # System backups

    # Storage Limits & Quotas
    storage_max_file_size_mb: int = Field(default=50)  # Max file size in MB
    storage_max_image_size_mb: int = Field(default=10)
    storage_max_audio_size_mb: int = Field(default=25)
    storage_max_document_size_mb: int = Field(default=20)

    # User Storage Quotas (in MB)
    storage_quota_free: int = Field(default=100)  # 100MB for free tier
    storage_quota_premium: int = Field(default=5120)  # 5GB for premium
    storage_quota_unlimited: int = Field(default=51200)  # 50GB for unlimited

    # ASR (Automatic Speech Recognition) Settings
    asr_enabled: bool = Field(default=True)
    asr_provider: Literal["google", "openai", "whisper"] = Field(default="google")
    asr_language: str = Field(default="fa-IR")  # Persian/Farsi
    asr_alternative_languages: str = Field(
        default="ar-SA,en-US"
    )  # Arabic, English for fallback
    asr_max_audio_duration_seconds: int = Field(default=600)  # 10 minutes
    google_asr_credentials_path: str | None = Field(default=None)  # Path to JSON credentials

    # Environment-Specific Settings
    environment_data_retention_days: int = Field(
        default=30,
        description="Data retention in days (auto-configured by environment)"
    )
    environment_allow_test_accounts: bool = Field(
        default=True,
        description="Allow test account creation (auto-configured by environment)"
    )
    environment_auto_cleanup_enabled: bool = Field(
        default=True,
        description="Enable automatic data cleanup (auto-configured by environment)"
    )
    environment_cleanup_schedule: str = Field(
        default="0 2 * * *",  # 2 AM daily
        description="Cron schedule for cleanup job"
    )

    # Promotion Settings
    promotion_enabled: bool = Field(default=True)
    promotion_require_approval: bool = Field(default=True)
    promotion_allowed_paths: str = Field(
        default="dev->stage,stage->prod,dev->prod",
        description="Comma-separated allowed promotion paths"
    )
    promotion_max_items_per_batch: int = Field(default=100)
    promotion_rollback_window_hours: int = Field(default=24)

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

    @field_validator("default_fallback_models", mode="before")
    @classmethod
    def parse_default_fallback_models(cls, v):
        """Parse comma-separated fallback models or return empty list."""
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return []
        if isinstance(v, str):
            return [model.strip() for model in v.split(",") if model.strip()]
        return v

    @field_validator("image_generation_models", mode="before")
    @classmethod
    def parse_image_generation_models(cls, v):
        """Parse comma-separated image generation models or use default."""
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return ["google/gemini-2.5-flash-image-preview"]
        if isinstance(v, str):
            return [model.strip() for model in v.split(",") if model.strip()]
        return v

    @field_validator("web_search_engine", mode="before")
    @classmethod
    def parse_web_search_engine(cls, v):
        """Convert empty string to None for web_search_engine."""
        if v == "" or (isinstance(v, str) and v.strip() == ""):
            return None
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

    @model_validator(mode="after")
    def configure_celery_urls(self):
        """Auto-configure Celery broker and result backend from Redis and Database URLs."""
        # Auto-configure Celery broker from Redis if not explicitly set
        if self.celery_broker_url is None:
            redis_db = self.get_redis_db("queue")  # Use queue DB for Celery
            # Parse base Redis URL and add queue DB
            if "//" in self.redis_url:
                base_url = self.redis_url.rsplit("/", 1)[0]
            else:
                base_url = self.redis_url
            self.celery_broker_url = f"{base_url}/{redis_db}"

        # Auto-configure Celery result backend from PostgreSQL if not explicitly set
        if self.celery_result_backend is None:
            # Use synchronous psycopg2 driver for Celery result backend
            sync_url = self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
            self.celery_result_backend = f"db+{sync_url}"

        return self

    @model_validator(mode="after")
    def configure_environment_settings(self):
        """Auto-configure environment-specific settings based on environment."""
        # Configure data retention based on environment
        retention_map = {
            "dev": 30,  # 30 days for dev
            "test": 30,  # 30 days for test
            "stage": 90,  # 90 days for stage
            "prod": 365,  # 1 year for prod (but manual delete still needed)
        }
        if not hasattr(self, '_retention_overridden'):
            self.environment_data_retention_days = retention_map.get(
                self.environment,
                self.environment_data_retention_days
            )

        # Configure test account creation
        if self.environment == "prod":
            # In prod, test accounts allowed but audited heavily
            self.environment_allow_test_accounts = True
        else:
            self.environment_allow_test_accounts = True

        # Configure auto-cleanup
        cleanup_map = {
            "dev": True,  # Aggressive cleanup in dev
            "test": True,  # Aggressive cleanup in test
            "stage": True,  # Moderate cleanup in stage
            "prod": False,  # No auto-cleanup in prod (manual only)
        }
        if not hasattr(self, '_cleanup_overridden'):
            self.environment_auto_cleanup_enabled = cleanup_map.get(
                self.environment,
                self.environment_auto_cleanup_enabled
            )

        return self

    @model_validator(mode="after")
    def validate_web_search_config(self):
        """Validate web search configuration."""
        if self.web_search_enabled and self.web_search_provider == "openrouter":
            # Warn if using a potentially deprecated model name pattern
            model = self.web_search_model.lower()
            deprecated_patterns = ["-preview", "-beta", "-alpha"]

            if any(pattern in model for pattern in deprecated_patterns):
                import warnings
                warnings.warn(
                    f"Web search model '{self.web_search_model}' appears to be a preview/beta version. "
                    f"These models may be deprecated. Consider using stable models like "
                    f"'perplexity/sonar-deep-research' or check https://openrouter.ai/models for current models.",
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

    # ========================================================================
    # Environment Resource Naming Helpers
    # ========================================================================

    def get_env_prefixed_name(self, base_name: str) -> str:
        """
        Get environment-prefixed resource name.

        Examples:
            >>> settings.get_env_prefixed_name("wisqu-images")
            "dev-wisqu-images"  # In dev environment
            "prod-wisqu-images"  # In prod environment
        """
        return f"{self.environment}-{base_name}"

    def get_collection_name(self, base_collection: str) -> str:
        """
        Get environment-specific Qdrant collection name.

        Examples:
            >>> settings.get_collection_name("islamic_knowledge")
            "islamic_knowledge_dev"  # In dev environment
        """
        return f"{base_collection}_{self.environment}"

    def get_bucket_name(self, base_bucket: str) -> str:
        """
        Get environment-prefixed MinIO bucket name.

        Examples:
            >>> settings.get_bucket_name("wisqu-images")
            "dev-wisqu-images"  # In dev environment
        """
        return self.get_env_prefixed_name(base_bucket)

    def get_redis_db(self, purpose: str) -> int:
        """
        Get environment-specific Redis DB number.

        Uses different DB ranges for each environment:
        - dev: 0-2
        - test: 3-5
        - stage: 6-8
        - prod: 9-11

        Examples:
            >>> settings.get_redis_db("cache")
            0  # In dev environment
            6  # In stage environment
        """
        env_offsets = {
            "dev": 0,
            "test": 3,
            "stage": 6,
            "prod": 9,
        }

        purpose_offsets = {
            "default": 0,
            "cache": 1,
            "queue": 2,
        }

        base_offset = env_offsets.get(self.environment, 0)
        purpose_offset = purpose_offsets.get(purpose, 0)

        return base_offset + purpose_offset


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    This function is used for dependency injection in FastAPI.

    Returns:
        Settings: The global settings instance
    """
    return settings
