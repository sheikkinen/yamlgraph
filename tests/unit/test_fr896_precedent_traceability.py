"""FR-896 RED witnesses — research-route precedent traceability.

Judged contract (FR-896 judgement, R-1..R-4 folded):
- Librarian URL reconciled against ``librarian_tool_results`` (AC-01).
- One shared librarian predicate across reducer and verifier (AC-02).
- Non-librarian precedent: existing committed identifier passes; explicit
  ``brief-echo`` marker demotes to ``verdict: echo`` (retained, excluded
  from scoring); nonexistent identifiers FAIL with a named violation —
  never silently echo (AC-03, AC-04, R-1).
- Committed-context block: deterministic, bounded, author-independent;
  CAP one-liners + ARCHITECTURE headings + Scripture keys; graph-shape
  inventory covers demos, graphs/, .chaplain/graphs/ (AC-05).
- ``solution_class`` and ``verdict`` closed enums; only the reducer sets
  ``echo``; convergence annotated ``convergent xN``; three same-class
  non-echo traceable findings PASS — distinct-class count is advisory,
  never blocking (AC-06, R-2).
- ``max_length=400`` on model-authored prose; over-length rejected, not
  truncated (AC-07).
- Provenance stamp: committed research-runs.jsonl line with brief/artifact
  hashes, code git SHA; verifier distinguishes matching / missing /
  mismatched — integrity, not execution proof (AC-08, R-3).
- The 2026-08-28 solution-shaped librarian output, replayed, is rejected
  (AC-09).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
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
FR890_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "fr890"
CLEAN_BRIEF = FR890_FIXTURES / "clean-brief.md"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def preflight():
    return _load("research_preflight_896", PREFLIGHT_PY)


@pytest.fixture(scope="module")
def tools():
    return _load("research_tools_896", TOOLS_PY)


OPA_URL = "https://www.openpolicyagent.org/docs/latest/"
TOOL_RESULTS = [
    {
        "tool": "search_web",
        "args": {"query": "policy as code gates"},
        "output": f"1. OPA docs\n   URL: {OPA_URL}\n   Policy-as-code gating.",
    }
]


def _finding(**overrides) -> dict:
    base = {
        "persona": "os-infra-primitivist",
        "candidate": "OS permission bit on the governed path",
        "solution_class": "os-permissions",
        "verdict": "pursue",
        "rationale": "kernel enforcement beats instruction text",
        "precedent": "FR-889 permission-boundary table",
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
            precedent="growth_as_default",
        ),
        _finding(
            persona="librarian",
            candidate="policy-as-code gate",
            solution_class="external-method",
            precedent=f"OPA conftest {OPA_URL}",
        ),
    ]


def _reduce(tools, findings, tmp_path, tool_results=TOOL_RESULTS):
    return tools.reduce_findings(
        findings,
        str(CLEAN_BRIEF),
        base_dir=str(tmp_path),
        librarian_tool_results=tool_results,
        repo_root=str(REPO_ROOT),
    )


# --- AC-01: librarian URL reconciled against tool results --------------------


@pytest.mark.req("REQ-YG-623")
def test_librarian_url_present_in_tool_results_passes(tools, tmp_path):
    result = _reduce(tools, _five_findings(), tmp_path)
    assert result["rows"] == 5


@pytest.mark.req("REQ-YG-623")
def test_librarian_url_absent_from_tool_results_fails(tools, tmp_path):
    findings = _five_findings()
    findings[4]["precedent"] = "made-up https://fabricated.example.com/pattern"
    with pytest.raises(ValueError, match="tool_results"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_librarian_fails_closed_without_tool_results(tools, tmp_path):
    with pytest.raises(ValueError, match="tool_results"):
        _reduce(tools, _five_findings(), tmp_path, tool_results=[])


# --- AC-02: one shared librarian predicate -----------------------------------


@pytest.mark.req("REQ-YG-623")
def test_web_librarian_label_hits_reconciliation_in_reducer(tools, tmp_path):
    findings = _five_findings()
    findings[4]["persona"] = "web-librarian"
    findings[4]["precedent"] = "vague https://fabricated.example.com/x"
    with pytest.raises(ValueError, match="tool_results"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_shared_predicate_exists_in_both_modules(tools, preflight):
    assert tools.is_librarian("Web-Librarian (grounded)")
    assert preflight.is_librarian("Web-Librarian (grounded)")
    assert not tools.is_librarian("subtractionist")
    assert tools.SOLUTION_CLASSES == preflight.SOLUTION_CLASSES, (
        "enum drift between reducer and verifier"
    )


# --- AC-03/AC-04: precedent three-way validation (R-1) ------------------------


@pytest.mark.req("REQ-YG-623")
def test_existing_committed_identifier_passes(tools, tmp_path):
    result = _reduce(tools, _five_findings(), tmp_path)
    assert result["non_echo_rows"] == 5


@pytest.mark.req("REQ-YG-623")
def test_explicit_brief_echo_is_demoted_and_retained(tools, tmp_path):
    """FR-938 supersedes the FR-896 demotion: the brief is not its own precedent.

    Demote-never-drop kept hollow rows in the record. With the personas
    now shown the FR corpus, an echo is a refusal to look, and the honest
    alternative is the bounded `none-retrieved` token.
    """
    findings = _five_findings()
    findings[0]["precedent"] = "brief-echo: restates the closure constraint"
    with pytest.raises(ValueError, match="brief-echo"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_nonexistent_identifier_fails_never_echo(tools, tmp_path):
    findings = _five_findings()
    findings[1]["precedent"] = "FR-99999 imaginary precedent"
    with pytest.raises(ValueError, match="precedent"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_malformed_path_fails(tools, tmp_path):
    findings = _five_findings()
    findings[1]["precedent"] = "see docs/never-written-analysis.md"
    with pytest.raises(ValueError, match="precedent"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_no_identifier_no_marker_fails(tools, tmp_path):
    findings = _five_findings()
    findings[1]["precedent"] = "the problem statement says so"
    with pytest.raises(ValueError, match="precedent"):
        _reduce(tools, findings, tmp_path)


@pytest.mark.req("REQ-YG-623")
def test_scripture_key_is_a_valid_identifier(tools, tmp_path):
    findings = _five_findings()
    findings[1]["precedent"] = "two_strike_split"
    result = _reduce(tools, findings, tmp_path)
    assert result["non_echo_rows"] == 5


@pytest.mark.req("REQ-YG-623")
def test_committed_demo_dir_name_is_a_valid_identifier(tools, tmp_path):
    """Live false positive 2026-08-28: 'corpus_census' names a committed demo."""
    findings = _five_findings()
    findings[1]["precedent"] = "corpus_census demo reducer"
    result = _reduce(tools, findings, tmp_path)
    assert result["non_echo_rows"] == 5


# --- AC-05: committed-context block + widened inventory ----------------------


@pytest.mark.req("REQ-YG-623")
def test_committed_context_block_contents(tools):
    block = tools.collect_committed_context(str(REPO_ROOT))
    assert "CAP-01" in block
    assert "two_strike_split" in block  # Scripture trap/cure key
    assert "Architecture" in block or "architecture" in block.lower()
    assert len(block.splitlines()) <= 300, "block must stay bounded"


@pytest.mark.req("REQ-YG-623")
def test_graph_shapes_cover_all_graph_dirs(tools):
    shapes = tools.collect_graph_shapes(str(REPO_ROOT))
    assert "research-route" in shapes  # demos
    assert shapes.count("\n") >= 20, "count threshold, not a named-demo canary"


# --- AC-06: closed enums, reducer-only echo, convergence-safe gate (R-2) -----


@pytest.mark.req("REQ-YG-623")
def test_free_text_class_fails_validation(tools):
    with pytest.raises(ValueError, match="solution_class"):
        tools.PersonaFinding(**_finding(solution_class="contamination-detection-gate"))


@pytest.mark.req("REQ-YG-623")
def test_free_text_verdict_fails_validation(tools):
    with pytest.raises(ValueError, match="verdict"):
        tools.PersonaFinding(**_finding(verdict="Deserves planning attention"))


@pytest.mark.req("REQ-YG-623")
def test_model_cannot_claim_echo_verdict(tools):
    with pytest.raises(ValueError, match="echo"):
        tools.PersonaFinding(**_finding(verdict="echo"))


@pytest.mark.req("REQ-YG-623")
def test_three_same_class_non_echo_rows_pass_and_annotate(tools, tmp_path):
    findings = _five_findings()
    for i in (0, 1):
        findings[i]["solution_class"] = "boundary-enforcement"
        findings[i]["precedent"] = "FR-890 reducer boundary"
    findings[2]["solution_class"] = "boundary-enforcement"
    findings[2]["precedent"] = "FR-890 reducer boundary"
    result = _reduce(tools, findings, tmp_path)
    assert result["rows"] == 5, "same-class convergence must never fail the gate"
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert "convergent x3" in text


@pytest.mark.req("REQ-YG-623")
def test_fewer_than_three_non_echo_traceable_findings_fails(tools, tmp_path):
    """The grounding floor still bites — now on ungrounded rows, not echoes."""
    findings = _five_findings()[:2]
    with pytest.raises(ValueError, match="fewer than 3 grounded findings"):
        _reduce(tools, findings, tmp_path)


# --- AC-07: max_length rejection ----------------------------------------------


@pytest.mark.req("REQ-YG-623")
def test_over_length_cell_rejected_not_truncated(tools, tmp_path):
    """FR-1005 re-homed (judgement AC-06): the over-length row is rejected as a
    row — never written, never truncated — and the named violation now lives
    in the artifact's persona accounting instead of killing the run."""
    findings = _five_findings()
    findings[1]["candidate"] = "x" * 401
    result = _reduce(tools, findings, tmp_path)
    assert result["rows"] == 4
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert "x" * 400 not in text  # not truncated, not written
    failed_line = next(
        ln for ln in text.splitlines() if ln.startswith("- personas failed:")
    )
    assert "data_process_finding" in failed_line
    assert "400" in failed_line and "string_too_long" in failed_line


