"""Copilot node factory.

Creates nodes that delegate to Copilot CLI.
FR-081: Copilot Node Type.
FR-105: Session Continuations.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from yamlgraph.executor import execute_prompt
from yamlgraph.models.schemas import CopilotResult
from yamlgraph.node_factory.base import GraphState, get_output_model_for_node
from yamlgraph.node_factory.copilot_runtime import (
    _execute_cli,
    normalize_backend,
    unknown_backend_message,
)
from yamlgraph.node_factory.copilot_runtime import (
    _load_and_render_prompt as _load_and_render_prompt_runtime,
)
from yamlgraph.node_factory.copilot_runtime_claude import (
    _execute_claude,
    validate_claude_cli_flags,
)
from yamlgraph.utils.expressions import resolve_state_expression
from yamlgraph.utils.guard_runtime import (
    evaluate_guards_once,
    extract_guard_rules,
)
from yamlgraph.utils.prompts import load_prompt as _load_prompt_for_compat

logger = logging.getLogger(__name__)

# Backward-compatible patch target for tests mocking prompt loading.
load_prompt = _load_prompt_for_compat

# Default timeout for copilot CLI (seconds)
DEFAULT_TIMEOUT = 300


def _load_and_render_prompt(
    prompt_path: str | Path,
    variables: dict[str, Any],
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
) -> str:
    """Render prompt text using a patchable module-level load_prompt target."""
    return _load_and_render_prompt_runtime(
        prompt_path=prompt_path,
        variables=variables,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
        load_prompt_fn=load_prompt,
    )


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


def _normalize_prompt_for_executor(
    prompt_path: str | Path,
    prompts_dir: Path | None,
    prompts_relative: bool,
) -> tuple[str, Path | None, bool]:
    """Normalize copilot prompt path for execute_prompt() resolution.

    Copilot nodes historically accepted explicit YAML file paths (including
    absolute paths with extension). execute_prompt() expects prompt names.
    """
    path_obj = Path(prompt_path)

    if path_obj.is_absolute():
        if path_obj.suffix in {".yaml", ".yml"}:
            return path_obj.stem, path_obj.parent, False
        return path_obj.name, path_obj.parent, False

    if path_obj.suffix in {".yaml", ".yml"}:
        return str(path_obj.with_suffix("")), prompts_dir, prompts_relative

    return str(prompt_path), prompts_dir, prompts_relative


def _resolve_api_backend_options(
    backend: str,
    config: dict[str, Any],
    prompt_path: str | Path,
    graph_path: Path | None,
    prompts_dir: Path | None,
    prompts_relative: bool,
) -> tuple[str, Path | None, bool, type | None]:
    """Resolve prompt/output-model options needed by backend='api'."""
    api_prompt_name = ""
    api_prompts_dir = prompts_dir
    api_prompts_relative = prompts_relative
    api_output_model = None

    if backend == "api":
        api_prompt_name, api_prompts_dir, api_prompts_relative = (
            _normalize_prompt_for_executor(
                prompt_path,
                prompts_dir=prompts_dir,
                prompts_relative=prompts_relative,
            )
        )
        api_model_config = {**config, "prompt": api_prompt_name}
        api_output_model = get_output_model_for_node(
            api_model_config,
            prompts_dir=api_prompts_dir,
            graph_path=graph_path,
            prompts_relative=api_prompts_relative,
        )

    return api_prompt_name, api_prompts_dir, api_prompts_relative, api_output_model


def _execute_backend_once(
    backend: str,
    node_name: str,
    state_key: str,
    state: dict[str, Any],
    resolved_vars: dict[str, Any],
    rendered_prompt: str,
    cli_flags: dict[str, Any],
    timeout: int,
    resolved_provider: str | None,
    resolved_model: str | None,
    api_prompt_name: str,
    api_output_model: type | None,
    graph_path: Path | None,
    api_prompts_dir: Path | None,
    api_prompts_relative: bool,
) -> dict:
    """Execute one copilot node call for the selected backend."""
    if backend == "api":
        return _execute_api(
            node_name=node_name,
            prompt_name=api_prompt_name,
            state_key=state_key,
            variables=resolved_vars,
            provider=resolved_provider,
            model=resolved_model,
            output_model=api_output_model,
            graph_path=graph_path,
            prompts_dir=api_prompts_dir,
            prompts_relative=api_prompts_relative,
            state=state,
        )
    if backend == "sampling":
        raise NotImplementedError("Copilot backend 'sampling' is not implemented")
    if backend == "claude":
        return _execute_claude(
            node_name=node_name,
            prompt=rendered_prompt,
            state_key=state_key,
            cli_flags=cli_flags,
            timeout=timeout,
            state=state,
        )
    if backend == "cli":
        return _execute_cli(
            node_name=node_name,
            prompt=rendered_prompt,
            state_key=state_key,
            cli_flags=cli_flags,
            timeout=timeout,
            state=state,  # FR-105: pass state for resume expression resolution
        )
    raise ValueError(unknown_backend_message(node_name, backend))


def create_copilot_node(
    node_name: str,
    config: dict[str, Any],
    defaults: dict[str, Any] | None = None,
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
            - model: Model name override (falls back to defaults.model)
            - cli_flags: Dict with allow_all_paths, allow_all_tools, model
            - timeout: Timeout in seconds (default 300)
            - variables: Variable mappings like {state.key}
            - requires: List of required state keys
            - on_error: Error handling strategy
            - model: Node-level model override (FR-266)
        defaults: Graph-level defaults dict (model, provider, etc.)
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path

    Returns:
        Node function compatible with LangGraph
    """
    prompt_path = config.get("prompt")
    state_key = config.get("state_key")
    backend = normalize_backend(node_name, config.get("backend"))

    cli_flags = config.get("cli_flags", {})
    validate_claude_cli_flags(node_name, cli_flags, backend)  # FR-959, before any probe
    defaults = defaults or {}

    # FR-266: Resolve model with priority chain:
    # cli_flags.model > node-level model > defaults.model > omit
    resolved_provider = config.get("provider") or defaults.get("provider")
    resolved_model = config.get("model") or defaults.get("model")
    if backend != "api":
        resolved_model = cli_flags.get("model") or resolved_model
    if resolved_model and backend != "api":
        cli_flags = {**cli_flags, "model": resolved_model}

    api_prompt_name, api_prompts_dir, api_prompts_relative, api_output_model = (
        _resolve_api_backend_options(
            backend=backend,
            config=config,
            prompt_path=prompt_path,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
            prompts_relative=prompts_relative,
        )
    )

    timeout = config.get("timeout", DEFAULT_TIMEOUT)
    variables_config = config.get("variables", {})
    guards_pre, guards_post = extract_guard_rules(config)

    if not state_key:
        raise ValueError(f"Copilot node '{node_name}' requires 'state_key'")

    def copilot_fn(state: GraphState) -> dict:
        """Execute copilot with CLI backend."""
        guard_errors = []
        pre_decision = evaluate_guards_once(
            node_name=node_name,
            phase="pre",
            rules=guards_pre,
            state=state,
            output=None,
        )
        guard_errors.extend(pre_decision.warnings)
        if pre_decision.action == "skip":
            if pre_decision.violation is not None:
                guard_errors.append(pre_decision.violation)
            return {
                state_key: None,
                "current_step": node_name,
                "_skipped": True,
                "_skip_reason": "guard",
                "errors": guard_errors,
            }
        if pre_decision.action == "halt":
            if pre_decision.violation is not None:
                guard_errors.append(pre_decision.violation)
            return {"current_step": node_name, "errors": guard_errors}

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

        def execute_once() -> dict:
            return _execute_backend_once(
                backend=backend,
                node_name=node_name,
                state_key=state_key,
                state=state,
                resolved_vars=resolved_vars,
                rendered_prompt=rendered_prompt,
                cli_flags=cli_flags,
                timeout=timeout,
                resolved_provider=resolved_provider,
                resolved_model=resolved_model,
                api_prompt_name=api_prompt_name,
                api_output_model=api_output_model,
                graph_path=graph_path,
                api_prompts_dir=api_prompts_dir,
                api_prompts_relative=api_prompts_relative,
            )

        update = execute_once()
        output = update[state_key]
        post_retry_budget = {
            i: int(rule.get("max_retries", 1))
            for i, rule in enumerate(guards_post)
            if rule.get("on_fail") == "retry"
        }
        while True:
            post_decision = evaluate_guards_once(
                node_name=node_name,
                phase="post",
                rules=guards_post,
                state=state,
                output=output,
            )
            guard_errors.extend(post_decision.warnings)
            if post_decision.action is None:
                break
            if (
                post_decision.action == "retry"
                and post_decision.failed_rule_index is not None
                and post_retry_budget.get(post_decision.failed_rule_index, 0) > 0
            ):
                post_retry_budget[post_decision.failed_rule_index] -= 1
                update = execute_once()
                output = update[state_key]
                continue
            if post_decision.violation is not None:
                guard_errors.append(post_decision.violation)
            return {
                state_key: output,
                "current_step": node_name,
                "errors": guard_errors,
            }
        if guard_errors:
            update["errors"] = guard_errors
        return update

    copilot_fn.__name__ = f"copilot_{node_name}"
    return copilot_fn


def _execute_api(
    node_name: str,
    prompt_name: str,
    state_key: str,
    variables: dict[str, Any],
    provider: str | None,
    model: str | None,
    output_model: type | None,
    graph_path: Path | None,
    prompts_dir: Path | None,
    prompts_relative: bool,
    state: dict[str, Any],
) -> dict:
    """Execute copilot via provider API backend."""
    result = execute_prompt(
        prompt_name=prompt_name,
        variables=variables,
        output_model=output_model,
        provider=provider,
        model=model,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
        state=state,
    )
    output_text = (
        result.model_dump_json() if isinstance(result, BaseModel) else str(result)
    )
    copilot_result = CopilotResult(
        output=output_text,
        exit_code=0,
        model=model,
        backend="api",
        session_id=None,
    )
    return {
        state_key: copilot_result,
        "current_step": node_name,
    }


__all__ = ["create_copilot_node"]
