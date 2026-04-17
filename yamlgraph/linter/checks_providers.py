"""Provider-specific lint checks.

Split from checks.py to keep modules under 450 lines.

Check functions:
- check_thinking_budget (W071-*): Extended thinking configuration for Anthropic/Google/Vertex
"""

from __future__ import annotations

from pathlib import Path

from yamlgraph.linter.checks import LintIssue, load_graph

# Providers that support thinking_budget natively (no W071-2 warning)
THINKING_SUPPORTED_PROVIDERS = {"anthropic", "google", "vertex"}

# Model substrings that support thinking (Anthropic and Google)
THINKING_CAPABLE_MODELS = [
    "claude-3-7",
    "claude-3-8",
    "claude-4",
    "gemini-2.5",
    "gemini-3",
]


def check_thinking_budget(graph_path: Path) -> list[LintIssue]:
    """Check thinking_budget configuration (FR-071, FR-230, REQ-YG-083, REQ-YG-230).

    Warns about:
    - thinking_budget > 0 with unsupported provider (not anthropic/google/vertex)
    - thinking_budget > 0 with non-thinking-capable model
    - 0 < thinking_budget < 1024 for anthropic (Anthropic minimum; Google has no minimum)
    - explicit temperature != 1 with thinking_budget > 0 for anthropic only

    Returns:
        List of lint issues
    """
    graph = load_graph(graph_path)
    defaults = graph.get("defaults", {})
    nodes = graph.get("nodes", {})
    issues: list[LintIssue] = []

    def check_config(config: dict, context: str, defaults: dict) -> list[LintIssue]:
        """Check a single config (defaults or node)."""
        local_issues: list[LintIssue] = []
        thinking_budget = config.get("thinking_budget")
        if thinking_budget is None:
            return local_issues

        provider = config.get("provider") or defaults.get("provider")

        # W071-1: temperature override warning — Anthropic only
        temperature = config.get("temperature")
        if (
            temperature is not None
            and temperature != 1
            and thinking_budget > 0
            and (provider is None or provider == "anthropic")
        ):
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

        # W071-2: unsupported provider warning — excludes google and vertex
        if (
            provider
            and provider not in THINKING_SUPPORTED_PROVIDERS
            and thinking_budget > 0
        ):
            local_issues.append(
                LintIssue(
                    severity="warning",
                    code="W071-2",
                    message=(
                        f"{context}: thinking_budget={thinking_budget} with "
                        f"provider='{provider}' (only {', '.join(sorted(THINKING_SUPPORTED_PROVIDERS))} "
                        "support extended thinking)"
                    ),
                    fix=f"Set provider to one of: {', '.join(sorted(THINKING_SUPPORTED_PROVIDERS))} or remove thinking_budget",
                )
            )

        # W071-3: model not thinking-capable
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
                        "expected claude-3.7+ or gemini-2.5+)"
                    ),
                    fix="Use a thinking-capable model like 'claude-3-7-sonnet-20250219' or 'gemini-2.5-flash'",
                )
            )

        # W071-4: below-minimum budget — Anthropic only (Google has no minimum)
        if 0 < thinking_budget < 1024 and (provider is None or provider == "anthropic"):
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
