"""Unit tests for FR-049: Interactive Tool Node Type.

TDD RED phase — all tests must fail initially, then pass after implementation.
Tests config-level expansion, negate_condition, interrupt idempotent flag,
validator, and linter integration.
"""

from unittest.mock import patch

import pytest

from yamlgraph.constants import NodeType

# ---------------------------------------------------------------------------
# 1. NodeType enum
# ---------------------------------------------------------------------------


class TestNodeTypeInteractiveTool:
    """NodeType.INTERACTIVE_TOOL constant should exist."""

    @pytest.mark.req("REQ-YG-075")
    def test_enum_value_exists(self):
        """NodeType should have INTERACTIVE_TOOL constant."""
        assert hasattr(NodeType, "INTERACTIVE_TOOL")
        assert NodeType.INTERACTIVE_TOOL == "interactive_tool"

    @pytest.mark.req("REQ-YG-075")
    def test_not_requires_prompt(self):
        """Interactive tool nodes don't require prompt."""
        assert not NodeType.requires_prompt("interactive_tool")


# ---------------------------------------------------------------------------
# 2. negate_condition (Constraint 11 — De Morgan's law)
# ---------------------------------------------------------------------------


class TestNegateCondition:
    """negate_condition() utility for loop-back edge generation."""

    @pytest.mark.req("REQ-YG-075")
    def test_negate_simple_eq(self):
        """Negate simple equality: a == 'x' → a != 'x'."""
        from yamlgraph.utils.conditions import negate_condition

        assert negate_condition("phase == 'completed'") == "phase != 'completed'"

    @pytest.mark.req("REQ-YG-075")
    def test_negate_simple_neq(self):
        """Negate simple inequality: a != 'x' → a == 'x'."""
        from yamlgraph.utils.conditions import negate_condition

        assert negate_condition("phase != 'running'") == "phase == 'running'"

    @pytest.mark.req("REQ-YG-075")
    def test_negate_or_to_and(self):
        """De Morgan: (a == 'x' or b == 'y') → (a != 'x' and b != 'y')."""
        from yamlgraph.utils.conditions import negate_condition

        result = negate_condition("phase == 'completed' or phase == 'error'")
        assert result == "phase != 'completed' and phase != 'error'"

    @pytest.mark.req("REQ-YG-075")
    def test_negate_and_to_or(self):
        """De Morgan: (a == 'x' and b == 'y') → (a != 'x' or b != 'y')."""
        from yamlgraph.utils.conditions import negate_condition

        result = negate_condition("phase == 'done' and status == 'ok'")
        assert result == "phase != 'done' or status != 'ok'"

    @pytest.mark.req("REQ-YG-075")
    def test_negate_lt_gt(self):
        """Negate ordering operators: < → >=, > → <=, etc."""
        from yamlgraph.utils.conditions import negate_condition

        assert negate_condition("score < 0.8") == "score >= 0.8"
        assert negate_condition("score > 5") == "score <= 5"
        assert negate_condition("score <= 10") == "score > 10"
        assert negate_condition("score >= 3") == "score < 3"

    @pytest.mark.req("REQ-YG-075")
    def test_negate_compound_or_with_many_parts(self):
        """Negate multi-part OR → AND of negations."""
        from yamlgraph.utils.conditions import negate_condition

        expr = (
            "auth_status == 'finished' or auth_status == 'expired' "
            "or auth_status == 'error'"
        )
        result = negate_condition(expr)
        assert result == (
            "auth_status != 'finished' and auth_status != 'expired' "
            "and auth_status != 'error'"
        )

    @pytest.mark.req("REQ-YG-075")
    def test_negate_invalid_expression_raises(self):
        """Should raise ValueError on malformed expressions."""
        from yamlgraph.utils.conditions import negate_condition

        with pytest.raises(ValueError):
            negate_condition("not a valid expr")

    @pytest.mark.req("REQ-YG-075")
    def test_negate_roundtrip_with_evaluate(self):
        """Negated condition should be the boolean complement of original."""
        from yamlgraph.utils.conditions import evaluate_condition, negate_condition

        state = {"phase": "completed"}
        expr = "phase == 'completed'"
        negated = negate_condition(expr)

        assert evaluate_condition(expr, state) is True
        assert evaluate_condition(negated, state) is False


