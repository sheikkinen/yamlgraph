"""Copilot pattern linter validations.

Validates copilot nodes follow YAMLGraph copilot pattern requirements:
- FR-105: resume and continue_session are mutually exclusive
"""

from pathlib import Path
from typing import Any

from yamlgraph.linter.checks import LintIssue, load_graph


def check_copilot_node_structure(
    node_name: str, node_config: dict[str, Any]
) -> list[LintIssue]:
    """Check copilot node structural requirements.

    Args:
        node_name: Name of the copilot node
        node_config: Node configuration dict

    Returns:
        List of validation issues
    """
    issues = []

    cli_flags = node_config.get("cli_flags", {})

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
    # doesn't reference a likely session_id path.
    # FR-168: Also accept direct session_id variable names (cross-graph handoff)
    if has_resume:
        resume_val = cli_flags.get("resume", "")
        if (
            isinstance(resume_val, str)
            and "{state." in resume_val
            and "session_id" not in resume_val
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

    for node_name, node_config in nodes.items():
        if node_config.get("type") == "copilot":
            issues.extend(check_copilot_node_structure(node_name, node_config))

    return issues
