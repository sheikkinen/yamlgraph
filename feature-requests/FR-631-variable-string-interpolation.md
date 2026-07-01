# FR-631: Variable String Interpolation in Node Variables

**Priority:** MEDIUM
**Type:** Feature
**Status:** Draft
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
