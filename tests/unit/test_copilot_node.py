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


@pytest.mark.req("REQ-YG-087")
class TestCopilotNodeErrorHandling:
    """Tests for copilot node error handling paths."""

    def test_missing_state_key_raises(self, tmp_path: Path) -> None:
        """Should raise ValueError when state_key is missing."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            # state_key intentionally missing
        }

        with pytest.raises(ValueError, match="requires 'state_key'"):
            create_copilot_node("test_copilot", config)

    def test_timeout_expired_raises(self, tmp_path: Path) -> None:
        """Should raise RuntimeError with helpful message on timeout."""
        import subprocess

        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "timeout": 10,
        }

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="copilot", timeout=10),
        ):
            node_fn = create_copilot_node("test_copilot", config)

            with pytest.raises(RuntimeError, match="timed out after 10s"):
                node_fn({})

    def test_variable_keyerror_fallback(self, tmp_path: Path) -> None:
        """Variables with missing state keys should fallback to empty string."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello {value}")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "variables": {"value": "{state.nonexistent_key}"},
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            # State doesn't have 'nonexistent_key' - should fallback to ""
            node_fn({})

            cmd = mock_run.call_args[0][0]
            prompt_idx = cmd.index("-p") + 1
            prompt_text = cmd[prompt_idx]
            # Variable should be empty string, not the placeholder
            assert "{state.nonexistent_key}" not in prompt_text

    def test_variable_resolution_generic_error_fallback(self, tmp_path: Path) -> None:
        """Variables that cause non-KeyError exceptions should fallback to empty."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello {value}")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "variables": {"value": "{state.data}"},
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        # Mock resolve_state_expression to raise a non-KeyError exception
        with (
            patch("subprocess.run", return_value=mock_result) as mock_run,
            patch(
                "yamlgraph.node_factory.copilot_node.resolve_state_expression",
                side_effect=ValueError("Unexpected error"),
            ),
        ):
            node_fn = create_copilot_node("test_copilot", config)
            # Should fallback to empty string, not crash
            node_fn({"data": "test"})

            cmd = mock_run.call_args[0][0]
            prompt_idx = cmd.index("-p") + 1
            prompt_text = cmd[prompt_idx]
            # Variable should be empty string due to fallback
            assert "Unexpected error" not in prompt_text

    def test_relative_prompt_path(self, tmp_path: Path) -> None:
        """Relative prompt paths should use load_prompt."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        # Create graph in a subdirectory with prompts
        graph_dir = tmp_path / "graphs"
        graph_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        prompt_file = prompts_dir / "test.yaml"
        prompt_file.write_text("system: Test system\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": "test.yaml",  # Relative path
            "state_key": "result",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        with (
            patch("subprocess.run", return_value=mock_result),
            patch(
                "yamlgraph.node_factory.copilot_node.load_prompt"
            ) as mock_load_prompt,
        ):
            mock_load_prompt.return_value = {
                "system": "Test system",
                "user": "Hello",
            }
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            # load_prompt should have been called for relative path
            mock_load_prompt.assert_called_once()

    def test_literal_variable_passthrough(self, tmp_path: Path) -> None:
        """Non-string variables should pass through unchanged."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello {count}")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "variables": {"count": 42},  # Non-string value
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            prompt_idx = cmd.index("-p") + 1
            prompt_text = cmd[prompt_idx]
            # Non-string value should be converted properly
            assert "42" in prompt_text


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


# =============================================================================
# FR-105: Session Continuation Tests
# =============================================================================


@pytest.mark.req("REQ-YG-105")
class TestCopilotSessionContinuation:
    """Tests for copilot node session continuation (FR-105)."""

    def test_resume_flag_passed_to_cli(self, tmp_path: Path) -> None:
        """cli_flags.resume should pass --resume <value> to copilot CLI."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Continue work")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "cli_flags": {
                "resume": "abc-123-def",
            },
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert "--resume" in cmd
            resume_idx = cmd.index("--resume")
            assert cmd[resume_idx + 1] == "abc-123-def"

    def test_continue_session_flag_passed_to_cli(self, tmp_path: Path) -> None:
        """cli_flags.continue_session should pass --continue to copilot CLI."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Continue work")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "cli_flags": {
                "continue_session": True,
            },
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert "--continue" in cmd

    def test_resume_with_state_expression(self, tmp_path: Path) -> None:
        """cli_flags.resume should resolve state expressions like {state.prev.session_id}."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Continue work")

        # Simulate previous CopilotResult in state
        prev_result = CopilotResult(
            output="Previous output",
            exit_code=0,
            backend="cli",
            session_id="session-uuid-456",
        )

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "cli_flags": {
                "resume": "{state.prev_result.session_id}",
            },
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({"prev_result": prev_result})

            cmd = mock_run.call_args[0][0]
            assert "--resume" in cmd
            resume_idx = cmd.index("--resume")
            assert cmd[resume_idx + 1] == "session-uuid-456"

    def test_session_id_extracted_from_share_file(self, tmp_path: Path) -> None:
        """FR-274: CopilotResult.session_id extracted from --share file, not stderr."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""  # Realistic: --silent produces empty stderr
        mock_result.returncode = 0

        share_content = (
            "# 🤖 Copilot CLI Session\n\n"
            "> [!NOTE]\n"
            "> - **Session ID:** `d0137402-936d-4e5c-a3fe-27e924ef5dd2`\n"
        )

        def mock_subprocess_run(cmd, **kwargs):
            # Write share file when --share flag is present
            if "--share" in cmd:
                share_idx = cmd.index("--share") + 1
                share_path = Path(cmd[share_idx])
                share_path.parent.mkdir(parents=True, exist_ok=True)
                share_path.write_text(share_content)
            return mock_result

        with patch("subprocess.run", side_effect=mock_subprocess_run) as mock_run:
            node_fn = create_copilot_node("test_copilot", config)
            result = node_fn({})

            # --share flag should be in the command
            cmd = mock_run.call_args[0][0]
            assert "--share" in cmd

            # Session ID extracted from share file
            copilot_result = result["result"]
            assert copilot_result.session_id == "d0137402-936d-4e5c-a3fe-27e924ef5dd2"

    def test_share_file_cleaned_up_after_extraction(self, tmp_path: Path) -> None:
        """FR-274 AC-3: Share file tempdir is cleaned up after extraction."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        created_share_dirs: list[Path] = []

        def mock_subprocess_run(cmd, **kwargs):
            if "--share" in cmd:
                share_idx = cmd.index("--share") + 1
                share_path = Path(cmd[share_idx])
                share_path.parent.mkdir(parents=True, exist_ok=True)
                created_share_dirs.append(share_path.parent)
                share_path.write_text("# Session\n> - **Session ID:** `abc-123`\n")
            return mock_result

        with patch("subprocess.run", side_effect=mock_subprocess_run):
            node_fn = create_copilot_node("test_copilot", config)
            node_fn({})

        # Tempdir should have been cleaned up
        assert len(created_share_dirs) == 1
        assert not created_share_dirs[0].exists()

    def test_share_file_missing_fallback_none(self, tmp_path: Path) -> None:
        """FR-274 AC-4: Missing share file → session_id=None, not crash."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        # Don't write the share file — simulates copilot not creating it
        with patch("subprocess.run", return_value=mock_result):
            node_fn = create_copilot_node("test_copilot", config)
            result = node_fn({})

            copilot_result = result["result"]
            assert copilot_result.session_id is None

    def test_share_file_unparseable_fallback_none(self, tmp_path: Path) -> None:
        """FR-274 AC-4: Unparseable share file → session_id=None."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
        }

        mock_result = MagicMock()
        mock_result.stdout = "Response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        def mock_subprocess_run(cmd, **kwargs):
            if "--share" in cmd:
                share_idx = cmd.index("--share") + 1
                share_path = Path(cmd[share_idx])
                share_path.parent.mkdir(parents=True, exist_ok=True)
                share_path.write_text("Random content without session ID")
            return mock_result

        with patch("subprocess.run", side_effect=mock_subprocess_run):
            node_fn = create_copilot_node("test_copilot", config)
            result = node_fn({})

            copilot_result = result["result"]
            assert copilot_result.session_id is None


@pytest.mark.req("REQ-YG-154")
def test_copilot_pre_guard_halt_prevents_subprocess_run(tmp_path: Path) -> None:
    """Pre-guard halt in copilot node blocks CLI invocation."""
    from yamlgraph.models.schemas import ErrorType
    from yamlgraph.node_factory.copilot_node import create_copilot_node

    prompt_file = tmp_path / "prompts" / "guard.yaml"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_text("system: Guard test\nuser: Hello")

    config = {
        "type": "copilot",
        "prompt": str(prompt_file),
        "state_key": "result",
        "guards": {
            "pre": [{"check": "state.allow == True", "on_fail": "halt"}],
        },
    }

    with patch("subprocess.run") as mock_run:
        node_fn = create_copilot_node("guarded_copilot", config)
        result = node_fn({"allow": False})

    mock_run.assert_not_called()
    assert result["current_step"] == "guarded_copilot"
    assert result["errors"][0].type == ErrorType.GUARD_ERROR
