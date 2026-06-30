"""RED acceptance tests for FR-625 write_data_file tool type."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _write_graph(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


@pytest.mark.req("REQ-YG-474")
def test_ac01_parse_write_data_file_tool_returns_typed_config() -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        parse_write_data_file_tools,
    )

    tools_config = {
        "save_wiki": {
            "type": "write_data_file",
            "state_key": "_wiki_written",
        }
    }

    parsed = parse_write_data_file_tools(tools_config)

    assert isinstance(parsed["save_wiki"], WriteDataFileToolConfig)
    assert parsed["save_wiki"].state_key == "_wiki_written"


@pytest.mark.req("REQ-YG-475")
def test_ac02_writes_dict_to_yaml_file(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_root = tmp_path
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")

    tool_fn = build_write_data_file_tool(
        "save_wiki",
        config,
        graph_root=graph_root,
        graph_path=graph_path,
        prompts_dir=None,
    )

    data = {"characters": [{"name": "Alice"}, {"name": "Bob"}]}
    result = tool_fn(state={"path": "wiki/world.yaml", "data": data})

    assert result["_written"] == str((tmp_path / "wiki/world.yaml").resolve())
    written_path = tmp_path / "wiki/world.yaml"
    assert written_path.exists()
    loaded = yaml.safe_load(written_path.read_text(encoding="utf-8"))
    assert loaded == data


@pytest.mark.req("REQ-YG-475")
def test_ac03_writes_list_to_yaml_file(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_root = tmp_path
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")

    tool_fn = build_write_data_file_tool(
        "save_list",
        config,
        graph_root=graph_root,
        graph_path=graph_path,
        prompts_dir=None,
    )

    data = [{"id": 1, "title": "First"}, {"id": 2, "title": "Second"}]
    result = tool_fn(state={"path": "output.yaml", "data": data})

    assert result["_written"] == str((tmp_path / "output.yaml").resolve())
    loaded = yaml.safe_load((tmp_path / "output.yaml").read_text(encoding="utf-8"))
    assert loaded == data


@pytest.mark.req("REQ-YG-476")
def test_ac04_rejects_absolute_path(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")

    tool_fn = build_write_data_file_tool(
        "save_wiki",
        config,
        graph_root=tmp_path,
        graph_path=graph_path,
        prompts_dir=None,
    )

    with pytest.raises(ValueError, match="absolute"):
        tool_fn(state={"path": "/etc/passwd", "data": {"x": 1}})


@pytest.mark.req("REQ-YG-476")
def test_ac05_rejects_path_traversal(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")

    tool_fn = build_write_data_file_tool(
        "save_wiki",
        config,
        graph_root=tmp_path,
        graph_path=graph_path,
        prompts_dir=None,
    )

    with pytest.raises(ValueError, match="escapes"):
        tool_fn(state={"path": "../../../etc/shadow", "data": {"x": 1}})


@pytest.mark.req("REQ-YG-477")
def test_ac06_rejects_writing_graph_file(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")

    tool_fn = build_write_data_file_tool(
        "save_wiki",
        config,
        graph_root=tmp_path,
        graph_path=graph_path,
        prompts_dir=None,
    )

    with pytest.raises(ValueError, match="self-modification"):
        tool_fn(state={"path": "graph.yaml", "data": {"x": 1}})


@pytest.mark.req("REQ-YG-477")
def test_ac07_rejects_writing_to_prompts_dir(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    tool_fn = build_write_data_file_tool(
        "save_wiki",
        config,
        graph_root=tmp_path,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
    )

    with pytest.raises(ValueError, match="self-modification"):
        tool_fn(state={"path": "prompts/secret.yaml", "data": {"x": 1}})


@pytest.mark.req("REQ-YG-475")
def test_ac08_only_yaml_extensions_accepted(tmp_path: Path) -> None:
    from yamlgraph.tools.write_data_file_tool import (
        WriteDataFileToolConfig,
        build_write_data_file_tool,
    )

    config = WriteDataFileToolConfig(state_key="_written")
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text("version: '1.0'\n", encoding="utf-8")

    tool_fn = build_write_data_file_tool(
        "save_wiki",
        config,
        graph_root=tmp_path,
        graph_path=graph_path,
        prompts_dir=None,
    )

    with pytest.raises(ValueError, match="extension"):
        tool_fn(state={"path": "output.json", "data": {"x": 1}})


@pytest.mark.req("REQ-YG-474")
def test_ac09_end_to_end_graph_execution(tmp_path: Path) -> None:
    from yamlgraph.graph_loader import load_and_compile

    graph_path = tmp_path / "graph.yaml"
    _write_graph(
        graph_path,
        """
version: "1.0"
name: fr625_write_data_file_e2e

state:
  wiki_data: dict
  _written: str

tools:
  save_wiki:
    type: write_data_file
    state_key: _written

nodes:
  persist:
    type: python
    tool: save_wiki
    variables:
      path: "output/wiki.yaml"
      data: "{state.wiki_data}"

edges:
  - from: START
    to: persist
  - from: persist
    to: END
""",
    )

    app = load_and_compile(graph_path).compile()
    wiki_data = {"world": "fantasy", "characters": ["Gandalf"]}
    result = app.invoke({"wiki_data": wiki_data})

    assert result["_written"] == str((tmp_path / "output/wiki.yaml").resolve())
    written = yaml.safe_load(
        (tmp_path / "output/wiki.yaml").read_text(encoding="utf-8")
    )
    assert written == wiki_data
