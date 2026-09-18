"""FR-1050: a ``loop_limits`` entry binds or compilation fails.

Two seams:

* **Runtime (D-2)** — a standalone ``race`` node checks its limit before
  incrementing and before firing any candidate, the ``llm`` contract of
  ``llm_nodes._run_node``. A router *with* candidates is NOT touched: its
  caller already checks and increments, so the regression test here proves
  the Nth permitted execution still fires (judgement R-2).
* **Compile (D-1)** — every graph-level ``loop_limits`` entry is validated
  against the raw authored node map, before ``interactive_tool`` and
  ``pipeline`` expansion erase their source nodes.
"""

from __future__ import annotations

import textwrap
from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config
from yamlgraph.compile.loop_limits import (
    LOOP_LIMIT_SUPPORTED_TYPES,
    LOOP_LIMIT_UNSUPPORTED_TYPES,
)
from yamlgraph.compile.node_compiler import GraphConfigError
from yamlgraph.constants import NodeType

REQ = "REQ-YG-683"

RACE_CONFIG = {
    "type": "race",
    "prompt": "irrelevant",
    "state_key": "response",
    "parse_json": True,
    "candidates": [
        {"provider": "anthropic", "model": "m1"},
        {"provider": "openai", "model": "m2"},
    ],
}


def _write_graph(tmp_path, body: str):
    path = tmp_path / "graph.yaml"
    path.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    return path


# --- D-2: standalone race enforces (AC-01, AC-02) ----------------------------


class TestStandaloneRaceEnforces:
    @pytest.mark.req(REQ)
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_at_limit_fires_no_candidate(self, mock_prepare, mock_create_llm):
        """AC-01/AC-02: exhaustion returns the flag and fires nothing."""
        from yamlgraph.node_factory.race_node import create_race_node

        node_fn = create_race_node("spin", {**RACE_CONFIG, "loop_limit": 2}, {})
        state = {"_loop_counts": {"spin": 2}}

        result = node_fn(state)

        assert result == {"_loop_limit_reached": True, "current_step": "spin"}
        assert "_loop_counts" not in result
        mock_prepare.assert_not_called()
        mock_create_llm.assert_not_called()

    @pytest.mark.req(REQ)
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_below_limit_still_races(self, mock_prepare, mock_create_llm):
        """The Nth permitted execution still fires (no off-by-one)."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_create_llm.side_effect = [_mock_llm("winner"), _mock_llm("loser")]

        node_fn = create_race_node("spin", {**RACE_CONFIG, "loop_limit": 2}, {})
        result = node_fn({"_loop_counts": {"spin": 1}})

        assert result["_loop_counts"]["spin"] == 2
        assert "_loop_limit_reached" not in result
        assert mock_create_llm.called


def _mock_llm(text: str):
    """Candidate that resolves immediately with ``text``."""
    mock = MagicMock()

    async def ainvoke(messages, config=None):
        result = MagicMock()
        result.content = text
        return result

    mock.ainvoke = ainvoke
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


# --- D-2 boundary: router with candidates is unchanged (AC-03) ---------------


class TestRouterWithCandidatesUnchanged:
    """R-2: the outer llm/router check already guards this path."""

    ROUTER_CONFIG = {
        "type": "router",
        "prompt": "irrelevant",
        "state_key": "decision",
        "parse_json": True,
        "routes": {"go": "next"},
        "default_route": "next",
        "candidates": [{"provider": "anthropic", "model": "m1"}],
    }

    @pytest.mark.req(REQ)
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    def test_router_race_at_limit_fires_no_candidate(self, mock_prepare, mock_llm):
        from yamlgraph.node_factory.llm_nodes import create_node_function

        node_fn = create_node_function(
            "decide", {**self.ROUTER_CONFIG, "loop_limit": 3}, {}
        )
        result = node_fn({"_loop_counts": {"decide": 3}})

        assert result == {"_loop_limit_reached": True, "current_step": "decide"}
        assert "_loop_counts" not in result
        mock_prepare.assert_not_called()
        mock_llm.assert_not_called()

    @pytest.mark.req(REQ)
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    def test_router_race_nth_permitted_execution_still_fires(
        self, mock_prepare, mock_llm
    ):
        """A second check inside _execute_router_race would suppress this."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_llm.return_value = _mock_llm("go")

        node_fn = create_node_function(
            "decide", {**self.ROUTER_CONFIG, "loop_limit": 3}, {}
        )
        result = node_fn({"_loop_counts": {"decide": 2}})

        assert result["_loop_counts"]["decide"] == 3
        assert "_loop_limit_reached" not in result
        assert mock_llm.called

    @pytest.mark.req(REQ)
    def test_router_race_node_has_no_loop_limit_check(self):
        """R-2 is a source-level contract: the check lives in the caller."""
        import inspect

        from yamlgraph.node_factory import router_race_node

        assert "check_loop_limit" not in inspect.getsource(router_race_node)


