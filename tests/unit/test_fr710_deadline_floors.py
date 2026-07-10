"""FR-710: provider deadline floors validated at the client boundary.

Field evidence (FR-709 run 2, verbatim): google rejected the judged 5 s
fixture at request time — `400 INVALID_ARGUMENT: "Manually set deadline 5s
is too short. Minimum allowed deadline is 10s."` Below-floor timeouts must
fail loudly at CONSTRUCTION, naming floor, value, and source — not as a
confusing 400 per request that silently drops the gemini hedge from races.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils.llm_providers import _PROVIDER_FACTORIES

_GOOGLE_WRAPPER = "langchain_google_genai.ChatGoogleGenerativeAI"


def _construct(provider: str, monkeypatch, **extra):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "p")
    captured: dict = {}

    class FakeWrapper(MagicMock):
        def __new__(cls, *args, **kwargs):
            captured.update(kwargs)
            return MagicMock()

    wrapper = (
        _GOOGLE_WRAPPER
        if provider in ("google", "vertex")
        else ("langchain_anthropic.ChatAnthropic")
    )
    with patch(wrapper, FakeWrapper):
        _PROVIDER_FACTORIES[provider]("some-model", 0.5, **extra)
    return captured


class TestFlooredProvidersRaise:
    """Below-floor timeouts raise at construction with floor + source named."""

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_env_below_floor_raises(self, provider, monkeypatch) -> None:
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "5")
        with pytest.raises(ValueError, match="10.*LLM_REQUEST_TIMEOUT"):
            _construct(provider, monkeypatch)

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_kwarg_below_floor_raises_naming_kwarg(self, provider, monkeypatch) -> None:
        monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)
        with pytest.raises(ValueError, match="10.*timeout="):
            _construct(provider, monkeypatch, timeout=5)

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_timeout_none_raises(self, provider, monkeypatch) -> None:
        """F3: None would TypeError the comparison and defeat the FR-708 bound."""
        monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)
        with pytest.raises(ValueError, match="deadline floor"):
            _construct(provider, monkeypatch, timeout=None)

    @pytest.mark.req("REQ-YG-539")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_at_floor_constructs(self, provider, monkeypatch) -> None:
        monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)
        kwargs = _construct(provider, monkeypatch, timeout=10)
        assert kwargs["timeout"] == 10

    @pytest.mark.req("REQ-YG-539")
    def test_default_unaffected(self, monkeypatch) -> None:
        """Default 30 s is above the floor — no behavior change."""
        monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)
        kwargs = _construct("google", monkeypatch)
        assert kwargs["timeout"] == 30.0


class TestNonFlooredProvidersUnchanged:
    @pytest.mark.req("REQ-YG-539")
    def test_anthropic_accepts_sub_floor(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "5")
        kwargs = _construct("anthropic", monkeypatch)
        assert kwargs["timeout"] == 5.0
