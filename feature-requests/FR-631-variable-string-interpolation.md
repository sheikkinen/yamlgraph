# FR-631: Variable String Interpolation in Node Variables

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — Authority GRANTED with constraints (2026-07-01)
**Effort:** 1 day
**Requested:** 2026-07-01
**Surfaced by:** FR-628 wiki-memory demo

## Summary

`resolve_template()` only handles full `{state.X}` replacement. A mixed string
like `wiki/{state.drafted_page.id}.yaml` is returned unchanged, forcing graph
authors to compute paths in Python nodes.

## Root Cause

In `yamlgraph/utils/expressions.py` line 192:

```python
if not (template.startswith("{") and template.endswith("}")):
    return template
```

Any string that doesn't start with `{` and end with `}` is returned as-is.
No f-string style interpolation is attempted.

## Proposed Fix

When a variable template contains `{state.` but isn't a full expression,
perform regex-based interpolation:

```python
import re

_INTERPOLATION_PATTERN = re.compile(r"\{state\.([^}]+)\}")

def resolve_template(template: str | Any, state: dict[str, Any]) -> Any:
    if not isinstance(template, str):
        return template

    # Full expression (existing behavior)
    if template.startswith("{") and template.endswith("}"):
        # ... existing logic ...

    # String interpolation: contains {state.X} embedded in larger string
    if "{state." in template:
        def _replace(match):
            path = match.group(1)
            value = resolve_state_path(path, state)
            return str(value) if value is not None else match.group(0)
        return _INTERPOLATION_PATTERN.sub(_replace, template)

    return template
```

## Constraints

- Must preserve type for full `{state.X}` (lists, dicts returned as-is)
- Interpolated strings always return `str` (mixed content = string)
- `None` values leave placeholder unreplaced (fail visible, not silent)
- Must not break existing `{state.X + 1}` arithmetic expressions

## Acceptance Criteria

- [ ] `wiki/{state.page.id}.yaml` resolves to `wiki/nodejs.yaml`
- [ ] Full `{state.X}` still preserves types (dict, list, int)
- [ ] `{state.missing}` in interpolation left as-is (not crash)
- [ ] Arithmetic expressions unaffected
- [ ] Linter warns on mixed interpolation with non-existent state paths

## Judgement

**Verdict: GRANTED — with constraints.**

The pain is real (FR-628 forced a Python node workaround) and the fix is
well-scoped. The regex approach is correct: `{state.X}` embedded in a larger
string must always stringify.

**Constraints:**
- Drop the linter warning criterion (scope creep — separate FR if needed)
- The regex must NOT match `{state.X + 1}` arithmetic patterns inside larger
  strings — verify with test
- `None` → leave placeholder unreplaced (fail visible, per existing convention)
- Only `{state.path}` syntax — do NOT support `{var_name}` without `state.`
  prefix (that would clash with simple variable substitution in prompts)

**Enforcement order:**
1. RED: Test `resolve_template("wiki/{state.id}.yaml", {"id": "nodejs"})` → `"wiki/nodejs.yaml"`
2. RED: Test full `{state.X}` still returns dict (not stringified)
3. RED: Test `{state.missing}` in mixed string → unchanged placeholder
4. GREEN: Add interpolation branch in `resolve_template()`
5. Verify all 4200+ tests pass
6. Commit
