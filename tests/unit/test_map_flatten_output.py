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
        from yamlgraph.map_compiler import flatten_map_results

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
        from yamlgraph.map_compiler import flatten_map_results

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
        from yamlgraph.map_compiler import flatten_map_results

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
        from yamlgraph.map_compiler import flatten_map_results

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
        from yamlgraph.map_compiler import flatten_map_results

        items = [
            {"_map_index": 0, "directly_added": "value"},
        ]

        flattened = flatten_map_results(items)

        assert flattened[0] == {"_map_index": 0, "directly_added": "value"}

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_overwrites_input_fields(self):
        """Output fields should overwrite input fields on conflict."""
        from yamlgraph.map_compiler import flatten_map_results

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
        from yamlgraph.map_compiler import flatten_map_results

        assert flatten_map_results([]) == []

    @pytest.mark.req("REQ-YG-075")
    def test_flatten_output_preserves_other_fields(self):
        """Non-_map fields should be preserved (e.g., _error)."""
        from yamlgraph.map_compiler import flatten_map_results

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
