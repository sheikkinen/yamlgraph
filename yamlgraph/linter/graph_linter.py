"""Graph linter for validating YAML graph files.

Checks for common issues:
- Missing state declarations
- Undefined tool references
- Missing prompt files
- Unreachable nodes
- Invalid node types
"""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel

from yamlgraph.linter.checks import (
    LintIssue,
    check_edge_coverage,
    check_node_types,
    check_prompt_files,
    check_state_declarations,
    check_tool_references,
)
from yamlgraph.linter.checks_contracts import (
    check_identifier_keys,
    check_python_node_variables,
    check_silent_fallback,
    check_skip_if_exists_add_reducer,
    check_skip_without_verification,
    check_top_level_provider_model,
)
from yamlgraph.linter.checks_providers import check_thinking_budget
from yamlgraph.linter.checks_semantic import (
    check_cross_references,
    check_edge_types,
    check_error_handling,
    check_expression_syntax,
    check_passthrough_nodes,
    check_skip_if_exists_in_cycle,
    check_tool_call_nodes,
    check_unguarded_cycles,
)
from yamlgraph.linter.patterns import (
    check_agent_patterns,
    check_copilot_patterns,
    check_interrupt_patterns,
    check_map_patterns,
    check_pipeline_patterns,
    check_race_patterns,
    check_router_patterns,
    check_subgraph_patterns,
)

logger = logging.getLogger(__name__)


class LintResult(BaseModel):
    """Result of linting a graph file."""

    file: str
    issues: list[LintIssue]
    valid: bool


def lint_graph(
    graph_path: Path | str, project_root: Path | str | None = None
) -> LintResult:
    """Lint a YAML graph file for issues.

    Args:
        graph_path: Path to the graph YAML file
        project_root: Root directory containing prompts/ folder

    Returns:
        LintResult with all issues found
    """
    graph_path = Path(graph_path)
    if project_root:
        project_root = Path(project_root)

    all_issues: list[LintIssue] = []

    # Run all checks
    all_issues.extend(check_state_declarations(graph_path, project_root))
    all_issues.extend(check_tool_references(graph_path))
    all_issues.extend(check_prompt_files(graph_path, project_root))
    all_issues.extend(check_edge_coverage(graph_path))
    all_issues.extend(check_node_types(graph_path))

    # FR-025: Cross-reference & semantic checks
    all_issues.extend(check_cross_references(graph_path))
    all_issues.extend(check_passthrough_nodes(graph_path))
    all_issues.extend(check_tool_call_nodes(graph_path))
    all_issues.extend(check_expression_syntax(graph_path))
    all_issues.extend(check_error_handling(graph_path))
    all_issues.extend(check_edge_types(graph_path))
    all_issues.extend(check_unguarded_cycles(graph_path))
    all_issues.extend(check_skip_if_exists_in_cycle(graph_path))

    # Pattern-specific checks
    all_issues.extend(check_router_patterns(graph_path, project_root))
    all_issues.extend(check_map_patterns(graph_path, project_root))
    all_issues.extend(check_interrupt_patterns(graph_path, project_root))
    all_issues.extend(check_agent_patterns(graph_path, project_root))
    all_issues.extend(check_subgraph_patterns(graph_path, project_root))
    all_issues.extend(check_copilot_patterns(graph_path))

    # FR-232: Race pattern checks
    all_issues.extend(check_race_patterns(graph_path))

    # FR-235: Pipeline template checks
    all_issues.extend(check_pipeline_patterns(graph_path))

    # FR-061: Contract violation checks
    all_issues.extend(check_python_node_variables(graph_path))
    all_issues.extend(check_identifier_keys(graph_path))
    all_issues.extend(check_skip_if_exists_add_reducer(graph_path))

    # FR-164: Verification gate lint
    all_issues.extend(check_skip_without_verification(graph_path))

    # FR-119: Top-level provider/model detection
    all_issues.extend(check_top_level_provider_model(graph_path))

    # FR-165: Silent fallback detection
    all_issues.extend(check_silent_fallback(graph_path))

    # FR-071: Thinking budget checks
    all_issues.extend(check_thinking_budget(graph_path))

    # Determine validity (no errors)
    has_errors = any(issue.severity == "error" for issue in all_issues)

    return LintResult(
        file=str(graph_path),
        issues=all_issues,
        valid=not has_errors,
    )


# Re-export for backwards compatibility
# Note: Check function names come from their respective modules
__all__ = [
    "LintIssue",
    "LintResult",
    "lint_graph",
]
