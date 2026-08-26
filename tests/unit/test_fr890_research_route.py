"""FR-890 RED witnesses — research sole route (closed-input alternatives).

Judged contract (FR-890 judgement, R-1..R-6 folded):
- Deterministic problem-brief closure preflight (R-2): required headings,
  forbidden solution/candidate sections, closed classification enum;
  stdlib only, never an LLM (AC-02).
- Frozen artifact schema (R-3): tmp/draft-alternatives.md with columns
  candidate/persona/class/verdict/precedent/is_this_a_graph/effort-risk,
  4-6 distinct solution classes, no empty required cells, disagreement
  preserved as rows (AC-06, AC-07).
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
]


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
        "verdict": "viable",
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
            solution_class="data-model",
            precedent="FR-884 skeleton JSONL",
        ),
        _finding(
            persona="yamlgraph-native-planner",
            candidate="map+reduce graph over personas",
            solution_class="graph",
            is_this_a_graph="yes: map node",
            precedent="examples/demos/map",
        ),
        _finding(
            persona="subtractionist",
            candidate="delete the requirement",
            solution_class="subtraction",
            verdict="rejected",
            precedent="growth_as_default (Scripture)",
        ),
        _finding(
            persona="librarian",
            candidate="policy-as-code gate",
            solution_class="external-tooling",
            precedent="OPA conftest https://www.openpolicyagent.org/",
        ),
    ]


# --- brief closure preflight (AC-02, R-2) ----------------------------------


@pytest.mark.req("REQ-YG-623")
def test_check_brief_accepts_clean_fixture(preflight):
    violations = preflight.check_brief(CLEAN_BRIEF.read_text())
    assert violations == []


@pytest.mark.req("REQ-YG-623")
def test_check_brief_rejects_contaminated_fixture(preflight):
    violations = preflight.check_brief(CONTAMINATED_BRIEF.read_text())
    joined = "\n".join(violations).lower()
    assert violations, "contaminated brief must be rejected"
    assert "proposed solution" in joined
    assert "candidate" in joined


@pytest.mark.req("REQ-YG-623")
def test_check_brief_requires_all_headings(preflight):
    text = CLEAN_BRIEF.read_text().replace("## Constraints", "## Notes")
    violations = preflight.check_brief(text)
    assert any("constraints" in v.lower() for v in violations)


@pytest.mark.req("REQ-YG-623")
def test_check_brief_rejects_unknown_classification(preflight):
    text = CLEAN_BRIEF.read_text().replace(
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
    result = tools.reduce_findings(
        _five_findings(), str(CLEAN_BRIEF), base_dir=str(tmp_path)
    )
    artifact = tmp_path / "tmp" / "draft-alternatives.md"
    assert artifact.exists()
    text = artifact.read_text()
    for column in COLUMNS:
        assert column in text, f"missing column: {column}"
    assert "clean-brief.md" in text  # brief filename in metadata header
    assert "librarian" in text
    assert result["rows"] == 5
    assert 4 <= result["classes"] <= 6


@pytest.mark.req("REQ-YG-623")
def test_reduce_preserves_conflicting_rows(tools, tmp_path):
    findings = _five_findings()
    findings.append(
        _finding(
            persona="subtractionist",
            candidate="OS permission bit on the governed path",
            solution_class="os-permissions",
            verdict="rejected",
            precedent="disagrees: permission bit is bypassable by owner",
        )
    )
    result = tools.reduce_findings(findings, str(CLEAN_BRIEF), base_dir=str(tmp_path))
    assert result["rows"] == 6, "disagreement must be preserved as rows, never voted"
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text()
    assert text.count("OS permission bit on the governed path") == 2


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_librarian_error_string(tools, tmp_path):
    findings = _five_findings()
    findings[4]["precedent"] = "Error: ddgs package not installed"
    with pytest.raises(ValueError, match="librarian"):
        tools.reduce_findings(findings, str(CLEAN_BRIEF), base_dir=str(tmp_path))


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_librarian_without_url(tools, tmp_path):
    findings = _five_findings()
    findings[4]["precedent"] = "some vague memory of a tool"
    with pytest.raises(ValueError, match="URL"):
        tools.reduce_findings(findings, str(CLEAN_BRIEF), base_dir=str(tmp_path))


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_empty_cell(tools, tmp_path):
    findings = _five_findings()
    findings[1]["precedent"] = ""
    with pytest.raises(ValueError, match="empty"):
        tools.reduce_findings(findings, str(CLEAN_BRIEF), base_dir=str(tmp_path))


@pytest.mark.req("REQ-YG-623")
def test_reduce_fails_closed_on_class_count(tools, tmp_path):
    findings = [_finding(persona=f"p{i}") for i in range(5)]  # 1 distinct class
    with pytest.raises(ValueError, match="class"):
        tools.reduce_findings(findings, str(CLEAN_BRIEF), base_dir=str(tmp_path))


# --- artifact verifier (wrapper shape check, AC-08) --------------------------


@pytest.mark.req("REQ-YG-623")
def test_verify_artifact_accepts_reduced_output(preflight, tools, tmp_path):
    tools.reduce_findings(_five_findings(), str(CLEAN_BRIEF), base_dir=str(tmp_path))
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text()
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
    path.write_text(f"#!/usr/bin/env bash\n{body}\n")
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
    (lock / "holder").write_text("pid=99999 started=2026-08-26T00:00:00Z\n")
    result = _run_wrapper([str(CLEAN_BRIEF)], tmp_path, None)
    assert result.returncode == 73
    assert "pid=99999" in result.stderr


@pytest.mark.req("REQ-YG-623")
def test_research_preflight_blocks_contaminated_brief(tmp_path):
    stub = _write_stub(tmp_path / "yg", 'touch "$RESEARCH_WORKDIR/tmp/graph-ran"')
    result = _run_wrapper([str(CONTAMINATED_BRIEF)], tmp_path, stub)
    assert result.returncode == 64
    assert not (
        tmp_path / "tmp" / "graph-ran"
    ).exists(), "preflight must run before any tokens are spent"


@pytest.mark.req("REQ-YG-623")
def test_research_stub_run_verifies_artifact(tools, tmp_path):
    valid_dir = tmp_path / "valid"
    tools.reduce_findings(_five_findings(), str(CLEAN_BRIEF), base_dir=str(valid_dir))
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
