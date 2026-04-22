"""Tests for router node with candidates: race support — FR-272.

Router nodes with candidates: fire the same prompt to N providers concurrently
and return the first successful result, then apply normal routing resolution.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Helpers
# =============================================================================


def _make_mock_llm(response_text: str, delay: float = 0.0, fail: bool = False):
    """Create a mock LLM that returns a fixed response after optional delay."""
    mock = MagicMock()

    async def ainvoke(messages):
        if delay:
            await asyncio.sleep(delay)
        if fail:
            raise RuntimeError(f"LLM failed: {response_text}")
        result = MagicMock()
        result.content = response_text
        return result

    mock.ainvoke = ainvoke
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


@pytest.fixture
def sample_state():
    return {
        "thread_id": "test-router-race-001",
        "message": "hello",
        "current_step": "init",
        "errors": [],
        "_loop_counts": {},
    }


# =============================================================================
# AC1: Router with candidates races and routes correctly
# =============================================================================


class TestRouterRaceRoutesCorrectly:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_router_race_routes_on_first_winner(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC1: Router with candidates races and routes based on winner output."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        # First candidate responds fast with valid JSON
        fast_llm = _make_mock_llm('{"intent": "medical_triage"}', delay=0.0)
        slow_llm = _make_mock_llm('{"intent": "elderlycare"}', delay=0.5)
        mock_create_llm.side_effect = [fast_llm, slow_llm]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {
                "medical_triage": "switch_to_triage",
                "elderlycare": "switch_to_interrai",
                "crisis": "crisis_response",
            },
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "candidates": [
                {"provider": "vertex", "model": "gemini-2.5-flash"},
                {"provider": "anthropic", "model": "claude-haiku-4-5"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        result = node_fn(sample_state)

        assert result["_route"] == "switch_to_triage"
        assert result["intent"] == "medical_triage"

    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_router_race_second_candidate_can_win(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC1: Second candidate can win the race and determine routing."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        slow_llm = _make_mock_llm('{"intent": "elderlycare"}', delay=0.5)
        fast_llm = _make_mock_llm('{"intent": "crisis"}', delay=0.0)
        mock_create_llm.side_effect = [slow_llm, fast_llm]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {
                "medical_triage": "switch_to_triage",
                "elderlycare": "switch_to_interrai",
                "crisis": "crisis_response",
            },
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "candidates": [
                {"provider": "vertex", "model": "gemini-2.5-flash"},
                {"provider": "anthropic", "model": "claude-haiku-4-5"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        result = node_fn(sample_state)

        assert result["_route"] == "crisis_response"
        assert result["intent"] == "crisis"


# =============================================================================
# AC2: Losers are cancelled
# =============================================================================


class TestRouterRaceLosersAreCancelled:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_losers_receive_cancellation(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC2: When a winner emerges, pending candidates are cancelled."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        cancelled = []

        async def slow_ainvoke(messages):
            try:
                await asyncio.sleep(10.0)
                result = MagicMock()
                result.content = '{"intent": "elderlycare"}'
                return result
            except asyncio.CancelledError:
                cancelled.append("slow_cancelled")
                raise

        fast_llm = _make_mock_llm('{"intent": "medical_triage"}', delay=0.0)
        slow_llm = MagicMock()
        slow_llm.ainvoke = slow_ainvoke
        slow_llm.with_structured_output = MagicMock(return_value=slow_llm)

        mock_create_llm.side_effect = [fast_llm, slow_llm]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {"medical_triage": "triage", "elderlycare": "interrai"},
            "default_route": "triage",
            "state_key": "intent",
            "candidates": [
                {"provider": "vertex", "model": "gemini"},
                {"provider": "anthropic", "model": "haiku"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        node_fn(sample_state)

        assert "slow_cancelled" in cancelled, "Slow candidate was not cancelled"


# =============================================================================
# AC3: Malformed JSON candidate disqualified, not fatal
# =============================================================================


class TestRouterRaceMalformedJsonDisqualified:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_bad_json_candidate_routes_to_default_not_fatal(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC3: A candidate returning invalid JSON does not raise; router falls to default_route.

        Per Judgement amendment: winner disqualification dropped.
        If winner's route_field is absent (bad JSON), use default_route — same
        as single-provider router behaviour. "Not fatal" is the core guarantee.
        """
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        # Fast candidate returns bad JSON — wins the race
        bad_llm = _make_mock_llm("not valid json at all {{{{", delay=0.0)
        # Slow candidate would return good JSON, but doesn't win
        good_llm = _make_mock_llm('{"intent": "elderlycare"}', delay=0.5)
        mock_create_llm.side_effect = [bad_llm, good_llm]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {
                "medical_triage": "switch_to_triage",
                "elderlycare": "switch_to_interrai",
            },
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "candidates": [
                {"provider": "vertex", "model": "gemini"},
                {"provider": "anthropic", "model": "haiku"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})

        # Must not raise — "not fatal" is the contract
        result = node_fn(sample_state)

        # Winner's route_field absent → fall to default_route
        assert result["_route"] == "switch_to_triage"
        # _race_winner still recorded for telemetry
        assert "_race_winner" in result


