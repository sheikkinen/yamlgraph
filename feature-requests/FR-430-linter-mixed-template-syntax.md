# Feature Request: FR-430 Linter Rule W024 Mixed Template Syntax

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-21

**Judge Verdict:** APPROVE — reuse `extract_template_variables` instead of new regex; drop vague block-scalar criterion.

## Summary

Add linter rule `W024` that warns when a prompt YAML file mixes simple substitution syntax (`{variable}`) with Jinja2 syntax (`{{variable}}` or `{%`). This catches a class of bugs where template variables silently fail to render.

## Value Statement

Graph authors get a lint-time warning when prompt files accidentally mix template engines, preventing silent rendering failures that only surface at runtime as literal `{variable}` text in LLM output.

## Problem

YAMLGraph supports two template syntaxes in prompt YAML files:
- **Simple substitution**: `{variable}` — replaced by `str.format()`
- **Jinja2**: `{{variable}}`, `{% for %}`, `{{ text | filter }}` — auto-detected when `{{` or `{%` is present

When both syntaxes appear in the same file, the Jinja2 engine takes over and `{variable}` is interpreted as a Python set literal or raises a `TemplateSyntaxError`. This is a silent failure — the prompt renders with wrong content, and the LLM gets garbled input.

From diary seed (2026-05-20, FR-425 reflection): "Can YAMLGraph detect and warn about mixed template syntax at lint time? A graph lint rule that flags `{word}` (simple substitution) co-occurring with `{{` or `{%` in the same prompt file would catch this class of bugs before runtime."

## Proposed Solution

Add `check_mixed_template_syntax()` to `yamlgraph/linter/checks.py`:

```python
def check_mixed_template_syntax(
    graph_path: Path, project_root: Path | None = None
) -> list[LintIssue]:
    """Warn when prompt files mix simple {var} and Jinja2 {{var}} syntax."""
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
            continue  # E004 handles missing files
        text = prompt_path.read_text()
        # Reuse existing extract_template_variables (used by W023) instead of
        # custom regex — avoids false positives on natural English like {set}.
        simple_vars = extract_template_variables(text)
        has_jinja = bool(re.search(r'\{\{|\{%', text))
        if simple_vars and has_jinja:
            issues.append(LintIssue(
                severity="warning",
                code="W024",
                message=(
                    f"Prompt '{prompt_name}' (node '{node_name}') mixes simple "
                    f"{{var}} and Jinja2 {{{{var}}}} syntax — simple variables "
                    f"will not render correctly under Jinja2"
                ),
                fix=(
                    f"Convert all variables in '{prompt_name}' to Jinja2 syntax: "
                    f"{{{{variable}}}} instead of {{variable}}"
                ),
            ))
    return issues
```

Register in `graph_linter.py`:
```python
from yamlgraph.linter.checks import check_mixed_template_syntax
# ... in lint_graph():
all_issues.extend(check_mixed_template_syntax(graph_path, project_root))
```

## Acceptance Criteria

- [x] `W024` rule added to `yamlgraph/linter/checks.py`
- [x] Simple variable detection reuses `extract_template_variables` (same as W023)
- [x] Rule registered in `graph_linter.py` `lint_graph()` function
- [x] `check_mixed_template_syntax` added to `__all__` in `checks.py`
- [x] `yamlgraph graph lint` reports W024 for prompts with mixed syntax
- [x] No false positives on pure-simple or pure-Jinja2 prompt files
- [x] Tests: mixed syntax warns, pure simple clean, pure Jinja2 clean, missing prompt skipped
- [x] Rule appears in linter output with fix suggestion
- [x] FR-429 hook automatically picks up W024 via `yamlgraph graph lint` (no hook changes needed)

## Implementation Notes (2026-05-21)

- Added `check_mixed_template_syntax()` to `yamlgraph/linter/checks.py` as warning rule `W024`.
- Registered `W024` in `yamlgraph/linter/graph_linter.py` so it runs with normal `yamlgraph graph lint`.
- Implemented mixed-syntax detection by stripping Jinja2 constructs and reusing `extract_template_variables` to detect remaining simple `{var}` placeholders.
- Added unit tests in `tests/unit/test_fr430_lint_mixed_template_syntax.py` covering mixed warning, pure simple, pure Jinja2, and missing prompt cases.

## Alternatives Considered

- **Implement in hook only**: Rejected — rule belongs in linter so CI, CLI, and hooks all benefit. Diary seed explicitly asked for "lint time" detection. Scripture `callsite_fix`: put the rule where all callers benefit.
- **Error instead of warning**: Rejected — there may be legitimate cases where `{` appears in prompt text without being a template variable (e.g., JSON examples). Warning lets the author decide.
- **Detect at prompt load time**: Already partially handled (Jinja2 auto-detection), but the failure mode is silent wrong output, not a crash. Lint-time warning is cheaper.

## Related

- [FR-429](FR-429-post-edit-yaml-checks.md): Hook extension that delivers this rule at edit time
- [checks.py](../yamlgraph/linter/checks.py): `check_unanchored_prompt_variables()` — similar pattern for prompt variable analysis
- Diary seed: `docs/diary/2026-05-20-reflection-fr-425-hook-classification-daemon-enforcement.md`
- Scripture trap: `plausible_wrong_answer` — "Output passes shape check but is semantically wrong"
