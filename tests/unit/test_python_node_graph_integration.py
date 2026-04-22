"""Integration tests: Python tool nodes inside compiled graphs.

Validates that Python nodes (type: python) returning dicts or scalars
integrate correctly with LangGraph state, and that downstream nodes
can resolve state expressions produced by python node output.

Tests use small programmatically-built graphs — no YAML fixtures needed.

Covers:
- Dict-returning python nodes merge keys to top-level state
- Scalar-returning python nodes wrap value under state_key
- Downstream variable resolution for python-produced state keys
- Worktree-like pattern: python dict → downstream copilot/passthrough variables
"""

from typing import Annotated, Any

import pytest
from langgraph.graph import StateGraph

from yamlgraph.models.state_builder import last_value
from yamlgraph.tools.python_tool import PythonToolConfig, create_python_node

# ============================================================================
# Helper functions used as python tool targets
# ============================================================================


def returns_dict(state: dict) -> dict:
    """Simulate worktree-like tool: returns dict with multiple keys."""
    return {
        "worktree_dir": f"tmp/worktrees/{state.get('branch_name', 'default')}",
        "branch": f"feat/{state.get('branch_name', 'default')}",
    }


def returns_scalar(state: dict) -> int:
    """Return a scalar value (should be wrapped under state_key)."""
    return len(state.get("input", ""))


def returns_dict_with_metadata(state: dict) -> dict:
    """Return dict that includes keys matching metadata fields."""
    return {
        "result": "processed",
        "extra": state.get("input", ""),
    }


# ============================================================================
# State class builders
# ============================================================================


def _build_state(fields: dict[str, type]) -> type:
    """Build a TypedDict with last_value reducers for all fields."""
    annotated_fields = {}
    for name, typ in fields.items():
        annotated_fields[name] = Annotated[typ, last_value]

    # current_step and _loop_counts are always needed by python nodes
    annotated_fields["current_step"] = Annotated[str, last_value]
    annotated_fields["_loop_counts"] = Annotated[dict, last_value]

    from typing import TypedDict

    return TypedDict("TestState", annotated_fields, total=False)  # type: ignore[call-overload]


def _make_python_node(name: str, func, state_key: str = "output", variables=None):
    """Create a python node from an inline function."""
    tools = {
        f"{name}_tool": PythonToolConfig(
            module=__name__,
            function=func.__name__,
        )
    }
    config = {"tool": f"{name}_tool", "state_key": state_key}
    if variables:
        config["variables"] = variables
    return create_python_node(name, config, tools)


def _passthrough_with_read(key_to_read: str):
    """Create a passthrough-like node that reads a state key and copies it."""

    def node_fn(state: dict[str, Any]) -> dict:
        value = state.get(key_to_read)
        return {
            "captured": str(value) if value is not None else "MISSING",
            "current_step": "reader",
        }

    node_fn.__name__ = "reader_node"
    return node_fn


# ============================================================================
# Tests
# ============================================================================


@pytest.mark.req("REQ-YG-020")
class TestPythonNodeDictReturnInGraph:
    """Dict-returning python nodes merge keys to top-level state."""

    def test_dict_keys_accessible_at_top_level(self):
        """When python tool returns dict, keys become top-level state fields."""
        State = _build_state({"branch_name": str, "worktree_dir": str, "branch": str})
        graph = StateGraph(State)

        node_fn = _make_python_node("create_wt", returns_dict)
        graph.add_node("create_wt", node_fn)
        graph.set_entry_point("create_wt")
        graph.set_finish_point("create_wt")

        compiled = graph.compile()
        result = compiled.invoke({"branch_name": "test-feature"})

        assert result["worktree_dir"] == "tmp/worktrees/test-feature"
        assert result["branch"] == "feat/test-feature"

    def test_dict_return_includes_node_metadata(self):
        """Dict return also includes current_step and _loop_counts."""
        State = _build_state({"branch_name": str, "worktree_dir": str, "branch": str})
        graph = StateGraph(State)

        node_fn = _make_python_node("create_wt", returns_dict)
        graph.add_node("create_wt", node_fn)
        graph.set_entry_point("create_wt")
        graph.set_finish_point("create_wt")

        compiled = graph.compile()
        result = compiled.invoke({"branch_name": "test"})

        assert result["current_step"] == "create_wt"
        assert result["_loop_counts"]["create_wt"] == 1


@pytest.mark.req("REQ-YG-020")
class TestPythonNodeScalarReturnInGraph:
    """Scalar-returning python nodes wrap value under state_key."""

    def test_scalar_stored_under_state_key(self):
        """Non-dict return is wrapped as {state_key: value}."""
        State = _build_state({"input": str, "length": int})
        graph = StateGraph(State)

        node_fn = _make_python_node("measure", returns_scalar, state_key="length")
        graph.add_node("measure", node_fn)
        graph.set_entry_point("measure")
        graph.set_finish_point("measure")

        compiled = graph.compile()
        result = compiled.invoke({"input": "hello world"})

        assert result["length"] == 11
        assert result["current_step"] == "measure"


