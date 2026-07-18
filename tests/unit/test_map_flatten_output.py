"""Tests for map node flatten_output option (FR-052).

Tests that flatten_output: true merges _map_xxx_sub contents into items,
making downstream nodes easier to write.
"""

import pytest
from pydantic import BaseModel


class TestFlattenOutput:
    """Tests for flatten_output option in map nodes."""

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_merges_sub_key_into_item(self):
        """flatten_output: true should merge _map_xxx_sub contents into item."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        items = [
            {"_map_index": 0, "_map_analyze_sub": {"score": 0.8, "title": "Hello"}},
            {"_map_index": 1, "_map_analyze_sub": {"score": 0.3, "title": "World"}},
        ]

        flattened = flatten_map_results(items)

        assert flattened[0] == {"_map_index": 0, "score": 0.8, "title": "Hello"}
        assert flattened[1] == {"_map_index": 1, "score": 0.3, "title": "World"}

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_preserves_map_index(self):
        """_map_index should always be preserved after flattening."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        items = [
            {"_map_index": 2, "_map_node_sub": {"value": "test"}},
        ]

        flattened = flatten_map_results(items)

        assert flattened[0]["_map_index"] == 2
        assert flattened[0]["value"] == "test"
        assert "_map_node_sub" not in flattened[0]

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_converts_pydantic_models(self):
        """Pydantic models in _map_xxx_sub should be converted to dicts."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        class Result(BaseModel):
            name: str
            score: float

        items = [
            {"_map_index": 0, "_map_process_sub": Result(name="test", score=0.9)},
        ]

        flattened = flatten_map_results(items)

        assert flattened[0]["name"] == "test"
        assert flattened[0]["score"] == 0.9
        assert "_map_process_sub" not in flattened[0]

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_noop_for_scalars(self):
        """Scalars in _map_xxx_sub should be kept as-is (no-op)."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        items = [
            {"_map_index": 0, "_map_compute_sub": 42},
            {"_map_index": 1, "_map_compute_sub": "hello"},
        ]

        flattened = flatten_map_results(items)

        # Scalars can't be flattened - keep wrapper
        assert flattened[0]["_map_compute_sub"] == 42
        assert flattened[1]["_map_compute_sub"] == "hello"

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_no_sub_key(self):
        """Items without _map_xxx_sub key should pass through unchanged."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        items = [
            {"_map_index": 0, "directly_added": "value"},
        ]

        flattened = flatten_map_results(items)

        assert flattened[0] == {"_map_index": 0, "directly_added": "value"}

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_overwrites_input_fields(self):
        """Output fields should overwrite input fields on conflict."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        items = [
            {
                "_map_index": 0,
                "title": "original",  # Input field
                "_map_analyze_sub": {"title": "updated", "score": 0.8},  # Output field
            },
        ]

        flattened = flatten_map_results(items)

        # Output overwrites input
        assert flattened[0]["title"] == "updated"
        assert flattened[0]["score"] == 0.8

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_empty_list(self):
        """Empty list should return empty list."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        assert flatten_map_results([]) == []

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_preserves_other_fields(self):
        """Non-_map fields should be preserved (e.g., _error)."""
        from yamlgraph.compile.map_compiler import flatten_map_results

        items = [
            {
                "_map_index": 0,
                "_map_process_sub": {"result": "ok"},
                "_error": None,
                "extra": "data",
            },
        ]

        flattened = flatten_map_results(items)

        assert flattened[0]["_map_index"] == 0
        assert flattened[0]["result"] == "ok"
        assert flattened[0]["_error"] is None
        assert flattened[0]["extra"] == "data"
        assert "_map_process_sub" not in flattened[0]


class TestWrapForReducerFlatten:
    """Tests for wrap_for_reducer with flatten_output option."""

    @pytest.mark.req("REQ-YG-075")
    def test_wrap_for_reducer_flatten_output_merges_sub_key(self):
        """wrap_for_reducer with flatten_output=True should flatten results."""
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        def node_fn(state: dict) -> dict:
            return {"result": {"score": 0.8, "tag": "relevant"}}

        wrapped = wrap_for_reducer(node_fn, "collected", "result", flatten_output=True)
        result = wrapped({"_map_index": 0, "item": "test"})

        # Should be flattened - no _map_xxx_sub wrapper
        assert result == {
            "collected": [{"_map_index": 0, "score": 0.8, "tag": "relevant"}]
        }

    @pytest.mark.req("REQ-YG-075")
    def test_wrap_for_reducer_flatten_output_false_preserves_structure(self):
        """wrap_for_reducer with flatten_output=False (default) preserves structure."""
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        def node_fn(state: dict) -> dict:
            return {"result": {"score": 0.8, "tag": "relevant"}}

        wrapped = wrap_for_reducer(node_fn, "collected", "result", flatten_output=False)
        result = wrapped({"_map_index": 0, "item": "test"})

        # Should have normal flattened output (no _map_xxx_sub key in this case
        # because result.get("result") extracts the dict directly)
        assert result == {
            "collected": [{"_map_index": 0, "score": 0.8, "tag": "relevant"}]
        }

    @pytest.mark.req("REQ-YG-075")
    def test_wrap_for_reducer_flatten_with_default_state_key_mismatch(self):
        """Test flattening when state_key doesn't match node output.

        This simulates the real bug: sub-node defaults state_key to node_name,
        but wrap_for_reducer defaults to "result". The result is the full
        dict gets included as extracted value with the node_name key.
        """
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        def node_fn(state: dict) -> dict:
            # Simulates what create_node_function produces when state_key
            # defaults to node_name (e.g., "_map_analyze_sub")
            return {"_map_analyze_sub": {"score": 0.8, "tag": "relevant"}}

        # state_key="result" doesn't exist, so extracted = full dict
        wrapped = wrap_for_reducer(node_fn, "collected", "result", flatten_output=True)
        result = wrapped({"_map_index": 0, "item": "test"})

        # With flatten_output=True, the _map_analyze_sub contents are merged
        assert result == {
            "collected": [{"_map_index": 0, "score": 0.8, "tag": "relevant"}]
        }

    @pytest.mark.req("REQ-YG-075")
    def test_wrap_for_reducer_flatten_without_mismatch(self):
        """Without flatten_output, the _map_xxx_sub key is preserved."""
        from yamlgraph.compile.map_compiler import wrap_for_reducer

        def node_fn(state: dict) -> dict:
            return {"_map_analyze_sub": {"score": 0.8, "tag": "relevant"}}

        wrapped = wrap_for_reducer(node_fn, "collected", "result", flatten_output=False)
        result = wrapped({"_map_index": 0, "item": "test"})

        # Without flatten_output, the full dict is included with the key
        assert result == {
            "collected": [
                {"_map_index": 0, "_map_analyze_sub": {"score": 0.8, "tag": "relevant"}}
            ]
        }
