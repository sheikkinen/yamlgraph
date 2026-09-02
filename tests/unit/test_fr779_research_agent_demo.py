"""FR-779: Research-agent demo rot — binding hygiene and grounded synthesis gate.

RED suite (CAP-221 / REQ-YG-581). Two defect classes:

1. Bare non-{state...} node variable bindings fall through resolve_template
   as literal strings — the model receives "{query}" and hallucinates.
2. synthesize_report runs unconditionally even when validate_findings
   reports empty findings / low confidence (fabrication from vacuum).

Terminal contract (judgement R-2): empty findings + low confidence ends
after validate_findings, verdict preserved, no report produced;
synthesize_report runs only for non-empty findings with non-low confidence.
"""

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).parent.parent.parent
DEMOS_DIR = REPO_ROOT / "examples" / "demos"
GRAPH_PATH = DEMOS_DIR / "research-agent" / "graph.yaml"

# Whole-string bare placeholder: "{name}" that is not {state....}
_BARE_BINDING = re.compile(r"^\{(?!state\.)[^{}]+\}$")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _bare_bindings(raw: dict) -> list[str]:
    """Whole-string non-{state...} placeholder bindings in node variables."""
    found = []
    for node_name, node in (raw.get("nodes") or {}).items():
        for var, template in (node.get("variables") or {}).items():
            if isinstance(template, str) and _BARE_BINDING.match(template.strip()):
                found.append(f"{node_name}.{var} = {template!r}")
    return found


class TestBindingHygiene:
    """AC-02: research-agent binds via {state...}; AC-03: repo-wide sweep."""

    @pytest.mark.req("REQ-YG-581")
    def test_research_agent_has_no_bare_bindings(self) -> None:
        raw = _load(GRAPH_PATH)
        assert _bare_bindings(raw) == []

    @pytest.mark.req("REQ-YG-581")
    def test_research_agent_binds_query_and_scope_from_state(self) -> None:
        raw = _load(GRAPH_PATH)
        nodes = raw["nodes"]
        assert nodes["extract_intent"]["variables"]["query"] == "{state.query}"
        assert nodes["plan_research"]["variables"]["scope"] == "{state.scope}"
        assert nodes["execute_research"]["variables"]["scope"] == "{state.scope}"
        assert nodes["synthesize_report"]["variables"]["query"] == "{state.query}"

    @pytest.mark.req("REQ-YG-581")
    def test_research_agent_declares_query_and_scope_state(self) -> None:
        """Lint E007 requires state declarations for CLI-var-only fields."""
        raw = _load(GRAPH_PATH)
        state = raw.get("state") or {}
        assert state.get("query") == "str"
        assert state.get("scope") == "str"

    @pytest.mark.req("REQ-YG-581")
    def test_no_demo_graph_has_bare_bindings(self) -> None:
        """Repo-wide rot guard (partial_remediation): all committed demos.

        C-4: a violation outside research-agent halts enforcement for
        split or re-judgement — this assertion IS that halt.
        """
        violations = []
        for graph_file in sorted(DEMOS_DIR.glob("*/graph.yaml")):
            raw = _load(graph_file)
            for finding in _bare_bindings(raw):
                violations.append(f"{graph_file.parent.name}: {finding}")
        assert violations == []


class TestSynthesisGate:
    """AC-04/AC-05: topology routes empty/low-confidence away from synthesis."""

    @pytest.mark.req("REQ-YG-581")
    def test_validate_findings_routes_conditionally(self) -> None:
        """validate_findings must not route unconditionally to synthesize_report."""
        raw = _load(GRAPH_PATH)
        outgoing = [e for e in raw["edges"] if e.get("from") == "validate_findings"]
        unconditional_to_synth = [
            e
            for e in outgoing
            if e.get("to") == "synthesize_report" and "condition" not in e
        ]
        assert unconditional_to_synth == []

    @pytest.mark.req("REQ-YG-581")
    def test_low_confidence_terminates_without_report(self) -> None:
        """An edge ends the graph when confidence is low or findings empty."""
        raw = _load(GRAPH_PATH)
        outgoing = [e for e in raw["edges"] if e.get("from") == "validate_findings"]
        end_edges = [e for e in outgoing if e.get("to") == "END"]
        assert end_edges, "no terminal edge from validate_findings"
        conditions = " ".join(e.get("condition", "") for e in end_edges)
        assert "validation.confidence == 'low'" in conditions
        assert "findings == ''" in conditions

    @pytest.mark.req("REQ-YG-581")
    def test_positive_path_reaches_synthesis(self) -> None:
        """AC-05: non-low confidence with non-empty findings still synthesizes."""
        raw = _load(GRAPH_PATH)
        outgoing = [e for e in raw["edges"] if e.get("from") == "validate_findings"]
        synth_edges = [e for e in outgoing if e.get("to") == "synthesize_report"]
        assert synth_edges, "no path to synthesize_report"
        cond = synth_edges[0].get("condition", "")
        assert "validation.confidence != 'low'" in cond
        assert "findings != ''" in cond

    @pytest.mark.req("REQ-YG-581")
    def test_graph_compiles(self) -> None:
        """The gated topology must still compile to a valid graph."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(str(GRAPH_PATH))
        assert config is not None