@pytest.mark.req("REQ-YG-106")
class TestWorktreePatternGraph:
    """Replicate chaplain worktree → downstream variable resolution pattern.

    The graph has two nodes:
    1. create_worktree (python, returns dict with worktree_dir + branch)
    2. reader (reads state.worktree_dir to verify it resolved)

    This is the exact pattern that was broken by {state.worktree_result.*}
    and fixed by referencing {state.worktree_dir} directly.
    """

    def test_downstream_reads_python_dict_output(self):
        """Downstream node can read keys produced by dict-returning python node."""
        State = _build_state(
            {
                "branch_name": str,
                "worktree_dir": str,
                "branch": str,
                "captured": str,
            }
        )
        graph = StateGraph(State)

        # Node 1: python tool returning dict
        wt_node = _make_python_node("create_wt", returns_dict)
        graph.add_node("create_wt", wt_node)

        # Node 2: reads worktree_dir from state
        reader = _passthrough_with_read("worktree_dir")
        graph.add_node("reader", reader)

        graph.add_edge("create_wt", "reader")
        graph.set_entry_point("create_wt")
        graph.set_finish_point("reader")

        compiled = graph.compile()
        result = compiled.invoke({"branch_name": "fr-153"})

        assert result["worktree_dir"] == "tmp/worktrees/fr-153"
        assert result["captured"] == "tmp/worktrees/fr-153"

    def test_downstream_reads_branch_key(self):
        """Branch key from dict return is also accessible downstream."""
        State = _build_state(
            {
                "branch_name": str,
                "worktree_dir": str,
                "branch": str,
                "captured": str,
            }
        )
        graph = StateGraph(State)

        wt_node = _make_python_node("create_wt", returns_dict)
        graph.add_node("create_wt", wt_node)

        reader = _passthrough_with_read("branch")
        graph.add_node("reader", reader)

        graph.add_edge("create_wt", "reader")
        graph.set_entry_point("create_wt")
        graph.set_finish_point("reader")

        compiled = graph.compile()
        result = compiled.invoke({"branch_name": "fr-153"})

        assert result["branch"] == "feat/fr-153"
        assert result["captured"] == "feat/fr-153"

    def test_state_key_ignored_for_dict_return(self):
        """state_key on a dict-returning python node is decorative — keys go top-level.

        This documents the current behavior that GH issue #153 aims to fix.
        When #153 is implemented, dict returns will be wrapped under state_key.
        """
        State = _build_state(
            {
                "branch_name": str,
                "worktree_dir": str,
                "branch": str,
                "wt_result": dict,
            }
        )
        graph = StateGraph(State)

        # state_key="wt_result" but returns_dict returns a plain dict
        wt_node = _make_python_node("create_wt", returns_dict, state_key="wt_result")
        graph.add_node("create_wt", wt_node)
        graph.set_entry_point("create_wt")
        graph.set_finish_point("create_wt")

        compiled = graph.compile()
        result = compiled.invoke({"branch_name": "test"})

        # Current behavior: dict keys merge at top level, state_key is ignored
        assert result["worktree_dir"] == "tmp/worktrees/test"
        assert result["branch"] == "feat/test"
        # wt_result is NOT populated by the node — state default is empty dict
        assert result.get("wt_result") == {}


@pytest.mark.req("REQ-YG-020")
class TestPythonNodeVariableResolution:
    """Variable expressions resolve correctly with python node output."""

    def test_variables_inject_state_into_effective_state(self):
        """Node variables resolve {state.X} and inject into effective_state."""
        tools = {
            "echo_tool": PythonToolConfig(
                module=__name__,
                function="returns_dict_with_metadata",
            )
        }
        config = {
            "tool": "echo_tool",
            "state_key": "output",
            "variables": {"input": "{state.raw_input}"},
        }
        node_fn = create_python_node("echo", config, tools)

        result = node_fn({"raw_input": "hello"})

        assert result["result"] == "processed"
        assert result["extra"] == "hello"

    def test_chained_variable_resolution(self):
        """Two-node graph: first node produces state, second resolves it."""
        State = _build_state(
            {
                "branch_name": str,
                "worktree_dir": str,
                "branch": str,
                "summary": str,
            }
        )
        graph = StateGraph(State)

        # Node 1: produces worktree_dir and branch
        wt_node = _make_python_node("create_wt", returns_dict)
        graph.add_node("create_wt", wt_node)

        # Node 2: uses a variable that references node 1's output
        def format_summary(state: dict) -> dict:
            wt = state.get("worktree_dir", "?")
            br = state.get("branch", "?")
            return {"summary": f"Worktree at {wt} on branch {br}"}

        tools2 = {
            "format_tool": PythonToolConfig(
                module=__name__,
                function="format_summary",
            )
        }
        # Inject this function into module scope for load_python_function
        import sys

        sys.modules[__name__].format_summary = format_summary

        config2 = {
            "tool": "format_tool",
            "state_key": "summary",
            "variables": {
                "worktree_dir": "{state.worktree_dir}",
                "branch": "{state.branch}",
            },
        }
        fmt_node = create_python_node("format", config2, tools2)
        graph.add_node("format", fmt_node)

        graph.add_edge("create_wt", "format")
        graph.set_entry_point("create_wt")
        graph.set_finish_point("format")

        compiled = graph.compile()
        result = compiled.invoke({"branch_name": "fr-200"})

        assert "tmp/worktrees/fr-200" in result["summary"]
        assert "feat/fr-200" in result["summary"]
