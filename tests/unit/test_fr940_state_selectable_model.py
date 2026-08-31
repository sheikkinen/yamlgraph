"""FR-940: state-selectable llm-node model/provider (core enablement).

An llm node may declare ``model: "{state.model}"`` / ``provider:
"{state.provider}"``; the reference is resolved from state at execution
time, falling back to the graph ``defaults`` value when the state key
is missing or empty. Literal values are untouched. This is the minimal
enablement for the corpus-census caller-selectable model variable.
"""

from unittest.mock import patch

import pytest

from yamlgraph.node_factory import create_node_function

DEFAULTS = {"provider": "anthropic", "model": "claude-haiku-4-5"}

NODE = {
    "type": "llm",
    "prompt": "judge_item",
    "provider": "{state.provider}",
    "model": "{state.model}",
    "state_key": "finding",
    "skip_if_exists": False,
}


def _run(state):
    with (
        patch("yamlgraph.node_factory.llm_nodes.execute_prompt") as mock_execute,
        patch(
            "yamlgraph.node_factory.llm_nodes.get_output_model_for_node"
        ) as mock_get_model,
    ):
        mock_get_model.return_value = None
        mock_execute.return_value = "ok"
        node_fn = create_node_function("judge", NODE, DEFAULTS)
        node_fn(state)
        return mock_execute.call_args.kwargs


class TestStateSelectableModel:
    @pytest.mark.req("REQ-YG-633")
    def test_state_ref_resolves_from_state(self):
        kwargs = _run({"model": "mercury-2", "provider": "inception"})
        assert kwargs["model"] == "mercury-2"
        assert kwargs["provider"] == "inception"

    @pytest.mark.req("REQ-YG-633")
    def test_missing_state_key_falls_back_to_graph_defaults(self):
        kwargs = _run({})
        assert kwargs["model"] == "claude-haiku-4-5"
        assert kwargs["provider"] == "anthropic"

    @pytest.mark.req("REQ-YG-633")
    def test_empty_state_value_falls_back_to_graph_defaults(self):
        kwargs = _run({"model": "  ", "provider": ""})
        assert kwargs["model"] == "claude-haiku-4-5"
        assert kwargs["provider"] == "anthropic"

    @pytest.mark.req("REQ-YG-633")
    def test_literal_model_untouched(self):
        with (
            patch("yamlgraph.node_factory.llm_nodes.execute_prompt") as mock_execute,
            patch(
                "yamlgraph.node_factory.llm_nodes.get_output_model_for_node"
            ) as mock_get_model,
        ):
            mock_get_model.return_value = None
            mock_execute.return_value = "ok"
            node_fn = create_node_function(
                "judge",
                {**NODE, "model": "claude-sonnet-4-5", "provider": "anthropic"},
                DEFAULTS,
            )
            node_fn({"model": "mercury-2"})
            assert mock_execute.call_args.kwargs["model"] == "claude-sonnet-4-5"

    @pytest.mark.req("REQ-YG-633")
    def test_non_string_state_value_raises(self):
        with pytest.raises(Exception, match="model|provider"):
            _run({"model": 42, "provider": "anthropic"})
