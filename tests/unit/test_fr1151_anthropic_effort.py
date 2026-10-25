"""FR-1151: an optional ``effort`` (low..max) on graph defaults and llm nodes, sent as ``output_config.effort``.

Anthropic only, refused on any other resolved provider; absent, every request is unchanged; refused at load on
race nodes and on routers with ``candidates:``, which would drop it.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from tests.unit.test_race_node import _make_mock_llm, _race_config
from yamlgraph.models.graph_schema import GraphConfigSchema, NodeConfig
from yamlgraph.utils.llm_factory import clear_cache, create_llm

OPUS = "claude-opus-5-5"


def _payload(llm):
    return llm._get_request_payload([HumanMessage("hi")])


def _graph(defaults: dict, node: dict) -> dict:
    return {
        "version": "1.0",
        "name": "fr1151",
        "defaults": defaults,
        "nodes": {"plan": node},
        "edges": [{"from": "START", "to": "plan"}, {"from": "plan", "to": "END"}],
    }


@pytest.mark.req("REQ-YG-725")
class TestCreateLLMEffort:
    def setup_method(self):
        clear_cache()

    def test_effort_reaches_output_config(self):
        """AC-01."""
        llm = create_llm(provider="anthropic", model=OPUS, effort="low")
        assert _payload(llm)["output_config"] == {"effort": "low"}

    def test_absent_effort_leaves_the_request_unchanged(self):
        """AC-02."""
        llm = create_llm(provider="anthropic", model=OPUS)
        assert "output_config" not in _payload(llm)
        assert llm.thinking is None

    def test_effort_on_another_provider_raises_before_any_client(self):
        """AC-03."""
        with (
            patch("yamlgraph.utils.llm_factory.dispatch_provider") as dispatch,
            pytest.raises(ValueError, match="effort") as err,
        ):
            create_llm(provider="openai", effort="low")
        assert "openai" in str(err.value)
        dispatch.assert_not_called()

    def test_effort_refused_on_the_resolved_provider(self, monkeypatch):
        """AC-19: provider from PROVIDER, not the argument."""
        monkeypatch.setenv("PROVIDER", "openai")
        with (
            patch("yamlgraph.utils.llm_factory.dispatch_provider") as dispatch,
            pytest.raises(ValueError, match="effort") as err,
        ):
            create_llm(effort="low")
        assert "openai" in str(err.value)
        dispatch.assert_not_called()

    def test_effort_is_in_the_cache_key(self):
        """AC-04."""
        low = create_llm(provider="anthropic", model=OPUS, effort="low")
        high = create_llm(provider="anthropic", model=OPUS, effort="high")
        assert low is not high
        assert create_llm(provider="anthropic", model=OPUS, effort="low") is low

    def test_effort_with_thinking_off_on_sonnet_5_5(self):
        """AC-08."""
        llm = create_llm(
            provider="anthropic",
            model="claude-sonnet-5-5",
            thinking_budget=0,
            effort="low",
        )
        payload = _payload(llm)
        assert payload["thinking"] == {"type": "between_tools"}
        assert payload["output_config"] == {"effort": "low"}

    def test_opus_5_5_low_effort_thinking_as_observed(self):
        """AC-16: langchain_anthropic 1.7.0's profile data gives claude-opus-5-5 no `xhigh` level, so its adaptive
        default (chat_models.py:1659-1669) does not apply: no `thinking` field is sent."""
        llm = create_llm(provider="anthropic", model=OPUS, effort="low")
        assert "thinking" not in _payload(llm)


@pytest.mark.req("REQ-YG-725")
class TestEffortSchema:
    def test_bad_value_refused_on_a_node(self):
        """AC-06."""
        with pytest.raises(ValidationError, match="xhigh"):
            NodeConfig(type="llm", prompt="p", effort="lowest")

    def test_bad_value_refused_in_defaults(self):
        """AC-06."""
        node = {"type": "llm", "prompt": "p"}
        with pytest.raises(ValidationError, match="xhigh"):
            GraphConfigSchema.model_validate(_graph({"effort": "lowest"}, node))

    @pytest.mark.parametrize(
        "node",
        [
            {
                "type": "race",
                "prompt": "p",
                "candidates": [{"model": "a"}, {"model": "b"}],
            },
            {
                "type": "router",
                "prompt": "p",
                "routes": {"a": "x"},
                "route_field": "intent",
                "candidates": [{"model": "a"}, {"model": "b"}],
            },
        ],
        ids=["race", "router-with-candidates"],
    )
    def test_effort_refused_where_it_would_be_dropped(self, node):
        """AC-17."""
        with pytest.raises(ValidationError, match="effort") as err:
            NodeConfig(**node, effort="low")
        assert node["type"] in str(err.value)

    @pytest.mark.parametrize(
        "node",
        [
            {"type": "llm", "prompt": "p"},
            {
                "type": "router",
                "prompt": "p",
                "routes": {"a": "x"},
                "route_field": "intent",
            },
        ],
        ids=["llm", "router"],
    )
    def test_effort_accepted_on_llm_and_plain_router(self, node):
        """AC-17."""
        assert NodeConfig(**node, effort="low").effort == "low"


@pytest.mark.req("REQ-YG-725")
class TestEffortNodeResolution:
    @pytest.mark.parametrize(
        ("node_extra", "defaults", "expected"),
        [
            ({"effort": "low"}, {}, "low"),
            ({}, {"effort": "high"}, "high"),
            ({}, {}, None),
        ],
        ids=["node", "defaults", "unset"],
    )
    def test_effort_resolves_and_reaches_execute_prompt(
        self, node_extra, defaults, expected
    ):
        """AC-05."""
        from yamlgraph.node_factory.llm_nodes import (
            create_node_function,
            resolve_llm_node_config,
        )

        node = {"type": "llm", "prompt": "p", "state_key": "out", **node_extra}
        assert resolve_llm_node_config("plan", node, defaults, None).effort == expected
        with (
            patch("yamlgraph.node_factory.llm_nodes.execute_prompt") as execute,
            patch(
                "yamlgraph.node_factory.llm_nodes.get_output_model_for_node",
                return_value=None,
            ),
        ):
            execute.return_value = "ok"
            create_node_function("plan", node, defaults)({})
        assert execute.call_args.kwargs["effort"] == expected

    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_defaults_effort_never_reaches_race_candidates(
        self, mock_prepare, mock_create_llm
    ):
        """AC-18."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "vertex", None)
        mock_create_llm.side_effect = [
            _make_mock_llm("a"),
            _make_mock_llm("b", delay=0.2),
        ]
        create_race_node("race", _race_config(), {"effort": "high"})({"x": 1})
        calls = mock_create_llm.call_args_list
        assert len(calls) == 2
        assert all("effort" not in c.kwargs for c in calls)
