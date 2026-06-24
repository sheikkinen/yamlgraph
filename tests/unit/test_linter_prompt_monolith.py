"""FR-586 tests: W026 prompt-monolith linter check.

Calibration witness: the plot_modeller 7-prompt audit. W026 must fire on the
four monoliths (assign_pre_eff, assign_causality, assign_affects, extract_agents)
and stay silent on the two clean prompts (extract_glosses, classify_kinds).
extract_goals is the documented boundary case and is asserted neither way.

Minimal analogues carry the EXACT audit phrases so the test is immune to later
decomposition of the real prompts (FR-585) while remaining the calibration
witness the Judgement froze.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.checks_prompts import check_prompt_complexity
from yamlgraph.linter.graph_linter import lint_graph

# Exact prose carried verbatim from the audited plot_modeller prompts.
PROMPT_BODIES: dict[str, str] = {
    # --- monoliths: W026 MUST fire ---
    "assign_pre_eff": (
        "system: Formalize beats into predicates.\n"
        "user: |\n"
        "  For each beat assign FOUR slices:\n"
        "  - pre_world / eff_world / pre_belief / eff_belief\n"
    ),
    "assign_causality": (
        "system: Assign causality.\n"
        "user: |\n"
        "  For each beat assign THREE fields:\n"
        "  CRITICAL - FORWARD ONLY: a beat may only depend on earlier beats.\n"
    ),
    "assign_affects": (
        "system: Assign affects.\n"
        "user: |\n"
        "  ARC CLOSURE - every arc you OPEN should CLOSE later in the sequence.\n"
    ),
    "extract_agents": (
        "system: Extract agents.\n"
        "user: |\n"
        "  Extract three sections from the synopsis below.\n"
    ),
    # --- clean prompts: W026 MUST stay silent (A2 knife-edge negatives) ---
    "extract_glosses": (
        "system: Decompose synopsis into beats.\n"
        "user: |\n"
        "  Break the synopsis into beats.\n"
        "  - Every major plot point should be its own beat.\n"
    ),
    "classify_kinds": (
        "system: Classify beats.\n"
        "user: |\n"
        "  Classify each beat below into exactly ONE action type from this alphabet.\n"
    ),
}

FIRE = {"assign_pre_eff", "assign_causality", "assign_affects", "extract_agents"}
SILENT = {"extract_glosses", "classify_kinds"}


def _write_prompt(tmp_path: Path, name: str, content: str) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    (prompts_dir / f"{name}.yaml").write_text(content)


def _build_corpus_graph(tmp_path: Path) -> Path:
    """Write all calibration prompts and a chain graph referencing each."""
    names = list(PROMPT_BODIES)
    for name, body in PROMPT_BODIES.items():
        _write_prompt(tmp_path, name, body)

    nodes = {name: {"type": "llm", "prompt": name, "state_key": name} for name in names}
    edges = [{"from": "START", "to": names[0]}]
    edges += [{"from": names[i], "to": names[i + 1]} for i in range(len(names) - 1)]
    edges.append({"from": names[-1], "to": "END"})

    graph = {
        "version": "1.0",
        "name": "fr586-calibration",
        "state": {name: "str" for name in names},
        "nodes": nodes,
        "edges": edges,
    }
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph))
    return graph_path


@pytest.mark.req("REQ-YG-473")
def test_w026_calibration_witness(tmp_path: Path) -> None:
    """W026 fires on the four monoliths and stays silent on the two clean prompts."""
    result = lint_graph(_build_corpus_graph(tmp_path), tmp_path)
    fired = {
        issue.message.split("'")[1] for issue in result.issues if issue.code == "W026"
    }

    assert fired >= FIRE, f"W026 must fire on monoliths; missing {FIRE - fired}"
    assert not (
        SILENT & fired
    ), f"W026 must stay silent on clean prompts: {SILENT & fired}"


@pytest.mark.req("REQ-YG-473")
def test_w026_is_warning_severity_only(tmp_path: Path) -> None:
    """W026 is advisory: warning severity, never an error."""
    result = lint_graph(_build_corpus_graph(tmp_path), tmp_path)
    w026 = [issue for issue in result.issues if issue.code == "W026"]

    assert w026, "expected at least one W026 on the calibration corpus"
    assert all(issue.severity == "warning" for issue in w026)
    # No W026 should ever be elevated to an error code.
    assert not any(issue.code == "E026" for issue in result.issues)


@pytest.mark.req("REQ-YG-473")
def test_w026_message_names_prompt_and_remedy(tmp_path: Path) -> None:
    """The warning names the suspected prompt and links the decomposition remedy."""
    result = lint_graph(_build_corpus_graph(tmp_path), tmp_path)
    monolith = next(
        issue
        for issue in result.issues
        if issue.code == "W026" and "assign_pre_eff" in issue.message
    )
    assert "FR-585" in (monolith.fix or "")


@pytest.mark.req("REQ-YG-473")
def test_w026_inline_schema_field_count(tmp_path: Path) -> None:
    """A prompt with >= 4 inline top-level output fields fires W026-1."""
    _write_prompt(
        tmp_path,
        "four_fields",
        "system: Analyze.\n"
        "user: Analyze {topic}.\n"
        "schema:\n"
        "  name: Analysis\n"
        "  fields:\n"
        "    a: {type: str}\n"
        "    b: {type: str}\n"
        "    c: {type: str}\n"
        "    d: {type: str}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr586-schema",
        "state": {"topic": "str", "out": "str"},
        "nodes": {"n": {"type": "llm", "prompt": "four_fields", "state_key": "out"}},
        "edges": [{"from": "START", "to": "n"}, {"from": "n", "to": "END"}],
    }
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph))

    result = lint_graph(graph_path, tmp_path)
    assert any(issue.code == "W026" for issue in result.issues)


@pytest.mark.req("REQ-YG-473")
def test_w026_inline_schema_below_threshold_silent(tmp_path: Path) -> None:
    """A prompt with 3 inline fields stays silent at the default threshold (4)."""
    _write_prompt(
        tmp_path,
        "three_fields",
        "system: Analyze.\n"
        "user: Analyze {topic}.\n"
        "schema:\n"
        "  name: Analysis\n"
        "  fields:\n"
        "    a: {type: str}\n"
        "    b: {type: str}\n"
        "    c: {type: str}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr586-schema-clean",
        "state": {"topic": "str", "out": "str"},
        "nodes": {"n": {"type": "llm", "prompt": "three_fields", "state_key": "out"}},
        "edges": [{"from": "START", "to": "n"}, {"from": "n", "to": "END"}],
    }
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph))

    result = lint_graph(graph_path, tmp_path)
    assert not any(issue.code == "W026" for issue in result.issues)


@pytest.mark.req("REQ-YG-473")
def test_w026_field_threshold_parameter(tmp_path: Path) -> None:
    """A1: threshold is a function parameter (no lint-config file).

    The same 3-field prompt that is silent at the default fires when the
    caller passes field_threshold=3 directly.
    """
    _write_prompt(
        tmp_path,
        "three_fields",
        "system: Analyze.\n"
        "user: Analyze {topic}.\n"
        "schema:\n"
        "  name: Analysis\n"
        "  fields:\n"
        "    a: {type: str}\n"
        "    b: {type: str}\n"
        "    c: {type: str}\n",
    )
    graph = {
        "version": "1.0",
        "name": "fr586-threshold",
        "state": {"topic": "str", "out": "str"},
        "nodes": {"n": {"type": "llm", "prompt": "three_fields", "state_key": "out"}},
        "edges": [{"from": "START", "to": "n"}, {"from": "n", "to": "END"}],
    }
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph))

    default = check_prompt_complexity(graph_path, tmp_path)
    assert not any(issue.code == "W026" for issue in default)

    custom = check_prompt_complexity(graph_path, tmp_path, field_threshold=3)
    assert any(issue.code == "W026" for issue in custom)


@pytest.mark.req("REQ-YG-473")
def test_w026_silent_when_prompt_missing(tmp_path: Path) -> None:
    """Missing prompt files produce no W026 (E004 handles missing files)."""
    graph = {
        "version": "1.0",
        "name": "fr586-missing",
        "state": {"out": "str"},
        "nodes": {"n": {"type": "llm", "prompt": "nope", "state_key": "out"}},
        "edges": [{"from": "START", "to": "n"}, {"from": "n", "to": "END"}],
    }
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph))

    result = lint_graph(graph_path, tmp_path)
    assert not any(issue.code == "W026" for issue in result.issues)
