"""Langfuse prompt management service for version control and deployment."""

from typing import Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptManager:
    """
    Manages prompts via Langfuse Prompt Management.

    Features:
    - Fetch prompts from Langfuse
    - Version control for prompts
    - A/B testing support
    - Fallback to default prompts when Langfuse is disabled
    - Caching for performance

    Usage:
        prompt_manager = PromptManager()
        prompt = await prompt_manager.get_prompt("system-prompt-v1")
        compiled = prompt.compile(user_name="John")
    """

    def __init__(self):
        """Initialize prompt manager."""
        self.langfuse_enabled = settings.langfuse_enabled
        self._cache = {}  # Simple in-memory cache

        if self.langfuse_enabled:
            from app.core.langfuse_client import get_langfuse_client
            self.langfuse = get_langfuse_client()
            logger.info("prompt_manager_initialized", langfuse_enabled=True)
        else:
            self.langfuse = None
            logger.info("prompt_manager_initialized", langfuse_enabled=False)

    def get_prompt(
        self,
        name: str,
        version: Optional[int] = None,
        label: Optional[str] = None,
        fallback_prompt: Optional[str] = None,
    ) -> "PromptTemplate":
        """
        Get a prompt from Langfuse by name.

        Args:
            name: Prompt name in Langfuse
            version: Specific version (optional, uses latest if not specified)
            label: Label for production/staging/etc (optional)
            fallback_prompt: Fallback prompt text if Langfuse is disabled

        Returns:
            PromptTemplate object

        Example:
            prompt = prompt_manager.get_prompt(
                "shia-chatbot-system-prompt",
                label="production",
                fallback_prompt="You are a helpful Shia Islamic assistant."
            )
            compiled = prompt.compile(user_name="Ali")
        """
        # Check cache first
        cache_key = f"{name}:{version}:{label}"
        if cache_key in self._cache:
            logger.debug("prompt_cache_hit", name=name, version=version)
            return self._cache[cache_key]

        # If Langfuse is disabled, use fallback
        if not self.langfuse_enabled:
            logger.debug("langfuse_disabled_using_fallback", name=name)
            template = PromptTemplate(
                name=name,
                prompt=fallback_prompt or "",
                version=None,
                config={},
                labels=[],
                tags=[],
            )
            self._cache[cache_key] = template
            return template

        # Fetch from Langfuse
        try:
            langfuse_prompt = self.langfuse.get_prompt(
                name=name,
                version=version,
                label=label,
            )

            template = PromptTemplate(
                name=langfuse_prompt.name,
                prompt=langfuse_prompt.prompt,
                version=langfuse_prompt.version,
                config=langfuse_prompt.config,
                labels=langfuse_prompt.labels,
                tags=langfuse_prompt.tags,
            )

            # Cache the prompt
            self._cache[cache_key] = template

            logger.info(
                "prompt_fetched_from_langfuse",
                name=name,
                version=langfuse_prompt.version,
                label=label,
            )

            return template

        except Exception as e:
            logger.error(
                "prompt_fetch_error",
                name=name,
                version=version,
                label=label,
                error=str(e),
            )

            # Fall back to default if provided
            if fallback_prompt:
                logger.warning(
                    "using_fallback_prompt",
                    name=name,
                    error=str(e),
                )
                return PromptTemplate(
                    name=name,
                    prompt=fallback_prompt,
                    version=None,
                    config={},
                    labels=[],
                    tags=[],
                )

            raise

    def clear_cache(self, name: Optional[str] = None):
        """
        Clear the prompt cache.

        Args:
            name: Optional prompt name to clear. If None, clears all.
        """
        if name:
            # Clear specific prompt versions
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{name}:")]
            for key in keys_to_delete:
                del self._cache[key]
            logger.info("prompt_cache_cleared", name=name)
        else:
            # Clear entire cache
            self._cache.clear()
            logger.info("prompt_cache_cleared_all")


class PromptTemplate:
    """
    Represents a prompt template from Langfuse.

    Supports variable interpolation via compile().
    """

    def __init__(
        self,
        name: str,
        prompt: str,
        version: Optional[int],
        config: dict[str, Any],
        labels: list[str],
        tags: list[str],
    ):
        """Initialize prompt template."""
        self.name = name
        self.prompt = prompt
        self.version = version
        self.config = config
        self.labels = labels
        self.tags = tags

    def compile(self, **kwargs) -> str:
        """
        Compile the prompt template with variables.

        Args:
            **kwargs: Variables to interpolate into the prompt

        Returns:
            Compiled prompt string

        Example:
            prompt = PromptTemplate(
                name="greeting",
                prompt="Hello {{user_name}}, welcome to {{app_name}}!",
                ...
            )
            result = prompt.compile(user_name="Ali", app_name="WisQu")
            # Returns: "Hello Ali, welcome to WisQu!"
        """
        compiled = self.prompt

        # Simple variable interpolation (supports {{variable}} syntax)
        for key, value in kwargs.items():
            compiled = compiled.replace(f"{{{{{key}}}}}", str(value))
            compiled = compiled.replace(f"{{{key}}}", str(value))

        return compiled

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a config value from the prompt.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            Config value
        """
        return self.config.get(key, default)

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptTemplate(name={self.name}, version={self.version})>"


# Global prompt manager instance
prompt_manager = PromptManager()
