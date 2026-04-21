"""Acceptance tests for FR-266: Copilot Node — Node-Level Model Selection.

Copilot nodes must support the same model selection contract as LLM nodes:
    cli_flags.model > node-level model > defaults.model > omit

TDD RED phase — these tests MUST fail before the implementation is applied.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.models.schemas import CopilotResult

# =============================================================================
# Helpers
# =============================================================================


def _make_prompt(tmp_path: Path) -> Path:
    """Create a minimal prompt YAML file and return its path."""
    prompt_file = tmp_path / "prompts" / "test.yaml"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text("system: Test\nuser: Hello")
    return prompt_file


def _mock_subprocess(stdout: str = "Response", returncode: int = 0) -> MagicMock:
    """Return a MagicMock that behaves like subprocess.CompletedProcess."""
    result = MagicMock()
    result.stdout = stdout
    result.returncode = returncode
    result.stderr = ""
    return result


# =============================================================================
# AC-01: NodeConfig has a model field
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestNodeConfigModelField:
    """NodeConfig schema must include model: str | None."""

    def test_nodeconfig_has_model_field(self) -> None:
        """NodeConfig must declare model as a Pydantic field."""
        from yamlgraph.models.graph_schema import NodeConfig

        assert (
            "model" in NodeConfig.model_fields
        ), "NodeConfig must have a 'model' field in graph_schema.py"

    def test_nodeconfig_model_defaults_to_none(self) -> None:
        """model field must default to None (optional)."""
        from yamlgraph.models.graph_schema import NodeConfig

        node = NodeConfig(type="copilot", state_key="result", prompt="test")
        assert node.model is None


# =============================================================================
# AC-02: create_copilot_node accepts defaults parameter
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestCopilotNodeAcceptsDefaults:
    """create_copilot_node() must accept a defaults parameter."""

    def test_accepts_defaults_kwarg(self, tmp_path: Path) -> None:
        """Factory must accept defaults without raising TypeError."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
        }
        defaults = {"model": "claude-sonnet-4-5"}

        # Must not raise TypeError for unexpected keyword argument
        node_fn = create_copilot_node("test", config, defaults=defaults)
        assert callable(node_fn)


# =============================================================================
# AC-03: _compile_copilot_node passes effective_defaults
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestCompilerPassesDefaults:
    """_compile_copilot_node must pass ctx.effective_defaults to factory."""

    def test_compile_passes_effective_defaults(self) -> None:
        """node_compiler must forward effective_defaults to copilot factory."""
        from yamlgraph.node_compiler import _compile_copilot_node

        # Build a minimal NodeCompileContext mock
        ctx = MagicMock()
        ctx.node_name = "test_copilot"
        ctx.node_config = {
            "type": "copilot",
            "prompt": "prompts/test",
            "state_key": "result",
        }
        ctx.effective_defaults = {"model": "claude-sonnet-4-5"}
        ctx.config.source_path = Path("/fake/graph.yaml")
        ctx.prompts_dir = None
        ctx.prompts_relative = False
        ctx.cache_policy = None

        with patch("yamlgraph.node_compiler.create_copilot_node") as mock_factory:
            mock_factory.return_value = lambda state: {}
            _compile_copilot_node(ctx)

            mock_factory.assert_called_once()
            call_kwargs = mock_factory.call_args
            # defaults must be passed (as kwarg or positional)
            assert "defaults" in call_kwargs.kwargs or (
                len(call_kwargs.args) >= 3
                and call_kwargs.args[2] == {"model": "claude-sonnet-4-5"}
            ), "effective_defaults not passed to create_copilot_node"


# =============================================================================
# AC-04/07: Node-level model passed as --model flag
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestNodeLevelModelPassedToCLI:
    """Node-level model field must be passed as --model flag to CLI."""

    def test_node_level_model_in_cli_command(self, tmp_path: Path) -> None:
        """config['model'] should produce --model flag in subprocess cmd."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
            "model": "claude-sonnet-4-5",  # node-level, NOT in cli_flags
        }

        with patch("subprocess.run", return_value=_mock_subprocess()) as mock_run:
            node_fn = create_copilot_node("test", config, defaults={})
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert "--model" in cmd, "node-level model must produce --model flag"
            model_idx = cmd.index("--model")
            assert cmd[model_idx + 1] == "claude-sonnet-4-5"


# =============================================================================
# AC-05/08: defaults.model used when no node-level or cli_flags model
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestDefaultsModelFallback:
    """defaults.model must be used when node and cli_flags have no model."""

    def test_defaults_model_produces_cli_flag(self, tmp_path: Path) -> None:
        """defaults['model'] should produce --model flag when node has none."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
            # No model, no cli_flags.model
        }
        defaults = {"model": "claude-haiku-4-5"}

        with patch("subprocess.run", return_value=_mock_subprocess()) as mock_run:
            node_fn = create_copilot_node("test", config, defaults=defaults)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert "--model" in cmd, "defaults.model must produce --model flag"
            model_idx = cmd.index("--model")
            assert cmd[model_idx + 1] == "claude-haiku-4-5"


