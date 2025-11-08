"""Unit tests for web search configuration."""

import pytest
import warnings
from pydantic import ValidationError

from app.core.config import Settings


class TestWebSearchConfigValidation:
    """Test web search configuration validation."""

    def test_default_web_search_config(self):
        """Test default web search configuration."""
        settings = Settings()

        assert settings.web_search_enabled is True
        assert settings.web_search_provider == "tavily"
        assert settings.web_search_model == "perplexity/sonar"
        assert settings.web_search_temperature == 0.3
        assert settings.web_search_max_tokens == 4096
        assert settings.web_search_context_size == "medium"
        assert settings.web_search_engine is None

    def test_openrouter_provider_config(self):
        """Test OpenRouter provider configuration."""
        settings = Settings(
            web_search_provider="openrouter",
            web_search_model="perplexity/sonar-pro",
        )

        assert settings.web_search_provider == "openrouter"
        assert settings.web_search_model == "perplexity/sonar-pro"

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises validation error."""
        with pytest.raises(ValidationError):
            Settings(web_search_provider="invalid")

    def test_preview_model_warning(self):
        """Test warning for preview model names."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            settings = Settings(
                web_search_provider="openrouter",
                web_search_model="openai/gpt-4o-search-preview",
                openrouter_api_key="test-key",
            )

            # Check that a warning was issued
            warning_messages = [str(warning.message) for warning in w]
            preview_warnings = [
                msg for msg in warning_messages if "preview" in msg.lower()
            ]

            # We expect at least one warning about preview models
            assert len(preview_warnings) > 0
            assert "deprecated" in preview_warnings[0].lower()

    def test_beta_model_warning(self):
        """Test warning for beta model names."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            Settings(
                web_search_provider="openrouter",
                web_search_model="some-provider/model-beta",
                openrouter_api_key="test-key",
            )

            # Check that a warning was issued
            warning_messages = [str(warning.message) for warning in w]
            beta_warnings = [
                msg for msg in warning_messages if "beta" in msg.lower()
            ]

            # We expect at least one warning about beta models
            assert len(beta_warnings) > 0

    def test_stable_model_no_warning(self):
        """Test no warning for stable model names."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            Settings(
                web_search_provider="openrouter",
                web_search_model="perplexity/sonar",
                openrouter_api_key="test-key",
            )

            # Filter for web search related warnings
            warning_messages = [str(warning.message) for warning in w]
            web_search_warnings = [
                msg for msg in warning_messages
                if "perplexity/sonar" in msg and "deprecated" in msg.lower()
            ]

            # Should not have warnings about this stable model
            assert len(web_search_warnings) == 0

    def test_web_search_disabled_no_validation(self):
        """Test that validation doesn't run when web search is disabled."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            Settings(
                web_search_enabled=False,
                web_search_provider="openrouter",
                web_search_model="openai/gpt-4o-search-preview",
                openrouter_api_key="test-key",
            )

            # Should not warn about preview model when search is disabled
            warning_messages = [str(warning.message) for warning in w]
            preview_warnings = [
                msg for msg in warning_messages
                if "preview" in msg.lower() and "gpt-4o-search" in msg
            ]

            assert len(preview_warnings) == 0

    def test_tavily_provider_no_openrouter_validation(self):
        """Test that OpenRouter validation doesn't run for Tavily provider."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            Settings(
                web_search_provider="tavily",
                web_search_model="openai/gpt-4o-search-preview",  # Preview model
                tavily_api_key="test-key",
            )

            # Should not warn about preview model when not using OpenRouter
            warning_messages = [str(warning.message) for warning in w]
            preview_warnings = [
                msg for msg in warning_messages
                if "preview" in msg.lower() and "gpt-4o" in msg
            ]

            assert len(preview_warnings) == 0


class TestWebSearchModelConfiguration:
    """Test web search model configuration options."""

    def test_perplexity_sonar_deep_research(self):
        """Test Perplexity Sonar deep research model."""
        settings = Settings(
            web_search_provider="openrouter",
            web_search_model="perplexity/sonar-deep-research",
        )

        assert settings.web_search_model == "perplexity/sonar-deep-research"

    def test_perplexity_sonar_pro(self):
        """Test Perplexity Sonar pro model."""
        settings = Settings(
            web_search_provider="openrouter",
            web_search_model="perplexity/sonar-pro",
        )

        assert settings.web_search_model == "perplexity/sonar-pro"

    def test_gpt4o_search_preview(self):
        """Test GPT-4o search preview model."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Ignore preview warnings for this test

            settings = Settings(
                web_search_provider="openrouter",
                web_search_model="openai/gpt-4o-search-preview",
            )

            assert settings.web_search_model == "openai/gpt-4o-search-preview"

    def test_gpt4o_mini_search_preview(self):
        """Test GPT-4o mini search preview model."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Ignore preview warnings for this test

            settings = Settings(
                web_search_provider="openrouter",
                web_search_model="openai/gpt-4o-mini-search-preview",
            )

            assert settings.web_search_model == "openai/gpt-4o-mini-search-preview"

    def test_custom_model_string(self):
        """Test custom model string."""
        settings = Settings(
            web_search_provider="openrouter",
            web_search_model="custom/provider-model-name",
        )

        assert settings.web_search_model == "custom/provider-model-name"


class TestWebSearchParameters:
    """Test web search parameter configuration."""

    def test_default_temperature(self):
        """Test default temperature setting."""
        settings = Settings()
        assert settings.web_search_temperature == 0.3

    def test_custom_temperature(self):
        """Test custom temperature setting."""
        settings = Settings(web_search_temperature=0.7)
        assert settings.web_search_temperature == 0.7

    def test_temperature_range(self):
        """Test temperature accepts valid range."""
        # Test low temperature
        settings_low = Settings(web_search_temperature=0.0)
        assert settings_low.web_search_temperature == 0.0

        # Test high temperature
        settings_high = Settings(web_search_temperature=1.0)
        assert settings_high.web_search_temperature == 1.0

    def test_default_max_tokens(self):
        """Test default max tokens setting."""
        settings = Settings()
        assert settings.web_search_max_tokens == 4096

    def test_custom_max_tokens(self):
        """Test custom max tokens setting."""
        settings = Settings(web_search_max_tokens=8192)
        assert settings.web_search_max_tokens == 8192

    def test_low_max_tokens(self):
        """Test low max tokens setting."""
        settings = Settings(web_search_max_tokens=512)
        assert settings.web_search_max_tokens == 512


class TestMultiProviderConfiguration:
    """Test multi-provider configuration scenarios."""

    def test_all_providers_configured(self):
        """Test all providers can be configured."""
        settings = Settings(
            tavily_api_key="tavily-key",
            serper_api_key="serper-key",
            openrouter_api_key="openrouter-key",
        )

        assert settings.tavily_api_key == "tavily-key"
        assert settings.serper_api_key == "serper-key"
        assert settings.openrouter_api_key == "openrouter-key"

    def test_switch_between_providers(self):
        """Test switching between providers."""
        # Tavily config
        settings_tavily = Settings(
            web_search_provider="tavily",
            tavily_api_key="test-key",
        )
        assert settings_tavily.web_search_provider == "tavily"

        # Serper config
        settings_serper = Settings(
            web_search_provider="serper",
            serper_api_key="test-key",
        )
        assert settings_serper.web_search_provider == "serper"

        # OpenRouter config
        settings_openrouter = Settings(
            web_search_provider="openrouter",
            openrouter_api_key="test-key",
        )
        assert settings_openrouter.web_search_provider == "openrouter"
