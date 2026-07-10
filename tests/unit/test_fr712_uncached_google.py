"""FR-712 unit gate: google/vertex are constructed fresh per call (LLM-free).

The cached google-genai client errors on ~50% of completed calls in fresh
event loops (FR-711 Finding A: aiohttp session internals bind to the first
loop). Cure: these providers are excluded from `_llm_cache` so the session
is born in — and dies with — the loop that uses it. Other providers keep
the cache.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils import llm_factory


@pytest.fixture(autouse=True)
def _clean_cache():
    """The cache is process-global — isolate every test (Judgement F3)."""
    llm_factory.clear_cache()
    yield
    llm_factory.clear_cache()


def _create_twice(provider: str) -> tuple[object, object]:
    with patch(
        "yamlgraph.utils.llm_factory.dispatch_provider",
        side_effect=lambda *a, **k: MagicMock(),
    ):
        first = llm_factory.create_llm(provider=provider, model="m")
        second = llm_factory.create_llm(provider=provider, model="m")
    return first, second


class TestUncachedProviders:
    @pytest.mark.req("REQ-YG-540")
    @pytest.mark.parametrize("provider", ["google", "vertex"])
    def test_fresh_object_per_call(self, provider) -> None:
        """Loop-affine SDKs must not be reused across loops → no cache."""
        first, second = _create_twice(provider)
        assert first is not second, (
            f"{provider} client was cached — cross-loop reuse errors on "
            "~50% of completed calls (FR-711 Finding A)"
        )

    @pytest.mark.req("REQ-YG-540")
    def test_uncached_set_is_annotated(self) -> None:
        """Vertex is same-class-inferred (F4) — the confession travels with the code."""
        import inspect

        src = inspect.getsource(llm_factory)
        assert "_UNCACHED_PROVIDERS" in src
        assert "FR-712" in src


class TestCachedProvidersUnchanged:
    @pytest.mark.req("REQ-YG-540")
    @pytest.mark.parametrize("provider", ["anthropic", "openai", "mistral"])
    def test_same_object_per_call(self, provider) -> None:
        first, second = _create_twice(provider)
        assert first is second, f"{provider} must stay cached"
