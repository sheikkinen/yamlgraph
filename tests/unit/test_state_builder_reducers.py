"""Tests for user-configurable reducers in YAML state section (FR-238).

TDD: Red phase — these tests define the expected behavior for dict-syntax
state definitions with reducer configuration.
"""

import logging
from operator import add
from typing import Annotated, Any, get_args, get_origin

import pytest

from yamlgraph.models.state_builder import (
    build_state_class,
    last_value,
    parse_state_config,
    sorted_add,
)
from yamlgraph.models.state_codegen import generate_typeddict_code


class TestParseStateConfigDictSyntax:
    """Test dict-syntax state definitions with reducer configuration."""

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_with_add_reducer(self) -> None:
        """Dict-syntax with reducer: add produces Annotated[list, add]."""
        config = {"glossary": {"type": "list", "reducer": "add"}}
        fields = parse_state_config(config)

        assert "glossary" in fields
        field_type = fields["glossary"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is list
        assert args[1] is add

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_with_last_value_reducer(self) -> None:
        """Dict-syntax with reducer: last_value produces Annotated[str, last_value]."""
        config = {"current": {"type": "str", "reducer": "last_value"}}
        fields = parse_state_config(config)

        field_type = fields["current"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is str
        assert args[1] is last_value

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_with_sorted_add_reducer(self) -> None:
        """Dict-syntax with reducer: sorted_add produces Annotated[list, sorted_add]."""
        config = {"results": {"type": "list", "reducer": "sorted_add"}}
        fields = parse_state_config(config)

        field_type = fields["results"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is list
        assert args[1] is sorted_add

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_without_reducer(self) -> None:
        """Dict-syntax without reducer key works as type-only."""
        config = {"concept": {"type": "str"}}
        fields = parse_state_config(config)

        assert fields["concept"] is str

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_defaults_type_to_any(self) -> None:
        """Dict-syntax without type key defaults to Any."""
        config = {"flexible": {"reducer": "add"}}
        fields = parse_state_config(config)

        field_type = fields["flexible"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is Any
        assert args[1] is add

    @pytest.mark.req("REQ-YG-241")
    def test_unknown_reducer_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unknown reducer name logs a warning and omits reducer."""
        config = {"data": {"type": "list", "reducer": "nonexistent"}}
        # yamlgraph logger has propagate=False; temporarily enable for caplog
        parent_logger = logging.getLogger("yamlgraph")
        original_propagate = parent_logger.propagate
        parent_logger.propagate = True
        try:
            with caplog.at_level(
                logging.WARNING, logger="yamlgraph.models.state_builder"
            ):
                fields = parse_state_config(config)

            assert fields["data"] is list
            assert "Unknown reducer 'nonexistent'" in caplog.text
            assert "add" in caplog.text  # lists supported reducers
        finally:
            parent_logger.propagate = original_propagate

    @pytest.mark.req("REQ-YG-241")
    def test_simple_string_syntax_unchanged(self) -> None:
        """Simple string syntax continues to work (no regression)."""
        config = {"name": "str", "count": "int", "items": "list"}
        fields = parse_state_config(config)

        assert fields["name"] is str
        assert fields["count"] is int
        assert fields["items"] is list

    @pytest.mark.req("REQ-YG-241")
    def test_mixed_string_and_dict_syntax(self) -> None:
        """Mixed simple strings and dict-syntax in same state config."""
        config = {
            "title": "str",
            "glossary": {"type": "list", "reducer": "add"},
            "count": "int",
        }
        fields = parse_state_config(config)

        assert fields["title"] is str
        assert fields["count"] is int
        field_type = fields["glossary"]
        assert get_origin(field_type) is Annotated
        args = get_args(field_type)
        assert args[0] is list
        assert args[1] is add


class TestReducerMapCompleteness:
    """Verify REDUCER_MAP contains all three built-in reducers."""

    @pytest.mark.req("REQ-YG-241")
    def test_reducer_map_has_add(self) -> None:
        """REDUCER_MAP contains 'add' mapping to operator.add."""
        from yamlgraph.models.state_builder import REDUCER_MAP

        assert "add" in REDUCER_MAP
        assert REDUCER_MAP["add"] is add

    @pytest.mark.req("REQ-YG-241")
    def test_reducer_map_has_last_value(self) -> None:
        """REDUCER_MAP contains 'last_value' mapping to last_value function."""
        from yamlgraph.models.state_builder import REDUCER_MAP

        assert "last_value" in REDUCER_MAP
        assert REDUCER_MAP["last_value"] is last_value

    @pytest.mark.req("REQ-YG-241")
    def test_reducer_map_has_sorted_add(self) -> None:
        """REDUCER_MAP contains 'sorted_add' mapping to sorted_add function."""
        from yamlgraph.models.state_builder import REDUCER_MAP

        assert "sorted_add" in REDUCER_MAP
        assert REDUCER_MAP["sorted_add"] is sorted_add


class TestGenerateTypedDictCodeDictSyntax:
    """Test generate_typeddict_code handles dict-syntax state entries."""

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_extracts_type_string(self) -> None:
        """Dict-syntax state entries appear in generated code with correct type."""
        config = {
            "name": "test-graph",
            "state": {
                "glossary": {"type": "list", "reducer": "add"},
            },
            "nodes": {},
        }
        code = generate_typeddict_code(config)

        assert "glossary: list" in code

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_type_only(self) -> None:
        """Dict-syntax without reducer still generates type string."""
        config = {
            "name": "test-graph",
            "state": {
                "concept": {"type": "str"},
            },
            "nodes": {},
        }
        code = generate_typeddict_code(config)

        assert "concept: str" in code

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_defaults_to_any(self) -> None:
        """Dict-syntax without type key generates Any."""
        config = {
            "name": "test-graph",
            "state": {
                "flexible": {"reducer": "add"},
            },
            "nodes": {},
        }
        code = generate_typeddict_code(config)

        assert "flexible: Any" in code

    @pytest.mark.req("REQ-YG-241")
    def test_mixed_string_and_dict_in_codegen(self) -> None:
        """Both string and dict-syntax appear in generated code."""
        config = {
            "name": "test-graph",
            "state": {
                "title": "str",
                "glossary": {"type": "list", "reducer": "add"},
            },
            "nodes": {},
        }
        code = generate_typeddict_code(config)

        assert "title: str" in code
        assert "glossary: list" in code


class TestBuildStateClassDictSyntax:
    """Test build_state_class integrates dict-syntax state definitions."""

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_with_reducer_in_built_state(self) -> None:
        """Dict-syntax reducer config flows through build_state_class."""
        config = {
            "state": {
                "glossary": {"type": "list", "reducer": "add"},
            },
            "nodes": {},
            "edges": [],
        }
        State = build_state_class(config)

        glossary_type = State.__annotations__["glossary"]
        assert get_origin(glossary_type) is Annotated
        args = get_args(glossary_type)
        assert args[0] is list
        assert args[1] is add

    @pytest.mark.req("REQ-YG-241")
    def test_dict_syntax_reducer_works_with_langgraph(self) -> None:
        """State with user-configured reducer accumulates in LangGraph."""
        from langgraph.graph import StateGraph

        config = {
            "state": {
                "glossary": {"type": "list", "reducer": "add"},
            },
            "nodes": {},
            "edges": [],
        }
        State = build_state_class(config)

        graph = StateGraph(State)
        graph.add_node("n1", lambda s: {"glossary": ["term_a"]})
        graph.add_node("n2", lambda s: {"glossary": ["term_b"]})
        graph.add_edge("n1", "n2")
        graph.set_entry_point("n1")
        graph.set_finish_point("n2")
        compiled = graph.compile()

        result = compiled.invoke({})
        assert result["glossary"] == ["term_a", "term_b"]
