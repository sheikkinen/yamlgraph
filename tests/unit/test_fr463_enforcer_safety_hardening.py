"""FR-463 Enforcer Demo Safety Hardening — Unit tests.

Tests the hardened enforcer demo: 10 tools (7 shell + 3 python),
no git_commit, path-restricted write_file/edit_file, run_command
honeypot, and updated ImplementationResult schema (no commit_hash).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

GRAPH_PATH = "examples/demos/enforcer/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "enforcer"
)


def _load_tool_module(name: str):
    """Dynamically import a Python tool module from the enforcer demo."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        f"{name}_tool", DEMO_DIR / "tools" / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestFR463ToolSurface:
    """FR-463: enforcer has 10 tools (7 shell + 3 python), no git_commit."""

    @pytest.mark.req("REQ-YG-427")
    def test_enforcer_has_ten_tools(self) -> None:
        """Enforcer node references exactly 10 tools."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        tools = config.nodes["enforcer"]["tools"]
        assert len(tools) == 10

    @pytest.mark.req("REQ-YG-427")
    def test_enforcer_tool_names(self) -> None:
        """Enforcer has the exact expected tool set."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        tools = set(config.nodes["enforcer"]["tools"])
        expected = {
            "read_file",
            "search",
            "list_dir",
            "git_log",
            "git_diff",
            "lint",
            "run_tests",
            "write_file",
            "edit_file",
            "run_command",
        }
        assert tools == expected

    @pytest.mark.req("REQ-YG-427")
    def test_no_git_commit_tool(self) -> None:
        """git_commit must not exist — committing is an orchestration concern."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert "git_commit" not in raw["tools"]

    @pytest.mark.req("REQ-YG-427")
    def test_tool_type_counts(self) -> None:
        """7 shell tools + 3 python tools."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        # FR-777: shared shell tools are declared via toolbelt manifest refs
        shell = [
            n
            for n, c in raw["tools"].items()
            if c.get("type") == "shell" or "toolbelt" in c.get("manifest", "")
        ]
        python = [n for n, c in raw["tools"].items() if c.get("type") == "python"]
        assert len(shell) == 7
        assert len(python) == 3

    @pytest.mark.req("REQ-YG-427")
    def test_git_log_tool_exists(self) -> None:
        """git_log shell tool must exist (parity with planner/judge)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert "git_log" in raw["tools"]
        # FR-777: declared via shared shell-runtime toolbelt manifest
        assert "toolbelt/git_log.tool.yaml" in raw["tools"]["git_log"]["manifest"]

    @pytest.mark.req("REQ-YG-427")
    def test_lint_tool_exists(self) -> None:
        """lint shell tool must exist (ruff check)."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert "lint" in raw["tools"]
        assert "ruff" in raw["tools"]["lint"]["command"]

    @pytest.mark.req("REQ-YG-427")
    def test_git_diff_tool_exists(self) -> None:
        """git_diff shell tool must exist."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert "git_diff" in raw["tools"]
        assert "git diff" in raw["tools"]["git_diff"]["command"]

    @pytest.mark.req("REQ-YG-427")
    def test_explicit_end_edge(self) -> None:
        """Graph must have explicit to: END edge."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        last_edge = raw["edges"][-1]
        assert last_edge.get("to") == "END"


