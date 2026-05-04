import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.chaplain"))
from actions.yamlgraph_async_action import YamlgraphAsyncAction


@pytest.mark.req("REQ-YG-027")
@pytest.mark.asyncio
class TestFR321YamlgraphAsyncSubprocessExec:
    """FR-321 acceptance tests for shell→exec argv migration."""

    @patch("actions.yamlgraph_async_action.asyncio.create_subprocess_exec")
    @patch("actions.yamlgraph_async_action.asyncio.create_subprocess_shell")
    async def test_ac01_uses_create_subprocess_exec_not_shell(
        self, mock_shell, mock_exec
    ):
        """AC-01: YamlgraphAsyncAction uses asyncio.create_subprocess_exec instead of create_subprocess_shell."""
        # Setup mocks
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"test output", b"")
        mock_exec.return_value = mock_process

        # Create action with minimal config
        action = YamlgraphAsyncAction({"graph": "test.yaml", "vars": {"key": "value"}})

        context = {"main_dir": "/test"}

        # Execute
        await action.execute(context)

        # AC-01: Should call create_subprocess_exec, not shell
        mock_exec.assert_called_once()
        mock_shell.assert_not_called()

        # Verify exec was called with individual argv components
        call_args = mock_exec.call_args
        assert call_args[0][0] == "yamlgraph"  # First argv component
        assert "graph" in call_args[0]
        assert "run" in call_args[0]

    @patch("actions.yamlgraph_async_action.asyncio.create_subprocess_exec")
    async def test_ac02_passes_var_payload_as_literal_argv_token(self, mock_exec):
        """AC-02: YamlgraphAsyncAction passes --var values as argv tokens (no shell command string join)."""
        # Setup mock
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"test output", b"")
        mock_exec.return_value = mock_process

        # Test with shell-significant characters
        action = YamlgraphAsyncAction(
            {
                "graph": "test.yaml",
                "vars": {
                    "shell_chars": 'value with "quotes" and $(echo dangerous) and ; rm -rf /'
                },
            }
        )

        context = {"main_dir": "/test"}

        # Execute
        await action.execute(context)

        # AC-02: Should pass vars as literal argv tokens
        call_args = mock_exec.call_args[0]

        # Find the --var argument
        var_index = call_args.index("--var")
        var_value = call_args[var_index + 1]

        # Should be literal key=value, not shell-escaped
        assert var_value.startswith("shell_chars=")
        # Should contain the dangerous characters as literal text
        assert '"quotes"' in var_value
        assert "$(echo dangerous)" in var_value
        assert "; rm -rf /" in var_value

    async def test_ac03_yamlgraph_async_action_has_no_shlex_quote_dependency(self):
        """AC-03: shlex.quote() is not used in YamlgraphAsyncAction var encoding."""
        # This test verifies the implementation doesn't use shlex.quote.
        import inspect

        from actions import yamlgraph_async_action

        # Get the source code of the execute method
        source = inspect.getsource(yamlgraph_async_action.YamlgraphAsyncAction.execute)

        # AC-03: Should not contain shlex.quote() calls
        assert "shlex.quote" not in source

    @patch("actions.yamlgraph_async_action.asyncio.create_subprocess_exec")
    async def test_ac04_event_map_routing_unchanged_with_exec_subprocess(
        self, mock_exec
    ):
        """AC-04: Existing success/error/event_map routing behavior remains unchanged for equivalent subprocess outputs."""
        # Setup mock with specific stdout for event_map testing
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"Status: APPROVED", b"")
        mock_exec.return_value = mock_process

        action = YamlgraphAsyncAction(
            {
                "graph": "test.yaml",
                "vars": {},
                "event_map": {"APPROVED": "approve_event", "REJECTED": "reject_event"},
                "success": "default_success",
            }
        )

        context = {"main_dir": "/test"}

        # Execute
        result = await action.execute(context)

        # AC-04: Should still route via event_map correctly
        assert result == "approve_event"

    @patch("actions.yamlgraph_async_action.asyncio.create_subprocess_exec")
    async def test_ac05_timeout_and_error_routing_unchanged(self, mock_exec):
        """AC-05: Existing cwd resolution and timeout handling behavior remains unchanged."""
        # Setup mock to simulate timeout
        mock_exec.side_effect = TimeoutError("Simulated timeout")

        action = YamlgraphAsyncAction(
            {"graph": "test.yaml", "vars": {}, "timeout": 60, "error": "timeout_error"}
        )

        context = {"main_dir": "/test", "wt_dir": "subdir"}

        # Execute
        result = await action.execute(context)

        # AC-05: Should still handle timeout and return error event
        assert result == "timeout_error"

        # Verify cwd was correctly resolved
        mock_exec.assert_called_once()
        call_kwargs = mock_exec.call_args[1]
        assert call_kwargs["cwd"] == "/test/subdir"