# =============================================================================
# AC4: Timeout falls back to default_route
# =============================================================================


class TestRouterRaceTimeout:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_timeout_routes_to_default_with_on_error_fallback(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC4: All candidates timeout → routes to default_route, records error."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        slow1 = _make_mock_llm("slow", delay=10.0)
        slow2 = _make_mock_llm("slow", delay=10.0)
        mock_create_llm.side_effect = [slow1, slow2]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {
                "medical_triage": "switch_to_triage",
                "elderlycare": "switch_to_interrai",
            },
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "timeout": 0.05,
            "on_error": "fallback",
            "candidates": [
                {"provider": "vertex", "model": "gemini"},
                {"provider": "anthropic", "model": "haiku"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        result = node_fn(sample_state)

        assert result["_route"] == "switch_to_triage"
        assert result.get("errors"), "Should record an error on timeout"

    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_timeout_with_no_on_error_routes_to_default(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC4: Timeout with on_error unset still routes to default_route."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        slow1 = _make_mock_llm("slow", delay=10.0)
        slow2 = _make_mock_llm("slow", delay=10.0)
        mock_create_llm.side_effect = [slow1, slow2]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {"medical_triage": "switch_to_triage"},
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "timeout": 0.05,
            # on_error not set
            "candidates": [
                {"provider": "vertex", "model": "gemini"},
                {"provider": "anthropic", "model": "haiku"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        result = node_fn(sample_state)

        assert result["_route"] == "switch_to_triage"
        assert result.get("errors")

    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_timeout_with_on_error_fail_raises(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC4: on_error=fail + timeout raises AllCandidatesFailedError."""
        from yamlgraph.node_factory.llm_nodes import create_node_function
        from yamlgraph.node_factory.race_node import AllCandidatesFailedError

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        slow1 = _make_mock_llm("slow", delay=10.0)
        slow2 = _make_mock_llm("slow", delay=10.0)
        mock_create_llm.side_effect = [slow1, slow2]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {"medical_triage": "switch_to_triage"},
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "timeout": 0.05,
            "on_error": "fail",
            "candidates": [
                {"provider": "vertex", "model": "gemini"},
                {"provider": "anthropic", "model": "haiku"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        with pytest.raises(AllCandidatesFailedError):
            node_fn(sample_state)


# =============================================================================
# AC5: Mutual exclusion: provider + candidates rejected at compile time
# =============================================================================


class TestRouterRaceMutualExclusion:
    @pytest.mark.req("REQ-YG-271")
    def test_provider_and_candidates_rejected_by_graph_config(self):
        """AC5: GraphConfig raises ValueError when provider + candidates both set."""
        from yamlgraph.graph_loader import GraphConfig

        config_dict = {
            "version": "1.0",
            "name": "test",
            "nodes": {
                "classify": {
                    "type": "router",
                    "prompt": "classify",
                    "provider": "anthropic",
                    "route_field": "intent",
                    "routes": {"medical": "handle_medical"},
                    "default_route": "handle_medical",
                    "candidates": [
                        {"provider": "vertex", "model": "gemini"},
                        {"provider": "anthropic", "model": "haiku"},
                    ],
                },
                "handle_medical": {"prompt": "medical"},
            },
            "edges": [
                {"from": "START", "to": "classify"},
                {"from": "classify", "to": ["handle_medical"], "type": "conditional"},
                {"from": "handle_medical", "to": "END"},
            ],
        }
        with pytest.raises(ValueError, match="candidates"):
            GraphConfig(config_dict)

    @pytest.mark.req("REQ-YG-271")
    def test_on_error_skip_rejected_for_router_with_candidates(self):
        """AC5: on_error=skip is invalid for router nodes with candidates."""
        from yamlgraph.graph_loader import GraphConfig

        config_dict = {
            "version": "1.0",
            "name": "test",
            "nodes": {
                "classify": {
                    "type": "router",
                    "prompt": "classify",
                    "route_field": "intent",
                    "routes": {"medical": "handle_medical"},
                    "default_route": "handle_medical",
                    "on_error": "skip",
                    "candidates": [
                        {"provider": "vertex", "model": "gemini"},
                        {"provider": "anthropic", "model": "haiku"},
                    ],
                },
                "handle_medical": {"prompt": "medical"},
            },
            "edges": [
                {"from": "START", "to": "classify"},
                {"from": "classify", "to": ["handle_medical"], "type": "conditional"},
                {"from": "handle_medical", "to": "END"},
            ],
        }
        with pytest.raises(ValueError, match="skip"):
            GraphConfig(config_dict)


# =============================================================================
# AC7: Telemetry — _race_winner metadata set in state
# =============================================================================


class TestRouterRaceWinnerMetadata:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.router_race_node.prepare_messages")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    def test_race_winner_metadata_in_state(
        self, mock_create_llm, mock_prepare, sample_state
    ):
        """AC7: _race_winner with provider and model is set in state."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        fast_llm = _make_mock_llm('{"intent": "medical_triage"}', delay=0.0)
        slow_llm = _make_mock_llm('{"intent": "elderlycare"}', delay=0.5)
        mock_create_llm.side_effect = [fast_llm, slow_llm]

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {"medical_triage": "switch_to_triage"},
            "default_route": "switch_to_triage",
            "state_key": "intent",
            "candidates": [
                {"provider": "vertex", "model": "gemini-2.5-flash"},
                {"provider": "anthropic", "model": "claude-haiku-4-5"},
            ],
        }
        node_fn = create_node_function("classify", node_config, {})
        result = node_fn(sample_state)

        assert "_race_winner" in result
        assert result["_race_winner"]["provider"] == "vertex"
        assert result["_race_winner"]["model"] == "gemini-2.5-flash"


# =============================================================================
# AC6: No regression — router nodes without candidates unchanged
# =============================================================================


class TestRouterSingleProviderUnchanged:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
    def test_single_provider_router_unchanged(self, mock_execute, sample_state):
        """AC6: Existing single-provider router still works."""
        from yamlgraph.node_factory.llm_nodes import create_node_function

        mock_result = MagicMock()
        mock_result.intent = "medical_triage"
        mock_execute.return_value = mock_result

        node_config = {
            "type": "router",
            "prompt": "classify",
            "output_model": "yamlgraph.models.GenericReport",
            "route_field": "intent",
            "routes": {"medical_triage": "switch_to_triage"},
            "default_route": "switch_to_triage",
            "state_key": "intent",
        }
        node_fn = create_node_function("classify", node_config, {})
        result = node_fn(sample_state)

        assert result["_route"] == "switch_to_triage"
        assert result["intent"] == "medical_triage"
        assert "_race_winner" not in result


# =============================================================================
# Compiler: router-with-candidates skips _maybe_wrap_timeout
# =============================================================================


class TestRouterRaceCompilePathSkipsTimeoutWrap:
    @pytest.mark.req("REQ-YG-271")
    @patch("yamlgraph.node_compiler._maybe_wrap_timeout")
    @patch("yamlgraph.node_factory.llm_nodes.create_node_function")
    def test_timeout_wrapper_skipped_for_router_with_candidates(
        self, mock_create_fn, mock_wrap_timeout
    ):
        """Compiler skips _maybe_wrap_timeout when router has candidates (like race)."""
        from yamlgraph.node_compiler import NodeCompileContext, _compile_llm_node

        mock_graph = MagicMock()
        mock_node_fn = MagicMock()
        mock_create_fn.return_value = mock_node_fn
        mock_wrap_timeout.return_value = mock_node_fn

        node_config = {
            "type": "router",
            "prompt": "classify",
            "parse_json": True,
            "route_field": "intent",
            "routes": {"a": "node_a"},
            "default_route": "node_a",
            "candidates": [
                {"provider": "vertex", "model": "gemini"},
                {"provider": "anthropic", "model": "haiku"},
            ],
        }

        ctx = NodeCompileContext(
            node_name="classify",
            node_config=node_config,
            config=MagicMock(source_path=None),
            effective_defaults={},
            graph=mock_graph,
            cache_policy=None,
            tools={},
            python_tools={},
            callable_registry={},
            prompts_dir=None,
            prompts_relative=False,
        )

        _compile_llm_node(ctx)
        mock_wrap_timeout.assert_not_called()


# =============================================================================
# State builder: router with candidates adds _race_winner field
# =============================================================================


class TestRouterRaceStateBuilder:
    @pytest.mark.req("REQ-YG-271")
    def test_router_with_candidates_adds_race_winner_field(self):
        """State builder adds _race_winner for router nodes with candidates."""
        from yamlgraph.models.state_builder import extract_node_fields

        nodes = {
            "classify": {
                "type": "router",
                "state_key": "intent",
                "route_field": "intent",
                "routes": {"a": "node_a"},
                "candidates": [
                    {"provider": "vertex"},
                    {"provider": "anthropic"},
                ],
            }
        }
        fields = extract_node_fields(nodes)
        assert "_race_winner" in fields
        assert "_route" in fields
