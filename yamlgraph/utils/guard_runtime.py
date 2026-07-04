"""Shared node guard runtime helpers for all guard-bearing node types.

Hosted in the bottom (side-effect) tier so both Layer 2 node factories
(llm/router/copilot) and Layer 3 tool factories (shell tool, python, agent)
can share one guard evaluation contract without crossing import boundaries.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from yamlgraph.models import ErrorType, GuardViolation, PipelineError
from yamlgraph.utils.guard_evaluator import (
    GuardExpressionError,
    evaluate_guard_expression,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuardDecision:
    """Result of evaluating a guard phase once."""

    action: str | None
    violation: GuardViolation | None
    warnings: list[GuardViolation]
    failed_rule_index: int | None


def _to_rule_dict(rule: Any) -> dict[str, Any]:
    if hasattr(rule, "model_dump"):
        dumped = rule.model_dump(exclude_none=True)
        return dumped if isinstance(dumped, dict) else {}
    return dict(rule) if isinstance(rule, dict) else {}


def extract_guard_rules(
    node_config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract normalized pre/post guard rule dicts from node config."""
    guards_cfg = node_config.get("guards")
    if guards_cfg is None:
        return [], []
    if hasattr(guards_cfg, "model_dump"):
        guards_cfg = guards_cfg.model_dump(exclude_none=True)
    if not isinstance(guards_cfg, dict):
        return [], []

    pre_raw = guards_cfg.get("pre") or []
    post_raw = guards_cfg.get("post") or []
    pre = [_to_rule_dict(rule) for rule in pre_raw]
    post = [_to_rule_dict(rule) for rule in post_raw]
    return pre, post


def _build_guard_violation(
    node_name: str,
    phase: str,
    rule: dict[str, Any],
    actual: Any,
    *,
    message_override: str | None = None,
) -> GuardViolation:
    check = str(rule.get("check", ""))
    on_fail = str(rule.get("on_fail", "halt"))
    message = (
        message_override
        or rule.get("message")
        or f"Guard {phase} check failed: {check}"
    )
    return GuardViolation(
        type=ErrorType.GUARD_ERROR,
        message=message,
        node=node_name,
        retryable=False,
        phase=phase,
        check=check,
        actual=repr(actual),
        on_fail=on_fail,
    )


def evaluate_guards_once(
    node_name: str,
    phase: str,
    rules: list[dict[str, Any]],
    state: dict[str, Any],
    output: Any,
) -> GuardDecision:
    """Evaluate all rules in one phase once (no retry loop)."""
    warnings: list[GuardViolation] = []
    for index, rule in enumerate(rules):
        check = str(rule.get("check", "")).strip()
        action = str(rule.get("on_fail", "halt"))
        try:
            passed = evaluate_guard_expression(check, state=state, output=output)
        except GuardExpressionError as exc:
            violation = _build_guard_violation(
                node_name=node_name,
                phase=phase,
                rule=rule,
                actual=f"expression_error:{exc}",
                message_override=f"Invalid guard expression: {exc}",
            )
            return GuardDecision(
                action="halt",
                violation=violation,
                warnings=warnings,
                failed_rule_index=index,
            )

        if passed:
            continue

        violation = _build_guard_violation(
            node_name=node_name,
            phase=phase,
            rule=rule,
            actual=False,
        )
        if action == "warn":
            warnings.append(violation)
            continue
        return GuardDecision(
            action=action,
            violation=violation,
            warnings=warnings,
            failed_rule_index=index,
        )

    return GuardDecision(
        action=None,
        violation=None,
        warnings=warnings,
        failed_rule_index=None,
    )


class GuardHaltError(RuntimeError):
    """Raised when a side-effect node's guard halts (or exhausts retries).

    Side-effect nodes (shell tool, python, agent) cannot silently return an
    error-state dict the way LLM nodes do, because their output is consumed as
    a concrete value. A failed ``on_fail: halt`` guard therefore raises, making
    the violation loud at the exact boundary where it occurred.
    """

    def __init__(self, violation: GuardViolation) -> None:
        self.violation = violation
        super().__init__(violation.message)


def _log_guard_warnings(warnings: list[GuardViolation]) -> None:
    for warning in warnings:
        logger.warning("Guard warning [%s]: %s", warning.node, warning.message)


def enforce_pre_guards(
    node_name: str,
    rules: list[dict[str, Any]],
    state: dict[str, Any],
) -> bool:
    """Evaluate pre-guards for a side-effect node.

    Returns ``True`` when the node should skip execution (``on_fail: skip``),
    ``False`` to proceed. Raises :class:`GuardHaltError` on ``on_fail: halt``.
    ``on_fail: warn`` violations are logged and do not block.
    """
    decision = evaluate_guards_once(node_name, "pre", rules, state, None)
    _log_guard_warnings(decision.warnings)
    if decision.action == "halt":
        raise GuardHaltError(decision.violation)  # type: ignore[arg-type]
    return decision.action == "skip"


def enforce_post_guards(
    node_name: str,
    rules: list[dict[str, Any]],
    state: dict[str, Any],
    output: Any,
    *,
    execute: Callable[[], Any] | None = None,
) -> Any:
    """Evaluate post-guards for a side-effect node.

    Re-executes via ``execute`` when a failing rule uses ``on_fail: retry``
    (bounded per-rule by ``max_retries``). Returns the final output. Raises
    :class:`GuardHaltError` on ``on_fail: halt`` or when retries are exhausted.
    ``on_fail: warn`` violations are logged and do not block.
    """
    retry_budget = {
        index: int(rule.get("max_retries") or 1)
        for index, rule in enumerate(rules)
        if str(rule.get("on_fail", "halt")) == "retry"
    }
    while True:
        decision = evaluate_guards_once(node_name, "post", rules, state, output)
        _log_guard_warnings(decision.warnings)
        if decision.action is None:
            return output
        can_retry = (
            decision.action == "retry"
            and execute is not None
            and decision.failed_rule_index is not None
            and retry_budget.get(decision.failed_rule_index, 0) > 0
        )
        if can_retry:
            retry_budget[decision.failed_rule_index] -= 1  # type: ignore[index]
            output = execute()
            continue
        raise GuardHaltError(decision.violation)  # type: ignore[arg-type]


def create_verify_node(rules: list[Any]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a terminal graph-level verification node function (FR-677).

    Evaluated once against final state before END. ``on_fail: halt`` raises
    GuardHaltError with the rule message; ``on_fail: warn`` logs and appends a
    PipelineError to ``state.errors``. No retry — a completed run has nothing to
    re-execute.
    """
    rule_dicts = [_to_rule_dict(rule) for rule in rules]

    def node_fn(state: dict[str, Any]) -> dict[str, Any]:
        decision = evaluate_guards_once("__verify__", "verify", rule_dicts, state, None)
        new_errors: list[PipelineError] = []
        for warning in decision.warnings:
            logger.warning("Verify warning: %s", warning.message)
            new_errors.append(
                PipelineError(
                    node="__verify__",
                    type=ErrorType.GUARD_ERROR,
                    message=warning.message,
                )
            )
        if decision.action == "halt":
            raise GuardHaltError(decision.violation)  # type: ignore[arg-type]
        # ``errors`` uses an add-reducer: return only the new deltas.
        return {"current_step": "__verify__", "errors": new_errors}

    return node_fn


__all__ = [
    "GuardDecision",
    "GuardHaltError",
    "create_verify_node",
    "enforce_post_guards",
    "enforce_pre_guards",
    "evaluate_guards_once",
    "extract_guard_rules",
]