# =============================================================================
# AC-09: cli_flags.model overrides node-level model
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestCliFlagsModelOverridesNodeLevel:
    """cli_flags.model must take priority over node-level model."""

    def test_cli_flags_model_wins_over_node_model(self, tmp_path: Path) -> None:
        """cli_flags.model > config.model in the priority chain."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
            "model": "claude-sonnet-4-5",  # node-level
            "cli_flags": {
                "model": "claude-opus-4",  # cli_flags — highest priority
            },
        }

        with patch("subprocess.run", return_value=_mock_subprocess()) as mock_run:
            node_fn = create_copilot_node("test", config, defaults={})
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert "--model" in cmd
            model_idx = cmd.index("--model")
            assert (
                cmd[model_idx + 1] == "claude-opus-4"
            ), "cli_flags.model must override node-level model"

    def test_cli_flags_model_wins_over_defaults_model(self, tmp_path: Path) -> None:
        """cli_flags.model > defaults.model in the priority chain."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
            "cli_flags": {
                "model": "claude-opus-4",
            },
        }
        defaults = {"model": "claude-haiku-4-5"}

        with patch("subprocess.run", return_value=_mock_subprocess()) as mock_run:
            node_fn = create_copilot_node("test", config, defaults=defaults)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            model_idx = cmd.index("--model")
            assert (
                cmd[model_idx + 1] == "claude-opus-4"
            ), "cli_flags.model must override defaults.model"


# =============================================================================
# AC-10: No --model flag when no model specified anywhere
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestNoModelOmitsFlag:
    """When no model is specified anywhere, --model flag must be omitted."""

    def test_no_model_anywhere_omits_flag(self, tmp_path: Path) -> None:
        """No model in cli_flags, node config, or defaults → no --model."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
        }

        with patch("subprocess.run", return_value=_mock_subprocess()) as mock_run:
            node_fn = create_copilot_node("test", config, defaults={})
            node_fn({})

            cmd = mock_run.call_args[0][0]
            assert (
                "--model" not in cmd
            ), "--model flag must be omitted when no model specified"


# =============================================================================
# AC-05: CopilotResult.model reflects resolved model from any source
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestCopilotResultReflectsResolvedModel:
    """CopilotResult.model must reflect the resolved model regardless of source."""

    def test_result_model_from_node_config(self, tmp_path: Path) -> None:
        """CopilotResult.model should show node-level model."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
            "model": "claude-sonnet-4-5",  # node-level
        }

        with patch("subprocess.run", return_value=_mock_subprocess()):
            node_fn = create_copilot_node("test", config, defaults={})
            output = node_fn({})

            copilot_result = output["result"]
            assert isinstance(copilot_result, CopilotResult)
            assert copilot_result.model == "claude-sonnet-4-5"

    def test_result_model_from_defaults(self, tmp_path: Path) -> None:
        """CopilotResult.model should show defaults model when no node model."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
        }
        defaults = {"model": "claude-haiku-4-5"}

        with patch("subprocess.run", return_value=_mock_subprocess()):
            node_fn = create_copilot_node("test", config, defaults=defaults)
            output = node_fn({})

            copilot_result = output["result"]
            assert isinstance(copilot_result, CopilotResult)
            assert copilot_result.model == "claude-haiku-4-5"


# =============================================================================
# AC-04: Full priority chain test
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestModelPriorityChain:
    """Verify the full priority chain: cli_flags > node > defaults > omit."""

    def test_node_model_overrides_defaults(self, tmp_path: Path) -> None:
        """Node-level model must beat defaults.model."""
        from yamlgraph.node_factory.copilot_node import create_copilot_node

        config = {
            "type": "copilot",
            "prompt": str(_make_prompt(tmp_path)),
            "state_key": "result",
            "model": "gpt-4o",  # node-level
        }
        defaults = {"model": "claude-haiku-4-5"}  # lower priority

        with patch("subprocess.run", return_value=_mock_subprocess()) as mock_run:
            node_fn = create_copilot_node("test", config, defaults=defaults)
            node_fn({})

            cmd = mock_run.call_args[0][0]
            model_idx = cmd.index("--model")
            assert (
                cmd[model_idx + 1] == "gpt-4o"
            ), "node-level model must override defaults.model"
