"""FR-926 witnesses — research failure must cite the recorded cause.

When a persona node exhausts retries, the retry handler records a
``PipelineError`` in ``state["errors"]`` and ``gather_findings`` raises
on the missing state key. These witnesses hold that the raise surfaces
the recorded cause (node, category, exception type, message) instead of
the symptom alone, that an empty error channel keeps the terse message,
and that the enriched text survives to the operator through
``scripts/research.sh``.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from yamlgraph.models.schemas import ErrorType, PipelineError

pytestmark = pytest.mark.process  # exercises scripts/ + examples/ (FR-756)

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_SH = REPO_ROOT / "scripts" / "research.sh"
TOOLS_PY = (
    REPO_ROOT / "examples" / "demos" / "research-route" / "nodes" / "research_tools.py"
)
CLEAN_BRIEF = REPO_ROOT / "tests" / "fixtures" / "fr890" / "clean-brief.md"

VALIDATION_MESSAGE = (
    "1 validation error for PersonaFinding\nrationale\n  "
    "String should have at most 400 characters "
    "[type=string_too_long, input_value='...', input_type=str]"
)


@pytest.fixture(scope="module")
def tools():
    spec = importlib.util.spec_from_file_location("research_tools_fr926", TOOLS_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["research_tools_fr926"] = module
    spec.loader.exec_module(module)
    return module


def _recorded_error() -> PipelineError:
    return PipelineError(
        type=ErrorType.VALIDATION_ERROR,
        message=VALIDATION_MESSAGE,
        node="yamlgraph_native_persona",
        details={"exception_type": "ValidationError"},
    )


def _state_missing_one(tools, **extra) -> dict:
    state = {
        key: {"persona": key}
        for key in tools.PERSONA_KEYS
        if key != "yamlgraph_native_finding"
    }
    state.update(extra)
    return state


@pytest.mark.req("REQ-YG-623")
def test_gather_cites_recorded_pipeline_error(tools):
    """AC-01: the raise names the missing key AND the recorded cause."""
    state = _state_missing_one(tools, errors=[_recorded_error()])

    with pytest.raises(ValueError) as excinfo:
        tools.gather_findings(state)

    message = str(excinfo.value)
    assert "yamlgraph_native_finding" in message
    assert "yamlgraph_native_persona" in message
    assert "validation_error" in message
    assert "ValidationError" in message
    assert "String should have at most 400 characters" in message


@pytest.mark.req("REQ-YG-623")
def test_gather_without_recorded_errors_keeps_terse_message(tools):
    """AC-02: no recorded cause means no invented detail."""
    expected = "missing persona findings: yamlgraph_native_finding"

    with pytest.raises(ValueError) as absent:
        tools.gather_findings(_state_missing_one(tools))
    assert str(absent.value) == expected

    with pytest.raises(ValueError) as empty:
        tools.gather_findings(_state_missing_one(tools, errors=[]))
    assert str(empty.value) == expected


@pytest.mark.req("REQ-YG-623")
def test_gather_cites_dict_errors_and_ignores_malformed(tools):
    """AC-03: dict entries render; unstructured entries are dropped."""
    state = _state_missing_one(
        tools,
        errors=[
            "boom",
            None,
            {"unrelated": "noise"},
            {
                "node": "librarian_persona",
                "type": "llm_error",
                "message": "rate limited",
            },
        ],
    )

    with pytest.raises(ValueError) as excinfo:
        tools.gather_findings(state)

    message = str(excinfo.value)
    assert "librarian_persona" in message
    assert "rate limited" in message
    assert "boom" not in message
    assert "noise" not in message


@pytest.mark.req("REQ-YG-623")
def test_gather_success_path_unchanged(tools):
    """AC-04: complete state still returns normalized findings."""
    state = {key: {"persona": key} for key in tools.PERSONA_KEYS}
    state["errors"] = [_recorded_error()]

    result = tools.gather_findings(state)

    assert list(result) == ["findings"]
    assert [f["persona"] for f in result["findings"]] == list(tools.PERSONA_KEYS)


@pytest.mark.req("REQ-YG-623")
def test_wrapper_surfaces_enriched_failure_text(tmp_path):
    """AC-05: research.sh does not swallow the graph's failure text."""
    enriched = (
        "missing persona findings: yamlgraph_native_finding\\n"
        "recorded node errors:\\n"
        "  yamlgraph_native_persona: validation_error (ValidationError): "
        "String should have at most 400 characters"
    )
    stub = tmp_path / "yg"
    stub.write_text(f'#!/usr/bin/env bash\nprintf "{enriched}\\n" >&2\nexit 1\n', encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("RESEARCH_EXECUTION", "YAMLGRAPH_BIN")
    }
    env["RESEARCH_WORKDIR"] = str(tmp_path)
    env["YAMLGRAPH_BIN"] = str(stub)
    result = subprocess.run(
        ["bash", str(RESEARCH_SH), str(CLEAN_BRIEF)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 65, result.stderr
    operator_output = result.stdout + result.stderr
    assert "missing persona findings: yamlgraph_native_finding" in operator_output
    assert "yamlgraph_native_persona" in operator_output
    assert "validation_error (ValidationError)" in operator_output
    assert "String should have at most 400 characters" in operator_output
    assert "contract violated" in result.stderr
