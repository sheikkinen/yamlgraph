"""Tests for FR-050: skip_if_exists truthiness behavior.

The skip_if_exists option should check truthiness, not existence.
Empty collections ([], {}), empty strings (""), None, 0, and False
should NOT trigger skip — only truthy values should.
"""

import pytest


class TestSkipIfExistsTruthiness:
    """Tests for skip_if_exists truthiness semantics."""

    @pytest.mark.req("REQ-YG-074")
    def test_empty_list_does_not_skip(self):
        """Empty list [] should NOT trigger skip — it's falsy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "seeds", {"seeds": []}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_populated_list_skips(self):
        """Non-empty list should trigger skip — it's truthy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "seeds", {"seeds": ["question?"]}) is True

    @pytest.mark.req("REQ-YG-074")
    def test_none_does_not_skip(self):
        """None should NOT trigger skip — it's falsy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "output", {"output": None}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_missing_key_does_not_skip(self):
        """Missing key should NOT trigger skip."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "seeds", {}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_empty_string_does_not_skip(self):
        """Empty string should NOT trigger skip — it's falsy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "output", {"output": ""}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_non_empty_string_skips(self):
        """Non-empty string should trigger skip — it's truthy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "output", {"output": "hello"}) is True

    @pytest.mark.req("REQ-YG-074")
    def test_zero_does_not_skip(self):
        """Zero should NOT trigger skip — it's falsy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "count", {"count": 0}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_non_zero_number_skips(self):
        """Non-zero number should trigger skip — it's truthy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "count", {"count": 42}) is True

    @pytest.mark.req("REQ-YG-074")
    def test_false_does_not_skip(self):
        """False should NOT trigger skip — it's falsy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "done", {"done": False}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_true_skips(self):
        """True should trigger skip — it's truthy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "done", {"done": True}) is True

    @pytest.mark.req("REQ-YG-074")
    def test_empty_dict_does_not_skip(self):
        """Empty dict {} should NOT trigger skip — it's falsy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "data", {"data": {}}) is False

    @pytest.mark.req("REQ-YG-074")
    def test_populated_dict_skips(self):
        """Non-empty dict should trigger skip — it's truthy."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        assert _should_skip_if_exists(True, "data", {"data": {"key": "value"}}) is True

    @pytest.mark.req("REQ-YG-074")
    def test_skip_if_exists_disabled(self):
        """skip_if_exists=False should never skip."""
        from yamlgraph.node_factory.llm_nodes import _should_skip_if_exists

        # Even with truthy value, should not skip when disabled
        assert _should_skip_if_exists(False, "seeds", {"seeds": ["data"]}) is False
