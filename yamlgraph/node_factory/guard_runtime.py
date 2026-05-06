"""Shared node guard runtime helpers for llm/router/copilot nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yamlgraph.models import ErrorType, GuardViolation
from yamlgraph.utils.guard_evaluator import (
    GuardExpressionError,
    evaluate_guard_expression,
)


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


__all__ = ["GuardDecision", "evaluate_guards_once", "extract_guard_rules"]