# --- AC-08: provenance stamp + integrity verifier (R-3) -----------------------


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


MINIMAL_ARTIFACT = """# Draft alternatives

- brief: clean-brief.md
- run date: 2026-08-28T00:00:00Z
- personas executed: a, b, c, d, librarian

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| a | os-infra-primitivist | os-permissions | pursue | FR-889 | no | low/low | r |
| b | data-process-planner | schema-data | pursue | FR-884 | no | low/low | r |
| c | yamlgraph-native-planner | graph-pipeline | pursue | FR-890 | yes | low/low | r |
| d | subtractionist | subtraction | dissent | growth_as_default | no | low/low | r |
| e | librarian | external-method | pursue | OPA https://www.openpolicyagent.org/ | no | low/low | r |
"""


@pytest.mark.req("REQ-YG-623")
def test_wrapper_appends_provenance_line(tmp_path):
    stub = _write_stub(
        tmp_path / "yg",
        'mkdir -p "$RESEARCH_WORKDIR/tmp"\n'
        f"cat > \"$RESEARCH_WORKDIR/tmp/draft-alternatives.md\" <<'ART'\n"
        f"{MINIMAL_ARTIFACT}ART",
    )
    result = _run_wrapper([str(CLEAN_BRIEF)], tmp_path, stub)
    assert result.returncode == 0, result.stderr
    log = tmp_path / "feature-requests" / "research-runs.jsonl"
    assert log.exists(), "provenance log must be written under feature-requests/"
    record = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    for key in (
        "brief_sha256",
        "artifact_sha256",
        "code_git_sha",
        "timestamp",
        "graph",
    ):
        assert key in record, f"missing provenance key: {key}"
    assert (
        record["brief_sha256"] == hashlib.sha256(CLEAN_BRIEF.read_bytes()).hexdigest()
    )


