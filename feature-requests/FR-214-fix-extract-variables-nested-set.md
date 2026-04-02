# Feature Request: Fix `extract_variables()` False Positive for `{% set %}` in Nested Blocks

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-02

## Summary

`extract_variables()` in `yamlgraph/utils/template.py` incorrectly reports `{% set %}` assignment targets as required input variables when the assignment appears inside nested `{% for %}` + `{% if %}` blocks, causing false "missing variable" errors at runtime.

## Value Statement

Graph authors using `{% set %}` inside conditional loops get false validation errors that block prompt execution — fixing this unblocks all prompts using that pattern without any workaround.

## Problem

`jinja2.meta.find_undeclared_variables()` has a known limitation: it cannot distinguish between a variable that is assigned locally via `{% set %}` and a variable that must be supplied by the caller when the assignment is inside nested block scopes.

```python
from jinja2 import Environment, meta
env = Environment()
ast = env.parse('{% for i in items %}{% if i %}{% set x = i %}{{ x }}{% endif %}{% endfor %}')
meta.find_undeclared_variables(ast)  # returns {'x', 'items'} — x is a false positive
```

The expected result is `{'items'}` only — `x` is locally defined by `{% set %}` and must not appear as a required caller-supplied variable.

Discovered via NC-196: the recap prompt uses this exact pattern, blocking all prompts that combine `{% set %}` with conditional loops.

## Proposed Solution

After calling `meta.find_undeclared_variables()`, walk the Jinja2 AST to collect all `Assign` node targets (every name bound by `{% set %}`), then subtract those names from the undeclared set.

Add `_collect_set_targets()` as a private helper in `yamlgraph/utils/template.py`:

```python
import jinja2.nodes as jnodes

def _collect_set_targets(ast) -> set[str]:
    """Walk the AST and return all names bound by {% set %} statements."""
    assigned: set[str] = set()
    for node in ast.find_all(jnodes.Assign):
        target = node.target
        if isinstance(target, jnodes.Name):
            assigned.add(target.name)
    return assigned
```

Then in the Jinja2 branch of `extract_variables()`:

```python
if is_jinja:
    env = Environment()
    ast = env.parse(template)
    undeclared = meta.find_undeclared_variables(ast)
    set_targets = _collect_set_targets(ast)
    variables = undeclared - set_targets
    # Also extract simple {var} placeholders (mixed syntax support)
    simple_pattern = r"(?<!\{)\{(\w+)\}(?!\})"
    variables.update(re.findall(simple_pattern, template))
```

The subtraction is safe: `find_undeclared_variables` already excludes `x` when `{% set x = y %}` appears at the top level (it resolves the scope chain), so subtracting `Assign` targets only corrects the nested-scope gap.

## Acceptance Criteria

- [ ] `extract_variables('{% for i in items %}{% if i %}{% set x = i %}{{ x }}{% endif %}{% endfor %}')` returns `{'items'}` (not `{'items', 'x'}`)
- [ ] Existing behaviour preserved: top-level `{% set %}` targets are also excluded (they are `Assign` nodes, so the fix covers them)
- [ ] `{% set %}` inside a plain `{% for %}` (no nested `{% if %}`) is also excluded
- [ ] A genuinely undeclared variable (e.g. `y` in `{% set x = y %}{{ x }}`) remains reported after subtracting Assign targets — confirmed by `test_extract_variables_set_before_use_still_reported`
- [ ] `validate_variables()` no longer raises for prompts using `{% set %}` inside conditional loops
- [ ] Both new tests committed RED (with `SKIP=pytest`) before the fix, GREEN after
- [ ] `pytest tests/unit/test_template.py` passes green after the fix
- [ ] No regressions in `pytest tests/` overall
- [ ] `REQ-YG-216` row added to `ARCHITECTURE.md` requirements table

### Required tests (commit RED first)

```python
@pytest.mark.req("REQ-YG-216")
def test_extract_variables_set_in_nested_for_if():
    """{% set %} inside {% for %}{% if %} must not appear as required."""
    template = '{% for i in items %}{% if i %}{% set x = i %}{{ x }}{% endif %}{% endfor %}'
    result = extract_variables(template)
    assert result == {'items'}, f"Expected {{'items'}}, got {result}"


@pytest.mark.req("REQ-YG-216")
def test_extract_variables_set_before_use_still_reported():
    """A variable genuinely undeclared must still be reported even if a
    {% set %} of the same name exists.  Verifies the subtraction does not
    silently drop real undeclared vars.

    NOTE: Jinja2's find_undeclared_variables already resolves top-level
    {% set x = y %} correctly (y is reported, x is not), so this test
    confirms the combined fix does not regress that behaviour.
    """
    # x is assigned via set, but y is never assigned — y must remain in result
    template = '{% set x = y %}{{ x }}'
    result = extract_variables(template)
    assert 'y' in result, f"Expected 'y' in result, got {result}"
    assert 'x' not in result, f"Expected 'x' not in result, got {result}"
```

## Alternatives Considered

1. **Post-process with regex** — strip `{% set varname ... %}` patterns before parsing. Fragile: misses multiline or complex set expressions and does not use the AST that is already available.
2. **Replace `find_undeclared_variables` entirely** — write a full AST walker. Higher risk of regressions; the targeted subtraction approach is minimal and surgical.
3. **Accept the false positive and document** — unacceptable: it blocks valid prompts and violates Commandment 6 (never substitute everything when a filter yields nothing).

## Related

- `yamlgraph/utils/template.py` — `extract_variables()`, line ~40
- `tests/unit/test_template.py` — existing tests for `extract_variables`
- NC-196 — recap prompt that triggered discovery
- Jinja2 known limitation: `meta.find_undeclared_variables` does not resolve scope in nested blocks
- `REQ-YG-216` to be added to `ARCHITECTURE.md`
