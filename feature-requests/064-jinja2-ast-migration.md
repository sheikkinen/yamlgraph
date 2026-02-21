# Feature Request: Migrate Jinja2 Variable Extraction to AST

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-02-21

## Summary

Replace regex-based Jinja2 variable extraction in `yamlgraph/utils/template.py` with `jinja2.meta.find_undeclared_variables()` for correctness.

## Problem

The current implementation uses 5+ regex patterns to extract variables from Jinja2 templates:

```python
# Current approach - fragile
simple_pattern = r"(?<!\{)\{(\w+)\}(?!\})"
jinja_var_pattern = r"\{\{\s*(\w+)"
jinja_loop_pattern = r"\{%\s*for\s+\w+\s+in\s+(\w+)"
jinja_if_blocks = re.findall(r"\{%[-\s]*(?:if|elif)\s+(.*?)%\}", template)
```

**Known edge cases that break:**
1. Quoted string comparands: `{% if x == "test" %}` — extracts "test" as variable
2. Nested filters: `{{ items | join(", ") | upper }}` — may extract filter names
3. Complex conditionals: `{% if x.y and z|length > 0 %}` — attribute access confusion
4. Inline comments: `{# comment #}` — not handled

**Real bug encountered:** Diary entry "The Quoted Comparand Trap" (2026-02-20) documented that `{% if x == "literal" %}` incorrectly extracted "literal" as a required variable.

## Proposed Solution

Use Jinja2's built-in AST parser:

```python
from jinja2 import Environment, meta

def extract_variables(template: str) -> set[str]:
    """Extract variables using Jinja2's AST parser."""
    env = Environment()
    ast = env.parse(template)
    return meta.find_undeclared_variables(ast)
```

**For simple `{var}` syntax (non-Jinja2):**
```python
def extract_variables(template: str) -> set[str]:
    """Extract all variable names required by a template."""
    variables: set[str] = set()

    # Check if template uses Jinja2 syntax
    is_jinja = "{{" in template or "{%" in template

    if is_jinja:
        # Use Jinja2 AST for correctness
        env = Environment()
        ast = env.parse(template)
        variables = meta.find_undeclared_variables(ast)
    else:
        # Simple {var} format only
        simple_pattern = r"\{(\w+)\}"
        variables = set(re.findall(simple_pattern, template))

    # Remove built-in names
    excluded = {"state", "loop", "range", "true", "false", "none"}
    return variables - excluded
```

## Acceptance Criteria

- [ ] `extract_variables()` uses `jinja2.meta.find_undeclared_variables()` for Jinja2 templates
- [ ] Simple `{var}` format still works (backward compatibility)
- [ ] Edge case: `{% if x == "literal" %}` → extracts `x`, not `literal`
- [ ] Edge case: `{{ items | join(", ") }}` → extracts `items`, not `join`
- [ ] Edge case: `{% for item in items %}{{ item }}{% endfor %}` → extracts `items`, not `item`
- [ ] Tests added for each edge case
- [ ] No performance regression (AST parse is fast for typical prompt sizes)

## Downstream Impact

| Component | Effect |
|-----------|--------|
| `yamlgraph/utils/template.py` | Simplified implementation (~60 lines → ~20 lines) |
| `yamlgraph/linter/checks.py` | May benefit if it also does variable extraction |
| Prompt validation | More accurate — fewer false "missing variable" errors |
| Error messages | Clearer — won't suggest providing string literals |

**Not affected:** Graph loader, executor, node factory — they call `extract_variables()` unchanged.

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Keep regex, add more patterns | Whack-a-mole; each fix creates new edge cases |
| Custom parser | Reinventing what Jinja2 already provides |
| Disable Jinja2 support | Would break existing templates |

## Related

- Diary entry: "The Quoted Comparand Trap" (2026-02-20)
- SWOT P0 item: "Migrate Jinja2 parsing to AST"
- `yamlgraph/utils/template.py` lines 37-67 (current implementation)
