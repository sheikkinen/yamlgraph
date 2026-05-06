"""Tests for FR-061 contract violation lint rules.

E012: Hyphen in identifier position (state key, node name, tool name, state_key value)
W021: skip_if_exists on list field with add reducer
W017: on_error: skip silently drops failures (FR-165)

Note: W020 (variables: on type: python) removed by FR-252 — python nodes
now resolve variables: expressions.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from yamlgraph.linter.checks_contracts import (
    check_guard_expressions,
    check_identifier_keys,
    check_python_node_variables,
    check_silent_fallback,
    check_skip_if_exists_add_reducer,
    check_top_level_provider_model,
)


def _create_temp_graph(graph_dict: dict) -> Path:
    """Create a temp YAML file from dict."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(graph_dict, f)
        return Path(f.name)


class TestW020PythonNodeVariables:
    """W020: variables on type: python — now resolved at runtime (FR-252)."""

    @pytest.mark.req("REQ-YG-061")
    def test_python_node_with_variables_no_warn(self):
        """Python node with variables: is valid after FR-252, no warning."""
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
        assert len(issues) == 0

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


class TestW016TopLevelProviderModel:
    """W016: provider/model at top level is silently ignored."""

    @pytest.mark.req("REQ-YG-003")
    def test_provider_at_top_level_only_warns(self):
        """Top-level provider without defaults should warn to move."""
        graph = _create_temp_graph(
            {
                "provider": "anthropic",
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 1
        assert issues[0].code == "W016"
        assert issues[0].severity == "warning"
        assert "'provider' at top level has no effect" in issues[0].message
        assert "defaults:" in issues[0].message

    @pytest.mark.req("REQ-YG-003")
    def test_model_at_top_level_only_warns(self):
        """Top-level model without defaults should warn to move."""
        graph = _create_temp_graph(
            {
                "model": "claude-haiku-4-5",
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 1
        assert issues[0].code == "W016"
        assert "'model' at top level has no effect" in issues[0].message

    @pytest.mark.req("REQ-YG-003")
    def test_both_provider_and_model_at_top_level_warns(self):
        """Both keys at top level should produce two warnings."""
        graph = _create_temp_graph(
            {
                "provider": "anthropic",
                "model": "claude-haiku-4-5",
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 2
        codes = {i.code for i in issues}
        assert codes == {"W016"}

    @pytest.mark.req("REQ-YG-003")
    def test_top_level_and_defaults_duplicate_warns(self):
        """Key at both top level and defaults should warn to remove top-level."""
        graph = _create_temp_graph(
            {
                "provider": "anthropic",
                "defaults": {"provider": "anthropic"},
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 1
        assert issues[0].code == "W016"
        assert "already set" in issues[0].message
        assert "remove" in issues[0].fix.lower()

    @pytest.mark.req("REQ-YG-003")
    def test_only_in_defaults_no_warning(self):
        """Keys only in defaults block should not warn."""
        graph = _create_temp_graph(
            {
                "defaults": {"provider": "anthropic", "model": "claude-haiku-4-5"},
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-003")
    def test_only_at_node_level_no_warning(self):
        """Keys only at node level should not warn."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "generate": {
                        "type": "llm",
                        "provider": "openai",
                        "model": "gpt-4",
                    }
                },
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-003")
    def test_neither_key_present_no_warning(self):
        """No provider/model anywhere should not warn."""
        graph = _create_temp_graph(
            {
                "nodes": {"generate": {"type": "llm"}},
            }
        )
        issues = check_top_level_provider_model(graph)
        assert len(issues) == 0


class TestW017SilentFallback:
    """W017: on_error: skip silently drops failures (FR-165)."""

    @pytest.mark.req("REQ-YG-114")
    def test_on_error_skip_warns(self):
        """Node with on_error: skip should produce W017 warning."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                        "on_error": "skip",
                    }
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 1
        assert issues[0].code == "W017"
        assert issues[0].severity == "warning"
        assert "summarize" in issues[0].message
        assert "silently dropped" in issues[0].message

    @pytest.mark.req("REQ-YG-114")
    def test_multiple_skip_nodes_warn(self):
        """Multiple nodes with on_error: skip should each produce a warning."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "fetch": {
                        "type": "python",
                        "function": "tools.fetch",
                        "on_error": "skip",
                    },
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                        "on_error": "skip",
                    },
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 2
        assert all(i.code == "W017" for i in issues)
        node_names = {i.message.split("'")[1] for i in issues}
        assert node_names == {"fetch", "summarize"}

    @pytest.mark.req("REQ-YG-114")
    def test_on_error_fail_no_warn(self):
        """on_error: fail should not produce W017."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                        "on_error": "fail",
                    }
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-114")
    def test_on_error_fallback_no_warn(self):
        """on_error: fallback should not produce W017."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                        "on_error": "fallback",
                        "fallback": {"provider": "openai"},
                    }
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-114")
    def test_on_error_retry_no_warn(self):
        """on_error: retry should not produce W017."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                        "on_error": "retry",
                    }
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-114")
    def test_no_on_error_no_warn(self):
        """Node without on_error should not produce W017."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                    }
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 0

    @pytest.mark.req("REQ-YG-114")
    def test_fix_suggests_alternatives(self):
        """W017 fix should suggest explicit alternatives."""
        graph = _create_temp_graph(
            {
                "nodes": {
                    "summarize": {
                        "type": "llm",
                        "prompt": "summarize",
                        "on_error": "skip",
                    }
                }
            }
        )
        issues = check_silent_fallback(graph)
        assert len(issues) == 1
        assert "on_error: fail" in issues[0].fix
        assert "on_error: fallback" in issues[0].fix


@pytest.mark.req("REQ-YG-154")
def test_w025_invalid_guard_expression_warning():
    """W025 warns for invalid guard expression syntax/filter usage."""
    graph = _create_temp_graph(
        {
            "nodes": {
                "guarded": {
                    "type": "llm",
                    "prompt": "generate",
                    "guards": {
                        "pre": [
                            {
                                "check": "state.path | unknown_filter",
                                "on_fail": "halt",
                            }
                        ]
                    },
                }
            }
        }
    )
    issues = check_guard_expressions(graph)
    assert any(i.code == "W025" for i in issues)
    assert any("invalid guard expression" in i.message for i in issues)
