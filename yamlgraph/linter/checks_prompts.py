"""Prompt-focused linter checks.

Contains prompt text analysis rules that operate across prompt files.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from yamlgraph.linter.checks import (
    LintIssue,
    get_prompt_path,
    load_graph,
    resolve_prompts_dir,
)
from yamlgraph.utils.template import extract_variables as extract_template_variables

# W026 default: at or above this many top-level inline-schema output fields, a
# prompt is flagged as possibly fusing independent judgements (FR-586).
DEFAULT_FIELD_THRESHOLD = 4

# W026-2 prose detectors. Curated and deliberately small — precision over
# recall. A linter that cries wolf gets disabled. The list may grow only with a
# fixture proving the addition is warranted (FR-586). `.` does not cross
# newlines, so `.*` stays within a single line and cannot match across
# unrelated sentences.
_ENUMERATED_OUTPUT_PATTERNS = (
    r"\bassign\s+(two|three|four|five|\d+)\s+(fields|slices|sections|outputs)\b",
    r"\bextract\s+(two|three|four|five|\d+)\s+sections\b",
)
_GLOBAL_CONSTRAINT_PATTERNS = (
    r"\bevery\b.*\b(should|must)\b.*\b(later|close)\b",
    r"\bforward[\s-]+only\b",
    r"\bmust\b.*\blater\b",
    r"\bexactly\s+one\b.*\band\s+one\b",
)

_W026_FIX = (
    "Consider splitting discrimination from bookkeeping (see FR-585 decode "
    "pattern) or pushing global cross-unit constraints to a deterministic "
    "post-pass."
)


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


def _count_inline_schema_fields(prompt_yaml: object) -> int:
    """Count top-level output fields in an inline schema / output_schema.

    Nested fields under one parent count as one — the signal is the number of
    independent top-level outputs, not depth. Returns 0 when no inline schema
    with a `fields` mapping is present.
    """
    if not isinstance(prompt_yaml, dict):
        return 0
    for key in ("schema", "output_schema"):
        schema = prompt_yaml.get(key)
        if isinstance(schema, dict):
            fields = schema.get("fields")
            if isinstance(fields, dict):
                return len(fields)
    return 0


def _match_prose_signal(text: str) -> str | None:
    """Return the first matched W026-2 prose phrase, or None.

    Matching is case-insensitive; `.*` stays within a line (default `.`),
    avoiding cross-sentence false positives.
    """
    for pattern in (*_ENUMERATED_OUTPUT_PATTERNS, *_GLOBAL_CONSTRAINT_PATTERNS):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def check_prompt_complexity(
    graph_path: Path,
    project_root: Path | None = None,
    field_threshold: int = DEFAULT_FIELD_THRESHOLD,
) -> list[LintIssue]:
    """W026: warn when a prompt fuses too many independent judgements (FR-586).

    Two complementary detectors, emitted at warning severity only (a smell, not
    a defect — never changes lint exit semantics):

    - W026-1: an inline ``schema``/``output_schema`` with ``field_threshold`` or
      more top-level fields.
    - W026-2: a curated prose phrase signalling enumerated multi-output or a
      global cross-unit constraint.

    At most one W026 is emitted per prompt (schema signal preferred).

    Args:
        graph_path: Path to the graph YAML file.
        project_root: Root directory containing the prompts/ folder.
        field_threshold: Inline-schema field count at or above which W026-1
            fires. Exposed as a parameter (no lint-config file).
    """
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

        prompt_yaml = yaml.safe_load(prompt_content)
        field_count = _count_inline_schema_fields(prompt_yaml)

        if field_count >= field_threshold:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W026",
                    message=(
                        f"Prompt '{prompt_name}' (node '{node_name}') declares "
                        f"{field_count} top-level output fields (>= {field_threshold}) "
                        "— it may fuse that many independent judgements into one "
                        "call; the hardest judgement can starve under load"
                    ),
                    fix=_W026_FIX,
                )
            )
            continue

        signal = _match_prose_signal(prompt_content)
        if signal:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W026",
                    message=(
                        f"Prompt '{prompt_name}' (node '{node_name}') signals "
                        f'multiple fused judgements ("{signal}") in one call; the '
                        "hardest judgement can starve under load"
                    ),
                    fix=_W026_FIX,
                )
            )

    return issues


__all__ = [
    "check_unanchored_prompt_variables",
    "check_mixed_template_syntax",
    "check_prompt_complexity",
]
