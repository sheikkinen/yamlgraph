"""Copilot node factory.

Creates nodes that delegate to Copilot CLI.
FR-081: Copilot Node Type.
"""

import logging
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from yamlgraph.executor_base import format_prompt
from yamlgraph.models.schemas import CopilotResult
from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.expressions import resolve_state_expression
from yamlgraph.utils.prompts import load_prompt

logger = logging.getLogger(__name__)

# Default timeout for copilot CLI (seconds)
DEFAULT_TIMEOUT = 300


def _resolve_variables(
    variables: dict[str, str], state: dict[str, Any]
) -> dict[str, Any]:
    """Resolve variable references like {state.key} or {state.key.attr} from state.

    Uses the consolidated resolve_state_expression which supports:
    - Simple paths: {state.field}
    - Nested paths: {state.analysis.output}
    - Object attributes: {state.result.score} for Pydantic models

    Args:
        variables: Dict of var_name -> expression (may contain {state.x.y})
        state: Current graph state

    Returns:
        Dict with resolved values
    """
    resolved = {}
    for key, expr in variables.items():
        if isinstance(expr, str):
            try:
                value = resolve_state_expression(expr, state)
                logger.debug(f"[resolve] {key}={expr!r} -> {type(value).__name__}")
                resolved[key] = value
            except KeyError as e:
                # Path not found - use empty string as fallback
                logger.warning(f"[resolve] {key}={expr!r} KeyError: {e}")
                resolved[key] = ""
            except Exception as e:
                # Catch any other resolution errors
                logger.warning(f"[resolve] {key}={expr!r} error: {e}")
                resolved[key] = ""
        else:
            resolved[key] = expr
    return resolved


def _load_and_render_prompt(
    prompt_path: str | Path,
    variables: dict[str, Any],
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
) -> str:
    """Load a prompt YAML file and render it with variables.

    Args:
        prompt_path: Path to prompt YAML file
        variables: Variables to substitute
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path

    Returns:
        Rendered prompt text (system + user combined)
    """
    # Handle absolute paths directly (needed for testing)
    path_obj = Path(prompt_path)
    if path_obj.is_absolute() and path_obj.exists():
        import yaml

        with open(path_obj) as f:
            prompt_config = yaml.safe_load(f)
    else:
        prompt_config = load_prompt(
            str(prompt_path),
            prompts_dir=prompts_dir,
            graph_path=graph_path,
            prompts_relative=prompts_relative,
        )

    # Build the prompt text from system + user
    parts = []
    if system := prompt_config.get("system"):
        rendered_system = format_prompt(system, variables, state=variables)
        parts.append(f"System: {rendered_system}")

    if user := prompt_config.get("user"):
        rendered_user = format_prompt(user, variables, state=variables)
        parts.append(f"User: {rendered_user}")

    return "\n\n".join(parts)


def create_copilot_node(
    node_name: str,
    config: dict[str, Any],
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
) -> Callable[[GraphState], dict]:
    """Create a copilot node that delegates to Copilot CLI.

    Args:
        node_name: Name of the node
        config: Node configuration with keys:
            - prompt: Prompt template path
            - state_key: Where to store CopilotResult (required)
            - cli_flags: Dict with allow_all_paths, allow_all_tools, model
            - timeout: Timeout in seconds (default 300)
            - variables: Variable mappings like {state.key}
            - requires: List of required state keys
            - on_error: Error handling strategy
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path

    Returns:
        Node function compatible with LangGraph
    """
    prompt_path = config.get("prompt")
    state_key = config.get("state_key")
    cli_flags = config.get("cli_flags", {})
    timeout = config.get("timeout", DEFAULT_TIMEOUT)
    variables_config = config.get("variables", {})

    if not state_key:
        raise ValueError(f"Copilot node '{node_name}' requires 'state_key'")

    def copilot_fn(state: GraphState) -> dict:
        """Execute copilot with CLI backend."""
        # Resolve variables from state
        resolved_vars = _resolve_variables(variables_config, state)

        # Load and render the prompt
        rendered_prompt = _load_and_render_prompt(
            prompt_path,
            resolved_vars,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
            prompts_relative=prompts_relative,
        )

        return _execute_cli(
            node_name=node_name,
            prompt=rendered_prompt,
            state_key=state_key,
            cli_flags=cli_flags,
            timeout=timeout,
        )

    copilot_fn.__name__ = f"copilot_{node_name}"
    return copilot_fn


def _execute_cli(
    node_name: str,
    prompt: str,
    state_key: str,
    cli_flags: dict[str, Any],
    timeout: int,
) -> dict:
    """Execute copilot via CLI backend.

    Args:
        node_name: Name of the node for error messages
        prompt: Rendered prompt text
        state_key: Where to store result
        cli_flags: CLI flags configuration
        timeout: Timeout in seconds

    Returns:
        State update dict with CopilotResult
    """
    # Build command as list (not shell=True) for injection safety
    cmd = ["copilot", "--silent"]

    # Add configured flags
    if cli_flags.get("allow_all_paths"):
        cmd.append("--allow-all-paths")

    if cli_flags.get("allow_all_tools"):
        cmd.append("--allow-all-tools")

    if model := cli_flags.get("model"):
        cmd.extend(["--model", model])

    # Add prompt
    cmd.extend(["-p", prompt])

    logger.info(f"[{node_name}] Executing copilot CLI with timeout={timeout}s")
    logger.debug(f"[{node_name}] Command: {' '.join(cmd[:5])}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        copilot_result = CopilotResult(
            output=result.stdout,
            exit_code=result.returncode,
            model=cli_flags.get("model"),
            backend="cli",
        )

        logger.info(
            f"[{node_name}] Copilot CLI completed with exit code {result.returncode}"
        )

        return {
            state_key: copilot_result,
            "current_step": node_name,
        }

    except FileNotFoundError as e:
        raise RuntimeError(
            f"copilot binary not found. Is GitHub Copilot CLI installed and in PATH? "
            f"Error: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"Copilot CLI timed out after {timeout}s in node '{node_name}'. "
            f"Consider increasing 'timeout' or simplifying the prompt."
        ) from e


__all__ = ["create_copilot_node"]
