"""FR-801: provider readiness preflight for live integration tests.

Key presence is not readiness (FR-798 Classes C/D): an exhausted
credential passes ``skipif(not KEY)`` and then fails mid-test as if the
product were broken. This preflight runs ONE cheap probe per provider
per pytest session and skips consuming tests during fixture setup —
before any product invocation — with a redacted, legible reason.

Judged mechanics (FR-801 R-3): the probe bounds its request through the
existing ``LLM_REQUEST_TIMEOUT`` construction path, bracketed by
``clear_cache()`` so the bounded client never leaks into live-test
client construction.
"""

from __future__ import annotations

import os

import pytest

CREDENTIAL_ENV = {"openai": "OPENAI_API_KEY"}
PROBE_TIMEOUT_SECONDS = "15"

_readiness_cache: dict[str, tuple[bool, str]] = {}


def _status_of(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return str(status) if status is not None else "no-status"


def probe_provider(provider: str) -> tuple[bool, str]:
    """One minimal live completion → (ready, redacted reason).

    Reads credentials AFTER ``yamlgraph.config`` import — the dotenv
    resurrection boundary (FR-798): "absent" means absent-after-dotenv.
    The reason carries only exception class + HTTP status, never the
    provider message body or identifiers.
    """
    import yamlgraph.config  # noqa: F401  # dotenv boundary: load .env first

    env_var = CREDENTIAL_ENV[provider]
    if not os.environ.get(env_var):
        return (
            False,
            f"provider {provider} not ready: credential absent after dotenv"
            f" ({env_var})",
        )

    from yamlgraph.utils.llm_factory import clear_cache, create_llm

    prior = os.environ.get("LLM_REQUEST_TIMEOUT")
    os.environ["LLM_REQUEST_TIMEOUT"] = PROBE_TIMEOUT_SECONDS
    clear_cache()
    try:
        create_llm(provider=provider).invoke("ping")
    except Exception as exc:
        return (
            False,
            f"provider {provider} not ready: {type(exc).__name__}/{_status_of(exc)}",
        )
    finally:
        if prior is None:
            os.environ.pop("LLM_REQUEST_TIMEOUT", None)
        else:
            os.environ["LLM_REQUEST_TIMEOUT"] = prior
        clear_cache()
    return True, "ready"


def provider_readiness(provider: str) -> tuple[bool, str]:
    """Session-memoized readiness: at most one probe per provider."""
    if provider not in _readiness_cache:
        _readiness_cache[provider] = probe_provider(provider)
    return _readiness_cache[provider]


def require_provider_ready(provider: str) -> None:
    ready, reason = provider_readiness(provider)
    if not ready:
        pytest.skip(reason)


@pytest.fixture
def openai_ready() -> None:
    """Skip during setup — before the test body — when OpenAI is not ready."""
    require_provider_ready("openai")
