"""Tests for copilot node backend='api' fallback behavior (FR-383)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.models.schemas import CopilotResult


@pytest.mark.req("REQ-YG-356")
class TestCopilotBackendApi:
    """Copilot node API backend execution path."""

    def test_backend_api_uses_execute_prompt_not_subprocess(
        self, tmp_path: Path
    ) -> None:
        """backend=api should route through execute_prompt and skip subprocess."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "decision.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Decide on {topic}", encoding="utf-8")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "api",
            "provider": "anthropic",
            "model": "claude-sonnet-4.6",
            "variables": {"topic": "{state.topic}"},
        }

        with (
            patch(
                "yamlgraph.node_factory.copilot_node.execute_prompt",
                return_value="API response",
            ) as mock_execute_prompt,
            patch("subprocess.run") as mock_run,
        ):
            node_fn = create_copilot_node("judge", config)
            result = node_fn({"topic": "FR-383"})

        mock_execute_prompt.assert_called_once()
        assert mock_execute_prompt.call_args.kwargs["variables"]["topic"] == "FR-383"
        mock_run.assert_not_called()
        assert isinstance(result["result"], CopilotResult)

    def test_backend_api_returns_copilot_result_with_api_backend(
        self, tmp_path: Path
    ) -> None:
        """API backend returns CopilotResult envelope with backend metadata."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "judge.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello", encoding="utf-8")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "judge_result",
            "backend": "api",
            "model": "claude-sonnet-4.6",
        }

        with patch(
            "yamlgraph.node_factory.copilot_node.execute_prompt",
            return_value="Reasoned response",
        ):
            node_fn = create_copilot_node("judge", config)
            result = node_fn({})

        output = result["judge_result"]
        assert isinstance(output, CopilotResult)
        assert output.output == "Reasoned response"
        assert output.exit_code == 0
        assert output.backend == "api"
        assert output.session_id is None
        assert output.model == "claude-sonnet-4.6"

    def test_backend_omitted_remains_cli_path(self, tmp_path: Path) -> None:
        """Omitting backend should preserve existing CLI execution behavior."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "judge.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text("system: Test\nuser: Hello", encoding="utf-8")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            # backend intentionally omitted
        }

        mock_result = MagicMock()
        mock_result.stdout = "CLI response"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch("subprocess.run", return_value=mock_result) as mock_run,
            patch("yamlgraph.node_factory.copilot_node.execute_prompt") as mock_api,
        ):
            node_fn = create_copilot_node("judge", config)
            result = node_fn({})

        mock_run.assert_called_once()
        mock_api.assert_not_called()
        assert result["result"].backend == "cli"

    def test_backend_api_supports_prompt_schema_output(self, tmp_path: Path) -> None:
        """API backend should pass inferred output_model from prompt schema."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        prompt_file = tmp_path / "prompts" / "schema_prompt.yaml"
        prompt_file.parent.mkdir(parents=True)
        prompt_file.write_text(
            "\n".join(
                [
                    "schema:",
                    "  name: Verdict",
                    "  fields:",
                    "    decision:",
                    "      type: str",
                    "      description: Final decision",
                    "system: Decide",
                    "user: Decision for {topic}",
                ]
            )
        , encoding="utf-8")

        config = {
            "type": "copilot",
            "prompt": str(prompt_file),
            "state_key": "result",
            "backend": "api",
            "model": "claude-sonnet-4.6",
            "variables": {"topic": "{state.topic}"},
        }

        def _mock_execute_prompt(**kwargs):
            output_model = kwargs["output_model"]
            assert output_model is not None
            return output_model(decision="accept")

        with patch(
            "yamlgraph.node_factory.copilot_node.execute_prompt",
            side_effect=_mock_execute_prompt,
        ):
            node_fn = create_copilot_node("judge", config)
            result = node_fn({"topic": "FR-383"})

        output = result["result"]
        assert output.backend == "api"
        assert '"decision":"accept"' in output.output
