"""FR-680: provider dispatch registry with keyless branch coverage.

`dispatch_provider` selected the provider factory with an 11-branch if/elif
chain (radon C) whose inception/replicate/xai/lmstudio branches never ran
under pytest (they skip without API keys). This suite condemns that: a
data-driven registry must select the correct factory for every provider
without a network or key, raise loudly on unknown providers, and plumb
`thinking_budget` only to providers that accept it.
"""

import pytest

from yamlgraph.utils import llm_providers
from yamlgraph.utils.llm_providers import (
    _PROVIDER_FACTORIES,
    _THINKING_PROVIDERS,
    dispatch_provider,
)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_registry_covers_all_twelve_providers():
    """Every supported provider has exactly one registry entry."""
    assert set(_PROVIDER_FACTORIES) == {
        "anthropic",
        "azure",
        "deepseek",
        "google",
        "inception",
        "lmstudio",
        "mistral",
        "openai",
        "replicate",
        "runpod",
        "vertex",
        "xai",
    }


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
@pytest.mark.parametrize("provider", sorted(_PROVIDER_FACTORIES))
def test_dispatch_selects_correct_factory(provider, monkeypatch):
    """Keyless: dispatch calls the registered factory with model+temperature."""
    calls = []

    def _recording_factory(*args, **kwargs):
        calls.append((args, kwargs))
        return "sentinel-llm"

    monkeypatch.setitem(_PROVIDER_FACTORIES, provider, _recording_factory)

    result = dispatch_provider(
        provider, "some-model", 0.5, thinking_budget=1024, extra="k"
    )

    assert result == "sentinel-llm"
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] == "some-model"
    assert args[1] == 0.5
    assert kwargs.get("extra") == "k"


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
@pytest.mark.parametrize("provider", sorted(_THINKING_PROVIDERS))
def test_thinking_providers_receive_thinking_budget(provider, monkeypatch):
    """anthropic/google/vertex factories get thinking_budget as 3rd positional."""
    calls = []
    monkeypatch.setitem(
        _PROVIDER_FACTORIES,
        provider,
        lambda *a, **k: calls.append(a) or "llm",
    )

    dispatch_provider(provider, "m", 0.3, thinking_budget=2048)

    assert calls[0] == ("m", 0.3, 2048)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
@pytest.mark.parametrize(
    "provider",
    sorted(set(_PROVIDER_FACTORIES) - set(_THINKING_PROVIDERS)),
)
def test_non_thinking_providers_do_not_receive_thinking_budget(provider, monkeypatch):
    """Providers without a thinking arg get only (model, temperature)."""
    calls = []
    monkeypatch.setitem(
        _PROVIDER_FACTORIES,
        provider,
        lambda *a, **k: calls.append(a) or "llm",
    )

    dispatch_provider(provider, "m", 0.3, thinking_budget=2048)

    assert calls[0] == ("m", 0.3)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_unknown_provider_raises_valueerror_listing_valid():
    """FR-680: the dispatch boundary has no silent Anthropic fallback."""
    with pytest.raises(ValueError, match="Unknown provider 'mistal'") as exc:
        dispatch_provider("mistal", "m", 0.3, thinking_budget=None)
    # Error lists valid providers to aid correction.
    assert "anthropic" in str(exc.value)
    assert "mistral" in str(exc.value)


@pytest.mark.req("REQ-YG-010", "REQ-YG-011")
def test_dispatch_has_no_ifelif_chain():
    """Registry lookup, not an if/elif chain (radon grade improvement)."""
    import inspect

    src = inspect.getsource(llm_providers.dispatch_provider)
    # A single membership check for thinking providers is allowed; provider
    # equality branches (the old chain) must be gone.
    assert 'provider == "azure"' not in src
    assert 'provider == "openai"' not in src
    assert "_PROVIDER_FACTORIES.get(provider)" in src
