"""Copilot pattern linter validations.

Validates copilot nodes follow YAMLGraph copilot pattern requirements:
- FR-105: resume and continue_session are mutually exclusive
- FR-383: backend-aware checks for `backend: api` (REQ-YG-357)
- FR-959: closed backend set, typed Claude flags, availability vs approval
  (REQ-YG-640)
"""

import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from yamlgraph.linter.checks import LintIssue, load_graph
from yamlgraph.models.schemas import (
    CLAUDE_ONLY_CLI_FLAGS,
    COPILOT_BACKENDS,
    ClaudeCliFlags,
)

# Models that only exist behind Copilot CLI (gpt-*, the *-sol variants).
_COPILOT_ONLY_MODEL = re.compile(r"^gpt-|-sol$")


def _issue(severity: str, code: str, message: str, fix: str) -> LintIssue:
    return LintIssue(severity=severity, code=code, message=message, fix=fix)


def _check_api_backend(
    node_name: str,
    node_config: dict[str, Any],
    cli_flags: dict[str, Any],
    graph_defaults: dict[str, Any],
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    has_model_signal = bool(node_config.get("model") or graph_defaults.get("model"))
    if not has_model_signal:
        issues.append(
            _issue(
                "warning",
                "W-COPILOT-API-MODEL",
                f"Copilot node '{node_name}' uses backend='api' without an "
                "explicit model signal (node.model or defaults.model)",
                "Set node.model or graph defaults.model for API backend nodes",
            )
        )

    cli_only_flags: list[str] = []
    if cli_flags.get("allow_all_tools"):
        cli_only_flags.append("allow_all_tools")
    if cli_flags.get("allow_all_paths"):
        cli_only_flags.append("allow_all_paths")
    if cli_flags.get("resume") is not None:
        cli_only_flags.append("resume")
    if cli_flags.get("continue_session") is True:
        cli_only_flags.append("continue_session")
    cli_only_flags.extend(k for k in CLAUDE_ONLY_CLI_FLAGS if k in cli_flags)

    if cli_only_flags:
        joined_flags = ", ".join(cli_only_flags)
        issues.append(
            _issue(
                "error",
                "E-COPILOT-API-FLAGS",
                f"Copilot node '{node_name}' uses backend='api' with "
                f"CLI-only flags: {joined_flags}",
                "Remove CLI-only cli_flags for backend='api' or switch backend to 'cli'",
            )
        )
    return issues


def _check_claude_backend(
    node_name: str,
    node_config: dict[str, Any],
    cli_flags: dict[str, Any],
    graph_defaults: dict[str, Any],
) -> list[LintIssue]:
    """FR-959 REQ-YG-640 rules for backend='claude'."""
    issues: list[LintIssue] = []
    try:
        ClaudeCliFlags.model_validate(cli_flags)
    except ValidationError as e:
        issues.append(
            _issue(
                "error",
                "E-COPILOT-CLAUDE-FLAG-SHAPE",
                f"Copilot node '{node_name}' has malformed cli_flags for "
                f"backend='claude': {e.error_count()} error(s): "
                + "; ".join(
                    f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
                    for err in e.errors()
                ),
                "tools/allowed_tools are list[str]; max_turns a positive int; "
                "switches are booleans; no unknown keys",
            )
        )
        return issues  # shape is wrong; the remaining checks would be noise

    if node_config.get("provider"):
        issues.append(
            _issue(
                "error",
                "E-COPILOT-CLAUDE-PROVIDER",
                f"Copilot node '{node_name}' sets provider with backend='claude'; "
                "provider selection is an API-key payer signal",
                "Remove 'provider' — the claude backend bills the subscription only",
            )
        )
    if cli_flags.get("allow_all_tools") and cli_flags.get("allowed_tools"):
        issues.append(
            _issue(
                "warning",
                "W-COPILOT-CLAUDE-TOOLS",
                f"Copilot node '{node_name}' sets allow_all_tools with "
                "allowed_tools; the narrow approval list is dead",
                "Drop allow_all_tools (keep the narrow list) or drop allowed_tools",
            )
        )
    if cli_flags.get("allowed_tools") and cli_flags.get("tools") is None:
        issues.append(
            _issue(
                "warning",
                "W-COPILOT-CLAUDE-APPROVE-WITHOUT-RESTRICT",
                f"Copilot node '{node_name}' auto-approves allowed_tools but "
                "leaves every default tool available (no 'tools' list)",
                "Add 'tools: [...]' — allowed_tools approves, it does not restrict",
            )
        )
    # Same precedence the runtime uses (FR-266): cli_flags > node > defaults.
    model = (
        cli_flags.get("model")
        or node_config.get("model")
        or graph_defaults.get("model")
    )
    if isinstance(model, str) and _COPILOT_ONLY_MODEL.search(model):
        issues.append(
            _issue(
                "warning",
                "W-COPILOT-CLAUDE-MODEL",
                f"Copilot node '{node_name}' model '{model}' looks Copilot-only; "
                "Claude Code will not resolve it",
                "Use a Claude alias ('opus', 'sonnet') or full claude-* id",
            )
        )
    return issues


def _check_session_flags(node_name: str, cli_flags: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    has_resume = cli_flags.get("resume") is not None
    has_continue = cli_flags.get("continue_session") is True

    # E-COPILOT-RESUME: resume and continue_session are mutually exclusive
    if has_resume and has_continue:
        issues.append(
            _issue(
                "error",
                "E-COPILOT-RESUME",
                f"Copilot node '{node_name}' has both 'resume' and "
                "'continue_session' set; these are mutually exclusive",
                "Use either 'resume: <session_id>' OR 'continue_session: true', not both",
            )
        )

    # W-COPILOT-SESSION: resume looks like a state expression but doesn't
    # reference a likely session_id path
    if has_resume:
        resume_val = cli_flags.get("resume", "")
        if (
            isinstance(resume_val, str)
            and "{state." in resume_val
            and ".session_id" not in resume_val
        ):
            issues.append(
                _issue(
                    "warning",
                    "W-COPILOT-SESSION",
                    f"Copilot node '{node_name}' resume expression "
                    f"'{resume_val}' doesn't reference .session_id",
                    "Use '{state.prev_result.session_id}' pattern for session continuation",
                )
            )
    return issues


def check_copilot_node_structure(
    node_name: str,
    node_config: dict[str, Any],
    graph_defaults: dict[str, Any] | None = None,
) -> list[LintIssue]:
    """Check copilot node structural requirements.

    Args:
        node_name: Name of the copilot node
        node_config: Node configuration dict
        graph_defaults: Graph-level defaults (model signal for backend=api)

    Returns:
        List of validation issues
    """
    graph_defaults = graph_defaults or {}
    raw_backend = node_config.get("backend")
    if raw_backend is None:
        backend = "cli"
    elif isinstance(raw_backend, str) and raw_backend in COPILOT_BACKENDS:
        backend = raw_backend  # exact match, same as the schema Literal (P4)
    else:
        return [
            _issue(
                "error",
                "E-COPILOT-BACKEND-UNKNOWN",
                f"Copilot node '{node_name}' has unknown backend {raw_backend!r}; "
                f"expected one of {', '.join(COPILOT_BACKENDS)}",
                "Fix the backend value — unknown values never fall back to Copilot",
            )
        ]

    cli_flags = node_config.get("cli_flags", {})
    if not isinstance(cli_flags, dict):
        cli_flags = {}

    if backend == "api":
        return _check_api_backend(node_name, node_config, cli_flags, graph_defaults)

    issues: list[LintIssue] = []
    if backend == "claude":
        issues.extend(
            _check_claude_backend(node_name, node_config, cli_flags, graph_defaults)
        )
    elif backend == "cli":
        claude_keys = [k for k in CLAUDE_ONLY_CLI_FLAGS if k in cli_flags]
        if claude_keys:
            issues.append(
                _issue(
                    "error",
                    "E-COPILOT-CLI-FLAGS",
                    f"Copilot node '{node_name}' uses backend='cli' with "
                    f"claude-only flags: {', '.join(claude_keys)}",
                    "Remove tools/allowed_tools/max_turns or set backend: claude",
                )
            )

    issues.extend(_check_session_flags(node_name, cli_flags))
    return issues


def check_copilot_patterns(graph_path: Path) -> list[LintIssue]:
    """Run all copilot pattern validations on a graph file.

    Args:
        graph_path: Path to graph YAML file

    Returns:
        List of all detected issues
    """
    config = load_graph(graph_path)
    if config is None:
        return []

    issues = []
    nodes = config.get("nodes", {})
    defaults = config.get("defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}

    for node_name, node_config in nodes.items():
        if node_config.get("type") == "copilot":
            issues.extend(
                check_copilot_node_structure(
                    node_name,
                    node_config,
                    graph_defaults=defaults,
                )
            )

    return issues
