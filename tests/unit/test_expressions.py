"""Tests for state expression resolution."""

import pytest

from showcase.utils.expressions import resolve_state_expression


class TestResolveStateExpression:
    """Tests for resolve_state_expression function."""

    def test_simple_key(self):
        """Resolve simple state key."""
        state = {"name": "test"}
        result = resolve_state_expression("{name}", state)
        assert result == "test"

    def test_nested_path(self):
        """Resolve nested path like {state.story.panels}."""
        state = {"story": {"panels": ["a", "b", "c"]}}
        result = resolve_state_expression("{state.story.panels}", state)
        assert result == ["a", "b", "c"]

    def test_state_prefix_stripped(self):
        """The 'state.' prefix is optional and stripped."""
        state = {"story": {"title": "My Story"}}
        # With prefix
        assert resolve_state_expression("{state.story.title}", state) == "My Story"
        # Without prefix
        assert resolve_state_expression("{story.title}", state) == "My Story"

    def test_literal_passthrough(self):
        """Non-expression strings pass through unchanged."""
        result = resolve_state_expression("literal string", {})
        assert result == "literal string"

    def test_non_string_passthrough(self):
        """Non-string values pass through unchanged."""
        result = resolve_state_expression(42, {})
        assert result == 42

    def test_missing_key_raises(self):
        """Missing key raises KeyError."""
        state = {"foo": "bar"}
        with pytest.raises(KeyError):
            resolve_state_expression("{missing}", state)

    def test_missing_nested_key_raises(self):
        """Missing nested key raises KeyError."""
        state = {"story": {"title": "test"}}
        with pytest.raises(KeyError):
            resolve_state_expression("{story.panels}", state)

    def test_deeply_nested_path(self):
        """Resolve deeply nested paths."""
        state = {"a": {"b": {"c": {"d": "deep"}}}}
        result = resolve_state_expression("{a.b.c.d}", state)
        assert result == "deep"

    def test_list_result(self):
        """Can resolve to list values."""
        state = {"items": [1, 2, 3]}
        result = resolve_state_expression("{items}", state)
        assert result == [1, 2, 3]

    def test_dict_result(self):
        """Can resolve to dict values."""
        state = {"config": {"key": "value"}}
        result = resolve_state_expression("{config}", state)
        assert result == {"key": "value"}

    def test_object_attribute_access(self):
        """Can resolve object attributes (Pydantic models)."""

        class MockModel:
            def __init__(self):
                self.title = "Test Title"
                self.panels = ["panel 1", "panel 2"]

        state = {"story": MockModel()}
        result = resolve_state_expression("{state.story.panels}", state)
        assert result == ["panel 1", "panel 2"]

    def test_mixed_dict_and_object_access(self):
        """Can resolve mixed dict and object paths."""

        class Inner:
            def __init__(self):
                self.value = "found"

        state = {"outer": {"middle": Inner()}}
        result = resolve_state_expression("{outer.middle.value}", state)
        assert result == "found"
