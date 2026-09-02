"""Tests for tool manifests: declaration reuse over existing runtimes.

FR-768: Tool Manifests — a `manifest:` key in a `tools:` entry loads a
typed manifest YAML and translates it into the equivalent inline tool
declaration. Translation only; no new execution engine.

RED contract: `yamlgraph.tools.manifest` does not exist yet.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.compile.graph_loader import load_graph_config

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

MINIMAL_GRAPH = {
    "version": "1.0",
    "name": "manifest-fixture",
    "state": {"topic": "str"},
    "nodes": {"noop": {"type": "python", "tool": "target"}},
    "edges": [{"from": "START", "to": "noop"}, {"from": "noop", "to": "END"}],
}


def write_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def write_graph(tmp_path: Path, tools: dict, filename: str = "graph.yaml") -> Path:
    graph = dict(MINIMAL_GRAPH)
    graph["tools"] = tools
    return write_yaml(tmp_path / filename, graph)


def write_tool_py(tmp_path: Path, name: str = "tool_impl.py") -> Path:
    impl = tmp_path / name
    impl.parent.mkdir(parents=True, exist_ok=True)
    impl.write_text("def run(state):\n    return {'topic': 'ok'}\n", encoding="utf-8")
    return impl


# ---------------------------------------------------------------------------
# AC-01 / AC-02: manifest reference accepted; path resolution semantics
# ---------------------------------------------------------------------------


class TestManifestResolution:
    @pytest.mark.req("REQ-YG-574")
    def test_sibling_manifest_resolves_relative_to_graph(self, tmp_path):
        write_tool_py(tmp_path)
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "A python tool.",
                "runtime": {
                    "type": "python",
                    "path": "tool_impl.py",
                    "function": "run",
                },
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "target.tool.yaml"}})

        config = load_graph_config(graph_path)

        assert config.tools["target"]["type"] == "python"
        assert config.tools["target"]["function"] == "run"

    @pytest.mark.req("REQ-YG-574")
    def test_nested_manifest_paths_resolve_relative_to_manifest(self, tmp_path):
        """AC-02: runtime paths are manifest-relative, not graph-relative."""
        write_tool_py(tmp_path, "nested/tool_impl.py")
        write_yaml(
            tmp_path / "nested" / "target.tool.yaml",
            {
                "name": "target",
                "description": "Nested python tool.",
                "runtime": {
                    "type": "python",
                    "path": "tool_impl.py",  # sibling of the manifest, not the graph
                    "function": "run",
                },
            },
        )
        graph_path = write_graph(
            tmp_path, {"target": {"manifest": "nested/target.tool.yaml"}}
        )

        config = load_graph_config(graph_path)

        resolved = Path(config.tools["target"]["path"])
        assert resolved.is_absolute()
        assert resolved == (tmp_path / "nested" / "tool_impl.py").resolve()


# ---------------------------------------------------------------------------
# AC-03: typed validation fails at graph load, before invocation
# ---------------------------------------------------------------------------


class TestLoadBoundaryValidation:
    @pytest.mark.req("REQ-YG-574")
    def test_missing_manifest_file_fails_load(self, tmp_path):
        graph_path = write_graph(tmp_path, {"target": {"manifest": "missing.yaml"}})
        with pytest.raises(ValueError, match="missing.yaml"):
            load_graph_config(graph_path)

    @pytest.mark.req("REQ-YG-574")
    def test_invalid_manifest_yaml_fails_load(self, tmp_path):
        (tmp_path / "bad.tool.yaml").write_text("{unclosed", encoding="utf-8")
        graph_path = write_graph(tmp_path, {"target": {"manifest": "bad.tool.yaml"}})
        with pytest.raises(ValueError, match="bad.tool.yaml"):
            load_graph_config(graph_path)

    @pytest.mark.req("REQ-YG-574")
    def test_unknown_runtime_type_fails_load(self, tmp_path):
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "x",
                "runtime": {"type": "docker", "image": "x"},
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "target.tool.yaml"}})
        with pytest.raises(ValueError, match="docker"):
            load_graph_config(graph_path)

    @pytest.mark.req("REQ-YG-574")
    def test_unknown_field_fails_load(self, tmp_path):
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "x",
                "unexpected": True,
                "runtime": {"type": "shell", "command": "echo hi"},
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "target.tool.yaml"}})
        with pytest.raises(ValueError, match="unexpected"):
            load_graph_config(graph_path)

    @pytest.mark.req("REQ-YG-574")
    def test_python_path_and_module_conflict_fails_load(self, tmp_path):
        write_tool_py(tmp_path)
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "x",
                "runtime": {
                    "type": "python",
                    "path": "tool_impl.py",
                    "module": "examples.shared.websearch",
                    "function": "run",
                },
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "target.tool.yaml"}})
        with pytest.raises(ValueError, match="path|module"):
            load_graph_config(graph_path)

    @pytest.mark.req("REQ-YG-574")
    def test_name_mismatch_fails_load(self, tmp_path):
        write_yaml(
            tmp_path / "other.tool.yaml",
            {
                "name": "other_name",
                "description": "x",
                "runtime": {"type": "shell", "command": "echo hi"},
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "other.tool.yaml"}})
        with pytest.raises(ValueError, match="other_name"):
            load_graph_config(graph_path)

    @pytest.mark.req("REQ-YG-574")
    def test_extra_keys_beside_manifest_fail_load(self, tmp_path):
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "x",
                "runtime": {"type": "shell", "command": "echo hi"},
            },
        )
        graph_path = write_graph(
            tmp_path,
            {"target": {"manifest": "target.tool.yaml", "command": "echo override"}},
        )
        with pytest.raises(ValueError, match="manifest"):
            load_graph_config(graph_path)


# ---------------------------------------------------------------------------
# AC-04..AC-07: per-runtime translation equivalence with inline declarations
# ---------------------------------------------------------------------------


class TestRuntimeEquivalence:
    @pytest.mark.req("REQ-YG-574")
    def test_shell_manifest_translates_to_inline_equivalent(self, tmp_path):
        """AC-04: command/description/parse survive translation."""
        write_yaml(
            tmp_path / "greet.tool.yaml",
            {
                "name": "greet",
                "description": "Echo a greeting.",
                "runtime": {
                    "type": "shell",
                    "command": "echo hello {name}",
                    "parse": "text",
                    "timeout": 5,
                },
            },
        )
        inline_tools = {
            "greet": {
                "type": "shell",
                "command": "echo hello {name}",
                "description": "Echo a greeting.",
                "parse": "text",
                "timeout": 5,
            }
        }
        manifest_tools = {"greet": {"manifest": "greet.tool.yaml"}}

        inline_cfg = load_graph_config(
            write_graph(tmp_path, inline_tools, "inline.yaml")
        )
        manifest_cfg = load_graph_config(
            write_graph(tmp_path, manifest_tools, "manifest.yaml")
        )

        from yamlgraph.tools.shell import parse_tools

        assert parse_tools(manifest_cfg.tools) == parse_tools(inline_cfg.tools)

    @pytest.mark.req("REQ-YG-574")
    def test_python_path_manifest_executes_like_inline(self, tmp_path):
        """AC-05: python path manifest produces a loadable, identical tool."""
        write_tool_py(tmp_path)
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "Python tool.",
                "runtime": {
                    "type": "python",
                    "path": "tool_impl.py",
                    "function": "run",
                },
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "target.tool.yaml"}})

        from yamlgraph.compile.graph_loader import compile_graph

        compiled = compile_graph(load_graph_config(graph_path)).compile()
        result = compiled.invoke({"topic": ""})
        assert result["topic"] == "ok"

    @pytest.mark.req("REQ-YG-574")
    def test_python_module_manifest_translates(self, tmp_path):
        """AC-06: python module manifests are supported."""
        write_yaml(
            tmp_path / "target.tool.yaml",
            {
                "name": "target",
                "description": "Module tool.",
                "runtime": {
                    "type": "python",
                    "module": "examples.shared.websearch",
                    "function": "search_web",
                },
            },
        )
        graph_path = write_graph(tmp_path, {"target": {"manifest": "target.tool.yaml"}})

        config = load_graph_config(graph_path)

        assert config.tools["target"]["module"] == "examples.shared.websearch"
        assert config.tools["target"]["function"] == "search_web"
        assert "path" not in config.tools["target"]

    @pytest.mark.req("REQ-YG-574")
    def test_graph_manifest_translates_with_manifest_relative_path(self, tmp_path):
        """AC-07: graph runtime translates to type: graph with resolved path."""
        child = {
            "version": "1.0",
            "name": "child",
            "state": {"echoed": "str"},
            "nodes": {
                "echo": {
                    "type": "python",
                    "tool": "echo_tool",
                }
            },
            "edges": [
                {"from": "START", "to": "echo"},
                {"from": "echo", "to": "END"},
            ],
            "tools": {
                "echo_tool": {
                    "type": "python",
                    "path": "child_impl.py",
                    "function": "run",
                }
            },
        }
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "child_impl.py").write_text(
            "def run(state):\n    return {'echoed': 'from-child'}\n"
        , encoding="utf-8")
        write_yaml(tmp_path / "sub" / "child.yaml", child)
        write_yaml(
            tmp_path / "sub" / "target.tool.yaml",
            {
                "name": "target",
                "description": "Child graph tool.",
                "runtime": {
                    "type": "graph",
                    "path": "child.yaml",
                    "input_mapping": {"question": "topic"},
                    "output_key": "echoed",
                },
            },
        )
        graph_path = write_graph(
            tmp_path, {"target": {"manifest": "sub/target.tool.yaml"}}
        )

        config = load_graph_config(graph_path)

        translated = config.tools["target"]
        assert translated["type"] == "graph"
        assert Path(translated["path"]) == (tmp_path / "sub" / "child.yaml").resolve()
        assert translated["input_mapping"] == {"question": "topic"}
        assert translated["output_key"] == "echoed"


# ---------------------------------------------------------------------------
# AC-08: inline declarations are untouched
# ---------------------------------------------------------------------------


class TestInlinePassthrough:
    @pytest.mark.req("REQ-YG-574")
    def test_inline_tools_load_unchanged(self, tmp_path):
        write_tool_py(tmp_path)
        tools = {
            "sh": {"type": "shell", "command": "echo hi", "description": "d"},
            "py": {
                "type": "python",
                "path": "tool_impl.py",
                "function": "run",
                "description": "d",
            },
        }
        graph = dict(MINIMAL_GRAPH)
        graph["tools"] = tools
        graph["nodes"] = {"noop": {"type": "python", "tool": "py"}}
        graph_path = write_yaml(tmp_path / "graph.yaml", graph)

        config = load_graph_config(graph_path)

        assert config.tools["sh"] == tools["sh"]
        assert config.tools["py"] == tools["py"]
