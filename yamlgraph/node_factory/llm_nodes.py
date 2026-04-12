"""LLM node factories — FR-223 decomposed phases.

Creates LangGraph nodes that invoke LLM prompts.
Each execution phase is an independently testable function.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yamlgraph.constants import ErrorHandler, NodeType
from yamlgraph.error_handlers import (
    check_loop_limit,
    check_requirements,
    handle_default,
    handle_fail,
    handle_fallback,
    handle_retry,
    handle_skip,
)
from yamlgraph.executor import execute_prompt
from yamlgraph.models import PipelineError
from yamlgraph.node_factory.base import GraphState, get_output_model_for_node
from yamlgraph.utils.expressions import resolve_node_variables
from yamlgraph.utils.json_extract import extract_json
from yamlgraph.verification import VerificationError, evaluate_verification

logger = logging.getLogger(__name__)


# =============================================================================
# Phase 1: Config resolution (FR-223)
# =============================================================================


@dataclass(frozen=True)
class LLMNodeConfig:
    """Resolved, validated config for a single LLM/router node."""

    prompt_name: str | None
    state_key: str
    provider: str | None
    model: str | None
    temperature: float
    max_tokens: int | None
    thinking_budget: int | None
    output_model: type | None
    parse_json: bool
    variable_templates: dict
    requires: list[str]
    on_error: str | None
    max_retries: int
    fallback_provider: str | None
    routes: dict
    default_route: str | None
    route_field: str | None
    loop_limit: int | None
    skip_if_exists: bool
    verification_question: str | None
    verification_on_fail: str | None
    verification_max_retries: int
    prompts_dir: Path | None
    prompts_relative: bool
    node_type: str


def resolve_llm_node_config(
    node_name: str,
    node_config: dict,
    defaults: dict,
    graph_path: Path | None,
) -> LLMNodeConfig:
    """Extract and validate all config — one job, no side effects.

    Args:
        node_name: Name of the node
        node_config: Node configuration from YAML
        defaults: Default configuration values
        graph_path: Path to graph YAML file (for relative prompt resolution)

    Returns:
        Frozen LLMNodeConfig dataclass with all resolved values
    """
    node_type = node_config.get("type", NodeType.LLM)

    # Prompt resolution options from defaults
    prompts_relative = defaults.get("prompts_relative", False)
    prompts_dir = defaults.get("prompts_dir")
    if prompts_dir:
        prompts_dir = Path(prompts_dir)

    # Resolve output model
    parse_json = node_config.get("parse_json", False)
    if parse_json:
        output_model = None
    else:
        output_model = get_output_model_for_node(
            node_config,
            prompts_dir=prompts_dir,
            graph_path=graph_path,
            prompts_relative=prompts_relative,
        )

    # Temperature: node > defaults > 0.7
    temperature = node_config.get("temperature")
    if temperature is None:
        temperature = defaults.get("temperature")
    if temperature is None:
        temperature = 0.7

    # Thinking budget: node > defaults
    thinking_budget = node_config.get("thinking_budget")
    if thinking_budget is None:
        thinking_budget = defaults.get("thinking_budget")

    # Error handling
    fallback_config = node_config.get("fallback", {})
    fallback_provider = fallback_config.get("provider") if fallback_config else None

    # Verification gate (FR-164)
    verification_config = node_config.get("verification")
    if isinstance(verification_config, dict):
        verification_question = verification_config.get("question")
        verification_on_fail = verification_config.get("on_fail", "warn")
        verification_max_retries = verification_config.get("max_retries", 1)
    elif verification_config is not None:
        # VerificationConfig Pydantic model (from validated NodeConfig)
        verification_question = verification_config.question
        verification_on_fail = verification_config.on_fail
        verification_max_retries = verification_config.max_retries
    else:
        verification_question = None
        verification_on_fail = None
        verification_max_retries = 1

    return LLMNodeConfig(
        prompt_name=node_config.get("prompt"),
        state_key=node_config.get("state_key", node_name),
        provider=node_config.get("provider", defaults.get("provider")),
        model=node_config.get("model", defaults.get("model")),
        temperature=temperature,
        max_tokens=node_config.get("max_tokens", defaults.get("max_tokens")),
        thinking_budget=thinking_budget,
        output_model=output_model,
        parse_json=parse_json,
        variable_templates=node_config.get("variables", {}),
        requires=node_config.get("requires", []),
        on_error=node_config.get("on_error"),
        max_retries=node_config.get("max_retries", 3),
        fallback_provider=fallback_provider,
        routes=node_config.get("routes", {}),
        default_route=node_config.get("default_route"),
        route_field=node_config.get("route_field"),
        loop_limit=node_config.get("loop_limit"),
        skip_if_exists=node_config.get("skip_if_exists", True),
        verification_question=verification_question,
        verification_on_fail=verification_on_fail,
        verification_max_retries=verification_max_retries,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
        node_type=node_type,
    )


# =============================================================================
# Phase 2: Execution helpers (FR-223)
# =============================================================================


def _should_skip_if_exists(skip_if_exists: bool, state_key: str, state: dict) -> bool:
    """Check if node should skip based on existing state value.

    FR-050: Uses truthiness check, not existence check.
    Empty collections ([], {}), empty strings (""), None, 0, and False
    do NOT trigger skip — only truthy values do.
    """
    if not skip_if_exists:
        return False
    return bool(state.get(state_key))


ExecuteFn = Callable[[str | None], tuple[Any, Exception | None]]


def _apply_verification(
    cfg: LLMNodeConfig,
    node_name: str,
    result: Any,
    state: dict,
    attempt_execute: ExecuteFn,
) -> tuple[Any, Any]:
    """Apply verification gate with optional retry (FR-164).

    Returns:
        (result, violation) — violation is None if verification passed
    """
    if cfg.verification_question is None:
        return result, None

    violation = evaluate_verification(
        question=cfg.verification_question,
        actual=result,
        state=state,
    )
    if violation is None:
        return result, None

    violation.node = node_name

    if cfg.verification_on_fail == "halt":
        raise VerificationError(node_name, violation)

    if cfg.verification_on_fail == "retry":
        for _attempt in range(cfg.verification_max_retries):
            retry_result, retry_error = attempt_execute(cfg.provider)
            if retry_error is not None:
                break
            if cfg.parse_json and isinstance(retry_result, str):
                retry_result = extract_json(retry_result)
            retry_violation = evaluate_verification(
                question=cfg.verification_question,
                actual=retry_result,
                state=state,
            )
            if retry_violation is None:
                return retry_result, None
            result = retry_result

    # warn (default) or retry exhausted
    logger.warning(
        f"⚠ Verification violated [{node_name}]: "
        f'predicted "{cfg.verification_question}", '
        f"got {repr(result)} "
        f"(check: {violation.check_type}, on_fail: {cfg.verification_on_fail})"
    )
    return result, violation


def _resolve_route(
    cfg: LLMNodeConfig,
    result: Any,
) -> tuple[str | None, Any]:
    """Resolve router routing from result (FR-107).

    Returns:
        (route_target, store_value) — both None for non-router nodes
    """
    if cfg.node_type != NodeType.ROUTER or not cfg.routes or not cfg.route_field:
        return None, None

    if isinstance(result, dict):
        route_key = result.get(cfg.route_field)
    else:
        route_key = getattr(result, cfg.route_field, None)

    if route_key and route_key in cfg.routes:
        route = cfg.routes[route_key]
    elif cfg.default_route:
        route = cfg.default_route
    else:
        route = list(cfg.routes.values())[0]

    return route, route_key


def _handle_error(
    cfg: LLMNodeConfig,
    node_name: str,
    error: Exception,
    state: dict,
    loop_counts: dict,
    attempt_execute: ExecuteFn,
) -> dict:
    """Dispatch error to the configured strategy handler.

    Returns:
        State update dict
    """
    if cfg.on_error == ErrorHandler.SKIP:
        handle_skip(node_name, error, loop_counts)
        return {
            cfg.state_key: None,
            "current_step": node_name,
            "_loop_counts": loop_counts,
            "_skipped": True,
            "_skip_reason": "error",
            "errors": [PipelineError.from_exception(error, node=node_name)],
        }

    if cfg.on_error == ErrorHandler.FAIL:
        handle_fail(node_name, error)

    if cfg.on_error == ErrorHandler.RETRY:
        nr = handle_retry(
            node_name,
            lambda: attempt_execute(cfg.provider),
            cfg.max_retries,
        )
        return nr.to_state_update(cfg.state_key, node_name, loop_counts)

    if cfg.on_error == ErrorHandler.FALLBACK and cfg.fallback_provider:
        nr = handle_fallback(node_name, attempt_execute, cfg.fallback_provider)
        return nr.to_state_update(cfg.state_key, node_name, loop_counts)

    nr = handle_default(node_name, error)
    return nr.to_state_update(cfg.state_key, node_name, loop_counts)


# =============================================================================
# Phase 3: Orchestrator (FR-223)
# =============================================================================


def create_node_function(
    node_name: str,
    node_config: dict,
    defaults: dict,
    graph_path: Path | None = None,
) -> Callable[[GraphState], dict]:
    """Create a node function from YAML config.

    Args:
        node_name: Name of the node
        node_config: Node configuration from YAML
        defaults: Default configuration values
        graph_path: Path to graph YAML file (for relative prompt resolution)

    Returns:
        Node function compatible with LangGraph
    """
    from yamlgraph.node_factory.streaming import create_streaming_node

    # Streaming early-return (before config resolution needs output_model)
    prompts_relative = defaults.get("prompts_relative", False)
    prompts_dir = defaults.get("prompts_dir")
    if prompts_dir:
        prompts_dir = Path(prompts_dir)

    if node_config.get("stream", False):
        return create_streaming_node(
            node_name,
            node_config,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
            prompts_relative=prompts_relative,
        )

    cfg = resolve_llm_node_config(node_name, node_config, defaults, graph_path)

    def node_fn(state: dict) -> dict:  # noqa: C901
        """Generated node function."""
        loop_counts = dict(state.get("_loop_counts") or {})
        current_count = loop_counts.get(node_name, 0)

        if check_loop_limit(node_name, cfg.loop_limit, current_count):
            return {"_loop_limit_reached": True, "current_step": node_name}

        loop_counts[node_name] = current_count + 1

        # FR-050: skip on truthy existing value
        if _should_skip_if_exists(cfg.skip_if_exists, cfg.state_key, state):
            logger.info(f"Node {node_name} skipped - {cfg.state_key} already in state")
            return {"current_step": node_name, "_loop_counts": loop_counts}

        if req_error := check_requirements(cfg.requires, state, node_name):
            return {
                "errors": [req_error],
                "current_step": node_name,
                "_loop_counts": loop_counts,
            }

        variables = resolve_node_variables(cfg.variable_templates, state)

        def attempt_execute(use_provider: str | None) -> tuple[Any, Exception | None]:
            try:
                r = execute_prompt(
                    prompt_name=cfg.prompt_name,
                    variables=variables,
                    output_model=cfg.output_model,
                    temperature=cfg.temperature,
                    provider=use_provider,
                    model=cfg.model,
                    graph_path=graph_path,
                    prompts_dir=cfg.prompts_dir,
                    prompts_relative=cfg.prompts_relative,
                    state=state,
                    max_tokens=cfg.max_tokens,
                    thinking_budget=cfg.thinking_budget,
                )
                return r, None
            except Exception as e:
                return None, e

        result, error = attempt_execute(cfg.provider)

        if error is not None:
            return _handle_error(
                cfg, node_name, error, state, loop_counts, attempt_execute
            )

        # Post-process: JSON extraction if enabled
        if cfg.parse_json and isinstance(result, str):
            result = extract_json(result)

        # FR-164: Verification gate
        result, violation = _apply_verification(
            cfg, node_name, result, state, attempt_execute
        )
        if violation is not None:
            return {
                cfg.state_key: result,
                "current_step": node_name,
                "_loop_counts": loop_counts,
                "errors": [violation],
            }

        logger.info(f"Node {node_name} completed successfully")
        update: dict[str, Any] = {
            cfg.state_key: result,
            "current_step": node_name,
            "_loop_counts": loop_counts,
        }

        # Router routing (FR-107)
        route, route_key = _resolve_route(cfg, result)
        if route is not None:
            update["_route"] = route
            if route_key is not None:
                update[cfg.state_key] = route_key
            logger.info(f"Router {node_name} routing to: {route}")

        return update

    node_fn.__name__ = f"{node_name}_node"
    return node_fn
