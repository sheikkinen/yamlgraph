"""FR-677 Move 2: graph-level ``verify:`` block terminal node.

A graph may declare a top-level ``verify:`` list of deterministic rules. They
are compiled into a single terminal ``__verify__`` node evaluated once against
final state before END. ``on_fail: halt`` raises; ``on_fail: warn`` records a
PipelineError and continues. ``retry`` is not a legal graph-level action, and a
malformed block fails at the loader boundary.
"""

import textwrap

import pytest
from pydantic import ValidationError

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config
from yamlgraph.compile.verify_insert import VERIFY_NODE_NAME, insert_verify_node
from yamlgraph.models.graph_schema import GraphConfigSchema
from yamlgraph.models.guard_schema import GraphVerifyRule
from yamlgraph.utils.guard_runtime import GuardHaltError, create_verify_node


# --- module-level python tool for the end-to-end graph -----------------------
def _emit(state):
    return state.get("seed", 0)


def _write_graph(tmp_path, on_fail, check="state.result >= 100"):
    """Write a minimal python-node graph carrying a graph-level verify block."""
    graph_yaml = textwrap.dedent(
        f"""
        version: "1.0"
        name: verify-e2e
        state:
          seed: int
          result: int
        tools:
          emit:
            type: python
            module: tests.unit.test_fr677_graph_verify
            function: _emit
        nodes:
          n1:
            type: python
            tool: emit
            state_key: result
        edges:
          - from: START
            to: n1
          - from: n1
            to: END
        verify:
          - check: "{check}"
            on_fail: {on_fail}
            message: "result too small: needs >= 100"
        """
    ).strip()
    path = tmp_path / "graph.yaml"
    path.write_text(graph_yaml, encoding="utf-8")
    return path


# --- Move 2a: config-level insert transform ----------------------------------
class TestVerifyInsertTransform:
    """insert_verify_node redirects explicit END destinations through verify."""

    @pytest.mark.req("REQ-YG-511")
    def test_no_verify_block_is_noop(self):
        config = {
            "nodes": {"a": {"type": "llm"}},
            "edges": [{"from": "a", "to": "END"}],
        }
        result = insert_verify_node(config)
        assert VERIFY_NODE_NAME not in result["nodes"]
        assert result["edges"] == [{"from": "a", "to": "END"}]

    @pytest.mark.req("REQ-YG-511")
    def test_scalar_end_edge_redirected_and_terminal_appended(self):
        config = {
            "nodes": {"a": {"type": "llm"}},
            "edges": [{"from": "START", "to": "a"}, {"from": "a", "to": "END"}],
            "verify": [{"check": "output", "on_fail": "halt"}],
        }
        result = insert_verify_node(config)
        assert result["nodes"][VERIFY_NODE_NAME] == {"type": "verify"}
        assert {"from": "a", "to": VERIFY_NODE_NAME} in result["edges"]
        assert {"from": VERIFY_NODE_NAME, "to": "END"} in result["edges"]
        # The original END-directed edge no longer targets END directly.
        assert {"from": "a", "to": "END"} not in result["edges"]

    @pytest.mark.req("REQ-YG-511")
    def test_list_end_targets_redirected(self):
        config = {
            "nodes": {"a": {"type": "router"}},
            "edges": [{"from": "a", "to": ["b", "END"], "type": "conditional"}],
            "verify": [{"check": "output", "on_fail": "warn"}],
        }
        result = insert_verify_node(config)
        edge = next(e for e in result["edges"] if e["from"] == "a")
        assert edge["to"] == ["b", VERIFY_NODE_NAME]

    @pytest.mark.req("REQ-YG-511")
    def test_router_routes_and_default_route_redirected(self):
        config = {
            "nodes": {
                "a": {
                    "type": "router",
                    "routes": {"done": "END", "again": "a"},
                    "default_route": "END",
                }
            },
            "edges": [{"from": "a", "to": ["a", "END"], "type": "conditional"}],
            "verify": [{"check": "output", "on_fail": "halt"}],
        }
        result = insert_verify_node(config)
        node = result["nodes"]["a"]
        assert node["routes"] == {"done": VERIFY_NODE_NAME, "again": "a"}
        assert node["default_route"] == VERIFY_NODE_NAME

    @pytest.mark.req("REQ-YG-511")
    def test_loop_exits_redirected(self):
        config = {
            "nodes": {"a": {"type": "llm"}},
            "edges": [{"from": "a", "to": "a", "condition": "x < 1"}],
            "loop_exits": {"a": "END"},
            "verify": [{"check": "output", "on_fail": "halt"}],
        }
        result = insert_verify_node(config)
        assert result["loop_exits"]["a"] == VERIFY_NODE_NAME

    @pytest.mark.req("REQ-YG-511")
    def test_reserved_node_name_conflict_raises(self):
        config = {
            "nodes": {VERIFY_NODE_NAME: {"type": "llm"}},
            "verify": [{"check": "output", "on_fail": "halt"}],
        }
        with pytest.raises(ValueError, match="reserved"):
            insert_verify_node(config)

    @pytest.mark.req("REQ-YG-511")
    def test_transform_does_not_mutate_input(self):
        config = {
            "nodes": {"a": {"type": "llm"}},
            "edges": [{"from": "a", "to": "END"}],
            "verify": [{"check": "output", "on_fail": "halt"}],
        }
        insert_verify_node(config)
        assert VERIFY_NODE_NAME not in config["nodes"]
        assert config["edges"] == [{"from": "a", "to": "END"}]


