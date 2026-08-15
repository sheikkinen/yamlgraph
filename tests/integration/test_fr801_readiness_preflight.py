"""FR-801 readiness-preflight witnesses — mocked probes, no live calls.

The preflight under test lives in tests/integration/conftest.py.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.integration import conftest as readiness

pytest_plugins = ["pytester"]

_CONFTEST_PATH = Path(readiness.__file__).resolve()


@pytest.fixture
def fresh_cache(monkeypatch: pytest.MonkeyPatch) -> dict:
    cache: dict[str, tuple[bool, str]] = {}
    monkeypatch.setattr(readiness, "_readiness_cache", cache)
    return cache


@pytest.mark.req("REQ-YG-591")
def test_probe_absent_after_dotenv(
    fresh_cache: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-02: absent-after-dotenv → not ready, absent-credential reason."""
    import yamlgraph.config  # noqa: F401  # dotenv already loaded; delenv wins after

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ready, reason = readiness.probe_provider("openai")
    assert ready is False
    assert reason == (
        "provider openai not ready: credential absent after dotenv (OPENAI_API_KEY)"
    )


@pytest.mark.req("REQ-YG-591")
def test_probe_exhausted_reports_class_and_status(
    fresh_cache: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-01: erroring probe → reason names exception class + HTTP status."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class RateLimitError(Exception):
        def __init__(self) -> None:
            super().__init__("You exceeded your quota; account acct-SECRET-123")
            self.status_code = 429

    llm = MagicMock()
    llm.invoke.side_effect = RateLimitError()
    with patch("yamlgraph.utils.llm_factory.create_llm", return_value=llm):
        ready, reason = readiness.probe_provider("openai")
    assert ready is False
    assert reason == "provider openai not ready: RateLimitError/429"


@pytest.mark.req("REQ-YG-591")
def test_probe_reason_redacts_message_body(
    fresh_cache: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-06: exception message (bodies, identifiers) never leaks into reason."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-VERYSECRET")

    class AuthenticationError(Exception):
        pass

    exc = AuthenticationError("bad key sk-VERYSECRET for org-1234, request req-999")
    llm = MagicMock()
    llm.invoke.side_effect = exc
    with patch("yamlgraph.utils.llm_factory.create_llm", return_value=llm):
        _, reason = readiness.probe_provider("openai")
    assert "sk-VERYSECRET" not in reason
    assert "org-1234" not in reason
    assert "req-999" not in reason
    assert reason == "provider openai not ready: AuthenticationError/no-status"


@pytest.mark.req("REQ-YG-591")
def test_probe_healthy(fresh_cache: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-03: healthy probe → ready; gate does not skip."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="ok")
    with patch("yamlgraph.utils.llm_factory.create_llm", return_value=llm):
        assert readiness.probe_provider("openai") == (True, "ready")
    readiness._readiness_cache["openai"] = (True, "ready")
    readiness.require_provider_ready("openai")  # must not raise Skipped


@pytest.mark.req("REQ-YG-591")
def test_probe_restores_timeout_env_and_cache(
    fresh_cache: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-09: LLM_REQUEST_TIMEOUT set for the probe only, then restored."""
    import os

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "77")
    seen: dict[str, str | None] = {}

    def fake_create_llm(provider: str):
        seen["timeout"] = os.environ.get("LLM_REQUEST_TIMEOUT")
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="ok")
        return llm

    with patch("yamlgraph.utils.llm_factory.create_llm", side_effect=fake_create_llm):
        readiness.probe_provider("openai")
    assert seen["timeout"] == readiness.PROBE_TIMEOUT_SECONDS
    assert os.environ["LLM_REQUEST_TIMEOUT"] == "77"


@pytest.mark.req("REQ-YG-591")
def test_readiness_memoized_once_per_session(
    fresh_cache: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-04: at most one probe per provider per session."""
    calls: list[str] = []

    def fake_probe(provider: str) -> tuple[bool, str]:
        calls.append(provider)
        return False, "provider openai not ready: RateLimitError/429"

    monkeypatch.setattr(readiness, "probe_provider", fake_probe)
    first = readiness.provider_readiness("openai")
    second = readiness.provider_readiness("openai")
    assert first == second
    assert calls == ["openai"]


@pytest.mark.req("REQ-YG-591")
def test_fixture_skips_before_test_body(pytester: pytest.Pytester) -> None:
    """AC-05: not-ready gate skips during setup; sentinel proves body never ran."""
    pytester.makeconftest(
        f"""
import importlib.util

spec = importlib.util.spec_from_file_location(
    "fr801_readiness", r"{_CONFTEST_PATH}"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod._readiness_cache["openai"] = (
    False, "provider openai not ready: RateLimitError/429"
)
openai_ready = mod.openai_ready
"""
    )
    pytester.makepyfile(
        """
from pathlib import Path

def test_body_must_not_run(openai_ready):
    Path("sentinel.txt").write_text("body ran")
"""
    )
    result = pytester.runpytest_inprocess("-p", "no:randomly", "--no-cov")
    result.assert_outcomes(skipped=1)
    assert not (pytester.path / "sentinel.txt").exists(), "test body executed"
    result.stdout.no_fnmatch_line("*body ran*")