# ---------------------------------------------------------------------------
# 3. create_interrupt_node idempotent flag (Constraint 10)
# ---------------------------------------------------------------------------


class TestInterruptIdempotentFlag:
    """Interrupt node with idempotent=False should regenerate message."""

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-075")
    def test_idempotent_true_reuses_cached_payload(self, mock_interrupt):
        """Default (idempotent=True) should reuse existing payload."""
        from yamlgraph.node_factory import create_interrupt_node

        mock_interrupt.return_value = "user reply"
        config = {"message": "old message", "state_key": "msg", "resume_key": "reply"}
        prepare_fn, interrupt_fn = create_interrupt_node("ask", config)

        state = {"msg": "cached payload"}
        prep_result = prepare_fn(state)

        # Should use cached payload, not config message
        assert prep_result["msg"] == "cached payload"

    @patch("langgraph.types.interrupt")
    @pytest.mark.req("REQ-YG-075")
    def test_idempotent_false_regenerates_message(self, mock_interrupt):
        """idempotent=False should always regenerate message from template."""
        from yamlgraph.node_factory import create_interrupt_node

        mock_interrupt.return_value = "user reply"
        config = {
            "message": "{bot_response}",
            "state_key": "msg",
            "resume_key": "reply",
            "idempotent": False,
        }
        prepare_fn, interrupt_fn = create_interrupt_node("ask", config)

        # Simulate loop iteration: state_key has old value, but bot_response changed
        state = {"msg": "old bot message", "bot_response": "new bot message"}
        prep_result = prepare_fn(state)

        # Should regenerate from template, not use cached
        assert prep_result["msg"] == "new bot message"


# ---------------------------------------------------------------------------
# 4. Config-level expansion (Constraint 8)
# ---------------------------------------------------------------------------


