"""Tests for FR-069: Per-Node Timeout for Map Branches."""

import concurrent.futures
import os
import time
from unittest.mock import MagicMock

import pytest

from yamlgraph.compile.map_compiler import compile_map_node, wrap_for_reducer
from yamlgraph.models import PipelineError
from yamlgraph.models.schemas import ErrorType


class TestNodeConfigTimeout:
    """Tests for timeout field on NodeConfig."""

    @pytest.mark.req("REQ-YG-078")
    def test_timeout_accepts_positive_float(self):
        """NodeConfig accepts positive float timeout."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(type="llm", prompt="test", timeout=30.0)
        assert config.timeout == 30.0

    @pytest.mark.req("REQ-YG-078")
    def test_timeout_accepts_positive_int(self):
        """NodeConfig accepts positive int timeout (copilot compat)."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(type="llm", prompt="test", timeout=60)
        assert config.timeout == 60

    @pytest.mark.req("REQ-YG-078")
    def test_timeout_rejects_zero(self):
        """NodeConfig rejects zero timeout."""
        from yamlgraph.models.graph_schema import NodeConfig

        with pytest.raises(ValueError, match="timeout must be positive"):
            NodeConfig(type="llm", prompt="test", timeout=0)

    @pytest.mark.req("REQ-YG-078")
    def test_timeout_rejects_negative(self):
        """NodeConfig rejects negative timeout."""
        from yamlgraph.models.graph_schema import NodeConfig

        with pytest.raises(ValueError, match="timeout must be positive"):
            NodeConfig(type="llm", prompt="test", timeout=-1.0)

    @pytest.mark.req("REQ-YG-078")
    def test_timeout_defaults_to_none(self):
        """NodeConfig timeout defaults to None."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(type="llm", prompt="test")
        assert config.timeout is None


class TestErrorTypeTimeout:
    """Tests for TIMEOUT_ERROR in ErrorType."""

    @pytest.mark.req("REQ-YG-078")
    def test_timeout_error_exists(self):
        """TIMEOUT_ERROR is a distinct ErrorType value."""
        assert ErrorType.TIMEOUT_ERROR == "timeout_error"

    @pytest.mark.req("REQ-YG-078")
    def test_from_exception_with_explicit_timeout_error(self):
        """PipelineError.from_exception with explicit error_type=TIMEOUT_ERROR."""
        error = concurrent.futures.TimeoutError("Branch timed out")
        pe = PipelineError.from_exception(
            error, node="test_node", error_type=ErrorType.TIMEOUT_ERROR
        )
        assert pe.type == ErrorType.TIMEOUT_ERROR
        assert pe.retryable is False

    @pytest.mark.req("REQ-YG-078")
    def test_from_exception_inference_unchanged(self):
        """from_exception still classifies TimeoutError as LLM_ERROR via inference.

        This verifies the from_exception classification logic is NOT modified.
        Transient LLM API timeouts must continue to be retryable LLM_ERROR.
        """
        error = concurrent.futures.TimeoutError("some timeout")
        pe = PipelineError.from_exception(error, node="test_node")
        assert pe.type == ErrorType.LLM_ERROR
        assert pe.retryable is True


class TestWrapForReducerTimeout:
    """Tests for timeout support in wrap_for_reducer."""

    @pytest.mark.req("REQ-YG-078")
    @pytest.mark.slow
    def test_slow_node_times_out(self):
        """A slow node exceeding timeout produces error result."""

        def slow_node(state):
            delay_scale = float(os.environ.get("TEST_DELAY_SCALE", "1.0"))
            time.sleep(2 * delay_scale)
            return {"result": "done"}

        wrapped = wrap_for_reducer(slow_node, "results", "result", timeout=0.05)
        result = wrapped({"_map_index": 0})

        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["_map_index"] == 0
        assert "_error" in result["results"][0]
        assert "timed out" in result["results"][0]["_error"].lower()
        assert "_error_type" in result["results"][0]
        assert result["results"][0]["_error_type"] == "TimeoutError"
        assert "errors" in result
        assert result["errors"][0].type == ErrorType.TIMEOUT_ERROR

    @pytest.mark.req("REQ-YG-078")
    def test_fast_node_completes_normally_with_timeout(self):
        """A fast node within timeout completes normally."""

        def fast_node(state):
            return {"result": state["item"] * 2}

        wrapped = wrap_for_reducer(fast_node, "results", "result", timeout=5.0)
        result = wrapped({"item": 5, "_map_index": 0})

        assert "results" in result
        assert result["results"][0] == {"_map_index": 0, "value": 10}

    @pytest.mark.req("REQ-YG-078")
    def test_no_timeout_unchanged_behavior(self):
        """Without timeout, behavior is unchanged."""

        def node_fn(state):
            return {"result": "ok"}

        wrapped = wrap_for_reducer(node_fn, "results", "result")
        result = wrapped({})

        assert result == {"results": ["ok"]}

    @pytest.mark.req("REQ-YG-078")
    @pytest.mark.slow
    def test_timeout_error_classified_as_timeout_not_llm(self):
        """TimeoutError caught before general Exception — classified as TIMEOUT_ERROR."""

        def slow_node(state):
            delay_scale = float(os.environ.get("TEST_DELAY_SCALE", "1.0"))
            time.sleep(2 * delay_scale)
            return {"result": "done"}

        wrapped = wrap_for_reducer(slow_node, "results", "result", timeout=0.05)
        result = wrapped({"_map_index": 0})

        assert result["errors"][0].type == ErrorType.TIMEOUT_ERROR
        assert result["errors"][0].retryable is False


class TestCompileMapNodeTimeout:
    """Tests for timeout propagation in compile_map_node."""

    @pytest.mark.req("REQ-YG-078")
    @pytest.mark.slow
    def test_timeout_passed_to_wrapped_node(self):
        """compile_map_node propagates timeout to the wrapped sub-node.

        Verifies by running a slow mock through the wrapped node and
        checking for timeout error result.
        """
        from unittest.mock import patch

        def slow_sub_node(state):
            delay_scale = float(os.environ.get("TEST_DELAY_SCALE", "1.0"))
            time.sleep(2 * delay_scale)
            return {"result": "done"}

        config = {
            "over": "{items}",
            "as": "item",
            "collect": "results",
            "timeout": 0.05,
            "node": {"type": "llm", "prompt": "test", "state_key": "result"},
        }
        builder = MagicMock()
        defaults = {}

        with patch(
            "yamlgraph.compile.map_compiler.create_node_function",
            return_value=slow_sub_node,
        ):
            compile_map_node("expand", config, builder, defaults)

        # Extract the wrapped node that was added to builder
        wrapped_node = builder.add_node.call_args[0][1]

        # Call it with state — should time out
        result = wrapped_node({"item": "x", "_map_index": 0})

        assert "results" in result
        assert "_error" in result["results"][0]
        assert "timed out" in result["results"][0]["_error"].lower()
        assert result["errors"][0].type == ErrorType.TIMEOUT_ERROR


class TestNonMapNodeTimeout:
    """Tests for timeout wrapping on non-map nodes."""

    @pytest.mark.req("REQ-YG-078")
    @pytest.mark.slow
    def test_maybe_wrap_timeout_wraps_slow_node(self):
        """_maybe_wrap_timeout wraps a node function with timeout."""
        from yamlgraph.compile.node_compiler import _maybe_wrap_timeout

        def slow_node(state):
            delay_scale = float(os.environ.get("TEST_DELAY_SCALE", "1.0"))
            time.sleep(2 * delay_scale)
            return {"result": "done", "current_step": "test"}

        wrapped = _maybe_wrap_timeout(
            slow_node, {"timeout": 0.05, "state_key": "result"}, "test_node"
        )
        result = wrapped({})

        assert "errors" in result
        assert result["errors"][0].type == ErrorType.TIMEOUT_ERROR
        assert result["result"] is None

    @pytest.mark.req("REQ-YG-078")
    def test_maybe_wrap_timeout_passes_fast_node(self):
        """_maybe_wrap_timeout passes fast node through unchanged result."""
        from yamlgraph.compile.node_compiler import _maybe_wrap_timeout

        def fast_node(state):
            return {"result": "done", "current_step": "test"}

        wrapped = _maybe_wrap_timeout(
            fast_node, {"timeout": 5.0, "state_key": "result"}, "test_node"
        )
        result = wrapped({})

        assert result == {"result": "done", "current_step": "test"}

    @pytest.mark.req("REQ-YG-078")
    def test_maybe_wrap_timeout_no_timeout_returns_original(self):
        """_maybe_wrap_timeout returns original fn when no timeout set."""
        from yamlgraph.compile.node_compiler import _maybe_wrap_timeout

        def original_node(state):
            return {"result": "done"}

        wrapped = _maybe_wrap_timeout(original_node, {}, "test_node")
        assert wrapped is original_node

    @pytest.mark.req("REQ-YG-078")
    def test_maybe_wrap_timeout_none_returns_original(self):
        """_maybe_wrap_timeout returns original fn when timeout is None."""
        from yamlgraph.compile.node_compiler import _maybe_wrap_timeout

        def original_node(state):
            return {"result": "done"}

        wrapped = _maybe_wrap_timeout(original_node, {"timeout": None}, "test_node")
        assert wrapped is original_node


class TestMapLintTimeout:
    """Tests for lint warning on map+agent without timeout."""

    @pytest.mark.req("REQ-YG-078")
    def test_map_agent_without_timeout_warns(self):
        """Map node with agent sub-node and no timeout emits warning."""
        from yamlgraph.linter.patterns.map import check_map_agent_timeout

        issues = check_map_agent_timeout(
            "analyze_all",
            {
                "type": "map",
                "over": "{state.articles}",
                "as": "article",
                "node": {"type": "agent", "prompt": "test", "state_key": "result"},
                "collect": "results",
            },
        )

        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "timeout" in issues[0].message.lower()

    @pytest.mark.req("REQ-YG-078")
    def test_map_agent_with_timeout_no_warning(self):
        """Map node with agent sub-node and timeout emits no warning."""
        from yamlgraph.linter.patterns.map import check_map_agent_timeout

        issues = check_map_agent_timeout(
            "analyze_all",
            {
                "type": "map",
                "over": "{state.articles}",
                "as": "article",
                "timeout": 30.0,
                "node": {"type": "agent", "prompt": "test", "state_key": "result"},
                "collect": "results",
            },
        )

        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-078")
    def test_map_llm_without_timeout_no_warning(self):
        """Map node with llm sub-node and no timeout emits no warning."""
        from yamlgraph.linter.patterns.map import check_map_agent_timeout

        issues = check_map_agent_timeout(
            "process",
            {
                "type": "map",
                "over": "{state.items}",
                "as": "item",
                "node": {"type": "llm", "prompt": "test", "state_key": "result"},
                "collect": "results",
            },
        )

        assert len(issues) == 0
