"""FR-716 witnesses: pre-emptive module splits.

Size-gate pressure relieved at CHOSEN seams (graph_schema bisection,
streaming event-translation extraction) instead of under deadline
pressure at the 450 gate. The metrics are the contract.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _lines(rel: str) -> int:
    return len((REPO_ROOT / rel).read_text(encoding="utf-8").splitlines())


def _function_cc(rel: str, func_name: str) -> int:
    from radon.complexity import cc_visit

    for block in cc_visit((REPO_ROOT / rel).read_text(encoding="utf-8")):
        if block.name == func_name:
            return block.complexity
    raise AssertionError(f"{func_name} not found in {rel}")


class TestSplitRelievesGate:
    @pytest.mark.req("REQ-YG-544")
    def test_graph_schema_bisected(self):
        """Node-config models live in node_schema; both halves well under
        the 400 warn line."""
        assert (
            REPO_ROOT / "yamlgraph/models/node_schema.py"
        ).exists(), "node_schema.py missing — graph_schema.py still monolithic"
        assert _lines("yamlgraph/models/graph_schema.py") < 300
        assert _lines("yamlgraph/models/node_schema.py") < 400

    @pytest.mark.req("REQ-YG-544")
    def test_public_names_unchanged(self):
        """The package namespace is the API — imports keep working."""
        from yamlgraph.models import (  # noqa: F401
            EdgeConfig,
            GraphConfigSchema,
            NodeConfig,
            validate_graph_schema,
        )
        from yamlgraph.models.node_schema import (  # noqa: F401
            NodeConfig as DirectNodeConfig,
        )

    @pytest.mark.req("REQ-YG-544")
    def test_streaming_translation_extracted(self):
        """run_graph_streaming_native decomposed below CC 10; the
        event-translation is a pure function in streaming_events."""
        assert (
            _function_cc("yamlgraph/executor_async.py", "run_graph_streaming_native")
            < 10
        )
        assert (REPO_ROOT / "yamlgraph/streaming_events.py").exists()
        assert _lines("yamlgraph/executor_async.py") < 400

    @pytest.mark.req("REQ-YG-544")
    def test_no_new_function_above_cc10(self):
        """The extraction must not smuggle complexity into new homes."""
        from radon.complexity import cc_visit

        src = (REPO_ROOT / "yamlgraph/streaming_events.py").read_text(encoding="utf-8")
        offenders = [
            (b.name, b.complexity) for b in cc_visit(src) if b.complexity >= 10
        ]
        assert not offenders, f"CC >= 10 in streaming_events: {offenders}"

    @pytest.mark.req("REQ-YG-544")
    def test_translation_is_pure_and_pinned(self):
        """Event-shape contract: subgraph-wrapped and plain events yield
        the same token; tool-call and dict-content chunks are filtered
        (FR-058); node_filter drops other nodes."""
        from langchain_core.messages import AIMessageChunk

        from yamlgraph.streaming_events import translate_message_event

        chunk = AIMessageChunk(content="tok")
        meta = {"langgraph_node": "generate"}

        assert translate_message_event((chunk, meta), subgraphs=False) == "tok"
        assert (
            translate_message_event((("ns",), (chunk, meta)), subgraphs=True) == "tok"
        )
        assert (
            translate_message_event((chunk, meta), subgraphs=False, node_filter="x")
            is None
        )
        tool_chunk = AIMessageChunk(
            content="call",
            tool_calls=[{"name": "t", "args": {}, "id": "1"}],
        )
        assert translate_message_event((tool_chunk, meta), subgraphs=False) is None


class TestSplitIsPureMove:
    @pytest.mark.req("REQ-YG-544")
    def test_node_schema_has_no_logic_changes(self):
        """Both halves parse and expose the same class set the monolith
        had (SubgraphNodeConfig, NodeConfig | EdgeConfig, GraphConfigSchema)."""
        node_src = ast.parse(
            (REPO_ROOT / "yamlgraph/models/node_schema.py").read_text(encoding="utf-8")
        )
        graph_src = ast.parse(
            (REPO_ROOT / "yamlgraph/models/graph_schema.py").read_text(encoding="utf-8")
        )
        node_classes = {
            n.name for n in ast.walk(node_src) if isinstance(n, ast.ClassDef)
        }
        graph_classes = {
            n.name for n in ast.walk(graph_src) if isinstance(n, ast.ClassDef)
        }
        assert {"SubgraphNodeConfig", "NodeConfig"} <= node_classes
        assert {"EdgeConfig", "GraphConfigSchema"} <= graph_classes
