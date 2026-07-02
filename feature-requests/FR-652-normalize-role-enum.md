# FR-652: Normalize role enum at persist boundary

**Priority:** LOW
**Type:** Bug
**Status:** Enforced
**Effort:** 0.25 days
**Requested:** 2026-07-02

## Summary

LLM returns free-text `role` values ("Elder scholar", "One-armed weapons-master") instead of the schema enum (`protagonist`/`antagonist`/`supporting`/`minor`). Add role normalization to `normalize_page` (FR-649).

## Value Statement

Reduces validation warnings for every secondary character the LLM generates, making the validation log meaningful instead of noisy.

## Problem

Evidence: serra_ashfeld gets `role: "Elder scholar and keeper of..."`, torvin_keel gets multiple validation errors including role. The Character schema has `role: Literal["protagonist", "antagonist", "supporting", "minor"]` but the LLM treats it as a description field.

## Proposed Solution

Add to `normalize_page()` in `persist_pages.py`:

```python
_VALID_ROLES = frozenset({"protagonist", "antagonist", "supporting", "minor"})

# In normalize_page:
if page.get("type") == "character":
    role = page.get("role", "")
    if role not in _VALID_ROLES:
        page["role"] = "supporting"  # safe default for LLM-generated characters
```

## Acceptance Criteria

- [ ] `normalize_page` coerces invalid role values to `"supporting"`
- [ ] Valid role values pass through unchanged
- [ ] Test covers role normalization
- [ ] Pipeline run shows fewer validation warnings for character pages

## Related

- FR-649: persist boundary normalization (parent)
- [nodes/persist_pages.py](../examples/novel_fandom/nodes/persist_pages.py)

## Judgement

**Verdict: Granted.** Clean, minimal, follows the established FR-649 normalize_page pattern. One constant, one conditional, one test. No amendments needed.
