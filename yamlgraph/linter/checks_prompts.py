"""Prompt-focused linter checks.

Contains prompt text analysis rules that operate across prompt files.
"""

from __future__ import annotations

import re
from pathlib import Path

from yamlgraph.linter.checks import (
    LintIssue,
    get_prompt_path,
    load_graph,
    resolve_prompts_dir,
)
from yamlgraph.utils.template import extract_variables as extract_template_variables


def _extract_state_qualified_jinja_variables(text: str) -> set[str]:
    """Extract keys from Jinja2 state-qualified variables like {{ state.key }}."""
    return set(re.findall(r"\{\{\s*state\.([A-Za-z_]\w*)", text))


def check_unanchored_prompt_variables(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Warn when nodes declare variables not referenced by prompt text."""
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    if project_root is None:
        project_root = graph_path.parent

    prompts_dir = resolve_prompts_dir(graph, graph_path, project_root)

    for node_name, node_config in graph.get("nodes", {}).items():
        prompt_name = node_config.get("prompt")
        node_variables = node_config.get("variables")

        if (
            not prompt_name
            or not isinstance(node_variables, dict)
            or not node_variables
        ):
            continue

        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path.exists():
            # check_prompt_files handles missing files (E004).
            continue

        with open(prompt_path) as f:
            prompt_content = f.read()

        anchored_variables = extract_template_variables(prompt_content)
        anchored_variables.update(
            _extract_state_qualified_jinja_variables(prompt_content)
        )

        declared_keys = set(node_variables.keys())
        unanchored_keys = sorted(declared_keys - anchored_variables)
        if unanchored_keys:
            joined_keys = ", ".join(unanchored_keys)
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W023",
                    message=(
                        f"Node '{node_name}' declares variables not referenced in "
                        f"prompt '{prompt_name}': {joined_keys}"
                    ),
                    fix=(
                        f"Reference variable(s) in prompt '{prompt_name}' or remove "
                        f"unused key(s): {joined_keys}"
                    ),
                )
            )

    return issues


def check_mixed_template_syntax(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Warn when prompt files mix simple {var} and Jinja2 syntax."""
    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    if project_root is None:
        project_root = graph_path.parent

    prompts_dir = resolve_prompts_dir(graph, graph_path, project_root)

    for node_name, node_config in graph.get("nodes", {}).items():
        prompt_name = node_config.get("prompt")
        if not prompt_name:
            continue

        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path.exists():
            # check_prompt_files handles missing files (E004).
            continue

        with open(prompt_path) as f:
            prompt_content = f.read()

        # Reuse shared extraction logic after removing Jinja constructs so
        # Jinja-only prompts do not produce false positives.
        simple_scan_text = re.sub(
            r"\{\{.*?\}\}|\{%.*?%\}",
            "",
            prompt_content,
            flags=re.DOTALL,
        )
        simple_vars = extract_template_variables(simple_scan_text)
        has_jinja = "{{" in prompt_content or "{%" in prompt_content

        if simple_vars and has_jinja:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W024",
                    message=(
                        f"Prompt '{prompt_name}' (node '{node_name}') mixes simple "
                        f"{{var}} and Jinja2 {{{{var}}}} syntax"
                    ),
                    fix=(
                        f"Convert simple placeholders in '{prompt_name}' to Jinja2 "
                        "syntax: {{variable}} instead of {variable}"
                    ),
                )
            )

    return issues


__all__ = [
    "check_unanchored_prompt_variables",
    "check_mixed_template_syntax",
]
