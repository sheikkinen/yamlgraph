# Feature Request: Migrate Jinja2 Variable Extraction to AST

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days (actual: 15 minutes)
**Requested:** 2026-02-21
**Judged:** 2026-02-21
**Implemented:** 2026-02-21

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

### Verified Failing Edge Cases (6/15 tests fail)

| Case | Template | Regex Result | Correct Result |
|------|----------|--------------|----------------|
| **comment** | `{# {{ foo }} #}{{ bar }}` | `{foo, bar}` ❌ | `{bar}` |
| **raw block** | `{% raw %}{{ not_a_var }}{% endraw %}{{ real }}` | `{not_a_var, real}` ❌ | `{real}` |
| **macro** | `{% macro m(a) %}{{ a }}{% endmacro %}{{ m(x) }}` | `{a, m}` ❌ | `{x}` |
| **ternary** | `{{ x if cond else y }}` | `{x}` ❌ | `{x, cond, y}` |
| **dict literal** | `{{ {"key": value}.key }}` | `{}` ❌ | `{value}` |
| **set stmt** | `{% set local = external %}{{ local }}` | `{local}` ❌ | `{external}` |

**Real bug encountered:** Diary entry "The Quoted Comparand Trap" (2026-02-20) documented that `{% if x == "literal" %}` incorrectly extracted "literal" as a required variable. (Note: This specific case now passes after prior regex fixes, but the 6 cases above do not.)

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
    excluded = {"state", "loop", "range", "true", "false", "none", "self"}
    return variables - excluded
```

## Acceptance Criteria

### Tests to Add (Red Phase)
- [x] `test_extract_jinja2_comment` — `{# {{ foo }} #}{{ bar }}` → `{bar}`
- [x] `test_extract_jinja2_raw_block` — `{% raw %}{{ not_a_var }}{% endraw %}{{ real }}` → `{real}`
- [x] `test_extract_jinja2_macro` — `{% macro m(a) %}{{ a }}{% endmacro %}{{ m(x) }}` → `{x}`
- [x] `test_extract_jinja2_ternary` — `{{ x if cond else y }}` → `{x, cond, y}`
- [x] `test_extract_jinja2_dict_literal` — `{{ {"key": value}.key }}` → `{value}`
- [x] `test_extract_jinja2_set_stmt` — `{% set local = external %}{{ local }}` → `{external}`

### Implementation (Green Phase)
- [x] `extract_variables()` uses `jinja2.meta.find_undeclared_variables()` for Jinja2 templates
- [x] Simple `{var}` format still works (backward compatibility)
- [x] Mixed `{var}` + `{{ var }}` syntax supported (regression caught and fixed)
- [x] Exclude list includes `self` (Jinja2 macro context) in addition to `state`, `loop`, `range`, etc.
- [x] All 6 new tests pass
- [x] All 23 existing tests in `test_template.py` still pass (29 total)

### Verification
- [x] No performance regression (AST parse is fast for typical prompt sizes)
- [x] `pytest tests/unit/test_template.py -v` passes (29/29)
- [x] `pytest tests/unit/ -q` passes (1698/1698)

## Implementation Order (The Path)

1. **Red**: Added 6 failing tests to `tests/unit/test_template.py` ✓
2. **Green**: Replaced regex with AST in `extract_variables()` ✓
3. **Regression**: Mixed `{var}` + `{{ var }}` test failed — added simple pattern extraction for mixed syntax ✓
4. **Refactor**: Dead regex patterns removed (~40 lines → ~20 lines) ✓
5. **Verify**: `pytest tests/unit/test_template.py -v` — 29/29 pass ✓
6. **Reflect**: Diary entry added

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
