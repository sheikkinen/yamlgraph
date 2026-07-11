"""FR-713 Part B witnesses: uniform cache policy, env-fingerprinted keys.

AC-12 (F15 — this file is the inversion of the FR-712 unit gate): with the
persistent bridge loop (Part A), loop affinity is honorable and the
`_UNCACHED_PROVIDERS` carve-out is special-cased code whose justifying
cause is gone (F13). Cache identity is the mechanical proof of the purity
claim: construction once per key ⇒ the vertex masked-env global-environ
mutation window opens once per key, not once per call.

AC-13 (F14): staleness is universal — a cached client must not survive a
change in the env it was born under, for ANY provider. The fingerprint
mechanism is uniform; the per-provider var list is declarative data.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils import llm_factory


@pytest.fixture(autouse=True)
def _clean_cache():
    """The cache is process-global — isolate every test (FR-712 F3)."""
    llm_factory.clear_cache()
    yield
    llm_factory.clear_cache()


def _create(provider: str) -> object:
    with patch(
        "yamlgraph.utils.llm_factory.dispatch_provider",
        side_effect=lambda *a, **k: MagicMock(),
    ):
        return llm_factory.create_llm(provider=provider, model="m")


def _create_twice(provider: str) -> tuple[object, object]:
    with patch(
        "yamlgraph.utils.llm_factory.dispatch_provider",
        side_effect=lambda *a, **k: MagicMock(),
    ):
        first = llm_factory.create_llm(provider=provider, model="m")
        second = llm_factory.create_llm(provider=provider, model="m")
    return first, second


class TestUniformCacheIdentity:
    """AC-12: one caching rule for all providers — zero carve-outs."""

    @pytest.mark.req("REQ-YG-540")
    @pytest.mark.parametrize(
        "provider", ["google", "vertex", "anthropic", "openai", "mistral"]
    )
    def test_same_object_per_call(self, provider) -> None:
        """Clients live their whole life on the persistent bridge loop
        (FR-713 Part A) — loop affinity is stable, the cache is uniform."""
        first, second = _create_twice(provider)
        assert first is second, (
            f"{provider} client was not cached — the FR-712 carve-out's "
            "justifying cause (fresh loop per call) was removed by FR-713 "
            "Part A; special-cased cache policy is entropy (F13)"
        )

    @pytest.mark.req("REQ-YG-540")
    def test_carve_out_is_deleted(self) -> None:
        """The `_UNCACHED_PROVIDERS` frozenset and its branch must not
        survive — a special case whose cause is gone (Commandment 8)."""
        import inspect

        src = inspect.getsource(llm_factory)
        assert "_UNCACHED_PROVIDERS" not in src, (
            "_UNCACHED_PROVIDERS still present — the carve-out outlived "
            "its justification (FR-713 F13/F15)"
        )


class TestEnvFingerprintStaleness:
    """AC-13 (F14): env change ⇒ new client; unchanged env ⇒ cache hit —
    uniformly, for every provider."""

    @pytest.mark.req("REQ-YG-540")
    @pytest.mark.parametrize(
        ("provider", "env_var"),
        [
            ("google", "GOOGLE_API_KEY"),
            ("vertex", "GOOGLE_CLOUD_PROJECT"),
            ("anthropic", "ANTHROPIC_API_KEY"),
        ],
    )
    def test_env_change_yields_new_client(self, monkeypatch, provider, env_var):
        monkeypatch.setenv(env_var, "fingerprint-a")
        first = _create(provider)
        monkeypatch.setenv(env_var, "fingerprint-b")
        second = _create(provider)
        assert first is not second, (
            f"{provider} client born under {env_var}=a was served after "
            f"{env_var} changed — stale credentials/config (FR-227: "
            "construction is env-sensitive)"
        )

    @pytest.mark.req("REQ-YG-540")
    @pytest.mark.parametrize(
        ("provider", "env_var"),
        [
            ("google", "GOOGLE_API_KEY"),
            ("vertex", "GOOGLE_CLOUD_PROJECT"),
            ("anthropic", "ANTHROPIC_API_KEY"),
        ],
    )
    def test_unchanged_env_is_cache_hit(self, monkeypatch, provider, env_var):
        monkeypatch.setenv(env_var, "fingerprint-a")
        first = _create(provider)
        second = _create(provider)
        assert first is second, (
            f"{provider}: unchanged env must be a cache hit — otherwise "
            "the fingerprint defeats the cache it guards"
        )

    @pytest.mark.req("REQ-YG-540")
    def test_common_timeout_var_fingerprinted(self, monkeypatch):
        """LLM_REQUEST_TIMEOUT is read by every constructor (FR-708) —
        it belongs to the common fingerprint, not a provider list."""
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "30")
        first = _create("anthropic")
        monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "60")
        second = _create("anthropic")
        assert first is not second, (
            "client born under a 30s request timeout survived the env "
            "changing to 60s — the bound is baked into the client (FR-708)"
        )
