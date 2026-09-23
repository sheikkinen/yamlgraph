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
from yamlgraph.utils.template import (
    is_jinja,
    scan_simple_fields,
    strip_jinja_raw_blocks,
)

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

        with open(prompt_path, encoding="utf-8") as f:
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


def _iter_prompt_messages(prompt_yaml: object) -> list[tuple[str, str]]:
    """Yield `(field_label, text)` for every renderable message (FR-1057).

    The frozen surface: scalar `system`, list-form `system`,
    `system_segments[*].content`, and `user`. Non-message fields such as
    `metadata.description` are never rendered and so can never be defects.
    """
    if not isinstance(prompt_yaml, dict):
        return []

    messages: list[tuple[str, str]] = []
    segments = prompt_yaml.get("system_segments")
    system_field = prompt_yaml.get("system")

    if isinstance(segments, list):
        for index, segment in enumerate(segments):
            if isinstance(segment, dict):
                messages.append(
                    (f"system_segments[{index}]", str(segment.get("content", "")))
                )
    elif isinstance(system_field, list):
        for index, item in enumerate(system_field):
            content = item.get("content", "") if isinstance(item, dict) else item
            messages.append((f"system[{index}]", str(content)))
    elif isinstance(system_field, str):
        messages.append(("system", system_field))

    user_field = prompt_yaml.get("user")
    if isinstance(user_field, str):
        messages.append(("user", user_field))

    return [(label, text) for label, text in messages if text]


def _load_prompt_messages(
    graph_path: Path, project_root: Path | None
) -> list[tuple[str, str, str, str]]:
    """Collect `(node, prompt, field_label, text)` across a graph's prompts."""
    graph = load_graph(graph_path)
    if project_root is None:
        project_root = graph_path.parent
    prompts_dir = resolve_prompts_dir(graph, graph_path, project_root)

    collected: list[tuple[str, str, str, str]] = []
    for node_name, node_config in graph.get("nodes", {}).items():
        prompt_name = node_config.get("prompt")
        if not prompt_name:
            continue

        prompt_path = get_prompt_path(prompt_name, prompts_dir)
        if not prompt_path.exists():
            # check_prompt_files handles missing files (E004).
            continue

        with open(prompt_path, encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)

        for field_label, text in _iter_prompt_messages(prompt_yaml):
            collected.append((node_name, prompt_name, field_label, text))

    return collected


def check_unrenderable_simple_messages(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """E013 — a non-Jinja message `str.format` will refuse to render."""
    issues: list[LintIssue] = []

    for node_name, prompt_name, field_label, text in _load_prompt_messages(
        graph_path, project_root
    ):
        if is_jinja(text):
            continue
        scan = scan_simple_fields(text)
        if not scan.brace_error and not scan.invalid_fields:
            continue

        detail = scan.brace_error or (
            f"invalid format field(s): {', '.join(scan.invalid_fields)}"
        )
        issues.append(
            LintIssue(
                severity="error",
                code="E013",
                message=(
                    f"Prompt '{prompt_name}' (node '{node_name}', field "
                    f"'{field_label}') is not a valid str.format template: {detail}"
                ),
                fix=(
                    "This message contains no Jinja syntax, so every brace is "
                    "significant. Rewrite the shape in prose, or wrap it in "
                    "{% raw %}...{% endraw %} so the message is rendered by Jinja."
                ),
            )
        )

    return issues


def check_simple_fields_in_jinja_messages(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """E014 — `{var}` inside a Jinja message, which Jinja never substitutes."""
    issues: list[LintIssue] = []

    for node_name, prompt_name, field_label, text in _load_prompt_messages(
        graph_path, project_root
    ):
        if not is_jinja(text):
            continue
        roots = sorted(scan_simple_fields(strip_jinja_raw_blocks(text)).bare_roots)
        if not roots:
            continue

        joined = ", ".join(f"{{{root}}}" for root in roots)
        issues.append(
            LintIssue(
                severity="error",
                code="E014",
                message=(
                    f"Prompt '{prompt_name}' (node '{node_name}', field "
                    f"'{field_label}') is a Jinja message but contains simple "
                    f"format field(s) Jinja will not substitute: {joined}"
                ),
                fix=(
                    f"Convert to Jinja syntax in '{prompt_name}': {{{{ variable }}}} "
                    "instead of {variable}."
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

        with open(prompt_path, encoding="utf-8") as f:
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
    "check_unrenderable_simple_messages",
    "check_simple_fields_in_jinja_messages",
    "check_prompt_complexity",
]
