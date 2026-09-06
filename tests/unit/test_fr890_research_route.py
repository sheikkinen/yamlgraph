"""FR-890 witnesses — research sole route (closed-input alternatives).

Updated for FR-896 (AC-11): closed enums, required rationale, librarian
tool-result reconciliation, non-echo grounding gate (distinct-class
count is now advisory). Original FR-890 contract otherwise unchanged:
- Deterministic problem-brief closure preflight (R-2): required headings,
  forbidden solution/candidate sections, closed classification enum;
  stdlib only, never an LLM (AC-02).
- Frozen artifact schema (R-3): tmp/draft-alternatives.md, no empty
  required cells, disagreement preserved as rows (AC-06, AC-07).
- Librarian fails closed (R-4): an ``Error:``/``No results`` string is
  not a citation; the librarian row must carry a URL (AC-05, C-4).
- Wrapper (judge.sh lineage): lock, lineage sentinel, preflight before
  tokens, artifact verified by schema/shape never exit code (AC-08).
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process  # exercises scripts/ + examples/ (FR-756)

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_PY = REPO_ROOT / "scripts" / "research_preflight.py"
RESEARCH_SH = REPO_ROOT / "scripts" / "research.sh"
TOOLS_PY = (
    REPO_ROOT / "examples" / "demos" / "research-route" / "nodes" / "research_tools.py"
)
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "fr890"
CLEAN_BRIEF = FIXTURES / "clean-brief.md"
CONTAMINATED_BRIEF = FIXTURES / "contaminated-brief.md"

COLUMNS = [
    "candidate",
    "persona",
    "class",
    "verdict",
    "precedent",
    "is_this_a_graph",
    "effort-risk",
    "rationale",
]

OPA_URL = "https://www.openpolicyagent.org/"
TOOL_RESULTS = [{"tool": "search_web", "output": f"OPA docs URL: {OPA_URL}"}]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def preflight():
    assert PREFLIGHT_PY.exists(), f"missing: {PREFLIGHT_PY}"
    return _load("research_preflight", PREFLIGHT_PY)


@pytest.fixture(scope="module")
def tools():
    assert TOOLS_PY.exists(), f"missing: {TOOLS_PY}"
    return _load("research_tools", TOOLS_PY)


def _finding(**overrides) -> dict:
    base = {
        "persona": "os-infra-primitivist",
        "candidate": "OS permission bit on the governed path",
        "solution_class": "os-permissions",
        "verdict": "pursue",
        "rationale": "kernel enforcement beats instruction text",
        "precedent": "chmod a-w precedent in FR-889",
        "is_this_a_graph": "no",
        "effort_risk": "low/low",
    }
    base.update(overrides)
    return base


def _five_findings() -> list[dict]:
    return [
        _finding(),
        _finding(
            persona="data-process-planner",
            candidate="schema change dissolving the parse",
            solution_class="schema-data",
            precedent="FR-884 skeleton JSONL",
        ),
        _finding(
            persona="yamlgraph-native-planner",
            candidate="map+reduce graph over personas",
            solution_class="graph-pipeline",
            is_this_a_graph="yes: map node",
            precedent="examples/demos/map/graph.yaml",
        ),
        _finding(
            persona="subtractionist",
            candidate="delete the requirement",
            solution_class="subtraction",
            verdict="dissent",
            precedent="growth_as_default (Scripture)",
        ),
        _finding(
            persona="librarian",
            candidate="policy-as-code gate",
            solution_class="external-method",
            precedent=f"OPA conftest {OPA_URL}",
        ),
    ]


def _reduce(tools, findings, base_dir, tool_results=TOOL_RESULTS):
    return tools.reduce_findings(
        findings,
        str(CLEAN_BRIEF),
        base_dir=str(base_dir),
        librarian_tool_results=tool_results,
        repo_root=str(REPO_ROOT),
    )


# --- brief closure preflight (AC-02, R-2) ----------------------------------


@pytest.mark.req("REQ-YG-623")
def test_check_brief_accepts_clean_fixture(preflight):
    violations = preflight.check_brief(CLEAN_BRIEF.read_text(encoding="utf-8"))
    assert violations == []


@pytest.mark.req("REQ-YG-623")
def test_check_brief_rejects_contaminated_fixture(preflight):
    violations = preflight.check_brief(CONTAMINATED_BRIEF.read_text(encoding="utf-8"))
    joined = "\n".join(violations).lower()
    assert violations, "contaminated brief must be rejected"
    assert "proposed solution" in joined
    assert "candidate" in joined


@pytest.mark.req("REQ-YG-623")
def test_check_brief_requires_all_headings(preflight):
    text = CLEAN_BRIEF.read_text(encoding="utf-8").replace("## Constraints", "## Notes")
    violations = preflight.check_brief(text)
    assert any("constraints" in v.lower() for v in violations)


@pytest.mark.req("REQ-YG-623")
def test_check_brief_rejects_unknown_classification(preflight):
    text = CLEAN_BRIEF.read_text(encoding="utf-8").replace(
        "judgement/analysis/generation", "vibes/unknown"
    )
    violations = preflight.check_brief(text)
    assert any("classification" in v.lower() for v in violations)


@pytest.mark.req("REQ-YG-623")
def test_preflight_cli_exit_codes(tmp_path):
    ok = subprocess.run(
        [sys.executable, str(PREFLIGHT_PY), str(CLEAN_BRIEF)],
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run(
        [sys.executable, str(PREFLIGHT_PY), str(CONTAMINATED_BRIEF)],
        capture_output=True,
        text=True,
    )
    assert bad.returncode == 64
    assert "Proposed Solution" in bad.stderr + bad.stdout


# --- reducer: frozen artifact schema (AC-06, AC-07, R-3) --------------------


@pytest.mark.req("REQ-YG-623")
def test_reduce_writes_artifact_with_frozen_schema(tools, tmp_path):
    result = _reduce(tools, _five_findings(), tmp_path)
    artifact = tmp_path / "tmp" / "draft-alternatives.md"
    assert artifact.exists()
    text = artifact.read_text(encoding="utf-8")
    for column in COLUMNS:
        assert column in text, f"missing column: {column}"
    assert "clean-brief.md" in text  # brief filename in metadata header
    assert "librarian" in text
    assert result["rows"] == 5
    assert result["classes"] == 5  # advisory report, not a gate (FR-896 R-2)


@pytest.mark.req("REQ-YG-623")
def test_reduce_preserves_conflicting_rows(tools, tmp_path):
    """FR-1005 re-homed to canonical five-slot input: the subtractionist slot
    dissents on the os-infra candidate; both rows survive, nothing is voted."""
    findings = _five_findings()
    findings[3] = _finding(
        persona="subtractionist",
        candidate="OS permission bit on the governed path",
        solution_class="os-permissions",
        verdict="dissent",
        precedent="FR-889: permission bit is bypassable by owner",
    )
    result = _reduce(tools, findings, tmp_path)
    assert result["rows"] == 5, "disagreement must be preserved as rows, never voted"
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert text.count("OS permission bit on the governed path") == 2


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_librarian_error_string(tools, tmp_path):
    findings = _five_findings()
    findings[4]["precedent"] = "Error: ddgs package not installed"
    with pytest.raises(ValueError, match="librarian"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_librarian_without_url(tools, tmp_path):
    findings = _five_findings()
    findings[4]["precedent"] = "some vague memory of a tool"
    with pytest.raises(ValueError, match="URL"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_empty_cell(tools, tmp_path):
    """FR-1005 re-homed: an empty cell is a model-owned defect, so the row is
    contained (never written, never repaired) and the run keeps four rows."""
    findings = _five_findings()
    findings[1]["precedent"] = ""
    result = _reduce(tools, findings, tmp_path)
    assert result["rows"] == 4
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert "schema change dissolving the parse" not in text.split("|---|")[-1]
    failed_line = next(
        ln for ln in text.splitlines() if ln.startswith("- personas failed:")
    )
    assert "data_process_finding" in failed_line and "empty" in failed_line


@pytest.mark.req("REQ-YG-623")
def test_reduce_single_class_convergence_is_advisory(tools, tmp_path):
    """FR-896 R-2 replacement witness: convergence never fails the gate."""
    findings = [
        _finding(persona=f"p{i}", precedent="FR-889 write lock") for i in range(5)
    ]
    result = _reduce(tools, findings, tmp_path)
    assert result["rows"] == 5
    assert result["classes"] == 1  # reported, not gated


# --- artifact verifier (wrapper shape check, AC-08) --------------------------


@pytest.mark.req("REQ-YG-623")
def test_verify_artifact_accepts_reduced_output(preflight, tools, tmp_path):
    _reduce(tools, _five_findings(), tmp_path)
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert preflight.verify_artifact(text) == []


@pytest.mark.req("REQ-YG-623")
def test_verify_artifact_rejects_missing_column(preflight):
    text = "# Draft alternatives\n\n| candidate | persona |\n|---|---|\n| x | y |\n"
    violations = preflight.verify_artifact(text)
    assert any("verdict" in v for v in violations)


# --- persona schema ----------------------------------------------------------


@pytest.mark.req("REQ-YG-623")
def test_persona_finding_schema_rejects_empty_fields(tools):
    with pytest.raises(ValueError):
        tools.PersonaFinding(**_finding(candidate=""))


@pytest.mark.req("REQ-YG-623")
def test_collect_graph_shapes_names_map(tools):
    shapes = tools.collect_graph_shapes(str(REPO_ROOT / "examples" / "demos"))
    assert "map" in shapes


# --- wrapper: scripts/research.sh (AC-08) ------------------------------------


def _write_stub(path: Path, body: str) -> Path:
    path.write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _run_wrapper(args, workdir: Path, stub: Path | None, extra_env=None):
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("RESEARCH_EXECUTION", "YAMLGRAPH_BIN")
    }
    env["RESEARCH_WORKDIR"] = str(workdir)
    if stub is not None:
        env["YAMLGRAPH_BIN"] = str(stub)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(RESEARCH_SH), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.req("REQ-YG-623")
def test_research_usage_exit_64(tmp_path):
    assert _run_wrapper([], tmp_path, None).returncode == 64


@pytest.mark.req("REQ-YG-623")
def test_research_missing_brief_exit_66(tmp_path):
    assert _run_wrapper([str(tmp_path / "nope.md")], tmp_path, None).returncode == 66


@pytest.mark.req("REQ-YG-623")
def test_research_sentinel_exit_70(tmp_path):
    result = _run_wrapper(
        [str(CLEAN_BRIEF)], tmp_path, None, {"RESEARCH_EXECUTION": "1"}
    )
    assert result.returncode == 70
    assert "do not re-invoke" in result.stderr


@pytest.mark.req("REQ-YG-623")
def test_research_fresh_lock_exit_73(tmp_path):
    lock = tmp_path / "tmp" / ".research.lock"
    lock.mkdir(parents=True)
    (lock / "holder").write_text(
        "pid=99999 started=2026-08-26T00:00:00Z\n", encoding="utf-8"
    )
    result = _run_wrapper([str(CLEAN_BRIEF)], tmp_path, None)
    assert result.returncode == 73
    assert "pid=99999" in result.stderr


@pytest.mark.req("REQ-YG-623")
def test_research_preflight_blocks_contaminated_brief(tmp_path):
    stub = _write_stub(tmp_path / "yg", 'touch "$RESEARCH_WORKDIR/tmp/graph-ran"')
    result = _run_wrapper([str(CONTAMINATED_BRIEF)], tmp_path, stub)
    assert result.returncode == 64
    assert not (tmp_path / "tmp" / "graph-ran").exists(), (
        "preflight must run before any tokens are spent"
    )


@pytest.mark.req("REQ-YG-623")
def test_research_stub_run_verifies_artifact(tools, tmp_path):
    valid_dir = tmp_path / "valid"
    _reduce(tools, _five_findings(), valid_dir)
    fixture = valid_dir / "tmp" / "draft-alternatives.md"
    stub = _write_stub(
        tmp_path / "yg",
        'mkdir -p "$RESEARCH_WORKDIR/tmp"\n'
        f'cp "{fixture}" "$RESEARCH_WORKDIR/tmp/draft-alternatives.md"',
    )
    result = _run_wrapper([str(CLEAN_BRIEF)], tmp_path, stub)
    assert result.returncode == 0, result.stderr


@pytest.mark.req("REQ-YG-623")
def test_research_artifact_contract_violation_exit_65(tmp_path):
    stub = _write_stub(
        tmp_path / "yg",
        'mkdir -p "$RESEARCH_WORKDIR/tmp"\n'
        'printf "junk\\n" > "$RESEARCH_WORKDIR/tmp/draft-alternatives.md"',
    )
    result = _run_wrapper([str(CLEAN_BRIEF)], tmp_path, stub)
    assert result.returncode == 65
    assert "contract" in result.stderr
