"""FR-766: RunPod provider via OpenAI-compatible endpoint.

RunPod (Public API and serverless vLLM workers) exposes an
OpenAI-compatible surface; the provider is the lmstudio-shaped
``ChatOpenAI + base_url`` pattern with a real API key. The judgement
requires fail-fast validation of all three env vars at the provider
boundary (R-1) and env-fingerprinted cache keys (R-2, REQ-YG-540).
"""

import importlib
import os
from typing import get_args
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils.llm_factory import clear_cache, create_llm

RUNPOD_ENV = {
    "RUNPOD_API_KEY": "rpa_test_key",
    "RUNPOD_ENDPOINT": "https://api.runpod.ai/v2/moonshot-kimi/openai/v1",
}


@pytest.fixture
def restore_config():
    """Reload yamlgraph.config after env teardown (fixture order: this
    finalizes AFTER monkeypatch undo, rebuilding DEFAULT_MODELS from the
    original environment)."""
    from yamlgraph import config

    yield config
    importlib.reload(config)


class TestRunpodProvider:
    """Unit tests for the runpod provider (mocked ChatOpenAI, keyless)."""

    def setup_method(self):
        clear_cache()

    @pytest.mark.req("REQ-YG-010")
    def test_runpod_provider_is_registered(self):
        """AC-01/AC-07: runpod in DEFAULT_MODELS, ProviderType, factories."""
        from yamlgraph.config import DEFAULT_MODELS
        from yamlgraph.utils.llm_factory import ProviderType
        from yamlgraph.utils.llm_providers import _PROVIDER_FACTORIES

        assert "runpod" in DEFAULT_MODELS
        assert "runpod" in get_args(ProviderType)
        assert "runpod" in _PROVIDER_FACTORIES

    @pytest.mark.req("REQ-YG-010")
    def test_runpod_not_a_thinking_provider(self):
        """C-5: thinking-budget semantics are not authorized."""
        from yamlgraph.utils.llm_factory import THINKING_PROVIDERS
        from yamlgraph.utils.llm_providers import _THINKING_PROVIDERS

        assert "runpod" not in THINKING_PROVIDERS
        assert "runpod" not in _THINKING_PROVIDERS

    @pytest.mark.req("REQ-YG-010")
    def test_chat_openai_receives_exact_kwargs(self):
        """AC-05: model, temperature, base_url, api_key, bounded kwargs."""
        with (
            patch.dict(os.environ, RUNPOD_ENV),
            patch("langchain_openai.ChatOpenAI") as mock_chat,
        ):
            mock_chat.return_value = MagicMock()
            clear_cache()

            create_llm(provider="runpod", model="kimi-k3", temperature=0.4)

            kwargs = mock_chat.call_args.kwargs
            assert kwargs["model"] == "kimi-k3"
            assert kwargs["temperature"] == 0.4
            assert kwargs["base_url"] == RUNPOD_ENV["RUNPOD_ENDPOINT"]
            assert kwargs["api_key"] == RUNPOD_ENV["RUNPOD_API_KEY"]
            # FR-708 work bounds applied at construction
            assert "timeout" in kwargs
            assert kwargs["max_retries"] == 2

    @pytest.mark.req("REQ-YG-010")
    def test_missing_api_key_fails_fast(self, monkeypatch):
        """AC-03 (R-1): blank RUNPOD_API_KEY raises before construction."""
        monkeypatch.setenv("RUNPOD_ENDPOINT", RUNPOD_ENV["RUNPOD_ENDPOINT"])
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            clear_cache()
            with pytest.raises(ValueError, match="RUNPOD_API_KEY"):
                create_llm(provider="runpod", model="kimi-k3")
            mock_chat.assert_not_called()

    @pytest.mark.req("REQ-YG-010")
    def test_missing_endpoint_fails_fast(self, monkeypatch):
        """AC-04: blank RUNPOD_ENDPOINT raises before construction."""
        monkeypatch.setenv("RUNPOD_API_KEY", RUNPOD_ENV["RUNPOD_API_KEY"])
        monkeypatch.delenv("RUNPOD_ENDPOINT", raising=False)
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            clear_cache()
            with pytest.raises(ValueError, match="RUNPOD_ENDPOINT"):
                create_llm(provider="runpod", model="kimi-k3")
            mock_chat.assert_not_called()

    @pytest.mark.req("REQ-YG-010")
    def test_empty_model_fails_fast(self):
        """AC-02: empty selected model raises naming RUNPOD_MODEL."""
        from yamlgraph.utils.llm_providers import _create_runpod_llm

        with (
            patch.dict(os.environ, RUNPOD_ENV),
            pytest.raises(ValueError, match="RUNPOD_MODEL"),
        ):
            _create_runpod_llm("", 0.7)

    @pytest.mark.req("REQ-YG-010")
    def test_default_model_reads_env_without_fallback(
        self, restore_config, monkeypatch
    ):
        """AC-02: DEFAULT_MODELS['runpod'] = RUNPOD_MODEL, no hard-coded default."""
        from yamlgraph import config

        # config re-runs load_dotenv() on reload, which would resurrect
        # RUNPOD_MODEL from the developer's .env — neutralize it so the
        # test observes the env contract, not the local dotfile.
        monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
        monkeypatch.delenv("RUNPOD_MODEL", raising=False)
        importlib.reload(config)
        assert config.DEFAULT_MODELS["runpod"] == ""

        monkeypatch.setenv("RUNPOD_MODEL", "kimi-k3")
        importlib.reload(config)
        assert config.DEFAULT_MODELS["runpod"] == "kimi-k3"

    @pytest.mark.req("REQ-YG-010")
    def test_fingerprint_vars_registered(self):
        """AC-06 (R-2): cache fingerprint covers api key + endpoint, not model."""
        from yamlgraph.utils.llm_factory import _PROVIDER_FINGERPRINT_VARS

        assert _PROVIDER_FINGERPRINT_VARS["runpod"] == (
            "RUNPOD_API_KEY",
            "RUNPOD_ENDPOINT",
        )

    @pytest.mark.req("REQ-YG-010")
    def test_endpoint_change_yields_distinct_cached_client(self, monkeypatch):
        """AC-06: changing a fingerprint env var must not serve a stale client."""
        monkeypatch.setenv("RUNPOD_API_KEY", RUNPOD_ENV["RUNPOD_API_KEY"])
        monkeypatch.setenv("RUNPOD_ENDPOINT", "https://api.runpod.ai/v2/aaa/openai/v1")
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            mock_chat.side_effect = lambda **k: MagicMock()
            clear_cache()

            first = create_llm(provider="runpod", model="kimi-k3")
            again = create_llm(provider="runpod", model="kimi-k3")
            assert again is first  # same env -> cache hit

            monkeypatch.setenv(
                "RUNPOD_ENDPOINT", "https://api.runpod.ai/v2/bbb/openai/v1"
            )
            moved = create_llm(provider="runpod", model="kimi-k3")
            assert moved is not first
            assert mock_chat.call_count == 2
