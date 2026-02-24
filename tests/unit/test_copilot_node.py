"""Unit tests for copilot node functionality.

FR-081: Copilot Node Type — CLI backend.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.models.schemas import CopilotResult


@pytest.mark.req("REQ-YG-087")
class TestCopilotNodeCLI:
    """Tests for copilot node CLI backend."""

    def test_creates_callable(self) -> None:
        """create_copilot_node should return a callable."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": "prompts/test.yaml",
            "state_key": "result",
            "backend": "cli",
        }
        node_fn = create_copilot_node("test_copilot", config)

        assert callable(node_fn)

    def test_invokes_copilot_cli(self, tmp_path: Path) -> None:
        """CLI backend should invoke copilot command with --silent."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        # Create a mock prompt file
        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test system\nuser: Hello {name}")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
            "variables": {"name": "World"},
        }

        mock_result = MagicMock()
        mock_result.stdout = "Hello from Copilot!"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            _ = node_fn({"name": "World"})  # Result not needed, testing CLI invocation

            # Verify subprocess.run was called with list (not shell=True)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args[0][0]

            assert isinstance(cmd, list)
            assert "copilot" in cmd[0]
            assert "--silent" in cmd
            assert "-p" in cmd
            assert call_args[1].get("shell") is not True

    def test_cli_flags_passed(self, tmp_path: Path) -> None:
        """CLI flags should be passed to copilot command."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
            "cli_flags": {
                "allow_all_paths": True,
                "allow_all_tools": True,
                "model": "claude-sonnet-4",
            },
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert "--allow-all-paths" in cmd
            assert "--allow-all-tools" in cmd
            assert "--model" in cmd
            assert "claude-sonnet-4" in cmd

    def test_timeout_configurable(self, tmp_path: Path) -> None:
        """Timeout should be configurable per-node."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
            "timeout": 600,
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            call_args = mock_run.call_args
            assert call_args[1].get("timeout") == 600

    def test_default_timeout_300s(self, tmp_path: Path) -> None:
        """Default timeout should be 300 seconds."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            call_args = mock_run.call_args
            assert call_args[1].get("timeout") == 300

    def test_returns_copilot_result(self, tmp_path: Path) -> None:
        """Node should return CopilotResult in state_key."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "copilot_output",
            "backend": "cli",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Hello from Copilot!"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            node_fn = create_copilot_node("test_copilot", config)
            result = node_fn({})

            assert "copilot_output" in result
            output = result["copilot_output"]
            assert isinstance(output, CopilotResult)
            assert output.output == "Hello from Copilot!"
            assert output.exit_code == 0
            assert output.backend == "cli"

    def test_graceful_file_not_found(self, tmp_path: Path) -> None:
        """Should raise clear error when copilot binary not found."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
        }

        with patch("subprocess.run", side_effect=FileNotFoundError("copilot")):
            node_fn = create_copilot_node("test_copilot", config)

            with pytest.raises(RuntimeError, match="copilot.*not found|not installed"):
                node_fn({})

    def test_variable_substitution(self, tmp_path: Path) -> None:
        """Variables should be substituted in prompts."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text(
            "system: Analyze {topic}\nuser: Give insights on {topic}"
        )

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
            "variables": {"topic": "{state.current_topic}"},
        }

        mock_result = MagicMock()
        mock_result.stdout = "Analysis complete"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({"current_topic": "AI Safety"})

            # The prompt should contain the substituted value
            cmd = mock_run.call_args[0][0]
            prompt_idx = cmd.index("-p") + 1
            prompt_text = cmd[prompt_idx]
            assert "AI Safety" in prompt_text

    def test_nested_variable_resolution(self, tmp_path: Path) -> None:
        """Variables like {state.result.output} should resolve Pydantic attributes."""
        from yamlgraph.models.schemas import CopilotResult
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        # Use pipe syntax to ensure YAML doesn't misparse {var} as dict
        prompt_file.write_text(
            "system: Review this\nuser: |\n  Review: {previous_output}"
        )

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "review",
            "backend": "cli",
            "variables": {"previous_output": "{state.analysis.output}"},
        }

        # State contains a CopilotResult Pydantic model
        state = {
            "analysis": CopilotResult(
                output="The analysis found key insights",
                exit_code=0,
                backend="cli",
            )
        }

        mock_result = MagicMock()
        mock_result.stdout = "Review complete"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn(state)

            # The prompt should contain the nested attribute value
            cmd = mock_run.call_args[0][0]
            prompt_idx = cmd.index("-p") + 1
            prompt_text = cmd[prompt_idx]
            assert "The analysis found key insights" in prompt_text


@pytest.mark.req("REQ-YG-087")
class TestCopilotNodeNodeCompiler:
    """Tests for copilot node integration with node_compiler."""

    def test_node_type_recognized(self) -> None:
        """NodeType.COPILOT should be in the enum."""
        from yamlgraph.constants import NodeType

        assert hasattr(NodeType, "COPILOT")
        assert NodeType.COPILOT == "copilot"

    def test_requires_prompt(self) -> None:
        """Copilot node should require prompt field."""
        from yamlgraph.constants import NodeType

        assert NodeType.requires_prompt("copilot") is True


@pytest.mark.req("REQ-YG-089")
class TestCopilotNodeComposition:
    """Tests for copilot node composition with other patterns."""

    def test_standard_node_guarantees(self, tmp_path: Path) -> None:
        """Copilot node should support requires, on_error, skip_if_exists."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "cli",
            "requires": ["input_data"],
            "on_error": "skip",
        }

        # Node creation should succeed with these fields
        node_fn = create_copilot_node("test_copilot", config)
        assert callable(node_fn)
