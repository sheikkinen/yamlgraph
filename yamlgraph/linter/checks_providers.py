"""Provider-specific lint checks.

Split from checks.py to keep modules under 450 lines.

Check functions:
- check_thinking_budget (W071-*): Extended thinking configuration for Anthropic/Google/Vertex
- check_unread_llm_settings (W072, W073): LLM settings written where they are never read
"""

from __future__ import annotations

from pathlib import Path

import yaml

from yamlgraph.constants import LLMSetting
from yamlgraph.linter.checks import (
    LintIssue,
    get_prompt_path,
    load_graph,
    resolve_prompts_dir,
)

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


# Settings a race forwards to every candidate (race_node.py, router_race_node.py)
RACE_FORWARDED_SETTINGS = {LLMSetting.TEMPERATURE, LLMSetting.THINKING_BUDGET}
CANDIDATE_KEYS = {"provider", "model"}


def _metadata_fix(key: str) -> str:
    fix = f"move it to defaults.{key} (or onto the node)"
    if key not in RACE_FORWARDED_SETTINGS:
        fix += "; race and router-race nodes do not apply it"
    return fix


def _metadata_issues(metadata: object, location: str) -> list[LintIssue]:
    if not isinstance(metadata, dict):
        return []
    return [
        LintIssue(
            severity="warning",
            code="W072",
            message=f"{location}: '{key}' is not read from metadata",
            fix=_metadata_fix(key),
        )
        for key in LLMSetting
        if key in metadata
    ]


def _candidate_fix(key: str) -> str:
    if key in RACE_FORWARDED_SETTINGS:
        return f"move it onto the node or defaults.{key}; it applies to every candidate"
    if key in frozenset(LLMSetting):
        return f"the race path does not apply '{key}'; remove it"
    return "candidates take only provider and model; remove it"


def _candidate_issues(node_name: str, candidates: object) -> list[LintIssue]:
    if not isinstance(candidates, list):
        return []
    return [
        LintIssue(
            severity="warning",
            code="W073",
            message=(
                f"node '{node_name}' race candidate {index}: "
                f"'{key}' is not read from race candidates"
            ),
            fix=_candidate_fix(key),
        )
        for index, candidate in enumerate(candidates)
        if isinstance(candidate, dict)
        for key in candidate
        if key not in CANDIDATE_KEYS
    ]


def check_unread_llm_settings(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Report LLM settings written where yamlgraph never reads them (FR-1166, REQ-YG-730).

    W072: an LLMSetting key in graph metadata or a referenced prompt's metadata.
    W073: any key but provider/model on a race or router-race candidate.
    """
    graph = load_graph(graph_path)
    issues = _metadata_issues(graph.get("metadata"), "graph metadata")

    if project_root is None:
        project_root = graph_path.parent
    prompts_dir = resolve_prompts_dir(graph, graph_path, project_root)
    seen_prompts: set[str] = set()

    for node_name, node_config in (graph.get("nodes") or {}).items():
        if not isinstance(node_config, dict):
            continue
        issues.extend(_candidate_issues(node_name, node_config.get("candidates")))

        prompt_name = node_config.get("prompt")
        if not isinstance(prompt_name, str) or prompt_name in seen_prompts:
            continue
        seen_prompts.add(prompt_name)
        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path.exists():
            # check_prompt_files handles missing files (E004).
            continue
        with open(prompt_path, encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        if isinstance(prompt_yaml, dict):
            issues.extend(
                _metadata_issues(
                    prompt_yaml.get("metadata"), f"prompt '{prompt_name}' metadata"
                )
            )

    return issues
