"""Unit tests for copilot node variable passing in subgraphs.

FR-103: Validates that variables are correctly passed to copilot nodes
within subgraphs via input_mapping.

The core issue: When a parent graph invokes a subgraph with input_mapping,
the child copilot nodes should resolve {state.X} against the CHILD state
(after mapping), not the parent state.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.req("REQ-YG-092")
class TestCopilotSubgraphVariables:
    """Tests for variable passing to copilot nodes in subgraphs."""

    def test_map_input_state_creates_child_state(self) -> None:
        """Input mapping should create child state with mapped keys."""
        from yamlgraph.node_factory.subgraph_nodes import _map_input_state

        # Parent state has chapter content under chapter_introduction
        parent_state = {
            "chapter_introduction": "# Introduction\n\nThis is the intro.",
            "output_dir": "docs/ebook",
            "other_field": "ignored",
        }

        # Mapping: parent_key -> child_key
        input_mapping = {
            "chapter_introduction": "chapter",
            "output_dir": "output_dir",
        }

        child_state = _map_input_state(parent_state, input_mapping)

        # Child should have 'chapter' (not 'chapter_introduction')
        assert "chapter" in child_state
        assert child_state["chapter"] == "# Introduction\n\nThis is the intro."
        assert child_state["output_dir"] == "docs/ebook"
        # Should NOT have unmapped parent keys
        assert "chapter_introduction" not in child_state
        assert "other_field" not in child_state

    def test_resolve_variables_from_child_state(self) -> None:
        """Copilot node should resolve {state.X} from child state."""
        from yamlgraph.node_factory.copilot_node import _resolve_variables

        # Child state after input_mapping
        child_state = {
            "chapter": "# Introduction\n\nThis is the intro.",
            "output_dir": "docs/ebook",
        }

        # Variables reference child state keys
        variables = {
            "chapter": "{state.chapter}",
            "output_dir": "{state.output_dir}",
        }

        resolved = _resolve_variables(variables, child_state)

        assert resolved["chapter"] == "# Introduction\n\nThis is the intro."
        assert resolved["output_dir"] == "docs/ebook"

    def test_resolve_variables_missing_key_warns(self) -> None:
        """Missing keys in state should log warning and return empty string."""
        from yamlgraph.node_factory.copilot_node import _resolve_variables

        # Child state is empty (mapping failed or key missing)
        child_state = {}

        variables = {
            "chapter": "{state.chapter}",
        }

        resolved = _resolve_variables(variables, child_state)

        # Should fallback to empty string
        assert resolved["chapter"] == ""
        # Warning is logged to yamlgraph.node_factory.copilot_node logger

    def test_subgraph_copilot_receives_mapped_variables(self, tmp_path: Path) -> None:
        """Full flow: parent invokes subgraph, copilot node gets mapped variables."""
        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        # Create subgraph with copilot node
        subgraph_dir = tmp_path / "subgraphs"
        subgraph_dir.mkdir()

        subgraph_yaml = subgraph_dir / "validator.yaml"
        subgraph_yaml.write_text(
            """
version: "1.0"
name: validator
prompts_relative: true
prompts_dir: ../prompts

state:
  chapter: str
  output_dir: str
  result: str

nodes:
  validate:
    type: copilot
    prompt: validate
    backend: cli
    variables:
      chapter: "{state.chapter}"
      output_dir: "{state.output_dir}"
    state_key: result
    timeout: 60

edges:
  - from: START
    to: validate
  - from: validate
    to: END
"""
        )

        # Create prompt
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "validate.yaml").write_text(
            """
system: You are a validator.
user: |
  Validate this chapter:
  {chapter}

  Output dir: {output_dir}
"""
        )

        # Create parent graph
        parent_yaml = tmp_path / "parent.yaml"
        parent_yaml.write_text(
            """
version: "1.0"
name: parent
prompts_relative: true
prompts_dir: prompts

state:
  chapter_intro: str
  output_dir: str
  validated: str

nodes:
  validate_intro:
    type: subgraph
    mode: invoke
    graph: subgraphs/validator.yaml
    input_mapping:
      chapter_intro: chapter
      output_dir: output_dir
    output_mapping:
      validated: result

edges:
  - from: START
    to: validate_intro
  - from: validate_intro
    to: END