# --- D-1: compile-time validation before expansion (AC-04, AC-05) ------------


class TestCompileTimeValidation:
    @pytest.mark.req(REQ)
    def test_dangling_key_raises(self, tmp_path):
        path = _write_graph(
            tmp_path,
            """
            version: "1.0"
            name: dangling
            nodes:
              real:
                type: passthrough
                output:
                  seen: "yes"
            edges:
              - from: START
                to: real
              - from: real
                to: END
            loop_limits:
              ghost: 3
            """,
        )
        with pytest.raises(GraphConfigError, match="ghost"):
            load_graph_config(path)

    @pytest.mark.req(REQ)
    def test_unsupported_type_names_node_type_and_supported_set(self, tmp_path):
        path = _write_graph(
            tmp_path,
            """
            version: "1.0"
            name: unsupported
            nodes:
              ask:
                type: interrupt
                message: "hi"
                resume_key: answer
            edges:
              - from: START
                to: ask
              - from: ask
                to: END
            loop_limits:
              ask: 3
            """,
        )
        with pytest.raises(GraphConfigError) as exc:
            load_graph_config(path)
        message = str(exc.value)
        assert "ask" in message
        assert "interrupt" in message
        assert "passthrough" in message and "race" in message

    @pytest.mark.req(REQ)
    @pytest.mark.parametrize("node_type", sorted(LOOP_LIMIT_UNSUPPORTED_TYPES))
    def test_every_unsupported_type_is_rejected(self, tmp_path, node_type):
        """AC-05: including the expansion-only macros."""
        path = _write_graph(
            tmp_path,
            f"""
            version: "1.0"
            name: reject-{node_type}
            nodes:
              target:
                type: {node_type}
            edges:
              - from: START
                to: target
              - from: target
                to: END
            loop_limits:
              target: 2
            """,
        )
        with pytest.raises(GraphConfigError, match="target"):
            load_graph_config(path)

    @pytest.mark.req(REQ)
    def test_macro_node_is_rejected_before_expansion_erases_it(self, tmp_path):
        """interactive_tool is gone by the time compile_node runs."""
        path = _write_graph(
            tmp_path,
            """
            version: "1.0"
            name: macro
            tools:
              probe:
                command: "echo hi"
            nodes:
              chat:
                type: interactive_tool
                tool: probe
                max_iterations: 4
            edges:
              - from: START
                to: chat
              - from: chat
                to: END
            loop_limits:
              chat: 2
            """,
        )
        with pytest.raises(GraphConfigError, match="interactive_tool"):
            load_graph_config(path)

    @pytest.mark.req(REQ)
    def test_cycle_bounded_only_by_unsupported_entry_fails_compilation(self, tmp_path):
        """AC-09: W012 can no longer report such a graph clean."""
        path = _write_graph(
            tmp_path,
            """
            version: "1.0"
            name: inert-cycle
            nodes:
              ask:
                type: interrupt
                message: "hi"
                resume_key: answer
              echo:
                type: passthrough
                output:
                  seen: "yes"
            edges:
              - from: START
                to: ask
              - from: ask
                to: echo
              - from: echo
                to: ask
            loop_limits:
              ask: 5
            """,
        )
        with pytest.raises(GraphConfigError):
            load_graph_config(path)


