"""FR-747: loader error UX — the two FR-744 boundary errors name their fix.

RED witnesses reproducing the exact field incidents (FR-744 enforce,
2026-07-17), asserting the actionable messages:

1. `messages:` role list in a prompt YAML → bare KeyError downstream;
   cure: `load_prompt` raises with the contract (F1: lazy load, fires
   before any LLM call in the node; F3: parsed-structure detection —
   top-level `messages:` key AND absent `system:`/`user:`).
2. `module: tools` from a graph dir → unhelpful ImportError; cure:
   hint appended ONLY when `<module>.py` exists relative to the graph
   dir (F2: verified file existence, never speculation).
3. AC-03: `graph lint` surfaces both defects pre-run (the lint ran
   clean over the broken prompt in FR-744 — a witnessed gap).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yamlgraph.linter.graph_linter import lint_graph
from yamlgraph.tools.python_tool import PythonToolConfig, load_python_function
from yamlgraph.utils.prompts import load_prompt

BAD_MESSAGES_PROMPT = """\
name: distill
messages:
  - role: system
    content: You distill.
  - role: user
    content: "Distill this: {text}"
"""

GOOD_PROMPT_WITH_MESSAGES_WORD = """\
name: chat
system: You are a chat summarizer.
user: "Summarize these messages: {messages}"
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


class TestPromptMessagesContract:
    @pytest.mark.req("REQ-YG-012")
    def test_messages_role_list_raises_actionable(self, tmp_path):
        """Field incident 1: the bare `'user'` KeyError becomes a contract."""
        _write(tmp_path / "prompts" / "distill.yaml", BAD_MESSAGES_PROMPT)
        with pytest.raises(ValueError, match=r"messages.*system.*user"):
            load_prompt("distill", prompts_dir=tmp_path / "prompts")

    @pytest.mark.req("REQ-YG-012")
    def test_messages_variable_does_not_fire(self, tmp_path):
        """F3 negative: a `messages` VARIABLE in a valid prompt stays legal."""
        _write(tmp_path / "prompts" / "chat.yaml", GOOD_PROMPT_WITH_MESSAGES_WORD)
        content = load_prompt("chat", prompts_dir=tmp_path / "prompts")
        assert content["system"].startswith("You are")


class TestModuleHint:
    @pytest.mark.req("REQ-YG-196")
    def test_hint_when_graph_local_file_exists(self, tmp_path):
        """Field incident 2: `module: tools` names the cure when tools.py
        sits next to the graph."""
        config = PythonToolConfig(module="no_such_module_fr747", function="f")
        _write(tmp_path / "no_such_module_fr747.py", "def f():\n    return 1\n")
        with pytest.raises(ImportError, match=r"path: no_such_module_fr747\.py"):
            load_python_function(config, graph_root=tmp_path)

    @pytest.mark.req("REQ-YG-196")
    def test_no_hint_without_graph_local_file(self, tmp_path):
        """F2: no speculative hint when no matching file exists."""
        config = PythonToolConfig(module="no_such_module_fr747", function="f")
        with pytest.raises(ImportError) as exc_info:
            load_python_function(config, graph_root=tmp_path)
        assert "hint" not in str(exc_info.value)


GRAPH_WITH_BOTH_DEFECTS = """\
version: "1.0"
name: fr747_defects
prompts_relative: true
prompts_dir: prompts
state:
  out: str
tools:
  local_tool:
    type: python
    module: fr747_local_tools
    function: f
nodes:
  distill:
    type: llm
    prompt: distill
    state_key: out
edges:
  - from: START
    to: distill
  - from: distill
    to: END
"""


class TestLintSurfacesBothDefects:
    @pytest.mark.req("REQ-YG-003")
    def test_lint_flags_messages_prompt(self, tmp_path):
        """AC-03: lint loads each node's prompt and catches the contract
        violation the FR-744 run only hit mid-run."""
        _write(tmp_path / "graph.yaml", GRAPH_WITH_BOTH_DEFECTS)
        _write(tmp_path / "prompts" / "distill.yaml", BAD_MESSAGES_PROMPT)
        _write(tmp_path / "fr747_local_tools.py", "def f():\n    return 1\n")
        result = lint_graph(tmp_path / "graph.yaml")
        codes = {i.code for i in result.issues}
        assert "E006" in codes, f"expected E006 in {codes}"

    @pytest.mark.req("REQ-YG-003")
    def test_lint_flags_module_with_graph_local_file(self, tmp_path):
        """AC-03: lint catches `module:` pointing at a graph-local file."""
        _write(tmp_path / "graph.yaml", GRAPH_WITH_BOTH_DEFECTS)
        _write(tmp_path / "prompts" / "distill.yaml", GOOD_PROMPT_WITH_MESSAGES_WORD)
        _write(tmp_path / "fr747_local_tools.py", "def f():\n    return 1\n")
        result = lint_graph(tmp_path / "graph.yaml")
        by_code = {i.code: i for i in result.issues}
        assert "E008" in by_code, f"expected E008 in {set(by_code)}"
        assert "path: fr747_local_tools.py" in by_code["E008"].fix

    @pytest.mark.req("REQ-YG-003")
    def test_lint_clean_when_module_has_no_local_file(self, tmp_path):
        """F2 at lint level: no flag when no matching graph-local file."""
        _write(tmp_path / "graph.yaml", GRAPH_WITH_BOTH_DEFECTS)
        _write(tmp_path / "prompts" / "distill.yaml", GOOD_PROMPT_WITH_MESSAGES_WORD)
        result = lint_graph(tmp_path / "graph.yaml")
        codes = {i.code for i in result.issues}
        assert "E008" not in codes and "E006" not in codes
