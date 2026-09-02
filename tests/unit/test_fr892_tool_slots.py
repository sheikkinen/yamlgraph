"""FR-892: invocation-time tool-slot binding.

A graph may declare a tool as `slot: true` with a `contract:` block; the
caller binds an FR-768 manifest at invocation via `--tool SLOT=path`.
All five contaminated-binding cases fail closed with typed errors BEFORE
any LLM call (judgement R-1/R-6). Deterministic tests only.
"""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "fr892"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


GOOD_MANIFEST = """\
name: list-items
description: Enumerate fixture items
runtime:
  type: shell
  command: "ls {folder}"
  parse: text
"""

WRONG_RUNTIME_MANIFEST = """\
name: list-items
description: Enumerate fixture items
runtime:
  type: python
  module: os.path
  function: join
"""

BAD_YAML_MANIFEST = "name: [unclosed\n"

SLOT_TOOLS = {
    "discover": {
        "slot": True,
        "contract": {"runtimes": ["shell"], "args": ["folder"]},
    },
    "plain": {"type": "shell", "command": "echo hi", "description": "inert"},
}


class TestParseToolBindings:
    """CLI `--tool NAME=PATH` parsing."""

    @pytest.mark.req("REQ-YG-624")
    def test_parses_bindings(self):
        from yamlgraph.tools.tool_slots import parse_tool_bindings

        out = parse_tool_bindings(["discover=a.yaml", "extract=b.yaml"])
        assert out == {"discover": "a.yaml", "extract": "b.yaml"}

    @pytest.mark.req("REQ-YG-624")
    def test_duplicate_binding_fatal(self):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            parse_tool_bindings,
        )

        with pytest.raises(ToolSlotBindingError, match="[Dd]uplicate"):
            parse_tool_bindings(["discover=a.yaml", "discover=b.yaml"])

    @pytest.mark.req("REQ-YG-624")
    def test_malformed_binding_fatal(self):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            parse_tool_bindings,
        )

        with pytest.raises(ToolSlotBindingError):
            parse_tool_bindings(["no-equals-sign"])


class TestResolveToolSlots:
    """Slot resolution: five fatal preflight cases + happy path."""

    @pytest.mark.req("REQ-YG-624")
    def test_happy_path_translates_to_manifest_entry(self, tmp_path):
        from yamlgraph.tools.tool_slots import resolve_tool_slots

        manifest = _write(tmp_path, "discover.manifest.yaml", GOOD_MANIFEST)
        out = resolve_tool_slots(
            dict(SLOT_TOOLS), {"discover": str(manifest)}, tmp_path
        )
        # slot translated to inline shell declaration (FR-768 translation)
        assert out["discover"]["type"] == "shell"
        assert out["discover"]["command"] == "ls {folder}"
        assert out["plain"] == SLOT_TOOLS["plain"]  # non-slots pass through

    @pytest.mark.req("REQ-YG-624")
    def test_missing_binding_fatal(self, tmp_path):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            resolve_tool_slots,
        )

        with pytest.raises(ToolSlotBindingError, match="discover"):
            resolve_tool_slots(dict(SLOT_TOOLS), {}, tmp_path)

    @pytest.mark.req("REQ-YG-624")
    def test_undeclared_slot_binding_fatal(self, tmp_path):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            resolve_tool_slots,
        )

        manifest = _write(tmp_path, "m.yaml", GOOD_MANIFEST)
        with pytest.raises(ToolSlotBindingError, match="undeclared|not a declared"):
            resolve_tool_slots(
                dict(SLOT_TOOLS),
                {"discover": str(manifest), "ghost": str(manifest)},
                tmp_path,
            )

    @pytest.mark.req("REQ-YG-624")
    def test_missing_manifest_file_fatal(self, tmp_path):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            resolve_tool_slots,
        )

        with pytest.raises(ToolSlotBindingError, match="not found|missing"):
            resolve_tool_slots(
                dict(SLOT_TOOLS), {"discover": str(tmp_path / "nope.yaml")}, tmp_path
            )

    @pytest.mark.req("REQ-YG-624")
    def test_invalid_manifest_yaml_fatal(self, tmp_path):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            resolve_tool_slots,
        )

        manifest = _write(tmp_path, "bad.yaml", BAD_YAML_MANIFEST)
        with pytest.raises(ToolSlotBindingError):
            resolve_tool_slots(dict(SLOT_TOOLS), {"discover": str(manifest)}, tmp_path)

    @pytest.mark.req("REQ-YG-624")
    def test_wrong_runtime_type_fatal(self, tmp_path):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            resolve_tool_slots,
        )

        manifest = _write(tmp_path, "wrong.yaml", WRONG_RUNTIME_MANIFEST)
        with pytest.raises(ToolSlotBindingError, match="runtime"):
            resolve_tool_slots(dict(SLOT_TOOLS), {"discover": str(manifest)}, tmp_path)

    @pytest.mark.req("REQ-YG-624")
    def test_contract_args_missing_from_shell_command_fatal(self, tmp_path):
        from yamlgraph.tools.tool_slots import (
            ToolSlotBindingError,
            resolve_tool_slots,
        )

        no_arg = GOOD_MANIFEST.replace("ls {folder}", "ls /tmp")
        manifest = _write(tmp_path, "noarg.yaml", no_arg)
        with pytest.raises(ToolSlotBindingError, match="contract|args"):
            resolve_tool_slots(dict(SLOT_TOOLS), {"discover": str(manifest)}, tmp_path)

    @pytest.mark.req("REQ-YG-624")
    def test_no_slots_no_bindings_passthrough(self, tmp_path):
        from yamlgraph.tools.tool_slots import resolve_tool_slots

        tools = {"plain": {"type": "shell", "command": "echo", "description": "x"}}
        assert resolve_tool_slots(dict(tools), None, tmp_path) == tools


class TestLoadGraphWithSlots:
    """load_graph_config end-to-end: slots resolve through FR-768 expansion."""

    GRAPH = """\
version: "1.0"
name: slot-test
description: slot binding test graph
state:
  items: list
tools:
  discover:
    slot: true
    contract:
      runtimes: [shell]
      args: [folder]
nodes:
  find:
    type: python
    tool: discover
    state_key: items
edges:
  - from: START
    to: find
  - from: find
    to: END
"""

    @pytest.mark.req("REQ-YG-624")
    def test_load_without_bindings_fatal(self, tmp_path):
        from yamlgraph.compile.graph_loader import load_graph_config
        from yamlgraph.tools.tool_slots import ToolSlotBindingError

        graph = _write(tmp_path, "graph.yaml", self.GRAPH)
        with pytest.raises(ToolSlotBindingError, match="discover"):
            load_graph_config(str(graph))

    @pytest.mark.req("REQ-YG-624")
    def test_load_with_binding_expands_manifest(self, tmp_path):
        from yamlgraph.compile.graph_loader import load_graph_config

        graph = _write(tmp_path, "graph.yaml", self.GRAPH)
        manifest = _write(tmp_path, "discover.manifest.yaml", GOOD_MANIFEST)
        config = load_graph_config(
            str(graph), tool_bindings={"discover": str(manifest)}
        )
        # FR-768 expansion turned the bound manifest into an inline shell tool
        assert config.tools["discover"]["type"] == "shell"
        assert config.tools["discover"]["command"] == "ls {folder}"
