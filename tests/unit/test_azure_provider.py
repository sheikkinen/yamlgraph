"""Tests for Azure OpenAI provider integration.

FR-263: Add Azure OpenAI Provider using AzureAIOpenAIApiChatModel
from langchain-azure-ai.
"""

import os
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils.llm_factory import clear_cache, create_llm


def _fake_azure_modules():
    """Create fake langchain_azure_ai modules for mocking when package not installed."""
    mock_class = MagicMock()

    parent = ModuleType("langchain_azure_ai")
    child = ModuleType("langchain_azure_ai.chat_models")
    child.AzureAIOpenAIApiChatModel = mock_class

    return {
        "langchain_azure_ai": parent,
        "langchain_azure_ai.chat_models": child,
    }, mock_class


class TestAzureProvider:
    """Tests for azure provider in llm_factory."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    @pytest.mark.req("REQ-YG-010")
    def test_azure_provider_is_valid(self):
        """azure should be a valid provider option."""
        from yamlgraph.config import DEFAULT_MODELS

        assert "azure" in DEFAULT_MODELS

    @pytest.mark.req("REQ-YG-010")
    def test_create_llm_with_azure_provider(self):
        """create_llm should accept azure provider."""
        fake_modules, mock_class = _fake_azure_modules()
        mock_class.return_value = MagicMock()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(
                os.environ,
                {
                    "AZURE_AI_ENDPOINT": "https://test.services.ai.azure.com/openai/v1",
                    "AZURE_AI_API_KEY": "test-key",
                },
            ),
        ):
            llm = create_llm(provider="azure")

            assert llm is not None
            mock_class.assert_called_once()

    @pytest.mark.req("REQ-YG-010")
    def test_azure_uses_endpoint_from_env(self):
        """azure should use AZURE_AI_ENDPOINT env var."""
        test_endpoint = "https://my-resource.services.ai.azure.com/openai/v1"
        fake_modules, mock_class = _fake_azure_modules()
        mock_class.return_value = MagicMock()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(
                os.environ,
                {
                    "AZURE_AI_ENDPOINT": test_endpoint,
                    "AZURE_AI_API_KEY": "test-key",
                },
            ),
        ):
            clear_cache()
            create_llm(provider="azure")

            call_kwargs = mock_class.call_args.kwargs
            assert call_kwargs["endpoint"] == test_endpoint

    @pytest.mark.req("REQ-YG-010")
    def test_azure_uses_api_key_from_env(self):
        """azure should use AZURE_AI_API_KEY env var as credential."""
        test_key = "sk-azure-test-key-12345"
        fake_modules, mock_class = _fake_azure_modules()
        mock_class.return_value = MagicMock()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(
                os.environ,
                {
                    "AZURE_AI_ENDPOINT": "https://test.services.ai.azure.com/openai/v1",
                    "AZURE_AI_API_KEY": test_key,
                },
            ),
        ):
            clear_cache()
            create_llm(provider="azure")

            call_kwargs = mock_class.call_args.kwargs
            assert call_kwargs["credential"] == test_key

    @pytest.mark.req("REQ-YG-010")
    def test_azure_raises_without_endpoint(self):
        """azure should raise ValueError when AZURE_AI_ENDPOINT is not set."""
        env = os.environ.copy()
        env.pop("AZURE_AI_ENDPOINT", None)
        env["AZURE_AI_API_KEY"] = "test-key"

        fake_modules, _ = _fake_azure_modules()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(os.environ, env, clear=True),
        ):
            clear_cache()
            with pytest.raises(ValueError, match="AZURE_AI_ENDPOINT"):
                create_llm(provider="azure")

    @pytest.mark.req("REQ-YG-010")
    def test_azure_raises_without_api_key(self):
        """azure should raise ValueError when AZURE_AI_API_KEY is not set."""
        env = os.environ.copy()
        env.pop("AZURE_AI_API_KEY", None)
        env["AZURE_AI_ENDPOINT"] = "https://test.services.ai.azure.com/openai/v1"

        fake_modules, _ = _fake_azure_modules()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(os.environ, env, clear=True),
        ):
            clear_cache()
            with pytest.raises(ValueError, match="AZURE_AI_API_KEY"):
                create_llm(provider="azure")

    @pytest.mark.req("REQ-YG-010")
    def test_azure_respects_temperature(self):
        """azure should pass temperature to AzureAIOpenAIApiChatModel."""
        fake_modules, mock_class = _fake_azure_modules()
        mock_class.return_value = MagicMock()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(
                os.environ,
                {
                    "AZURE_AI_ENDPOINT": "https://test.services.ai.azure.com/openai/v1",
                    "AZURE_AI_API_KEY": "test-key",
                },
            ),
        ):
            clear_cache()
            create_llm(provider="azure", temperature=0.3)

            call_kwargs = mock_class.call_args.kwargs
            assert call_kwargs["temperature"] == 0.3

    @pytest.mark.req("REQ-YG-010")
    def test_azure_respects_model_override(self):
        """create_llm model parameter should override default."""
        custom_model = "gpt-4o-mini"
        fake_modules, mock_class = _fake_azure_modules()
        mock_class.return_value = MagicMock()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(
                os.environ,
                {
                    "AZURE_AI_ENDPOINT": "https://test.services.ai.azure.com/openai/v1",
                    "AZURE_AI_API_KEY": "test-key",
                },
            ),
        ):
            clear_cache()
            create_llm(provider="azure", model=custom_model)

            call_kwargs = mock_class.call_args.kwargs
            assert call_kwargs["model"] == custom_model

    @pytest.mark.req("REQ-YG-010")
    def test_azure_uses_model_from_config(self):
        """azure should use configured default model."""
        fake_modules, mock_class = _fake_azure_modules()
        mock_class.return_value = MagicMock()

        with (
            patch.dict(sys.modules, fake_modules),
            patch.dict(
                os.environ,
                {
                    "AZURE_AI_ENDPOINT": "https://test.services.ai.azure.com/openai/v1",
                    "AZURE_AI_API_KEY": "test-key",
                },
            ),
        ):
            clear_cache()
            create_llm(provider="azure")

            call_kwargs = mock_class.call_args.kwargs
            assert "model" in call_kwargs
            assert call_kwargs["model"] is not None
