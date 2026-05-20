"""RED acceptance tests for FR-426 schema_loader tool type."""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.graph_loader import load_and_compile


def _write_graph(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


@pytest.mark.req("REQ-YG-417")
def test_ac01_parse_schema_loader_tool_type_returns_typed_config() -> None:
    from yamlgraph.tools.schema_loader_tool import (
        SchemaLoaderToolConfig,
        parse_schema_loader_tools,
    )

    tools_config = {
        "load_fields": {
            "type": "schema_loader",
            "path": "schemas/symptom.yaml",
            "state_key": "schema",
        }
    }

    parsed = parse_schema_loader_tools(tools_config)

    assert isinstance(parsed["load_fields"], SchemaLoaderToolConfig)
    assert parsed["load_fields"].path == "schemas/symptom.yaml"
    assert parsed["load_fields"].state_key == "schema"


@pytest.mark.req("REQ-YG-417")
def test_ac02_single_path_loads_schema_into_state_key(tmp_path: Path) -> None:
    (tmp_path / "schema.yaml").write_text(
        "fields:\n  - id: subject_person\n    required: true\n", encoding="utf-8"
    )
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr426_single_schema_loader

state:
  schema: dict

tools:
  load_fields:
    type: schema_loader
    path: schema.yaml
    state_key: schema

nodes:
  load_schema:
    type: python
    tool: load_fields

edges:
  - from: START
    to: load_schema
  - from: load_schema
    to: END
""",
    )

    app = load_and_compile(graph_path).compile()
    result = app.invoke({})

    assert result["schema"]["fields"][0]["id"] == "subject_person"


@pytest.mark.req("REQ-YG-418")
def test_ac03_merge_paths_from_state_with_dedup_and_additive(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "symptom.yaml").write_text(
        "fields:\n  - id: subject_person\n  - id: symptom\n", encoding="utf-8"
    )
    (schemas / "appointment.yaml").write_text(
        "fields:\n  - id: subject_person\n  - id: appointment_time\n", encoding="utf-8"
    )

    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr426_merge_schema_loader

state:
  schema: dict
  active_topics: list

tools:
  load_merged:
    type: schema_loader
    paths_from_state: active_topics
    schema_dir: schemas
    suffix: ".yaml"
    state_key: schema
    deduplicate_by: id
    merge_mode: additive

nodes:
  load_schema:
    type: python
    tool: load_merged

edges:
  - from: START
    to: load_schema
  - from: load_schema
    to: END
""",
    )

    app = load_and_compile(graph_path).compile()
    result = app.invoke(
        {
            "active_topics": ["symptom", "appointment"],
            "schema": {"fields": [{"id": "existing_field"}]},
        }
    )

    ids = [f["id"] for f in result["schema"]["fields"]]
    assert ids == ["existing_field", "subject_person", "symptom", "appointment_time"]


@pytest.mark.req("REQ-YG-418")
def test_ac04_missing_schema_file_raises_explicit_error(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr426_missing_file

state:
  schema: dict

tools:
  load_fields:
    type: schema_loader
    path: missing.yaml
    state_key: schema

nodes:
  load_schema:
    type: python
    tool: load_fields

edges:
  - from: START
    to: load_schema
  - from: load_schema
    to: END
""",
    )

    app = load_and_compile(graph_path).compile()
    with pytest.raises(Exception, match="missing|not found|schema_loader"):
        app.invoke({})


@pytest.mark.req("REQ-YG-418")
def test_ac05_path_traversal_is_rejected(tmp_path: Path) -> None:
    graph_dir = tmp_path / "graphs"
    graph_dir.mkdir()
    outside = tmp_path / "secret.yaml"
    outside.write_text("fields:\n  - id: secret\n", encoding="utf-8")

    graph_path = graph_dir / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr426_path_traversal

state:
  schema: dict

tools:
  load_fields:
    type: schema_loader
    path: ../secret.yaml
    state_key: schema

nodes:
  load_schema:
    type: python
    tool: load_fields

edges:
  - from: START
    to: load_schema
  - from: load_schema
    to: END
""",
    )

    app = load_and_compile(graph_path).compile()
    with pytest.raises(Exception, match="escapes graph directory|traversal|outside"):
        app.invoke({})


@pytest.mark.req("REQ-YG-418")
def test_ac06_paths_resolve_relative_to_graph_root_not_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph_dir = tmp_path / "project" / "graphs"
    graph_dir.mkdir(parents=True)
    (graph_dir / "schema.yaml").write_text(
        "fields:\n  - id: graph_relative\n", encoding="utf-8"
    )
    graph_path = graph_dir / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr426_graph_relative_resolution

state:
  schema: dict

tools:
  load_fields:
    type: schema_loader
    path: schema.yaml
    state_key: schema

nodes:
  load_schema:
    type: python
    tool: load_fields

edges:
  - from: START
    to: load_schema
  - from: load_schema
    to: END
""",
    )

    monkeypatch.chdir(tmp_path)
    app = load_and_compile(graph_path).compile()
    result = app.invoke({})
    assert result["schema"]["fields"][0]["id"] == "graph_relative"


@pytest.mark.req("REQ-YG-417")
def test_ac07_rejects_configs_with_both_path_and_paths_from_state() -> None:
    from yamlgraph.tools.schema_loader_tool import parse_schema_loader_tools

    tools_config = {
        "bad_loader": {
            "type": "schema_loader",
            "path": "schemas/symptom.yaml",
            "paths_from_state": "active_topics",
            "schema_dir": "schemas",
            "state_key": "schema",
        }
    }

    with pytest.raises(ValueError, match="exactly one of 'path' or 'paths_from_state'"):
        parse_schema_loader_tools(tools_config)