class TestInteractiveToolExpansion:
    """Config-level expansion of interactive_tool into inline nodes + edges."""

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_creates_start_ask_step_nodes(self):
        """Should expand into __start, __ask, __step nodes."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = {
            "nodes": {
                "chat": {
                    "type": "interactive_tool",
                    "start": "create_session",
                    "step": "send_message",
                    "end": "close_session",
                    "resume_key": "user_msg",
                    "response_key": "bot_reply",
                    "loop_until": "phase == 'done'",
                },
            },
            "edges": [
                {"from": "START", "to": "chat"},
                {"from": "chat", "to": "END"},
            ],
            "tools": {
                "create_session": {
                    "type": "python",
                    "module": "tools",
                    "function": "create_session",
                },
                "send_message": {
                    "type": "python",
                    "module": "tools",
                    "function": "send_message",
                },
                "close_session": {
                    "type": "python",
                    "module": "tools",
                    "function": "close_session",
                },
            },
        }
        result = expand_interactive_tools(config)

        # Original node removed
        assert "chat" not in result["nodes"]

        # Expanded nodes created
        assert "chat__start" in result["nodes"]
        assert "chat__ask" in result["nodes"]
        assert "chat__step" in result["nodes"]
        assert "chat__end" in result["nodes"]

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_node_types(self):
        """Expanded nodes should have correct types."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        result = expand_interactive_tools(config)

        assert result["nodes"]["chat__start"]["type"] == "python"
        assert result["nodes"]["chat__ask"]["type"] == "interrupt"
        assert result["nodes"]["chat__step"]["type"] == "python"
        assert result["nodes"]["chat__end"]["type"] == "python"

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_rewrites_edges(self):
        """Incoming edges → __start, outgoing edges → __end."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        result = expand_interactive_tools(config)

        # START → chat becomes START → chat__start
        start_edges = [e for e in result["edges"] if e["from"] == "START"]
        assert any(e["to"] == "chat__start" for e in start_edges)

        # chat → END becomes chat__end → END
        end_edges = [e for e in result["edges"] if e["to"] == "END"]
        assert any(e["from"] == "chat__end" for e in end_edges)

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_internal_edges(self):
        """Should create internal edges: start→ask, ask→step, step→ask/end."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        result = expand_interactive_tools(config)

        edges = result["edges"]
        edge_pairs = [(e["from"], e["to"]) for e in edges]

        assert ("chat__start", "chat__ask") in edge_pairs
        assert ("chat__ask", "chat__step") in edge_pairs

        # Conditional edges: step → ask (loop back) and step → end (exit)
        step_edges = [e for e in edges if e["from"] == "chat__step"]
        assert len(step_edges) == 2  # loop-back + exit

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_loop_until_condition(self):
        """Exit edge should use loop_until condition, loop-back uses negated."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        result = expand_interactive_tools(config)

        step_edges = [e for e in result["edges"] if e["from"] == "chat__step"]
        exit_edge = next(e for e in step_edges if e["to"] == "chat__end")
        loop_edge = next(e for e in step_edges if e["to"] == "chat__ask")

        assert exit_edge["condition"] == "phase == 'done'"
        assert loop_edge["condition"] == "phase != 'done'"

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_without_end_tool(self):
        """When end is null, outgoing edges go from __step (exit condition)."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config(end=None)
        result = expand_interactive_tools(config)

        assert "chat__end" not in result["nodes"]

        # Outgoing chat→END becomes exit from step with condition
        end_edges = [e for e in result["edges"] if e["to"] == "END"]
        assert any(e["from"] == "chat__step" for e in end_edges)

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_max_iterations_default(self):
        """Max iterations should default to 10 on expanded step node."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        result = expand_interactive_tools(config)

        # step node should have loop_limit for max_iterations enforcement
        assert result["nodes"]["chat__step"].get("loop_limit") == 10

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_custom_max_iterations(self):
        """Custom max_iterations should be passed to step node."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config(max_iterations=5)
        result = expand_interactive_tools(config)

        assert result["nodes"]["chat__step"].get("loop_limit") == 5

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_interrupt_node_config(self):
        """Ask node should have correct message template and resume_key."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        result = expand_interactive_tools(config)

        ask = result["nodes"]["chat__ask"]
        assert ask["resume_key"] == "user_msg"
        assert ask.get("idempotent") is False
        assert "{bot_reply}" in ask.get("message", "")

    @pytest.mark.req("REQ-YG-075")
    def test_expansion_preserves_other_nodes(self):
        """Non-interactive nodes should pass through unchanged."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = _minimal_interactive_config()
        config["nodes"]["other"] = {"type": "llm", "prompt": "greet"}
        result = expand_interactive_tools(config)

        assert "other" in result["nodes"]
        assert result["nodes"]["other"] == {"type": "llm", "prompt": "greet"}

    @pytest.mark.req("REQ-YG-075")
    def test_no_interactive_tools_passthrough(self):
        """Config without interactive tools should pass through unchanged."""
        from yamlgraph.interactive_tool import expand_interactive_tools

        config = {
            "nodes": {"greet": {"type": "llm", "prompt": "greet"}},
            "edges": [{"from": "START", "to": "greet"}, {"from": "greet", "to": "END"}],
        }
        result = expand_interactive_tools(config)
        assert result["nodes"] == config["nodes"]
        assert result["edges"] == config["edges"]


# ---------------------------------------------------------------------------
# 5. Validator
# ---------------------------------------------------------------------------