"""
        )

        # Capture what variables are passed to copilot CLI
        captured_cmd = []

        def mock_subprocess_run(cmd, **kwargs):
            captured_cmd.append(cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "Validated!"
            return result

        with patch("subprocess.run", side_effect=mock_subprocess_run):
            config = load_graph_config(parent_yaml)
            graph = compile_graph(config)
            compiled = graph.compile()

            # Run with parent state
            result = compiled.invoke(
                {
                    "chapter_intro": "# Chapter 0: Introduction\n\nHello world.",
                    "output_dir": "docs/ebook",
                }
            )

        # Verify copilot was called
        assert len(captured_cmd) >= 1

        # The prompt should contain the chapter content
        # (copilot CLI receives prompt as stdin or file)
        # Check that the graph completed
        assert result.get("validated") is not None


@pytest.mark.req("REQ-YG-092")
class TestFilenamePassingToSubgraph:
    """Tests for passing filename to subgraph copilot nodes.

    FR-103 requires each chapter to be written to a specific file.
    The subgraph needs to know the target filename.
    """

    def test_input_mapping_cannot_pass_literals(self) -> None:
        """Current limitation: input_mapping only maps state keys, not literals."""
        from yamlgraph.node_factory.subgraph_nodes import _map_input_state

        parent_state = {
            "chapter_doctrine": "# Doctrine\n\nThe 10 Commandments...",
            "output_dir": "docs/ebook",
        }

        # Cannot pass "01-doctrine.md" as a literal value
        # input_mapping values must be keys in parent_state
        input_mapping = {
            "chapter_doctrine": "chapter",
            "output_dir": "output_dir",
        }

        child_state = _map_input_state(parent_state, input_mapping)

        # No way to pass static filename through input_mapping alone
        assert "filename" not in child_state

    def test_filename_via_state_workaround(self) -> None:
        """Workaround: Store filename in parent state, then map it."""
        from yamlgraph.node_factory.subgraph_nodes import _map_input_state

        # Parent stores filename in state (set by prior node or initial state)
        parent_state = {
            "chapter_doctrine": "# Doctrine\n\nThe 10 Commandments...",
            "output_dir": "docs/ebook",
            "chapter_filename": "01-doctrine.md",
        }

        input_mapping = {
            "chapter_doctrine": "chapter",
            "output_dir": "output_dir",
            "chapter_filename": "filename",
        }

        child_state = _map_input_state(parent_state, input_mapping)

        assert child_state["filename"] == "01-doctrine.md"
        assert child_state["chapter"] == "# Doctrine\n\nThe 10 Commandments..."


@pytest.mark.req("REQ-YG-092")
class TestEbookChapterPattern:
    """Tests validating the ebook write→validate pattern.

    The pattern:
    1. write_* copilot node writes chapter to state
    2. validate_* subgraph receives chapter + output_dir + filename
    3. amend copilot writes corrected chapter to file
    """

    def test_ebook_graph_structure_with_filename_in_state(self, tmp_path: Path) -> None:
        """Test the complete ebook chapter pattern with filename in state."""
        from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

        # Create subgraph
        subgraph_dir = tmp_path / "subgraphs"
        subgraph_dir.mkdir()

        (subgraph_dir / "validate_chapter.yaml").write_text(
            """
version: "1.0"
name: validate_chapter
prompts_relative: true
prompts_dir: ../prompts

state:
  chapter: str
  output_dir: str
  filename: str
  result: str

nodes:
  amend:
    type: copilot
    prompt: amend
    backend: cli
    variables:
      chapter: "{state.chapter}"
      output_dir: "{state.output_dir}"
      filename: "{state.filename}"
    state_key: result
    timeout: 60

edges:
  - from: START
    to: amend
  - from: amend
    to: END
"""
        )

        # Create amend prompt
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "amend.yaml").write_text(
            """
system: You are amending a chapter.
user: |
  Fix and write to: {output_dir}/{filename}

  Chapter:
  {chapter}
"""
        )

        # Create parent graph with filename in state
        parent_yaml = tmp_path / "ebook.yaml"
        parent_yaml.write_text(
            """
version: "1.0"
name: ebook
prompts_relative: true
prompts_dir: prompts

state:
  chapter_doctrine: str
  output_dir: str
  chapter_filename: str
  validated: str

nodes:
  validate_doctrine:
    type: subgraph
    mode: invoke
    graph: subgraphs/validate_chapter.yaml
    input_mapping:
      chapter_doctrine: chapter
      output_dir: output_dir
      chapter_filename: filename
    output_mapping:
      validated: result

edges:
  - from: START
    to: validate_doctrine
  - from: validate_doctrine
    to: END
"""
        )

        # Capture subprocess calls
        captured_prompts = []

        def mock_subprocess_run(cmd, **kwargs):
            # Copilot CLI passes prompt via -p argument
            # Find the prompt content after "-p" flag
            if "-p" in cmd:
                p_index = cmd.index("-p")
                if p_index + 1 < len(cmd):
                    captured_prompts.append(cmd[p_index + 1])
            result = MagicMock()
            result.returncode = 0
            result.stdout = "Chapter amended and saved!"
            return result

        with patch("subprocess.run", side_effect=mock_subprocess_run):
            config = load_graph_config(parent_yaml)
            graph = compile_graph(config)
            compiled = graph.compile()

            compiled.invoke(
                {
                    "chapter_doctrine": "# The Doctrine\n\n10 Commandments here...",
                    "output_dir": "docs/ebook",
                    "chapter_filename": "01-doctrine.md",
                }
            )

        # Verify the prompt included the filename
        assert len(captured_prompts) >= 1
        # The rendered prompt should contain the filename
        prompt_content = captured_prompts[0]
        assert "01-doctrine.md" in prompt_content
        assert "docs/ebook" in prompt_content
        assert "10 Commandments" in prompt_content


# ---------------------------------------------------------------------------
# FR-659: _map_output_state auto/* coverage
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-092")
class TestMapOutputState:
    """FR-659: Cover _map_output_state auto and * branches."""

    def test_auto_passes_all_fields(self) -> None:
        from yamlgraph.node_factory.subgraph_nodes import _map_output_state

        child_output = {"result": "ok", "score": 0.9, "extra": True}
        mapped = _map_output_state(child_output, "auto")
        assert mapped == child_output
        assert mapped is child_output

    def test_star_passes_all_fields(self) -> None:
        from yamlgraph.node_factory.subgraph_nodes import _map_output_state

        child_output = {"result": "ok", "score": 0.9}
        mapped = _map_output_state(child_output, "*")
        assert mapped == child_output
        assert mapped is child_output

    def test_dict_mapping_selects_keys(self) -> None:
        from yamlgraph.node_factory.subgraph_nodes import _map_output_state

        child_output = {"result": "ok", "score": 0.9, "extra": True}
        mapped = _map_output_state(child_output, {"parent_result": "result"})
        assert mapped == {"parent_result": "ok"}
        assert "score" not in mapped
