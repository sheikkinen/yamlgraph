"""FR-659: Coverage gaps in schema_loader_tool.py (83% → ≥90%).

Tests for uncovered validation branches in parse_schema_loader_tools,
_load_yaml_schema error paths, _coerce_state, _deduplicate_fields,
and _build_merge_mode runtime type checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.tools.schema_loader_tool import (
    SchemaLoaderToolConfig,
    _coerce_state,
    _deduplicate_fields,
    _load_yaml_schema,
    _resolve_schema_path,
    build_schema_loader_tool,
    parse_schema_loader_tools,
)

# ---------------------------------------------------------------------------
# parse_schema_loader_tools validation branches
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-417")
class TestParseValidation:
    """Cover validation error branches in parse_schema_loader_tools."""

    def test_missing_state_key_raises(self):
        with pytest.raises(ValueError, match="state_key"):
            parse_schema_loader_tools(
                {"t": {"type": "schema_loader", "path": "x.yaml"}}
            )

    def test_empty_state_key_raises(self):
        with pytest.raises(ValueError, match="state_key"):
            parse_schema_loader_tools(
                {"t": {"type": "schema_loader", "path": "x.yaml", "state_key": ""}}
            )

    def test_invalid_suffix_raises(self):
        with pytest.raises(ValueError, match="suffix"):
            parse_schema_loader_tools(
                {
                    "t": {
                        "type": "schema_loader",
                        "path": "x.yaml",
                        "state_key": "s",
                        "suffix": "",
                    }
                }
            )

    def test_invalid_deduplicate_by_raises(self):
        with pytest.raises(ValueError, match="deduplicate_by"):
            parse_schema_loader_tools(
                {
                    "t": {
                        "type": "schema_loader",
                        "path": "x.yaml",
                        "state_key": "s",
                        "deduplicate_by": "",
                    }
                }
            )

    def test_unsupported_merge_mode_raises(self):
        with pytest.raises(ValueError, match="merge_mode"):
            parse_schema_loader_tools(
                {
                    "t": {
                        "type": "schema_loader",
                        "path": "x.yaml",
                        "state_key": "s",
                        "merge_mode": "replace",
                    }
                }
            )

    def test_missing_schema_dir_with_paths_from_state_raises(self):
        with pytest.raises(ValueError, match="schema_dir"):
            parse_schema_loader_tools(
                {
                    "t": {
                        "type": "schema_loader",
                        "paths_from_state": "topics",
                        "state_key": "s",
                    }
                }
            )

    def test_neither_path_nor_paths_from_state_raises(self):
        with pytest.raises(ValueError, match="exactly one"):
            parse_schema_loader_tools(
                {"t": {"type": "schema_loader", "state_key": "s"}}
            )


# ---------------------------------------------------------------------------
# _resolve_schema_path
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-418")
class TestResolveSchemaPath:
    """Cover path escape detection."""

    def test_path_escape_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="escapes graph directory"):
            _resolve_schema_path(tmp_path, "../outside.yaml", tool_name="t")

    def test_valid_path_resolves(self, tmp_path: Path):
        result = _resolve_schema_path(tmp_path, "schemas/x.yaml", tool_name="t")
        assert result == (tmp_path / "schemas" / "x.yaml").resolve()


# ---------------------------------------------------------------------------
# _load_yaml_schema error paths
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-418")
class TestLoadYamlSchema:
    """Cover error branches in _load_yaml_schema."""

    def test_file_not_found_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="not found"):
            _load_yaml_schema(tmp_path, "missing.yaml", tool_name="t")

    def test_invalid_yaml_raises(self, tmp_path: Path):
        (tmp_path / "bad.yaml").write_text(":\n  :\n    - [broken", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid YAML"):
            _load_yaml_schema(tmp_path, "bad.yaml", tool_name="t")

    def test_non_dict_content_raises(self, tmp_path: Path):
        (tmp_path / "list.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(TypeError, match="must contain a mapping"):
            _load_yaml_schema(tmp_path, "list.yaml", tool_name="t")

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path):
        (tmp_path / "empty.yaml").write_text("", encoding="utf-8")
        result = _load_yaml_schema(tmp_path, "empty.yaml", tool_name="t")
        assert result == {}


# ---------------------------------------------------------------------------
# _coerce_state
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-418")
class TestCoerceState:
    """Cover _coerce_state kwargs fallback."""

    def test_dict_state_returned(self):
        state = {"key": "val"}
        assert _coerce_state(state, {"other": "x"}) is state

    def test_none_state_returns_kwargs(self):
        kwargs = {"key": "val"}
        assert _coerce_state(None, kwargs) is kwargs

    def test_non_dict_state_returns_kwargs(self):
        kwargs = {"key": "val"}
        assert _coerce_state("not a dict", kwargs) is kwargs


# ---------------------------------------------------------------------------
# _deduplicate_fields
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-418")
class TestDeduplicateFields:
    """Cover error branches in _deduplicate_fields."""

    def test_non_dict_field_raises(self):
        with pytest.raises(TypeError, match="must be a mapping"):
            _deduplicate_fields(["not_a_dict"], deduplicate_by="id", tool_name="t")

    def test_missing_dedup_key_raises(self):
        with pytest.raises(KeyError, match="missing deduplicate key"):
            _deduplicate_fields([{"name": "x"}], deduplicate_by="id", tool_name="t")

    def test_dedup_removes_duplicates(self):
        result = _deduplicate_fields(
            [{"id": "a"}, {"id": "b"}, {"id": "a"}],
            deduplicate_by="id",
            tool_name="t",
        )
        assert [f["id"] for f in result] == ["a", "b"]


# ---------------------------------------------------------------------------
# _build_merge_mode runtime errors
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-418")
class TestBuildMergeModeRuntime:
    """Cover runtime type check branches in merge mode."""

    def _make_merge_fn(self, tmp_path: Path):
        """Create a merge-mode callable with a valid schema dir."""
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "topic1.yaml").write_text(
            "fields:\n  - id: f1\n", encoding="utf-8"
        )
        config = SchemaLoaderToolConfig(
            state_key="schema",
            paths_from_state="topics",
            schema_dir="schemas",
        )
        return build_schema_loader_tool("t", config, graph_root=tmp_path)

    def test_non_list_topics_raises(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        with pytest.raises(TypeError, match="to be list"):
            fn({"topics": "not_a_list", "schema": {}})

    def test_non_dict_existing_schema_raises(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        with pytest.raises(TypeError, match="to be dict"):
            fn({"topics": ["topic1"], "schema": "not_a_dict"})

    def test_non_string_topic_raises(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        with pytest.raises(TypeError, match="non-empty string"):
            fn({"topics": [123], "schema": {}})

    def test_empty_string_topic_raises(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        with pytest.raises(TypeError, match="non-empty string"):
            fn({"topics": [""], "schema": {}})

    def test_non_list_existing_fields_raises(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        with pytest.raises(TypeError, match="fields must be list"):
            fn({"topics": ["topic1"], "schema": {"fields": "not_a_list"}})

    def test_null_existing_fields_treated_as_empty(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        result = fn({"topics": ["topic1"], "schema": {"fields": None}})
        assert result["schema"]["fields"] == [{"id": "f1"}]

    def test_null_existing_schema_treated_as_empty(self, tmp_path: Path):
        fn = self._make_merge_fn(tmp_path)
        result = fn({"topics": ["topic1"], "schema": None})
        assert result["schema"]["fields"] == [{"id": "f1"}]