class TestInteractiveToolValidation:
    """Validation of interactive_tool required fields."""

    @pytest.mark.req("REQ-YG-075")
    def test_missing_start_raises(self):
        """Should raise if start tool is missing."""
        from yamlgraph.utils.validators import validate_interactive_tool_node

        with pytest.raises(ValueError, match="start"):
            validate_interactive_tool_node(
                "chat",
                {
                    "type": "interactive_tool",
                    "step": "send",
                    "resume_key": "msg",
                    "response_key": "reply",
                    "loop_until": "done == true",
                },
            )

    @pytest.mark.req("REQ-YG-075")
    def test_missing_step_raises(self):
        """Should raise if step tool is missing."""
        from yamlgraph.utils.validators import validate_interactive_tool_node

        with pytest.raises(ValueError, match="step"):
            validate_interactive_tool_node(
                "chat",
                {
                    "type": "interactive_tool",
                    "start": "create",
                    "resume_key": "msg",
                    "response_key": "reply",
                    "loop_until": "done == true",
                },
            )

    @pytest.mark.req("REQ-YG-075")
    def test_missing_resume_key_raises(self):
        """Should raise if resume_key is missing."""
        from yamlgraph.utils.validators import validate_interactive_tool_node

        with pytest.raises(ValueError, match="resume_key"):
            validate_interactive_tool_node(
                "chat",
                {
                    "type": "interactive_tool",
                    "start": "create",
                    "step": "send",
                    "response_key": "reply",
                    "loop_until": "done == true",
                },
            )

    @pytest.mark.req("REQ-YG-075")
    def test_missing_response_key_raises(self):
        """Should raise if response_key is missing."""
        from yamlgraph.utils.validators import validate_interactive_tool_node

        with pytest.raises(ValueError, match="response_key"):
            validate_interactive_tool_node(
                "chat",
                {
                    "type": "interactive_tool",
                    "start": "create",
                    "step": "send",
                    "resume_key": "msg",
                    "loop_until": "done == true",
                },
            )

    @pytest.mark.req("REQ-YG-075")
    def test_missing_loop_until_raises(self):
        """Should raise if loop_until is missing."""
        from yamlgraph.utils.validators import validate_interactive_tool_node

        with pytest.raises(ValueError, match="loop_until"):
            validate_interactive_tool_node(
                "chat",
                {
                    "type": "interactive_tool",
                    "start": "create",
                    "step": "send",
                    "resume_key": "msg",
                    "response_key": "reply",
                },
            )

    @pytest.mark.req("REQ-YG-075")
    def test_valid_config_passes(self):
        """Should not raise for valid config."""
        from yamlgraph.utils.validators import validate_interactive_tool_node

        # Should not raise
        validate_interactive_tool_node(
            "chat",
            {
                "type": "interactive_tool",
                "start": "create",
                "step": "send",
                "resume_key": "msg",
                "response_key": "reply",
                "loop_until": "done == true",
            },
        )


# ---------------------------------------------------------------------------
# 6. Linter — node name warning
# ---------------------------------------------------------------------------


class TestLinterDoubleUnderscore:
    """Linter should warn on node names containing __."""

    @pytest.mark.req("REQ-YG-075")
    def test_warn_on_double_underscore(self, tmp_path):
        """Should emit warning for user-defined node name with __."""
        import yaml

        from yamlgraph.linter.checks import check_node_types

        graph = {
            "nodes": {
                "my__bad__name": {"type": "llm", "prompt": "greet"},
            },
            "edges": [
                {"from": "START", "to": "my__bad__name"},
                {"from": "my__bad__name", "to": "END"},
            ],
        }
        path = tmp_path / "graph.yaml"
        path.write_text(yaml.dump(graph), encoding="utf-8")

        issues = check_node_types(path)
        warnings = [i for i in issues if "__" in i.message]
        assert len(warnings) >= 1
        assert warnings[0].severity == "warning"

    @pytest.mark.req("REQ-YG-075")
    def test_no_warn_on_normal_names(self, tmp_path):
        """Should not warn on normal node names."""
        import yaml

        from yamlgraph.linter.checks import check_node_types

        graph = {
            "nodes": {
                "greet_user": {"type": "llm", "prompt": "greet"},
            },
            "edges": [
                {"from": "START", "to": "greet_user"},
                {"from": "greet_user", "to": "END"},
            ],
        }
        path = tmp_path / "graph.yaml"
        path.write_text(yaml.dump(graph), encoding="utf-8")

        issues = check_node_types(path)
        underscore_warnings = [i for i in issues if "__" in i.message]
        assert len(underscore_warnings) == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_interactive_config(
    end: str | None = "close_session",
    max_iterations: int | None = None,
) -> dict:
    """Create minimal valid interactive_tool config for testing."""
    node_config: dict = {
        "type": "interactive_tool",
        "start": "create_session",
        "step": "send_message",
        "resume_key": "user_msg",
        "response_key": "bot_reply",
        "loop_until": "phase == 'done'",
    }
    if end is not None:
        node_config["end"] = end
    if max_iterations is not None:
        node_config["max_iterations"] = max_iterations

    return {
        "nodes": {
            "chat": node_config,
        },
        "edges": [
            {"from": "START", "to": "chat"},
            {"from": "chat", "to": "END"},
        ],
        "tools": {
            "create_session": {
                "type": "python",
                "module": "tools",
                "function": "create_session",
            },
            "send_message": {
                "type": "python",
                "module": "tools",
                "function": "send_message",
            },
            "close_session": {
                "type": "python",
                "module": "tools",
                "function": "close_session",
            },
        },
    }
