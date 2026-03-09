"""Unit tests for cross-graph session handoff.

FR-168: Cross-Graph Session Continuity — file-based session ID handoff
between plan-judge and enforce pipelines.
"""

from pathlib import Path

import pytest

from yamlgraph.models.schemas import CopilotResult


@pytest.mark.req("REQ-YG-156")
class TestWriteSessionId:
    """Tests for write_session_id tool — exports session ID to file."""

    def test_writes_session_id_from_copilot_result(self, tmp_path: Path) -> None:
        """write_session_id extracts session_id from CopilotResult and writes to file."""
        from examples.shared.session_handoff import write_session_id

        judge_result = CopilotResult(
            output="Verdict: Approved",
            exit_code=0,
            backend="cli",
            session_id="abc-123-def",
        )
        state = {"judge_result": judge_result}

        result = write_session_id(state, output_dir=tmp_path)

        assert result["session_exported"] is True
        session_file = tmp_path / "last-plan-session-id"
        assert session_file.exists()
        assert session_file.read_text() == "abc-123-def"

    def test_writes_empty_when_no_session_id(self, tmp_path: Path) -> None:
        """write_session_id writes empty string when session_id is None."""
        from examples.shared.session_handoff import write_session_id

        judge_result = CopilotResult(
            output="Verdict: Approved",
            exit_code=0,
            backend="cli",
            session_id=None,
        )
        state = {"judge_result": judge_result}

        result = write_session_id(state, output_dir=tmp_path)

        assert result["session_exported"] is False
        session_file = tmp_path / "last-plan-session-id"
        assert session_file.exists()
        assert session_file.read_text() == ""

    def test_writes_from_dict_state(self, tmp_path: Path) -> None:
        """write_session_id handles dict-based judge_result (not Pydantic)."""
        from examples.shared.session_handoff import write_session_id

        state = {
            "judge_result": {
                "output": "Approved",
                "session_id": "dict-session-456",
            }
        }

        result = write_session_id(state, output_dir=tmp_path)

        assert result["session_exported"] is True
        session_file = tmp_path / "last-plan-session-id"
        assert session_file.read_text() == "dict-session-456"

    def test_handles_missing_judge_result(self, tmp_path: Path) -> None:
        """write_session_id handles state with no judge_result."""
        from examples.shared.session_handoff import write_session_id

        result = write_session_id({}, output_dir=tmp_path)

        assert result["session_exported"] is False
        session_file = tmp_path / "last-plan-session-id"
        assert session_file.exists()
        assert session_file.read_text() == ""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """write_session_id creates parent directories if needed."""
        from examples.shared.session_handoff import write_session_id

        output_dir = tmp_path / "nested" / "dir"
        state = {
            "judge_result": CopilotResult(
                output="OK",
                exit_code=0,
                backend="cli",
                session_id="nested-789",
            )
        }

        result = write_session_id(state, output_dir=output_dir)

        assert result["session_exported"] is True
        assert (output_dir / "last-plan-session-id").read_text() == "nested-789"


@pytest.mark.req("REQ-YG-156")
class TestReadSessionId:
    """Tests for read_session_id — reads session ID from handoff file."""

    def test_reads_existing_session_id(self, tmp_path: Path) -> None:
        """read_session_id reads session ID from file."""
        from examples.shared.session_handoff import read_session_id

        session_file = tmp_path / "last-plan-session-id"
        session_file.write_text("read-session-abc")

        result = read_session_id(tmp_path)

        assert result == "read-session-abc"

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        """read_session_id returns None when file doesn't exist."""
        from examples.shared.session_handoff import read_session_id

        result = read_session_id(tmp_path)

        assert result is None

    def test_returns_none_for_empty_file(self, tmp_path: Path) -> None:
        """read_session_id returns None when file is empty."""
        from examples.shared.session_handoff import read_session_id

        session_file = tmp_path / "last-plan-session-id"
        session_file.write_text("")

        result = read_session_id(tmp_path)

        assert result is None

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        """read_session_id strips trailing whitespace/newlines."""
        from examples.shared.session_handoff import read_session_id

        session_file = tmp_path / "last-plan-session-id"
        session_file.write_text("  session-with-spaces  \n")

        result = read_session_id(tmp_path)

        assert result == "session-with-spaces"