# --- D-1: the classification cannot drift (AC-06) ----------------------------


class TestClassificationCannotDrift:
    @pytest.mark.req(REQ)
    def test_classifications_are_disjoint(self):
        assert not (LOOP_LIMIT_SUPPORTED_TYPES & LOOP_LIMIT_UNSUPPORTED_TYPES)

    @pytest.mark.req(REQ)
    def test_classifications_cover_every_node_type(self):
        """A new NodeType must be classified before it can be shipped."""
        classified = LOOP_LIMIT_SUPPORTED_TYPES | LOOP_LIMIT_UNSUPPORTED_TYPES
        assert classified == {str(t) for t in NodeType}


# --- D-3: every supported type enforces behaviorally (AC-07) -----------------


def _python_work(state):
    _python_work.calls += 1
    return "done"


_python_work.calls = 0


@contextmanager
def _supported_node(node_type: str, loop_limit: int):
    """Yield ``(node_fn, work_probe)`` with the type's work seam patched."""
    from yamlgraph.node_factory.control_nodes import create_passthrough_node
    from yamlgraph.node_factory.llm_nodes import create_node_function
    from yamlgraph.node_factory.race_node import create_race_node
    from yamlgraph.tools.nodes import create_tool_node
    from yamlgraph.tools.python_tool import PythonToolConfig, create_python_node
    from yamlgraph.tools.shell import ShellToolConfig

    with ExitStack() as stack:
        if node_type in (NodeType.LLM, NodeType.ROUTER):
            probe = stack.enter_context(
                patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
            )
            config = {
                "type": node_type,
                "prompt": "irrelevant",
                "state_key": "out",
                "parse_json": True,
                "loop_limit": loop_limit,
            }
            if node_type == NodeType.ROUTER:
                config |= {"routes": {"go": "next"}, "default_route": "next"}
            yield create_node_function("n", config, {}), probe
        elif node_type == NodeType.RACE:
            stack.enter_context(
                patch("yamlgraph.node_factory.race_node.prepare_messages")
            )
            probe = stack.enter_context(
                patch("yamlgraph.node_factory.race_node.create_llm")
            )
            yield (
                create_race_node("n", {**RACE_CONFIG, "loop_limit": loop_limit}, {}),
                probe,
            )
        elif node_type == NodeType.PYTHON:
            _python_work.calls = 0
            tools = {
                "work": PythonToolConfig(
                    function="_python_work",
                    module="tests.unit.test_fr1050_loop_limits_bind_or_fail",
                )
            }
            node_fn = create_python_node(
                "n", {"tool": "work", "loop_limit": loop_limit}, tools
            )
            yield node_fn, _python_work
        elif node_type == NodeType.TOOL:
            probe = stack.enter_context(
                patch("yamlgraph.tools.nodes.execute_shell_tool")
            )
            tools = {"work": ShellToolConfig(command="echo hi")}
            node_fn = create_tool_node(
                "n", {"tool": "work", "loop_limit": loop_limit}, tools
            )
            yield node_fn, probe
        elif node_type == NodeType.PASSTHROUGH:
            probe = stack.enter_context(
                patch("yamlgraph.utils.expressions.resolve_template")
            )
            node_fn = create_passthrough_node(
                "n", {"output": {"seen": "yes"}, "loop_limit": loop_limit}
            )
            yield node_fn, probe
        else:  # pragma: no cover - guarded by AC-07's coverage assertion
            raise AssertionError(f"no builder for supported type {node_type!r}")


