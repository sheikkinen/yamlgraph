"""Tests for yamlgraph.contrib.utils module (FR-044 Phase 1).

Tests for shared utilities extracted from pipeline patterns:
- get_map_result: unwrap single-key _map_*_sub dicts from map output
- to_serializable: convert Pydantic models to dicts recursively
"""

import pytest
from pydantic import BaseModel


class TestGetMapResult:
    """Tests for get_map_result helper function."""

    @pytest.mark.req("REQ-YG-070")
    def test_extracts_value_from_map_key(self):
        """Should extract value from _map_*_sub key."""
        from yamlgraph.contrib.utils import get_map_result

        item = {"_map_generate_sub": {"title": "Hello", "content": "World"}}
        result = get_map_result(item)
        assert result == {"title": "Hello", "content": "World"}

    @pytest.mark.req("REQ-YG-070")
    def test_returns_none_for_none_input(self):
        """Should return None for None input."""
        from yamlgraph.contrib.utils import get_map_result

        assert get_map_result(None) is None

    @pytest.mark.req("REQ-YG-070")
    def test_returns_none_for_non_dict(self):
        """Should return None for non-dict inputs."""
        from yamlgraph.contrib.utils import get_map_result

        assert get_map_result("string") is None
        assert get_map_result(123) is None
        assert get_map_result([1, 2, 3]) is None

    @pytest.mark.req("REQ-YG-070")
    def test_returns_none_for_empty_dict(self):
        """Should return None for empty dict."""
        from yamlgraph.contrib.utils import get_map_result

        assert get_map_result({}) is None

    @pytest.mark.req("REQ-YG-070")
    def test_returns_none_for_dict_without_map_key(self):
        """Should return None for dict without _map_*_sub key."""
        from yamlgraph.contrib.utils import get_map_result

        assert get_map_result({"title": "Hello"}) is None
        assert get_map_result({"_other_key": "value"}) is None

    @pytest.mark.req("REQ-YG-070")
    def test_handles_pydantic_model_value(self):
        """Should work when value is a Pydantic model."""
        from yamlgraph.contrib.utils import get_map_result

        class Item(BaseModel):
            name: str

        item = {"_map_node_sub": Item(name="test")}
        result = get_map_result(item)
        assert isinstance(result, Item)
        assert result.name == "test"


class TestToSerializable:
    """Tests for to_serializable function."""

    @pytest.mark.req("REQ-YG-070")
    def test_converts_pydantic_model_to_dict(self):
        """Should convert Pydantic model to dict."""
        from yamlgraph.contrib.utils import to_serializable

        class Item(BaseModel):
            name: str
            count: int

        model = Item(name="test", count=42)
        result = to_serializable(model)
        assert result == {"name": "test", "count": 42}
        assert isinstance(result, dict)

    @pytest.mark.req("REQ-YG-070")
    def test_returns_primitives_unchanged(self):
        """Should return primitives unchanged."""
        from yamlgraph.contrib.utils import to_serializable

        assert to_serializable("string") == "string"
        assert to_serializable(42) == 42
        assert to_serializable(3.14) == 3.14
        assert to_serializable(True) is True
        assert to_serializable(None) is None

    @pytest.mark.req("REQ-YG-070")
    def test_converts_nested_pydantic_models(self):
        """Should recursively convert nested Pydantic models."""
        from yamlgraph.contrib.utils import to_serializable

        class Inner(BaseModel):
            value: int

        class Outer(BaseModel):
            inner: Inner
            name: str

        model = Outer(inner=Inner(value=10), name="outer")
        result = to_serializable(model)
        assert result == {"inner": {"value": 10}, "name": "outer"}

    @pytest.mark.req("REQ-YG-070")
    def test_converts_list_of_pydantic_models(self):
        """Should convert list containing Pydantic models."""
        from yamlgraph.contrib.utils import to_serializable

        class Item(BaseModel):
            id: int

        items = [Item(id=1), Item(id=2), Item(id=3)]
        result = to_serializable(items)
        assert result == [{"id": 1}, {"id": 2}, {"id": 3}]

    @pytest.mark.req("REQ-YG-070")
    def test_converts_dict_with_pydantic_values(self):
        """Should convert dict values that are Pydantic models."""
        from yamlgraph.contrib.utils import to_serializable

        class Item(BaseModel):
            name: str

        data = {"a": Item(name="first"), "b": Item(name="second")}
        result = to_serializable(data)
        assert result == {"a": {"name": "first"}, "b": {"name": "second"}}

    @pytest.mark.req("REQ-YG-070")
    def test_handles_mixed_nested_structures(self):
        """Should handle deeply nested mixed structures."""
        from yamlgraph.contrib.utils import to_serializable

        class Item(BaseModel):
            value: str

        data = {
            "items": [Item(value="a"), {"nested": Item(value="b")}],
            "plain": "string",
            "number": 42,
        }
        result = to_serializable(data)
        assert result == {
            "items": [{"value": "a"}, {"nested": {"value": "b"}}],
            "plain": "string",
            "number": 42,
        }
