"""Race pattern linter validations — FR-232.

Validates race nodes follow YAMLGraph race pattern requirements:
- Required field: candidates (list with ≥ 2 entries)
- Each candidate must specify provider or model
- Required field: prompt
"""

from pathlib import Path
from typing import Any

from yamlgraph.linter.checks import LintIssue, load_graph


def check_race_node_structure(
    node_name: str, node_config: dict[str, Any]
) -> list[LintIssue]:
    """Check race node structural requirements.

    Args:
        node_name: Name of the race node
        node_config: Node configuration dict

    Returns:
        List of validation issues
    """
    issues = []

    # E301: missing required field 'candidates'
    candidates = node_config.get("candidates")
    if not candidates:
        issues.append(
            LintIssue(
                severity="error",
                code="E301",
                message=f"Race node '{node_name}' missing required field 'candidates'",
                fix="Add 'candidates' field with ≥ 2 provider/model entries",
            )
        )
        return issues  # Can't check further without candidates

    # E302: too few candidates
    if len(candidates) < 2:
        issues.append(
            LintIssue(
                severity="error",
                code="E302",
                message=(
                    f"Race node '{node_name}' has {len(candidates)} candidate(s) "
                    f"— requires at least 2 (use regular llm node for single provider)"
                ),
                fix="Add at least 2 candidates with different providers or models",
            )
        )

    # E303: candidate missing both provider and model
    for i, candidate in enumerate(candidates):
        if not candidate.get("provider") and not candidate.get("model"):
            issues.append(
                LintIssue(
                    severity="error",
                    code="E303",
                    message=(
                        f"Race node '{node_name}' candidate {i} "
                        f"must specify at least 'provider' or 'model'"
                    ),
                    fix="Add 'provider' and/or 'model' to the candidate",
                )
            )

    # E304: missing prompt
    if not node_config.get("prompt"):
        issues.append(
            LintIssue(
                severity="error",
                code="E304",
                message=f"Race node '{node_name}' missing required field 'prompt'",
                fix="Add 'prompt' field specifying the prompt template name",
            )
        )

    return issues


def check_race_patterns(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Validate all race nodes in the graph follow pattern requirements.

    Args:
        graph_path: Path to the graph YAML file
        project_root: Project root directory (unused, kept for API consistency)

    Returns:
        List of all race-related validation issues
    """
    issues = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") == "race":
            issues.extend(check_race_node_structure(node_name, node_config))

    return issues


__all__ = [
    "check_race_patterns",
    "check_race_node_structure",
]
