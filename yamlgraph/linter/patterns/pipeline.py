"""Pipeline pattern linter validations — FR-235.

Validates pipeline nodes follow structural requirements:
- E401: items must be non-empty list
- E402: stages must be non-empty list
- E403: all {item.*} references must resolve against item fields
- E404: items and stages must have 'name' field
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from yamlgraph.linter.checks import LintIssue, load_graph

_ITEM_REF_PATTERN = re.compile(r"\{item\.(\w+)\}")


def _extract_item_refs_from_value(value: Any) -> set[str]:
    """Extract {item.field} references from a value (string or dict)."""
    refs: set[str] = set()
    if isinstance(value, str):
        refs.update(_ITEM_REF_PATTERN.findall(value))
    elif isinstance(value, dict):
        for v in value.values():
            refs.update(_extract_item_refs_from_value(v))
    return refs


def check_pipeline_node_structure(
    node_name: str, node_config: dict[str, Any]
) -> list[LintIssue]:
    """Check pipeline node structural requirements.

    Args:
        node_name: Name of the pipeline node
        node_config: Node configuration dict

    Returns:
        List of validation issues
    """
    issues: list[LintIssue] = []

    # E401: items must be non-empty
    items = node_config.get("items")
    if not items:
        issues.append(
            LintIssue(
                severity="error",
                code="E401",
                message=f"Pipeline node '{node_name}' requires non-empty 'items' list",
                fix="Add at least one item with a 'name' field to 'items'",
            )
        )

    # E402: stages must be non-empty
    stages = node_config.get("stages")
    if not stages:
        issues.append(
            LintIssue(
                severity="error",
                code="E402",
                message=f"Pipeline node '{node_name}' requires non-empty 'stages' list",
                fix="Add at least one stage with 'name' and 'type' fields to 'stages'",
            )
        )

    # Can't check further without both items and stages
    if not items or not stages:
        return issues

    # E404: items must have 'name' field
    for i, item in enumerate(items):
        if not item.get("name"):
            issues.append(
                LintIssue(
                    severity="error",
                    code="E404",
                    message=(
                        f"Pipeline node '{node_name}' item {i} "
                        f"missing required 'name' field"
                    ),
                    fix="Add 'name' field to the item",
                )
            )

    # E404: stages must have 'name' field
    for i, stage in enumerate(stages):
        if not stage.get("name"):
            issues.append(
                LintIssue(
                    severity="error",
                    code="E404",
                    message=(
                        f"Pipeline node '{node_name}' stage {i} "
                        f"missing required 'name' field"
                    ),
                    fix="Add 'name' field to the stage",
                )
            )

    # E403: all {item.*} references must resolve
    # Collect all item field names (union across all items)
    all_item_fields: set[str] = set()
    for item in items:
        all_item_fields.update(item.keys())

    for stage in stages:
        for key in ("prompt", "variables", "state_key"):
            value = stage.get(key)
            if value is None:
                continue
            refs = _extract_item_refs_from_value(value)
            for ref in refs:
                if ref not in all_item_fields:
                    issues.append(
                        LintIssue(
                            severity="error",
                            code="E403",
                            message=(
                                f"Pipeline node '{node_name}' stage "
                                f"'{stage.get('name', '?')}' references "
                                f"'{{item.{ref}}}' but no item defines field '{ref}'"
                            ),
                            fix=f"Add '{ref}' field to pipeline items or fix the reference",
                        )
                    )

    return issues


def check_pipeline_patterns(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Validate all pipeline nodes in the graph.

    Args:
        graph_path: Path to the graph YAML file
        project_root: Project root directory (unused, kept for API consistency)

    Returns:
        List of all pipeline-related validation issues
    """
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    for node_name, node_config in graph.get("nodes", {}).items():
        if node_config.get("type") == "pipeline":
            issues.extend(check_pipeline_node_structure(node_name, node_config))

    return issues


__all__ = [
    "check_pipeline_patterns",
    "check_pipeline_node_structure",
]