@pytest.mark.req("REQ-YG-623")
def test_verify_promotion_matching_missing_mismatched(preflight, tmp_path):
    artifact_text = MINIMAL_ARTIFACT
    brief = tmp_path / "brief.md"
    brief.write_text("problem\n", encoding="utf-8")
    record = tmp_path / "FR-900.research.md"
    record.write_text("<!-- header -->\n\n" + artifact_text, encoding="utf-8")
    line = {
        "brief_path": str(brief),
        "brief_sha256": hashlib.sha256(brief.read_bytes()).hexdigest(),
        "artifact_sha256": hashlib.sha256(artifact_text.encode()).hexdigest(),
        "code_git_sha": "deadbeef",
        "timestamp": "2026-08-28T00:00:00Z",
        "graph": "examples/demos/research-route/graph.yaml",
    }
    log = tmp_path / "research-runs.jsonl"
    log.write_text(json.dumps(line) + "\n", encoding="utf-8")
    assert (
        preflight.verify_promotion(
            record.read_text(encoding="utf-8"),
            log.read_text(encoding="utf-8"),
            str(tmp_path),
        )
        == "matching"
    )
    assert (
        preflight.verify_promotion(
            record.read_text(encoding="utf-8"), "", str(tmp_path)
        )
        == "missing"
    )
    tampered = record.read_text(encoding="utf-8").replace("FR-889", "FR-000")
    assert (
        preflight.verify_promotion(
            tampered, log.read_text(encoding="utf-8"), str(tmp_path)
        )
        == "mismatched"
    )


