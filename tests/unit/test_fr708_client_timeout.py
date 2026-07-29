"""FR-708: bound provider work at the client boundary (LLM-free).

Matrix RED: every provider constructor must pass an explicit finite request
timeout and bounded retries to its wrapper — today none do (verified: zero
timeout/max_retries across all 11 constructors), so a hung endpoint hangs
forever and accumulates transport channels (Fly freeze RCA 2026-07-10).

Honesty bound (Judgement F4, mock_escape_hatch): these tests assert what WE
pass to the wrapper constructors — SDK timeout behavior itself is verified
by the consumer-side Fly probe, not by mocks.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils import llm_providers
from yamlgraph.utils.llm_providers import _PROVIDER_FACTORIES

# Wrapper-correct timeout parameter per provider (Judgement F1).
_TIMEOUT_PARAM = {
    "anthropic": "timeout",
    "azure": "timeout",
    "deepseek": "timeout",
    "google": "timeout",
    "inception": "timeout",
    "lmstudio": "timeout",
    "mistral": "timeout",
    "openai": "timeout",
    "replicate": "request_timeout",
    "runpod": "timeout",
    "vertex": "timeout",
    "xai": "timeout",
}

# Wrapper class path patched per provider (constructor capture, no network).
_WRAPPER_PATH = {
    "anthropic": "langchain_anthropic.ChatAnthropic",
    "azure": "langchain_azure_ai.chat_models.AzureAIOpenAIApiChatModel",
    "deepseek": "langchain_openai.ChatOpenAI",
    "google": "langchain_google_genai.ChatGoogleGenerativeAI",
    "inception": "langchain_openai.ChatOpenAI",
    "lmstudio": "langchain_openai.ChatOpenAI",
    "mistral": "langchain_mistralai.ChatMistralAI",
    "openai": "langchain_openai.ChatOpenAI",
    "replicate": "langchain_litellm.ChatLiteLLM",
    "runpod": "langchain_openai.ChatOpenAI",
    "vertex": "langchain_google_genai.ChatGoogleGenerativeAI",
    "xai": "langchain_openai.ChatOpenAI",
}

_ENV = {
    "AZURE_AI_ENDPOINT": "https://x.services.ai.azure.com/openai/v1",
    "AZURE_AI_API_KEY": "k",
    "REPLICATE_API_TOKEN": "k",
    "GOOGLE_CLOUD_PROJECT": "p",
    "RUNPOD_ENDPOINT": "https://api.runpod.ai/v2/x/openai/v1",
    "RUNPOD_API_KEY": "k",
}


def _construct(provider: str, monkeypatch, **extra):
    """Invoke the provider factory with its wrapper patched; return kwargs."""
    wrapper_path = _WRAPPER_PATH[provider]
    pytest.importorskip(
        wrapper_path.rsplit(".", 1)[0],
        reason=f"optional SDK for {provider} not installed",
    )
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)
    captured: dict = {}

    class FakeWrapper(MagicMock):
        def __new__(cls, *args, **kwargs):
            captured.update(kwargs)
            return MagicMock()

    with patch(wrapper_path, FakeWrapper):
        _PROVIDER_FACTORIES[provider]("some-model", 0.5, **extra)
    return captured


class TestProviderTimeoutMatrix:
    """Every constructed client carries a finite request timeout (F3 RED)."""

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", sorted(_PROVIDER_FACTORIES))
    def test_client_carries_finite_timeout(self, provider, monkeypatch) -> None:
        kwargs = _construct(provider, monkeypatch)
        param = _TIMEOUT_PARAM[provider]
        assert param in kwargs, f"{provider}: no {param}= passed to wrapper"
        assert (
            isinstance(kwargs[param], int | float) and kwargs[param] > 0
        ), f"{provider}: {param} not a finite positive number: {kwargs[param]!r}"

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", sorted(_PROVIDER_FACTORIES))
    def test_client_carries_bounded_retries(self, provider, monkeypatch) -> None:
        kwargs = _construct(provider, monkeypatch)
        assert (
            kwargs.get("max_retries") == 2
        ), f"{provider}: max_retries not bounded: {kwargs.get('max_retries')!r}"

    @pytest.mark.req("REQ-YG-539")
    def test_caller_kwargs_win(self, monkeypatch) -> None:
        """Explicit caller timeout overrides the default."""
        kwargs = _construct("openai", monkeypatch, timeout=7)
        assert kwargs["timeout"] == 7


class TestRequestTimeoutEnv:
    """LLM_REQUEST_TIMEOUT: env-overridable, garbage raises (F5)."""

    @pytest.mark.req("REQ-YG-539")
    def test_default_is_30(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)
        assert llm_providers._request_timeout() == 30.0

    @pytest.mark.req("REQ-YG-539")
    def test_env_override(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "12.5")
        assert llm_providers._request_timeout() == 12.5

    @pytest.mark.req("REQ-YG-539")
    def test_garbage_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "soon")
        with pytest.raises(ValueError, match="LLM_REQUEST_TIMEOUT"):
            llm_providers._request_timeout()

    @pytest.mark.req("REQ-YG-539")
    def test_nonpositive_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "0")
        with pytest.raises(ValueError, match="LLM_REQUEST_TIMEOUT"):
            llm_providers._request_timeout()


class TestVertexTransportKnob:
    """VERTEX_TRANSPORT=rest|grpc → transport= for google + vertex (F5)."""

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_rest_plumbs_transport(self, provider, monkeypatch) -> None:
        monkeypatch.setenv("VERTEX_TRANSPORT", "rest")
        kwargs = _construct(provider, monkeypatch)
        assert kwargs.get("transport") == "rest"

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_default_passes_no_transport(self, provider, monkeypatch) -> None:
        monkeypatch.delenv("VERTEX_TRANSPORT", raising=False)
        kwargs = _construct(provider, monkeypatch)
        assert "transport" not in kwargs, "default must leave SDK transport unchanged"

    @pytest.mark.req("REQ-YG-539")
    def test_vertex_express_branch_gets_transport(self, monkeypatch) -> None:
        monkeypatch.setenv("VERTEX_TRANSPORT", "rest")
        monkeypatch.setenv("VERTEX_API_KEY", "k")
        kwargs = _construct("vertex", monkeypatch)
        assert kwargs.get("transport") == "rest"
        assert kwargs.get("google_api_key") == "k"

    @pytest.mark.req("REQ-YG-539")
    def test_invalid_transport_raises(self, monkeypatch) -> None:
        monkeypatch.setenv("VERTEX_TRANSPORT", "carrier-pigeon")
        with pytest.raises(ValueError, match="VERTEX_TRANSPORT"):
            _construct("vertex", monkeypatch)