# --- Move 2b: verify node function ------------------------------------------
class TestVerifyNodeFunction:
    """create_verify_node evaluates rules once against final state."""

    @pytest.mark.req("REQ-YG-511")
    def test_halt_rule_raises_with_message(self):
        node_fn = create_verify_node(
            [{"check": "state.n >= 10", "on_fail": "halt", "message": "too small"}]
        )
        with pytest.raises(GuardHaltError, match="too small"):
            node_fn({"n": 3})

    @pytest.mark.req("REQ-YG-511")
    def test_warn_rule_appends_error_and_continues(self):
        node_fn = create_verify_node(
            [{"check": "state.n >= 10", "on_fail": "warn", "message": "soft fail"}]
        )
        update = node_fn({"n": 3})
        assert update["current_step"] == VERIFY_NODE_NAME
        assert len(update["errors"]) == 1
        assert update["errors"][0].message == "soft fail"

    @pytest.mark.req("REQ-YG-511")
    def test_passing_rule_returns_no_errors(self):
        node_fn = create_verify_node([{"check": "state.n >= 10", "on_fail": "halt"}])
        update = node_fn({"n": 50})
        assert update["errors"] == []

    @pytest.mark.req("REQ-YG-511")
    def test_errors_return_is_delta_only(self):
        """errors uses an add-reducer — verify must return only new deltas."""
        node_fn = create_verify_node(
            [{"check": "state.n >= 10", "on_fail": "warn", "message": "soft fail"}]
        )
        # State already carries prior errors; verify must not re-emit them.
        update = node_fn({"n": 3, "errors": ["prior-a", "prior-b"]})
        assert len(update["errors"]) == 1


# --- Move 2c: schema boundary ------------------------------------------------
class TestGraphVerifySchema:
    """GraphVerifyRule permits warn|halt only; malformed blocks fail at load."""

    @pytest.mark.req("REQ-YG-511")
    @pytest.mark.parametrize("action", ["warn", "halt"])
    def test_verify_rule_accepts_warn_and_halt(self, action):
        rule = GraphVerifyRule(check="output", on_fail=action)
        assert rule.on_fail == action

    @pytest.mark.req("REQ-YG-511")
    def test_verify_rule_rejects_retry(self):
        with pytest.raises(ValidationError):
            GraphVerifyRule(check="output", on_fail="retry")

    @pytest.mark.req("REQ-YG-511")
    def test_verify_rule_rejects_max_retries(self):
        with pytest.raises(ValidationError):
            GraphVerifyRule(check="output", on_fail="halt", max_retries=2)

    @pytest.mark.req("REQ-YG-511")
    def test_graph_schema_parses_verify_field(self):
        schema = GraphConfigSchema.model_validate(
            {
                "nodes": {"a": {"type": "passthrough"}},
                "edges": [{"from": "START", "to": "a"}, {"from": "a", "to": "END"}],
                "verify": [{"check": "output", "on_fail": "warn"}],
            }
        )
        assert len(schema.verify) == 1
        assert schema.verify[0].on_fail == "warn"

    @pytest.mark.req("REQ-YG-511")
    def test_malformed_verify_fails_at_load(self, tmp_path):
        path = _write_graph(tmp_path, on_fail="retry")
        with pytest.raises(ValueError):
            load_graph_config(str(path))


# --- Move 2d: end-to-end graph execution -------------------------------------
class TestGraphVerifyEndToEnd:
    """A compiled graph runs the terminal verify node before END."""

    @pytest.mark.req("REQ-YG-511")
    def test_verify_halt_stops_run(self, tmp_path):
        path = _write_graph(tmp_path, on_fail="halt")
        config = load_graph_config(str(path))
        graph = compile_graph(config).compile()
        with pytest.raises(GuardHaltError, match="result too small"):
            graph.invoke({"seed": 5})

    @pytest.mark.req("REQ-YG-511")
    def test_verify_warn_surfaces_to_errors(self, tmp_path):
        path = _write_graph(tmp_path, on_fail="warn")
        config = load_graph_config(str(path))
        graph = compile_graph(config).compile()
        result = graph.invoke({"seed": 5})
        # Run completes; the warn is recorded in state.errors.
        assert result["result"] == 5
        messages = [e.message for e in result["errors"]]
        assert any("result too small" in m for m in messages)

    @pytest.mark.req("REQ-YG-511")
    def test_verify_pass_runs_clean(self, tmp_path):
        path = _write_graph(tmp_path, on_fail="halt")
        config = load_graph_config(str(path))
        graph = compile_graph(config).compile()
        result = graph.invoke({"seed": 150})
        assert result["result"] == 150
        assert result.get("errors", []) == []
