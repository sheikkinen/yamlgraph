"""A2A call pattern linter validations — FR-240.

Validates a2a_call nodes follow structural requirements:
- Required field: agent_url (E901)
- Required field: message (E902)
- Required field: state_key (E903)
"""

from pathlib import Path
from typing import Any

from yamlgraph.linter.checks import LintIssue, load_graph


def check_a2a_call_node_structure(
    node_name: str, node_config: dict[str, Any]
) -> list[LintIssue]:
    """Check a2a_call node structural requirements.

    Args:
        node_name: Name of the a2a_call node
        node_config: Node configuration dict

    Returns:
        List of validation issues
    """
    issues = []

    # E901: missing required field 'agent_url'
    if not node_config.get("agent_url"):
        issues.append(
            LintIssue(
                severity="error",
                code="E901",
                message=f"a2a_call node '{node_name}' missing required field 'agent_url'",
                fix="Add 'agent_url' field with the A2A agent server URL",
            )
        )

    # E902: missing required field 'message'
    if not node_config.get("message"):
        issues.append(
            LintIssue(
                severity="error",
                code="E902",
                message=f"a2a_call node '{node_name}' missing required field 'message'",
                fix="Add 'message' field with the Jinja2 template for the agent message",
            )
        )

    # E903: missing required field 'state_key'
    if not node_config.get("state_key"):
        issues.append(
            LintIssue(
                severity="error",
                code="E903",
                message=f"a2a_call node '{node_name}' missing required field 'state_key'",
                fix="Add 'state_key' field to specify where to store the agent response",
            )
        )

    return issues


def check_a2a_call_patterns(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Validate all a2a_call nodes in the graph follow pattern requirements.

    Args:
        graph_path: Path to the graph YAML file
        project_root: Project root directory (unused, kept for API consistency)

    Returns:
        List of all a2a_call-related validation issues
    """
    issues = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") == "a2a_call":
            issues.extend(check_a2a_call_node_structure(node_name, node_config))

    return issues


__all__ = [
    "check_a2a_call_patterns",
    "check_a2a_call_node_structure",
]