@pytest.mark.req("REQ-YG-156")
class TestCleanupSessionId:
    """Tests for cleanup_session_id — removes handoff file after consumption."""

    def test_removes_file(self, tmp_path: Path) -> None:
        """cleanup_session_id removes the session ID file."""
        from examples.shared.session_handoff import cleanup_session_id

        session_file = tmp_path / "last-plan-session-id"
        session_file.write_text("to-be-cleaned")

        cleanup_session_id(tmp_path)

        assert not session_file.exists()

    def test_noop_if_file_missing(self, tmp_path: Path) -> None:
        """cleanup_session_id is a no-op if file doesn't exist."""
        from examples.shared.session_handoff import cleanup_session_id

        # Should not raise
        cleanup_session_id(tmp_path)


@pytest.mark.req("REQ-YG-157")
class TestEnforceGraphResumeFlag:
    """Tests for enforce graph's implement node accepting plan_session_id."""

    def test_resume_flag_passed_when_session_id_provided(self, tmp_path: Path) -> None:
        """Implement node should pass --resume when plan_session_id is in state."""
        from unittest.mock import MagicMock, patch

        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Implement\nuser: Do the work")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "implement_result",
            "cli_flags": {
                "allow_all_paths": True,
                "allow_all_tools": True,
                "resume": "{state.plan_session_id}",
            },
            "variables": {"fr_path": "{state.fr_path}"},
        }

        mock_result = MagicMock()
        mock_result.stdout = "Implementation complete"
        mock_result.returncode = 0
        mock_result.stderr = "Session: impl-session-001"

        state = {
            "plan_session_id": "plan-session-abc-123",
            "fr_path": "feature-requests/FR-168.md",
        }

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("implement", config)
            result = node_fn(state)

            cmd = mock_run.call_args[0][0]
            assert "--resume" in cmd
            resume_idx = cmd.index("--resume")
            assert cmd[resume_idx + 1] == "plan-session-abc-123"

            assert "implement_result" in result

    def test_no_resume_flag_when_session_id_empty(self, tmp_path: Path) -> None:
        """Implement node should NOT pass --resume when plan_session_id is empty."""
        from unittest.mock import MagicMock, patch

        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Implement\nuser: Do the work")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "implement_result",
            "cli_flags": {
                "allow_all_paths": True,
                "allow_all_tools": True,
                "resume": "{state.plan_session_id}",
            },
        }

        mock_result = MagicMock()
        mock_result.stdout = "Fresh session"
        mock_result.returncode = 0
        mock_result.stderr = ""

        # Empty string → should not resume
        state = {"plan_session_id": ""}

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("implement", config)
            node_fn(state)

            cmd = mock_run.call_args[0][0]
            assert "--resume" not in cmd

    def test_no_resume_flag_when_session_id_missing(self, tmp_path: Path) -> None:
        """Implement node should NOT pass --resume when plan_session_id is not in state."""
        from unittest.mock import MagicMock, patch

        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "test.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Implement\nuser: Do the work")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "implement_result",
            "cli_flags": {
                "allow_all_paths": True,
                "allow_all_tools": True,
                "resume": "{state.plan_session_id}",
            },
        }

        mock_result = MagicMock()
        mock_result.stdout = "Fresh session"
        mock_result.returncode = 0
        mock_result.stderr = ""

        # No plan_session_id in state at all
        state = {"fr_path": "some/path.md"}

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            node_fn = create_copilot_node("implement", config)
            node_fn(state)

            cmd = mock_run.call_args[0][0]
            assert "--resume" not in cmd
