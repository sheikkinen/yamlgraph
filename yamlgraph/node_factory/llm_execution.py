"""Execution helpers extracted from llm_nodes for module size discipline."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from yamlgraph.constants import ErrorHandler, NodeType
from yamlgraph.error_handlers import (
    handle_default,
    handle_fail,
    handle_fallback,
    handle_retry,
    handle_skip,
)
from yamlgraph.models import PipelineError
from yamlgraph.utils.json_extract import extract_json
from yamlgraph.verification import VerificationError, evaluate_verification

logger = logging.getLogger(__name__)

ExecuteFn = Callable[[str | None], tuple[Any, Exception | None]]


def should_skip_if_exists(skip_if_exists: bool, state_key: str, state: dict) -> bool:
    """FR-050 skip policy: skip only when target value is truthy."""
    if not skip_if_exists:
        return False
    return bool(state.get(state_key))


def apply_verification(
    cfg: Any,
    node_name: str,
    result: Any,
    state: dict,
    attempt_execute: ExecuteFn,
) -> tuple[Any, Any]:
    """Apply verification gate with optional retry (FR-164)."""
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

    logger.warning(
        f"⚠ Verification violated [{node_name}]: "
        f'predicted "{cfg.verification_question}", '
        f"got {repr(result)} "
        f"(check: {violation.check_type}, on_fail: {cfg.verification_on_fail})"
    )
    return result, violation


def resolve_route(cfg: Any, result: Any) -> tuple[str | None, Any]:
    """Resolve router route target from node result (FR-107)."""
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


def handle_error(
    cfg: Any,
    node_name: str,
    error: Exception,
    state: dict,
    loop_counts: dict,
    attempt_execute: ExecuteFn,
) -> dict:
    """Dispatch node execution error to configured error strategy."""
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


__all__ = [
    "ExecuteFn",
    "apply_verification",
    "handle_error",
    "resolve_route",
    "should_skip_if_exists",
]
