"""LLM node factories — FR-223 decomposed phases.

Creates LangGraph nodes that invoke LLM prompts.
Each execution phase is an independently testable function.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from yamlgraph.constants import NodeType
from yamlgraph.error_handlers import check_loop_limit, check_requirements
from yamlgraph.executor import execute_prompt
from yamlgraph.models import PipelineError
from yamlgraph.node_factory.base import GraphState, get_output_model_for_node
from yamlgraph.node_factory.llm_execution import (
    apply_verification as _apply_verification,
)
from yamlgraph.node_factory.llm_execution import (
    handle_error as _handle_error,
)
from yamlgraph.node_factory.llm_execution import (
    resolve_route as _resolve_route,
)
from yamlgraph.node_factory.llm_execution import (
    should_skip_if_exists as _should_skip_if_exists,
)
from yamlgraph.utils.expressions import (
    resolve_config_state_ref,
    resolve_node_variables,
)
from yamlgraph.utils.guard_runtime import (
    evaluate_guards_once,
    extract_guard_rules,
)
from yamlgraph.utils.json_extract import extract_json

logger = logging.getLogger(__name__)


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
    candidates: list[dict[str, Any]] | None = field(default=None)
    timeout: float | None = field(default=None)
    guards_pre: list[dict[str, Any]] = field(default_factory=list)
    guards_post: list[dict[str, Any]] = field(default_factory=list)
    default_provider: str | None = field(default=None)
    default_model: str | None = field(default=None)


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
    guards_pre, guards_post = extract_guard_rules(node_config)

    return LLMNodeConfig(
        prompt_name=node_config.get("prompt"),
        state_key=node_config.get("state_key", node_name),
        provider=node_config.get("provider", defaults.get("provider")),
        model=node_config.get("model", defaults.get("model")),
        default_provider=defaults.get("provider"),
        default_model=defaults.get("model"),
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
        candidates=node_config.get("candidates"),
        timeout=node_config.get("timeout"),
        guards_pre=guards_pre,
        guards_post=guards_post,
    )


def _evaluate_pre_guards(
    cfg: LLMNodeConfig,
    node_name: str,
    state: dict,
    loop_counts: dict,
) -> tuple[list[PipelineError], dict | None]:
    """Evaluate pre-guards and return either errors or an early state update."""
    guard_errors: list[PipelineError] = []
    pre_decision = evaluate_guards_once(
        node_name=node_name,
        phase="pre",
        rules=cfg.guards_pre,
        state=state,
        output=None,
    )
    guard_errors.extend(pre_decision.warnings)

    if pre_decision.action == "skip":
        if pre_decision.violation is not None:
            guard_errors.append(pre_decision.violation)
        return guard_errors, {
            cfg.state_key: None,
            "current_step": node_name,
            "_loop_counts": loop_counts,
            "_skipped": True,
            "_skip_reason": "guard",
            "errors": guard_errors,
        }

    if pre_decision.action == "halt":
        if pre_decision.violation is not None:
            guard_errors.append(pre_decision.violation)
        return guard_errors, {
            "errors": guard_errors,
            "current_step": node_name,
            "_loop_counts": loop_counts,
        }

    return guard_errors, None


def _evaluate_post_guards(
    cfg: LLMNodeConfig,
    node_name: str,
    state: dict,
    result: Any,
    loop_counts: dict,
    attempt_execute: Callable[[str | None], tuple[Any, Exception | None]],
) -> tuple[Any, list[PipelineError], dict | None]:
    """Evaluate post-guards, including retry policy."""
    guard_errors: list[PipelineError] = []
    post_retry_budget = {
        i: int(rule.get("max_retries", 1))
        for i, rule in enumerate(cfg.guards_post)
        if rule.get("on_fail") == "retry"
    }

    while True:
        post_decision = evaluate_guards_once(
            node_name=node_name,
            phase="post",
            rules=cfg.guards_post,
            state=state,
            output=result,
        )
        guard_errors.extend(post_decision.warnings)

        if post_decision.action is None:
            return result, guard_errors, None

        can_retry = (
            post_decision.action == "retry"
            and post_decision.failed_rule_index is not None
            and post_retry_budget.get(post_decision.failed_rule_index, 0) > 0
        )
        if can_retry:
            post_retry_budget[post_decision.failed_rule_index] -= 1
            retry_result, retry_error = attempt_execute(cfg.provider)
            if retry_error is not None:
                update = _handle_error(
                    cfg, node_name, retry_error, state, loop_counts, attempt_execute
                )
                return result, guard_errors, update
            if cfg.parse_json and isinstance(retry_result, str):
                retry_result = extract_json(retry_result)
            result = retry_result
            continue

        if post_decision.violation is not None:
            guard_errors.append(post_decision.violation)
        # FR-632: Normalize Pydantic at boundary even on guard violation path
        normalized = _normalize_result(result)
        return (
            result,
            guard_errors,
            {
                cfg.state_key: normalized,
                "current_step": node_name,
                "_loop_counts": loop_counts,
                "errors": guard_errors,
            },
        )


def _normalize_result(result: Any) -> Any:
    """FR-632: Normalize Pydantic models to dicts at the LLM output boundary."""
    if hasattr(result, "model_dump") and hasattr(type(result), "model_fields"):
        return result.model_dump()
    return result


def _run_node(
    cfg: LLMNodeConfig,
    node_name: str,
    state: dict,
    graph_path: Path | None,
) -> dict:  # noqa: C901
    """Execute one llm/router node with guards, verification, and routing."""
    loop_counts = dict(state.get("_loop_counts") or {})
    current_count = loop_counts.get(node_name, 0)

    if check_loop_limit(node_name, cfg.loop_limit, current_count):
        return {"_loop_limit_reached": True, "current_step": node_name}

    loop_counts[node_name] = current_count + 1
    if _should_skip_if_exists(cfg.skip_if_exists, cfg.state_key, state):
        logger.info(f"Node {node_name} skipped - {cfg.state_key} already in state")
        return {"current_step": node_name, "_loop_counts": loop_counts}

    if req_error := check_requirements(cfg.requires, state, node_name):
        return {
            "errors": [req_error],
            "current_step": node_name,
            "_loop_counts": loop_counts,
        }

    guard_errors, pre_update = _evaluate_pre_guards(
        cfg=cfg,
        node_name=node_name,
        state=state,
        loop_counts=loop_counts,
    )
    if pre_update is not None:
        return pre_update

    variables = resolve_node_variables(cfg.variable_templates, state)
    resolved_model = resolve_config_state_ref(
        cfg.model, state, cfg.default_model, "model"
    )
    resolved_provider = resolve_config_state_ref(
        cfg.provider, state, cfg.default_provider, "provider"
    )
    if cfg.candidates and cfg.node_type == NodeType.ROUTER:
        from yamlgraph.node_factory.router_race_node import _execute_router_race

        return _execute_router_race(
            cfg, node_name, variables, state, loop_counts, graph_path
        )

    def attempt_execute(
        use_provider: str | None, feedback: str | None = None
    ) -> tuple[Any, Exception | None]:
        try:
            result = execute_prompt(
                prompt_name=cfg.prompt_name,
                variables=variables,
                output_model=cfg.output_model,
                temperature=cfg.temperature,
                provider=resolve_config_state_ref(
                    use_provider, state, cfg.default_provider, "provider"
                ),
                model=resolved_model,
                graph_path=graph_path,
                prompts_dir=cfg.prompts_dir,
                prompts_relative=cfg.prompts_relative,
                state=state,
                max_tokens=cfg.max_tokens,
                thinking_budget=cfg.thinking_budget,
                retry_feedback=feedback,
            )
            return result, None
        except Exception as error:
            return None, error

    result, error = attempt_execute(resolved_provider)
    if error is not None:
        return _handle_error(cfg, node_name, error, state, loop_counts, attempt_execute)

    if cfg.parse_json and isinstance(result, str):
        result = extract_json(result)

    result, post_guard_errors, post_update = _evaluate_post_guards(
        cfg=cfg,
        node_name=node_name,
        state=state,
        result=result,
        loop_counts=loop_counts,
        attempt_execute=attempt_execute,
    )
    guard_errors.extend(post_guard_errors)
    if post_update is not None:
        return post_update

    # FR-632: Normalize Pydantic models to dicts at the LLM output boundary.
    # Downstream nodes (Jinja2 tojson, write_data_file) expect plain dicts.
    result = _normalize_result(result)

    result, violation = _apply_verification(
        cfg, node_name, result, state, attempt_execute
    )
    if violation is not None:
        guard_errors.append(violation)
        return {
            cfg.state_key: result,
            "current_step": node_name,
            "_loop_counts": loop_counts,
            "errors": guard_errors,
        }

    logger.info(f"Node {node_name} completed successfully")
    update: dict[str, Any] = {
        cfg.state_key: result,
        "current_step": node_name,
        "_loop_counts": loop_counts,
    }
    route, route_key = _resolve_route(cfg, result)
    if route is not None:
        update["_route"] = route
        if route_key is not None:
            update[cfg.state_key] = route_key
        logger.info(f"Router {node_name} routing to: {route}")
    if guard_errors:
        update["errors"] = guard_errors
    return update


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
    cfg = resolve_llm_node_config(node_name, node_config, defaults, graph_path)

    def node_fn(state: dict) -> dict:
        """Generated node function."""
        return _run_node(
            cfg=cfg, node_name=node_name, state=state, graph_path=graph_path
        )

    node_fn.__name__ = f"{node_name}_node"
    return node_fn
