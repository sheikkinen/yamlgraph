"""Tests for tool_call inline dict args with per-value resolution.

FR-772: `tool_call.args` accepts an inline YAML mapping; each value is
resolved through `resolve_node_variables` (FR-252 semantics). The inline
branch rejects resolved values still containing "{state." (embedded
interpolation of missing paths). The string form is unchanged.

RED contract: inline dicts currently pass through resolve_template
unchanged, dispatching literal "{state.image}" strings as kwargs.
"""

import pytest

from yamlgraph.node_factory import create_tool_call_node


def recording_tool(**kwargs) -> dict:
    """Tool that returns exactly what it was called with."""
    return {"received": kwargs}


@pytest.fixture
def registry():
    return {"recorder": recording_tool}


def make_node(args_config, registry):
    return create_tool_call_node(
        "describe",
        {"tool": "recorder", "args": args_config, "state_key": "out"},
        registry,
    )


class TestInlineDictArgs:
    @pytest.mark.req("REQ-YG-576")
    def test_templated_values_resolve_and_literals_pass_through(self, registry):
        node = make_node(
            {
                "image": "{state.image}",
                "instruction": "Describe it.",
                "provider": "google",
            },
            registry,
        )
        result = node({"image": "fixtures/pixel.png"})

        envelope = result["out"]
        assert envelope["success"] is True
        assert envelope["result"]["received"] == {
            "image": "fixtures/pixel.png",
            "instruction": "Describe it.",
            "provider": "google",
        }

    @pytest.mark.req("REQ-YG-576")
    def test_non_string_state_values_keep_their_type(self, registry):
        node = make_node({"count": "{state.count}", "items": "{state.items}"}, registry)
        result = node({"count": 3, "items": ["a", "b"]})

        received = result["out"]["result"]["received"]
        assert received["count"] == 3
        assert received["items"] == ["a", "b"]

    @pytest.mark.req("REQ-YG-576")
    def test_simple_missing_path_resolves_to_none(self, registry):
        """FR-252 semantics pinned: {state.missing} → None, not rejected."""
        node = make_node({"image": "{state.missing}"}, registry)
        result = node({})

        assert result["out"]["result"]["received"] == {"image": None}

    @pytest.mark.req("REQ-YG-576")
    def test_embedded_missing_interpolation_raises(self, registry):
        """AC-04: resolved value still containing '{state.' is rejected."""
        node = make_node({"caption": "prefix {state.missing} suffix"}, registry)

        with pytest.raises(ValueError, match="describe.*caption|caption.*describe"):
            node({})

    @pytest.mark.req("REQ-YG-576")
    def test_empty_inline_dict_calls_tool_with_no_args(self, registry):
        """Empty inline mapping must NOT fall back to whole-state passing."""
        node = make_node({}, registry)
        result = node({"stray": "value"})

        assert result["out"]["result"]["received"] == {}


class TestStringFormUnchanged:
    @pytest.mark.req("REQ-YG-576")
    def test_string_form_still_resolves_dict_from_state(self, registry):
        node = make_node("{state.tool_args}", registry)
        result = node({"tool_args": {"image": "x.png"}})

        assert result["out"]["result"]["received"] == {"image": "x.png"}

    @pytest.mark.req("REQ-YG-576")
    def test_string_form_non_dict_still_falls_back_to_empty(self, registry):
        node = make_node("{state.not_a_dict}", registry)
        result = node({"not_a_dict": "scalar"})

        assert result["out"]["result"]["received"] == {}