# --- AC-09: 2026-08-28 solution-shaped librarian output, replayed -------------

SOLUTION_SHAPED_LIBRARIAN = {
    "persona": "librarian",
    "candidate": (
        "Implement a secondary contamination gate that parses the brief's "
        "constraints and incidents sections to extract seeded concepts"
    ),
    "solution_class": "contamination-detection-gate",
    "verdict": "pursue",
    "rationale": "closes the gap without LLM verdicts",
    "precedent": "https://www.mechanisticmindset.com/wiki/epistemic-contamination",
    "is_this_a_graph": "No. This is a procedural gate",
    "effort_risk": "Medium effort, low risk",
}


@pytest.mark.req("REQ-YG-623")
def test_solution_shaped_librarian_replay_rejected(tools):
    with pytest.raises(ValueError, match="solution_class"):
        tools.PersonaFinding(**SOLUTION_SHAPED_LIBRARIAN)


# --- artifact verifier: new gate semantics (AC-11) ----------------------------


@pytest.mark.req("REQ-YG-623")
def test_verify_artifact_accepts_same_class_convergence(preflight):
    text = MINIMAL_ARTIFACT.replace("schema-data", "os-permissions").replace(
        "graph-pipeline", "os-permissions"
    )
    assert preflight.verify_artifact(text) == []


@pytest.mark.req("REQ-YG-623")
def test_verify_artifact_rejects_free_text_class(preflight):
    text = MINIMAL_ARTIFACT.replace("os-permissions", "vibes-based-class")
    violations = preflight.verify_artifact(text)
    assert any("class" in v for v in violations)


@pytest.mark.req("REQ-YG-623")
def test_verify_artifact_counts_non_echo_rows(preflight):
    text = MINIMAL_ARTIFACT
    for verdict in ("| pursue |", "| dissent |"):
        text = text.replace(verdict, "| echo |")
    violations = preflight.verify_artifact(text)
    assert any("non-echo" in v for v in violations)