_SUPPORTED_NODE_BODIES = {
    NodeType.LLM: "    type: llm\n    prompt: irrelevant\n    state_key: out",
    NodeType.ROUTER: (
        "    type: router\n    prompt: irrelevant\n    state_key: out\n"
        "    route_field: out\n"
        "    routes:\n      go: END\n    default_route: END"
    ),
    NodeType.RACE: (
        "    type: race\n    prompt: irrelevant\n    state_key: out\n"
        "    parse_json: true\n    candidates:\n"
        "      - provider: anthropic\n        model: m1\n"
        "      - provider: openai\n        model: m2"
    ),
    NodeType.PYTHON: "    type: python\n    tool: work\n    state_key: out",
    NodeType.TOOL: "    type: tool\n    tool: probe\n    state_key: out",
    NodeType.PASSTHROUGH: '    type: passthrough\n    output:\n      out: "hi"',
}


def _supported_graph_yaml(node_type: str) -> str:
    """Minimal single-node graph of ``node_type`` carrying a loop limit."""
    return (
        'version: "1.0"\n'
        f"name: accept-{node_type}\n"
        "state:\n  out: str\n"
        "tools:\n"
        '  probe:\n    command: "echo hi"\n'
        "  work:\n    type: python\n"
        "    module: tests.unit.test_fr1050_loop_limits_bind_or_fail\n"
        "    function: _python_work\n"
        "nodes:\n  target:\n"
        f"{_SUPPORTED_NODE_BODIES[node_type]}\n"
        "edges:\n  - from: START\n    to: target\n"
        "  - from: target\n    to: END\n"
        "loop_limits:\n  target: 2\n"
    )


class TestEverySupportedTypeEnforces:
    @pytest.mark.req(REQ)
    @pytest.mark.parametrize("node_type", sorted(LOOP_LIMIT_SUPPORTED_TYPES))
    def test_supported_type_stops_at_limit(self, node_type):
        """AC-07: flag set, counter unchanged, zero work calls."""
        with _supported_node(node_type, loop_limit=2) as (node_fn, probe):
            state = {"_loop_counts": {"n": 2}}
            result = node_fn(state)

            assert result == {"_loop_limit_reached": True, "current_step": "n"}
            assert "_loop_counts" not in result
            assert state["_loop_counts"] == {"n": 2}
            calls = probe.calls if probe is _python_work else probe.call_count
            assert calls == 0

    @pytest.mark.req(REQ)
    @pytest.mark.parametrize("node_type", sorted(LOOP_LIMIT_SUPPORTED_TYPES))
    def test_supported_type_compiles_with_a_loop_limit(self, tmp_path, node_type):
        path = tmp_path / "graph.yaml"
        path.write_text(_supported_graph_yaml(node_type), encoding="utf-8")

        assert load_graph_config(path).loop_limits == {"target": 2}


# --- D-3: exhausted race reaches its loop_exits target (AC-08) ---------------


class TestLoopExitsSeamUnchanged:
    @pytest.mark.req(REQ)
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_exhausted_race_routes_to_loop_exit_target(
        self, mock_prepare, mock_llm, tmp_path
    ):
        path = _write_graph(
            tmp_path,
            """
            version: "1.0"
            name: race-loop-exit
            state:
              response: str
              landed: str
            nodes:
              spin:
                type: race
                prompt: irrelevant
                state_key: response
                parse_json: true
                candidates:
                  - provider: anthropic
                    model: m1
                  - provider: openai
                    model: m2
              landing:
                type: passthrough
                output:
                  landed: "yes"
            edges:
              - from: START
                to: spin
              - from: spin
                to: spin
                condition: response == null
              - from: spin
                to: landing
                condition: response != null
              - from: landing
                to: END
            loop_limits:
              spin: 1
            loop_exits:
              spin: landing
            """,
        )
        graph = compile_graph(load_graph_config(path)).compile()

        final = graph.invoke({"_loop_counts": {"spin": 1}})

        assert final["_loop_limit_reached"] is True
        assert final["landed"] == "yes"
        mock_llm.assert_not_called()
