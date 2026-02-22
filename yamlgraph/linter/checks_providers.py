"""Provider-specific lint checks.

Split from checks.py to keep modules under 450 lines.

Check functions:
- check_thinking_budget (W071-*): Anthropic extended thinking configuration
"""

from __future__ import annotations

from pathlib import Path

from yamlgraph.linter.checks import LintIssue, load_graph


def check_thinking_budget(graph_path: Path) -> list[LintIssue]:
    """Check thinking_budget configuration (FR-071, REQ-YG-083).

    Warns about:
    - thinking_budget > 0 with non-Anthropic provider
    - thinking_budget > 0 with pre-3.7 model (when model is explicitly set)
    - 0 < thinking_budget < 1024 (below Anthropic minimum)
    - explicit temperature != 1 with thinking_budget > 0

    Returns:
        List of lint issues
    """
    graph = load_graph(graph_path)
    defaults = graph.get("defaults", {})
    nodes = graph.get("nodes", {})
    issues: list[LintIssue] = []

    # Model substrings that support thinking
    THINKING_CAPABLE_MODELS = ["claude-3-7", "claude-3-8", "claude-4"]

    def check_config(config: dict, context: str, defaults: dict) -> list[LintIssue]:
        """Check a single config (defaults or node)."""
        local_issues: list[LintIssue] = []
        thinking_budget = config.get("thinking_budget")
        if thinking_budget is None:
            return local_issues

        # Check for explicit temperature != 1
        temperature = config.get("temperature")
        if temperature is not None and temperature != 1 and thinking_budget > 0:
            local_issues.append(
                LintIssue(
                    severity="warning",
                    code="W071-1",
                    message=(
                        f"{context}: temperature={temperature} will be overridden "
                        f"to 1 when thinking_budget={thinking_budget} "
                        "(Anthropic requirement)"
                    ),
                    fix="Set temperature=1 or remove explicit temperature",
                )
            )

        # Check provider
        provider = config.get("provider") or defaults.get("provider")
        if provider and provider != "anthropic" and thinking_budget > 0:
            local_issues.append(
                LintIssue(
                    severity="warning",
                    code="W071-2",
                    message=(
                        f"{context}: thinking_budget={thinking_budget} with "
                        f"provider='{provider}' (only 'anthropic' supports "
                        "extended thinking)"
                    ),
                    fix="Set provider='anthropic' or remove thinking_budget",
                )
            )

        # Check model (only if explicitly set in this config)
        model = config.get("model")
        if (
            model is not None
            and thinking_budget > 0
            and not any(substring in model for substring in THINKING_CAPABLE_MODELS)
        ):
            local_issues.append(
                LintIssue(
                    severity="warning",
                    code="W071-3",
                    message=(
                        f"{context}: thinking_budget={thinking_budget} with "
                        f"model='{model}' (may not support extended thinking; "
                        "expected claude-3.7+)"
                    ),
                    fix="Use a thinking-capable model like 'claude-3-7-sonnet-20250219'",
                )
            )

        # Check for below-minimum budget
        if 0 < thinking_budget < 1024:
            local_issues.append(
                LintIssue(
                    severity="warning",
                    code="W071-4",
                    message=(
                        f"{context}: thinking_budget={thinking_budget} is below "
                        "Anthropic minimum (1024)"
                    ),
                    fix="Set thinking_budget=0 (disable) or >= 1024",
                )
            )

        return local_issues

    # Check defaults
    issues.extend(check_config(defaults, "defaults", defaults))

    # Check each node
    for node_name, node_config in nodes.items():
        issues.extend(check_config(node_config, f"node '{node_name}'", defaults))

    return issues


__all__ = ["check_thinking_budget"]
