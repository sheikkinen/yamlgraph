"""FR-982: the unit suite must not run with the operator's LangSmith tracer live.

Witnesses for the pytest-session tracing boundary (REQ-YG-644) and the
FR-960 argv-dispatching ``subprocess.run`` stand-in (REQ-YG-642).
"""

from __future__ import annotations

import os

import pytest
from langchain_core.tracers.context import _tracing_v2_is_enabled
from langsmith.utils import get_env_var, tracing_is_enabled

TRACING_ENV_VARS = (
    "LANGSMITH_TRACING_V2",
    "LANGCHAIN_TRACING_V2",
    "LANGSMITH_TRACING",
    "LANGCHAIN_TRACING",
)


@pytest.mark.req("REQ-YG-644")
class TestTracingOffInTests:
    def test_all_four_aliases_are_false_inside_a_test(self):
        assert {k: os.environ.get(k) for k in TRACING_ENV_VARS} == dict.fromkeys(
            TRACING_ENV_VARS, "false"
        )

    def test_both_tracing_predicates_are_off(self):
        get_env_var.cache_clear()
        assert tracing_is_enabled() is False
        assert not _tracing_v2_is_enabled()

    def test_opt_in_via_highest_priority_alias_still_works(self, monkeypatch):
        monkeypatch.setenv("LANGSMITH_TRACING_V2", "true")
        get_env_var.cache_clear()
        try:
            assert tracing_is_enabled() is True
            assert _tracing_v2_is_enabled()
        finally:
            monkeypatch.undo()
            get_env_var.cache_clear()
        assert os.environ["LANGSMITH_TRACING_V2"] == "false"
        assert tracing_is_enabled() is False


@pytest.mark.req("REQ-YG-642")
def test_claude_cli_stub_dispatches_on_argv_not_position():
    from tests.unit.test_fr960_claude_judge_variant import _claude_cli, _proc

    responses = [_proc("v"), _proc("auth"), _proc("envelope")]
    run = _claude_cli(responses)
    seen = []
    for argv in (
        ["uname", "-p"],
        ["file", "-b", "x"],
        ["claude", "--version"],
        ["file", "-b", "x"],
        ["claude", "auth", "status"],
        ["claude", "-p", "…"],
    ):
        seen.append(run(argv, capture_output=True))
    claude_results = [seen[2], seen[4], seen[5]]
    assert [r.stdout for r in claude_results] == ["v", "auth", "envelope"]
    for other in (seen[0], seen[1], seen[3]):
        assert other.returncode == 0
        assert isinstance(other.stdout, bytes)
