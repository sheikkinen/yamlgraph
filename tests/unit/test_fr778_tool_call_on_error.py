"""Tests for tool_call on_error: fail — prerequisite failures fail the graph.

FR-778 (judged): `on_error: fail` raises at the tool_call node with the
tool's actual error; default/`skip` keeps the byte-identical failure
envelope; graph load rejects values outside skip/fail for tool_call.

RED contract: create_tool_call_node ignores on_error today, and
validate_config accepts any ErrorHandler value on tool_call nodes.
"""

import pytest
import yaml

from yamlgraph.node_factory.tool_nodes import create_tool_call_node
from yamlgraph.utils.validators import validate_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def boom(**kwargs):
    raise RuntimeError("pdfinfo not found: install poppler")


def ok(**kwargs):
    return {"chunks": ["c1"]}


REGISTRY = {"split_document": ok, "broken_tool": boom}


def make_node(on_error=None, tool="broken_tool"):
    config = {"tool": tool, "args": {}, "state_key": "split_result"}
    if on_error is not None:
        config["on_error"] = on_error
    return create_tool_call_node("split", config, REGISTRY)


def graph_config(on_error):
    return yaml.safe_load(f"""
version: "1.0"
name: fixture
state:
  x: str
nodes:
  split:
    type: tool_call
    tool: split_document
    args: {{}}
    on_error: {on_error}
    state_key: split_result
edges:
  - from: START
    to: split
  - from: split
    to: END
""")


# ---------------------------------------------------------------------------
# AC-01: fail raises at the node for callable exceptions, chained
# ---------------------------------------------------------------------------


class TestFailOnException:
    @pytest.mark.req("REQ-YG-580")
    def test_fail_raises_with_node_tool_and_original_message(self):
        node = make_node(on_error="fail")
        with pytest.raises(ValueError) as exc:
            node({})
        message = str(exc.value)
        assert "split" in message
        assert "broken_tool" in message
        assert "pdfinfo not found" in message

    @pytest.mark.req("REQ-YG-580")
    def test_fail_preserves_exception_chain(self):
        node = make_node(on_error="fail")
        with pytest.raises(ValueError) as exc:
            node({})
        assert isinstance(exc.value.__cause__, RuntimeError)


# ---------------------------------------------------------------------------
# AC-02: fail raises for unknown tool
# ---------------------------------------------------------------------------


class TestFailOnUnknownTool:
    @pytest.mark.req("REQ-YG-580")
    def test_fail_raises_naming_unknown_tool(self):
        node = make_node(on_error="fail", tool="no_such_tool")
        with pytest.raises(ValueError) as exc:
            node({})
        message = str(exc.value)
        assert "split" in message
        assert "no_such_tool" in message
        assert "Unknown tool" in message


# ---------------------------------------------------------------------------
# AC-03: default and skip keep the byte-identical envelope
# ---------------------------------------------------------------------------


class TestEnvelopeDefaultPreserved:
    EXPECTED_EXC = {
        "split_result": {
            "task_id": None,
            "tool": "broken_tool",
            "success": False,
            "result": None,
            "error": "pdfinfo not found: install poppler",
        },
        "current_step": "split",
    }
    EXPECTED_UNKNOWN = {
        "split_result": {
            "task_id": None,
            "tool": "no_such_tool",
            "success": False,
            "result": None,
            "error": "Unknown tool: no_such_tool",
        },
        "current_step": "split",
    }

    @pytest.mark.req("REQ-YG-580")
    def test_default_envelope_for_exception(self):
        assert make_node()({}) == self.EXPECTED_EXC

    @pytest.mark.req("REQ-YG-580")
    def test_skip_envelope_for_exception(self):
        assert make_node(on_error="skip")({}) == self.EXPECTED_EXC

    @pytest.mark.req("REQ-YG-580")
    def test_default_envelope_for_unknown_tool(self):
        assert make_node(tool="no_such_tool")({}) == self.EXPECTED_UNKNOWN

    @pytest.mark.req("REQ-YG-580")
    def test_skip_envelope_for_unknown_tool(self):
        node = make_node(on_error="skip", tool="no_such_tool")
        assert node({}) == self.EXPECTED_UNKNOWN

    @pytest.mark.req("REQ-YG-580")
    def test_fail_success_path_envelope_unchanged(self):
        node = make_node(on_error="fail", tool="split_document")
        result = node({})
        assert result["split_result"]["success"] is True
        assert result["split_result"]["result"] == {"chunks": ["c1"]}


# ---------------------------------------------------------------------------
# AC-04: graph load rejects on_error outside skip/fail for tool_call
# ---------------------------------------------------------------------------


class TestLoadTimeValidation:
    @pytest.mark.req("REQ-YG-580")
    @pytest.mark.parametrize("bad", ["retry", "fallback", "explode"])
    def test_rejects_unsupported_values_naming_valid_set(self, bad):
        with pytest.raises(ValueError) as exc:
            validate_config(graph_config(bad))
        message = str(exc.value)
        assert "split" in message
        assert "skip, fail" in message

    @pytest.mark.req("REQ-YG-580")
    @pytest.mark.parametrize("good", ["skip", "fail"])
    def test_accepts_skip_and_fail(self, good):
        validate_config(graph_config(good))  # must not raise


# ---------------------------------------------------------------------------
# AC-05: regression — witnessed shape vs fail-at-source
# ---------------------------------------------------------------------------


class TestWitnessedRegression:
    """book1.pdf incident: failed envelope + downstream template = misleading."""

    @pytest.mark.req("REQ-YG-580")
    def test_skip_envelope_hides_prerequisite_from_downstream(self):
        from yamlgraph.utils.expressions import resolve_template

        state = make_node()({})  # default: envelope, graph continues
        assert state["split_result"]["success"] is False
        # Downstream map resolves chunks from the failed envelope: whatever
        # it sees is unusable and carries no trace of the prerequisite
        # message — the misleading-distance failure witnessed with book1.pdf.
        resolved = resolve_template("{state.split_result.result.chunks}", state)
        assert not isinstance(resolved, list)
        assert "pdfinfo" not in str(resolved)

    @pytest.mark.req("REQ-YG-580")
    def test_fail_names_prerequisite_at_source(self):
        node = make_node(on_error="fail")
        with pytest.raises(ValueError, match="pdfinfo not found"):
            node({})
