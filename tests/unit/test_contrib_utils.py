"""Tests for yamlgraph.contrib.utils module (FR-044 Phase 1).

Tests for shared utilities extracted from pipeline patterns:
- to_serializable: convert Pydantic models to dicts recursively
"""

import pytest
from pydantic import BaseModel


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
