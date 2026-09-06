"""FR-1005 witnesses — one attributable failed persona is a recorded row.

Three research-route runs on 2026-09-05 died on one cell each: an enum
field carrying prose killed run 1 in the reducer; a 471-character
``candidate`` killed runs 2 and 3 in the persona node and then in
``gather_findings``. The artifact contract needs four rows, three of them
grounded, and a librarian row. These witnesses hold the judged contract:
exactly one non-librarian persona may fail, and only on a defect the model
owns, attributed by canonical slot through a typed record; the artifact
carries JSON persona accounting whose invariants the verifier re-checks;
every structural, ambiguous, librarian, or precedent failure stays fatal
and leaves no artifact behind; nothing is truncated or repaired.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from yamlgraph.models.schemas import ErrorType, PipelineError

pytestmark = pytest.mark.process  # exercises scripts/ + examples/ (FR-756)

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_PY = REPO_ROOT / "scripts" / "research_preflight.py"
RESEARCH_SH = REPO_ROOT / "scripts" / "research.sh"
ROUTE_DIR = REPO_ROOT / "examples" / "demos" / "research-route"
TOOLS_PY = ROUTE_DIR / "nodes" / "research_tools.py"
GRAPH_YAML = ROUTE_DIR / "graph.yaml"
CLEAN_BRIEF = REPO_ROOT / "tests" / "fixtures" / "fr890" / "clean-brief.md"

OPA_URL = "https://www.openpolicyagent.org/"
TOOL_RESULTS = [{"tool": "search_web", "output": f"OPA docs URL: {OPA_URL}"}]
EXECUTED_HEADER = "- persona keys executed:"
FAILED_HEADER = "- personas failed:"

# The run-1 cell, verbatim (evidence file): valid enum head, rationale tail.
RUN1_CLASS_CELL = (
    "process-boundary. The four per-vendor concerns (headless contract, "
    "tool-call gate, transcript, session id) belong in a single abstraction "
    "boundary, not scattered across adapters and hooks."
)
# The run-2/3 candidate, 471 characters (evidence file).
RUN3_CANDIDATE = (
    "Introduce a vendor-neutral backend abstraction layer as a YAMLGraph "
    "extension point. Each backend (Copilot CLI, Claude Code) registers its "
    "contract (session recovery, auth probes, flag matrix, stdout parsing) "
    "through a common interface. The graph author declares `backend: copilot` "
    "or `backend: claude-code` in the node; the runtime dispatches to the "
    "registered handler without embedding vendor logic in copilot_runtime.py."
)
PARSE_MESSAGE = (
    "Failed to parse YamlgraphNativeFinding from completion {...}. Got: "
    "1 validation error for YamlgraphNativeFinding\ncandidate\n  "
    "String should have at most 400 characters [type=string_too_long]"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tools():
    return _load("research_tools_fr1005", TOOLS_PY)


@pytest.fixture(scope="module")
def preflight():
    return _load("research_preflight_fr1005", PREFLIGHT_PY)


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


def _reduce(tools, findings, base_dir):
    return tools.reduce_findings(
        findings,
        str(CLEAN_BRIEF),
        base_dir=str(base_dir),
        librarian_tool_results=TOOL_RESULTS,
        repo_root=str(REPO_ROOT),
    )


def _artifact_path(base_dir) -> Path:
    return base_dir / "tmp" / "draft-alternatives.md"


def _artifact(base_dir) -> str:
    return _artifact_path(base_dir).read_text(encoding="utf-8")


def _header(text: str, label: str) -> str:
    line = next(line for line in text.splitlines() if line.startswith(label))
    return line[len(label) :].strip()


def _parse_error(node: str = "yamlgraph_native_planner") -> PipelineError:
    """The shape the retry handler recorded in runs 2 and 3 (evidence file)."""
    return PipelineError(
        type=ErrorType.UNKNOWN_ERROR,
        message=PARSE_MESSAGE,
        node=node,
        details={"exception_type": "OutputParserException"},
    )


def _validation_error(node: str = "yamlgraph_native_planner") -> PipelineError:
    return PipelineError(
        type=ErrorType.VALIDATION_ERROR,
        message="1 validation error for PersonaFinding\nrationale\n  too long",
        node=node,
        details={"exception_type": "ValidationError"},
    )


def _failed_record(
    tools, key: str = "yamlgraph_native_finding", cause: str = "x: y"
) -> dict:
    return tools.FailedPersona(state_key=key, cause=cause).model_dump()


def _state_missing(tools, *missing: str, **extra) -> dict:
    state = {
        key: _finding(persona=key) for key in tools.PERSONA_KEYS if key not in missing
    }
    state.update(extra)
    return state


# --- AC-01, AC-04: gather contains one attributable model-output failure -----


@pytest.mark.req("REQ-YG-665")
@pytest.mark.parametrize("error_factory", [_parse_error, _validation_error])
def test_gather_contains_attributable_model_output_failure(tools, error_factory):
    state = _state_missing(tools, "yamlgraph_native_finding", errors=[error_factory()])

    result = tools.gather_findings(state)

    findings = result["findings"]
    assert len(findings) == len(tools.PERSONA_KEYS)
    record = tools.FailedPersona.model_validate(findings[2])  # canonical slot
    assert record.outcome == "row_failed"
    assert record.state_key == "yamlgraph_native_finding"
    for fragment in ("yamlgraph_native_planner", error_factory().type.value):
        assert fragment in record.cause
    assert error_factory().details["exception_type"] in record.cause
    assert error_factory().message.splitlines()[0] in record.cause
    assert [f.get("persona") for i, f in enumerate(findings) if i != 2] == [
        k for k in tools.PERSONA_KEYS if k != "yamlgraph_native_finding"
    ]


@pytest.mark.req("REQ-YG-665")
def test_gather_all_five_present_is_unchanged(tools):
    state = {key: {"persona": key} for key in tools.PERSONA_KEYS}
    state["errors"] = [_parse_error()]

    result = tools.gather_findings(state)

    assert list(result) == ["findings"]
    assert result["findings"] == [{"persona": key} for key in tools.PERSONA_KEYS]


# --- AC-02: everything not attributable stays fatal, with diagnostics --------


@pytest.mark.req("REQ-YG-665")
@pytest.mark.parametrize(
    ("label", "errors"),
    [
        ("absent channel", None),
        ("empty channel", []),
        ("malformed only", ["boom", None, {"unrelated": "noise"}]),
        ("no matching node", [_parse_error("librarian_structure")]),
        ("ambiguous", [_parse_error(), _validation_error()]),
        (
            "non-model failure",
            [
                {
                    "node": "yamlgraph_native_planner",
                    "type": "llm_error",
                    "message": "rate limited",
                    "details": {"exception_type": "RateLimitError"},
                }
            ],
        ),
    ],
)
def test_gather_stays_fatal_when_not_attributable(tools, label, errors):
    state = _state_missing(tools, "yamlgraph_native_finding")
    if errors is not None:
        state["errors"] = errors

    with pytest.raises(ValueError) as excinfo:
        tools.gather_findings(state)

    message = str(excinfo.value)
    assert message.startswith("missing persona findings: yamlgraph_native_finding"), (
        label
    )
    if label in ("absent channel", "empty channel", "malformed only"):
        assert message == "missing persona findings: yamlgraph_native_finding", label
    if label == "no matching node":
        assert "librarian_structure" in message
    if label == "non-model failure":
        assert "rate limited" in message and "RateLimitError" in message
    if label == "ambiguous":
        assert message.count("yamlgraph_native_planner") == 2
    assert "boom" not in message and "noise" not in message


@pytest.mark.req("REQ-YG-665")
def test_gather_never_contains_the_librarian(tools):
    state = _state_missing(
        tools, "librarian_finding", errors=[_parse_error("librarian_structure")]
    )
    with pytest.raises(ValueError, match="missing persona findings: librarian_finding"):
        tools.gather_findings(state)


# --- AC-03, AC-10: explicit attribution map, mirrored constants ----------------


@pytest.mark.req("REQ-YG-665")
def test_persona_node_map_is_explicit_and_matches_the_graph(tools):
    assert tuple(tools.PERSONA_NODES) == tools.PERSONA_KEYS
    graph_nodes = set(yaml.safe_load(GRAPH_YAML.read_text(encoding="utf-8"))["nodes"])
    for key, nodes in tools.PERSONA_NODES.items():
        assert nodes, key
        assert set(nodes) <= graph_nodes, (key, nodes - graph_nodes)
    assert tools.PERSONA_NODES["librarian_finding"] == frozenset(
        {"librarian_research", "librarian_structure"}
    )
    assert tools.LIBRARIAN_KEY == "librarian_finding"


@pytest.mark.req("REQ-YG-665")
def test_verifier_mirrors_reducer_constants(tools, preflight):
    assert len(tools.PERSONA_KEYS) == preflight.PERSONA_COUNT
    assert tuple(preflight.PERSONA_KEYS) == tools.PERSONA_KEYS
    assert preflight.MIN_ROWS == tools.MIN_VALID_ROWS
    assert preflight.LIBRARIAN_KEY == tools.LIBRARIAN_KEY


# --- AC-05, AC-06: reducer contains one row by canonical slot -----------------


@pytest.mark.req("REQ-YG-665")
def test_reduce_writes_four_rows_with_json_accounting(tools, preflight, tmp_path):
    findings = _five_findings()
    cause = (
        "yamlgraph_native_planner: unknown_error (OutputParserException): "
        + " ".join(PARSE_MESSAGE.split())
    )
    findings[2] = _failed_record(tools, cause=cause)

    result = _reduce(tools, findings, tmp_path)

    assert result["rows"] == 4
    assert result["failed"] == 1
    text = _artifact(tmp_path)
    executed = json.loads(_header(text, EXECUTED_HEADER))
    failed = json.loads(_header(text, FAILED_HEADER))
    assert executed == [
        k for k in tools.PERSONA_KEYS if k != "yamlgraph_native_finding"
    ]
    assert failed == {"yamlgraph_native_finding": cause}
    assert "yamlgraph-native-planner" not in _header(text, "- personas executed:")
    assert preflight.verify_artifact(text) == []


@pytest.mark.req("REQ-YG-665")
def test_reduce_full_run_has_no_failure_line(tools, preflight, tmp_path):
    result = _reduce(tools, _five_findings(), tmp_path)
    text = _artifact(tmp_path)
    assert result["failed"] == 0
    assert json.loads(_header(text, EXECUTED_HEADER)) == list(tools.PERSONA_KEYS)
    assert FAILED_HEADER not in text
    assert preflight.verify_artifact(text) == []


@pytest.mark.req("REQ-YG-665")
@pytest.mark.parametrize(
    ("slot", "field", "value", "error_type"),
    [
        (2, "candidate", RUN3_CANDIDATE, "string_too_long"),
        (1, "solution_class", RUN1_CLASS_CELL, "value_error"),
        (3, "verdict", "dissent: the requirement itself is the defect", "value_error"),
        (1, "precedent", "", "value_error"),
    ],
)
def test_reduce_contains_invalid_cell_without_repair(
    tools, preflight, tmp_path, slot, field, value, error_type
):
    findings = _five_findings()
    findings[slot][field] = value
    key = tools.PERSONA_KEYS[slot]

    result = _reduce(tools, findings, tmp_path)

    assert result["rows"] == 4
    assert result["failed"] == 1
    text = _artifact(tmp_path)
    failed = json.loads(_header(text, FAILED_HEADER))
    assert list(failed) == [key]
    assert field in failed[key] and error_type in failed[key]
    table = text.split("|---|")[-1]
    assert findings[slot]["candidate"] not in table  # the row was not written
    assert "process-boundary" not in table if field == "solution_class" else True
    assert preflight.verify_artifact(text) == []


# --- AC-07, AC-08, AC-12: fatal classes leave no artifact ----------------------


def _fatal_cases(tools) -> dict[str, list]:
    two_failures = _five_findings()
    two_failures[0]["candidate"] = RUN3_CANDIDATE
    two_failures[2] = _failed_record(tools)

    librarian_record = _five_findings()
    librarian_record[4] = _failed_record(
        tools, key="librarian_finding", cause="librarian_structure: llm_error: 429"
    )

    librarian_invalid = _five_findings()
    librarian_invalid[4]["candidate"] = RUN3_CANDIDATE

    six = _five_findings() + [_finding(persona="extra")]

    non_dict = _five_findings()
    non_dict[1] = "not a finding"

    wrong_slot = _five_findings()
    wrong_slot[1] = _failed_record(tools, key="yamlgraph_native_finding")

    fabricated = _five_findings()
    fabricated[0]["precedent"] = "CAP-628 keyed store"

    librarian_url = _five_findings()
    librarian_url[4]["precedent"] = "some vague memory of a tool"

    return {
        "two failures": two_failures,
        "librarian failed record": librarian_record,
        "librarian invalid row": librarian_invalid,
        "more findings than slots": six,
        "non-dict entry": non_dict,
        "record in the wrong slot": wrong_slot,
        "fabricated precedent": fabricated,
        "librarian without URL": librarian_url,
    }


@pytest.mark.req("REQ-YG-665")
def test_every_fatal_class_raises_before_any_artifact(tools, tmp_path):
    for label, findings in _fatal_cases(tools).items():
        base = tmp_path / label.replace(" ", "_")
        with pytest.raises(ValueError) as excinfo:
            _reduce(tools, findings, base)
        assert not _artifact_path(base).exists(), label
        message = str(excinfo.value)
        if label == "two failures":
            assert (
                "os_infra_finding" in message and "yamlgraph_native_finding" in message
            )
            assert "string_too_long" in message and "x: y" in message
        if label.startswith("librarian"):
            assert "librarian" in message.lower()
        if label == "fabricated precedent":
            assert "nonexistent CAP-628" in message


# --- AC-09: verifier re-checks the accounting invariants ----------------------


def _short_artifact(tools, tmp_path) -> str:
    findings = _five_findings()
    findings[2] = _failed_record(tools, cause="yamlgraph_native_planner: parse failed")
    _reduce(tools, findings, tmp_path)
    return _artifact(tmp_path)


def _replace_header(text: str, label: str, new_value: str | None) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith(label):
            if new_value is None:
                continue
            line = f"{label} {new_value}"
        lines.append(line)
    return "\n".join(lines) + "\n"


@pytest.mark.req("REQ-YG-665")
def test_verify_artifact_rejects_every_accounting_violation(tools, preflight, tmp_path):
    text = _short_artifact(tools, tmp_path)
    assert preflight.verify_artifact(text) == []
    executed = [k for k in tools.PERSONA_KEYS if k != "yamlgraph_native_finding"]

    mutations = {
        "missing executed line": _replace_header(text, EXECUTED_HEADER, None),
        "missing failed line": _replace_header(text, FAILED_HEADER, None),
        "malformed json": _replace_header(text, FAILED_HEADER, "{not json"),
        "unknown key": _replace_header(
            text, FAILED_HEADER, json.dumps({"ghost_finding": "x"})
        ),
        "duplicate executed key": _replace_header(
            text, EXECUTED_HEADER, json.dumps(executed[:-1] + [executed[0]])
        ),
        "overlapping sets": _replace_header(
            text, FAILED_HEADER, json.dumps({"os_infra_finding": "x"})
        ),
        "incomplete union": _replace_header(
            text, EXECUTED_HEADER, json.dumps(executed[:-1])
        ),
        "empty cause": _replace_header(
            text, FAILED_HEADER, json.dumps({"yamlgraph_native_finding": ""})
        ),
        "two failed keys": _replace_header(
            text,
            FAILED_HEADER,
            json.dumps({"yamlgraph_native_finding": "x", "os_infra_finding": "y"}),
        ),
        "failed librarian": _replace_header(
            text, FAILED_HEADER, json.dumps({"librarian_finding": "x"})
        ).replace(
            json.dumps(executed),
            json.dumps([k for k in tools.PERSONA_KEYS if k != "librarian_finding"]),
        ),
    }
    for label, mutated in mutations.items():
        violations = preflight.verify_artifact(mutated)
        assert violations, label
        assert any("persona" in v.lower() for v in violations), (label, violations)

    full = _reduce(tools, _five_findings(), tmp_path / "full") and _artifact(
        tmp_path / "full"
    )
    with_failure = full.replace(
        "\n\n|",
        f"\n{FAILED_HEADER} " + json.dumps({"os_infra_finding": "x"}) + "\n\n|",
        1,
    )
    violations = preflight.verify_artifact(with_failure)
    assert any("five" in v or "full run" in v for v in violations), violations


# --- AC-12: a failed graph cannot pass the wrapper by stale output --------------


@pytest.mark.req("REQ-YG-665")
def test_wrapper_never_verifies_a_stale_artifact(tmp_path):
    stale = tmp_path / "tmp" / "draft-alternatives.md"
    stale.parent.mkdir()
    stale.write_text("# Draft alternatives\nstale\n", encoding="utf-8")
    stub = tmp_path / "yg"
    stub.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
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
    assert "contract violated" in result.stderr
    assert not stale.exists()


# --- the runtime loader seam (witnessed live 2026-09-06) -------------------------


@pytest.mark.req("REQ-YG-665")
def test_failed_persona_builds_under_the_runtime_module_loader():
    """``yamlgraph.tools.python_tool.load_python_function`` execs the module
    without registering it in ``sys.modules``; a deferred ``Literal``
    annotation on ``FailedPersona`` made the live run die with
    "`FailedPersona` is not fully defined". Load the module the same way."""
    spec = importlib.util.spec_from_file_location(TOOLS_PY.stem, TOOLS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # no sys.modules entry, as the runtime does

    record = module.FailedPersona(state_key="yamlgraph_native_finding", cause="x: y")

    assert record.outcome == "row_failed"
    assert module.FailedPersona.model_validate(record.model_dump()) == record
    with pytest.raises(Exception, match="outcome"):
        module.FailedPersona(
            outcome="ok", state_key="yamlgraph_native_finding", cause="x"
        )
