"""Copilot node factory.

Creates nodes that delegate to Copilot CLI or MCP sampling.
FR-081: Copilot Node Type.
"""

import asyncio
import logging
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from yamlgraph.executor_base import format_prompt
from yamlgraph.models.schemas import CopilotResult
from yamlgraph.node_factory.base import GraphState
from yamlgraph.utils.prompts import load_prompt

logger = logging.getLogger(__name__)

# Default timeout for copilot CLI (seconds)
DEFAULT_TIMEOUT = 300


def _resolve_variables(
    variables: dict[str, str], state: dict[str, Any]
) -> dict[str, Any]:
    """Resolve variable references like {state.key} from state.

    Args:
        variables: Dict of var_name -> expression (may contain {state.x})
        state: Current graph state

    Returns:
        Dict with resolved values
    """
    resolved = {}
    pattern = re.compile(r"\{state\.(\w+)\}")

    for key, expr in variables.items():
        if isinstance(expr, str):
            # Replace {state.key} with actual state value
            match = pattern.match(expr)
            if match:
                state_key = match.group(1)
                resolved[key] = state.get(state_key, "")
            elif "{state." in expr:
                # Multiple replacements or partial match
                def replacer(m: re.Match) -> str:
                    return str(state.get(m.group(1), ""))

                resolved[key] = pattern.sub(replacer, expr)
            else:
                resolved[key] = expr
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
    """Create a copilot node that delegates to Copilot CLI or MCP sampling.

    Args:
        node_name: Name of the node
        config: Node configuration with keys:
            - prompt: Prompt template path
            - state_key: Where to store CopilotResult (required)
            - backend: "cli" (default) or "sampling"
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
    backend = config.get("backend", "cli")
    cli_flags = config.get("cli_flags", {})
    timeout = config.get("timeout", DEFAULT_TIMEOUT)
    variables_config = config.get("variables", {})

    if not state_key:
        raise ValueError(f"Copilot node '{node_name}' requires 'state_key'")

    def copilot_fn(state: GraphState) -> dict:
        """Execute copilot with CLI or sampling backend."""
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

        if backend == "cli":
            return _execute_cli(
                node_name=node_name,
                prompt=rendered_prompt,
                state_key=state_key,
                cli_flags=cli_flags,
                timeout=timeout,
            )
        elif backend == "sampling":
            return _execute_sampling(
                node_name=node_name,
                prompt=rendered_prompt,
                state_key=state_key,
                timeout=timeout,
            )
        else:
            raise ValueError(
                f"Unknown backend '{backend}' for copilot node '{node_name}'"
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


def _execute_sampling(
    node_name: str,
    prompt: str,
    state_key: str,
    timeout: int,
) -> dict:
    """Execute copilot via MCP sampling backend.

    REQ-YG-088: Calls session.create_message() when in MCP server context.

    Args:
        node_name: Name of the node for error messages
        prompt: Rendered prompt text
        state_key: Where to store result
        timeout: Timeout in seconds for the sampling call

    Returns:
        State update dict with CopilotResult
    """
    from yamlgraph.mcp_context import get_mcp_context

    session, loop = get_mcp_context()
    if session is None or loop is None:
        raise RuntimeError(
            f"Sampling backend for node '{node_name}' requires MCP server context. "
            f"Run the graph via the YAMLGraph MCP server, or use backend='cli'."
        )

    # Lazy import mcp.types to avoid hard dependency for non-MCP usage
    import mcp.types as types

    logger.info(f"[{node_name}] Executing copilot sampling with timeout={timeout}s")

    coro = session.create_message(
        messages=[
            types.SamplingMessage(
                role="user",
                content=types.TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=4096,
    )

    future = asyncio.run_coroutine_threadsafe(coro, loop)
    result = future.result(timeout=timeout)

    # Extract response text - handle both TextContent and string fallback
    if hasattr(result.content, "text"):
        response_text = result.content.text
    else:
        response_text = str(result.content)

    model_used = getattr(result, "model", None)

    logger.info(f"[{node_name}] Copilot sampling completed successfully")

    return {
        state_key: CopilotResult(
            output=response_text,
            exit_code=0,
            model=model_used,
            backend="sampling",
        ),
        "current_step": node_name,
    }


__all__ = ["create_copilot_node"]