class TestFR463WriteFilePathRestriction:
    """FR-463: write_file rejects paths outside project root."""

    @pytest.mark.req("REQ-YG-427")
    def test_write_file_rejects_absolute_outside_path(self, tmp_path: Path) -> None:
        """write_file returns error for paths outside project root."""
        mod = _load_tool_module("write_file")
        result = mod.write_file("/etc/evil.txt", "pwned")
        assert "Error" in result
        assert not Path("/etc/evil.txt").exists()

    @pytest.mark.req("REQ-YG-427")
    def test_write_file_rejects_traversal(self, tmp_path: Path) -> None:
        """write_file rejects ../../../ traversal."""
        mod = _load_tool_module("write_file")
        result = mod.write_file("../../../tmp/evil.txt", "pwned")
        assert "Error" in result

    @pytest.mark.req("REQ-YG-427")
    def test_write_file_accepts_relative_path(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """write_file works for paths under CWD."""
        monkeypatch.chdir(tmp_path)
        mod = _load_tool_module("write_file")
        result = mod.write_file("subdir/test.txt", "hello")
        assert "5 bytes" in result
        assert (tmp_path / "subdir" / "test.txt").read_text(encoding="utf-8") == "hello"


class TestFR463EditFileTool:
    """FR-463: edit_file with path restriction and unique-match validation."""

    @pytest.mark.req("REQ-YG-427")
    def test_edit_file_replaces_text(self, tmp_path: Path, monkeypatch) -> None:
        """edit_file performs surgical text replacement."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "test.py"
        target.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
        mod = _load_tool_module("edit_file")
        result = mod.edit_file("test.py", "return 'world'", "return 'universe'")
        assert "Replaced" in result
        assert "universe" in target.read_text(encoding="utf-8")

    @pytest.mark.req("REQ-YG-427")
    def test_edit_file_rejects_missing_text(self, tmp_path: Path, monkeypatch) -> None:
        """edit_file returns error when old_text not found."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "test.py"
        target.write_text("hello world\n", encoding="utf-8")
        mod = _load_tool_module("edit_file")
        result = mod.edit_file("test.py", "not found text", "replacement")
        assert "Error" in result
        assert "not found" in result

    @pytest.mark.req("REQ-YG-427")
    def test_edit_file_rejects_duplicate_match(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """edit_file returns error when old_text appears multiple times."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "test.py"
        target.write_text("import os\nimport os\n", encoding="utf-8")
        mod = _load_tool_module("edit_file")
        result = mod.edit_file("test.py", "import os", "import sys")
        assert "Error" in result
        assert "2 times" in result

    @pytest.mark.req("REQ-YG-427")
    def test_edit_file_rejects_outside_path(self, tmp_path: Path) -> None:
        """edit_file rejects paths outside project root."""
        mod = _load_tool_module("edit_file")
        result = mod.edit_file("/etc/passwd", "root", "evil")
        assert "Error" in result

    @pytest.mark.req("REQ-YG-427")
    def test_edit_file_is_python_tool(self) -> None:
        """edit_file must be type: python in graph."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert raw["tools"]["edit_file"]["type"] == "python"


class TestFR463RunCommandHoneypot:
    """FR-463: run_command is a no-op honeypot that logs and returns error."""

    @pytest.mark.req("REQ-YG-427")
    def test_run_command_returns_error(self) -> None:
        """run_command returns error directing agent to specific tools."""
        mod = _load_tool_module("run_command")
        result = mod.run_command("rm -rf /")
        assert "not available" in result
        assert "read_file" in result

    @pytest.mark.req("REQ-YG-427")
    def test_run_command_is_python_tool(self) -> None:
        """run_command must be type: python in graph."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert raw["tools"]["run_command"]["type"] == "python"


class TestFR463Schema:
    """FR-463: ImplementationResult schema updated — no commit_hash."""

    @pytest.mark.req("REQ-YG-427")
    def test_schema_has_four_fields(self) -> None:
        """ImplementationResult has 4 fields (no commit_hash)."""
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "enforcer.yaml").read_text(encoding="utf-8"))
        fields = set(prompt["schema"]["fields"].keys())
        expected = {"success", "files_changed", "tests_passed", "summary"}
        assert fields == expected

    @pytest.mark.req("REQ-YG-427")
    def test_no_commit_hash_in_schema(self) -> None:
        """commit_hash must not exist in schema."""
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "enforcer.yaml").read_text(encoding="utf-8"))
        assert "commit_hash" not in prompt["schema"]["fields"]


class TestFR463Prompt:
    """FR-463: prompt updated — no commit step, has lint/diff/history."""

    @pytest.mark.req("REQ-YG-427")
    def test_no_commit_instruction(self) -> None:
        """Prompt must not instruct agent to commit."""
        text = (DEMO_DIR / "prompts" / "enforcer.yaml").read_text(encoding="utf-8")
        assert "git_commit" not in text
        assert "Commit changes to git" not in text

    @pytest.mark.req("REQ-YG-427")
    def test_lint_step_in_prompt(self) -> None:
        """Prompt instructs agent to lint."""
        text = (DEMO_DIR / "prompts" / "enforcer.yaml").read_text(encoding="utf-8")
        assert "lint" in text.lower() or "Lint" in text

    @pytest.mark.req("REQ-YG-427")
    def test_diff_step_in_prompt(self) -> None:
        """Prompt instructs agent to review changes."""
        text = (DEMO_DIR / "prompts" / "enforcer.yaml").read_text(encoding="utf-8")
        assert "diff" in text.lower() or "review" in text.lower()


class TestFR463DemoSh:
    """FR-463: demo.sh shows post-run commit command."""

    @pytest.mark.req("REQ-YG-427")
    def test_demo_sh_shows_commit_guidance(self) -> None:
        """demo.sh must show how to commit after review."""
        text = (DEMO_DIR / "demo.sh").read_text(encoding="utf-8")
        assert "git" in text.lower() and "commit" in text.lower()


class TestFR463GraphCompiles:
    """FR-463: hardened graph still compiles."""

    @pytest.mark.req("REQ-YG-427")
    def test_graph_compiles(self) -> None:
        """Hardened graph compiles to a LangGraph StateGraph."""
        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(GRAPH_PATH)
        graph = compile_graph(config)
        assert graph is not None
