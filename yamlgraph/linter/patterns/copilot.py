"""Copilot pattern linter validations.

Validates copilot nodes follow YAMLGraph copilot pattern requirements:
- FR-105: resume and continue_session are mutually exclusive
"""

from pathlib import Path
from typing import Any

from yamlgraph.linter.checks import LintIssue, load_graph


def check_copilot_node_structure(
    node_name: str,
    node_config: dict[str, Any],
    graph_defaults: dict[str, Any] | None = None,
) -> list[LintIssue]:
    """Check copilot node structural requirements.

    Args:
        node_name: Name of the copilot node
        node_config: Node configuration dict

    Returns:
        List of validation issues
    """
    issues = []

    graph_defaults = graph_defaults or {}
    backend = node_config.get("backend") or "cli"
    backend = backend.lower() if isinstance(backend, str) else "cli"

    cli_flags = node_config.get("cli_flags", {})
    if not isinstance(cli_flags, dict):
        cli_flags = {}

    if backend == "api":
        has_model_signal = bool(node_config.get("model") or graph_defaults.get("model"))
        if not has_model_signal:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W-COPILOT-API-MODEL",
                    message=(
                        f"Copilot node '{node_name}' uses backend='api' without an "
                        "explicit model signal (node.model or defaults.model)"
                    ),
                    fix="Set node.model or graph defaults.model for API backend nodes",
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

        if cli_only_flags:
            joined_flags = ", ".join(cli_only_flags)
            issues.append(
                LintIssue(
                    severity="error",
                    code="E-COPILOT-API-FLAGS",
                    message=(
                        f"Copilot node '{node_name}' uses backend='api' with "
                        f"CLI-only flags: {joined_flags}"
                    ),
                    fix=(
                        "Remove CLI-only cli_flags for backend='api' or switch "
                        "backend to 'cli'"
                    ),
                )
            )

        return issues

    # E-COPILOT-RESUME: resume and continue_session are mutually exclusive
    has_resume = cli_flags.get("resume") is not None
    has_continue = cli_flags.get("continue_session") is True

    if has_resume and has_continue:
        issues.append(
            LintIssue(
                severity="error",
                code="E-COPILOT-RESUME",
                message=(
                    f"Copilot node '{node_name}' has both 'resume' and "
                    "'continue_session' set; these are mutually exclusive"
                ),
                fix="Use either 'resume: <session_id>' OR 'continue_session: true', not both",
            )
        )

    # W-COPILOT-SESSION: Warning if resume looks like a state expression but
    # doesn't reference a likely session_id path
    if has_resume:
        resume_val = cli_flags.get("resume", "")
        if (
            isinstance(resume_val, str)
            and "{state." in resume_val
            and ".session_id" not in resume_val
        ):
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W-COPILOT-SESSION",
                    message=(
                        f"Copilot node '{node_name}' resume expression "
                        f"'{resume_val}' doesn't reference .session_id"
                    ),
                    fix="Use '{state.prev_result.session_id}' pattern for session continuation",
                )
            )

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
