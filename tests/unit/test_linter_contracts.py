"""Tests for FR-061 contract violation lint rules.

E012: Hyphen in identifier position (state key, node name, tool name, state_key value)
W020: variables: on type: python (silent no-op)
W021: skip_if_exists on list field with add reducer
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.checks_contracts import (
    check_identifier_keys,
    check_python_node_variables,
    check_skip_if_exists_add_reducer,
)


def _create_temp_graph(graph_dict: dict) -> Path:
    """Create a temp YAML file from dict."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(graph_dict, f)
        return Path(f.name)


class TestW020PythonNodeVariables:
    """W020: variables on type: python is silently ignored."""

    @pytest.mark.req("REQ-YG-061")
    def test_python_node_with_variables_warns(self):
        """Python node with variables: should warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "my_python_node": {
                        "type": "python",
                        "function": "some_module.func",
                        "variables": {"topic": "state.topic"},
                    }
                }
            }
        )
        issues = check_python_node_variables(graph)
        assert len(issues) == 1
        assert issues[0].code == "W020"
        assert "my_python_node" in issues[0].message

    @pytest.mark.req("REQ-YG-061")
    def test_llm_node_with_variables_no_warn(self):
        """LLM node with variables: is valid, no warning."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "generate": {
                        "type": "llm",
                        "prompt": "generate.yaml",
                        "variables": {"topic": "state.topic"},
                    }
                }
            }
        )
        issues = check_python_node_variables(graph)
        assert len(issues) == 0


class TestE012HyphenInIdentifier:
    """E012: Hyphens in identifiers break Python."""

    @pytest.mark.req("REQ-YG-061")
    def test_state_key_with_hyphen_errors(self):
        """State key with hyphen should error."""
        graph = _create_temp_graph(
            {
                "state": {"my-key": "str"},
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_identifier_keys(graph)
        assert len(issues) == 1
        assert issues[0].code == "E012"
        assert "my-key" in issues[0].message
        assert "my_key" in issues[0].fix

    @pytest.mark.req("REQ-YG-061")
    def test_node_name_with_hyphen_errors(self):
        """Node name with hyphen should error."""
        graph = _create_temp_graph(
            {
                "nodes": {"my-node": {"type": "llm"}},
            }
        )
        issues = check_identifier_keys(graph)
        assert len(issues) == 1
        assert issues[0].code == "E012"
        assert "my-node" in issues[0].message
        assert "my_node" in issues[0].fix

    @pytest.mark.req("REQ-YG-061")
    def test_tool_name_with_hyphen_errors(self):
        """Tool name with hyphen should error."""
        graph = _create_temp_graph(
            {
                "tools": {"my-tool": {"function": "some.func"}},
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_identifier_keys(graph)
        assert len(issues) == 1
        assert issues[0].code == "E012"
        assert "my-tool" in issues[0].message

    @pytest.mark.req("REQ-YG-061")
    def test_state_key_value_with_hyphen_errors(self):
        """state_key value with hyphen should error."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "generate": {
                        "type": "llm",
                        "state_key": "my-output",
                    }
                },
            }
        )
        issues = check_identifier_keys(graph)
        assert len(issues) == 1
        assert issues[0].code == "E012"
        assert "my-output" in issues[0].message

    @pytest.mark.req("REQ-YG-061")
    def test_valid_identifiers_no_errors(self):
        """Valid identifiers (underscore) should pass."""
        graph = _create_temp_graph(
            {
                "state": {"my_key": "str"},
                "nodes": {"my_node": {"type": "llm", "state_key": "my_output"}},
                "tools": {"my_tool": {"function": "some.func"}},
            }
        )
        issues = check_identifier_keys(graph)
        assert len(issues) == 0


class TestW021SkipIfExistsAddReducer:
    """W021: skip_if_exists on list fields triggers after turn 1."""

    @pytest.mark.req("REQ-YG-061")
    def test_explicit_skip_if_exists_on_list_warns(self):
        """Explicit skip_if_exists: true on list field should warn."""
        graph = _create_temp_graph(
            {
                "state": {"messages": "list[str]"},
                "nodes": {
                    "chat": {
                        "type": "llm",
                        "state_key": "messages",
                        "skip_if_exists": True,
                    }
                },
            }
        )
        issues = check_skip_if_exists_add_reducer(graph)
        assert len(issues) == 1
        assert issues[0].code == "W021"
        assert "messages" in issues[0].message

    @pytest.mark.req("REQ-YG-061")
    def test_implicit_skip_if_exists_on_list_warns(self):
        """LLM node defaults to skip_if_exists: true — should warn on list."""
        graph = _create_temp_graph(
            {
                "state": {"messages": {"type": "list[str]"}},
                "nodes": {
                    "chat": {
                        "type": "llm",
                        "state_key": "messages",
                        # skip_if_exists defaults to True for LLM nodes
                    }
                },
            }
        )
        issues = check_skip_if_exists_add_reducer(graph)
        assert len(issues) == 1
        assert issues[0].code == "W021"

    @pytest.mark.req("REQ-YG-061")
    def test_skip_if_exists_false_on_list_no_warn(self):
        """Explicit skip_if_exists: false on list field should not warn."""
        graph = _create_temp_graph(
            {
                "state": {"messages": "list[str]"},
                "nodes": {
                    "chat": {
                        "type": "llm",
                        "state_key": "messages",
                        "skip_if_exists": False,
                    }
                },
            }
        )
        issues = check_skip_if_exists_add_reducer(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-061")
    def test_skip_if_exists_on_str_field_no_warn(self):
        """skip_if_exists on non-list field should not warn."""
        graph = _create_temp_graph(
            {
                "state": {"summary": "str"},
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "state_key": "summary",
                        "skip_if_exists": True,
                    }
                },
            }
        )
        issues = check_skip_if_exists_add_reducer(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-061")
    def test_python_node_implicit_skip_no_warn(self):
        """Python node doesn't default to skip_if_exists: true."""
        graph = _create_temp_graph(
            {
                "state": {"items": "list[str]"},
                "nodes": {
                    "process": {
                        "type": "python",
                        "function": "some.func",
                        "state_key": "items",
                        # No skip_if_exists — python nodes don't default True
                    }
                },
            }
        )
        issues = check_skip_if_exists_add_reducer(graph)
        assert len(issues) == 0
