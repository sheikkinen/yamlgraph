# Feature Request: Allow changelog req: for FRs enhancing legacy capabilities

**Priority:** LOW
**Type:** Fix
**Status:** Planned
**Effort:** 0.5 days
**Requested:** 2026-07-03

## Summary

`test_no_req_collision_across_unrelated_frs` fires a false positive when a new FR's changelog fragment claims a REQ-YG-XXX that belongs to a `fr: legacy` capability. The test assumes every FR claiming a REQ must have its own capability entry, but many FRs enhance existing capabilities without creating new CAPs.

## Value Statement

Changelog fragments can carry `req:` traceability for FRs that enhance legacy capabilities, instead of omitting the field to work around the test.

## Problem

The cross-wiring test at `tests/unit/test_changelog_req_cross_wiring.py:99` (`test_no_req_collision_across_unrelated_frs`) builds a mapping of FR→REQs from `capabilities/CAP-*.yaml` files. It skips capabilities with `fr: legacy`. When two FRs claim the same REQ in their changelog fragments, it checks that both FRs have a capability entry mapping to that REQ.

FRs that enhance a legacy capability (e.g., FR-660 enhances CAP-05 `tool-agent-integration` which has `fr: legacy`) have no capability entry. The test sees `FR-660 capability has no capability` and reports a collision.

**Concrete case:** FR-660 (agent tool unification) legitimately enhances REQ-YG-018 (agent tool integration, CAP-05). FR-451 (temperature fix, released) also claimed REQ-YG-018. CAP-05 has `fr: legacy`. Both FRs correctly enhance the same legacy capability but the test flags them.

**Current workaround:** We omit `req:` from the changelog fragment, losing traceability.

## Proposed Solution

In `test_no_req_collision_across_unrelated_frs`, when an FR has no capability entry (`fr_to_reqs.get(fr)` returns empty), check if the claimed REQ belongs to any `fr: legacy` capability. If it does, that's a legitimate enhancement — not a collision.

```python
# Build set of REQs that belong to legacy capabilities
legacy_reqs = set()
for filepath in sorted(CAPABILITIES_DIR.glob("CAP-*.yaml")):
    data = yaml.safe_load(filepath.read_text())
    if data.get("fr") == "legacy":
        legacy_reqs.update(r["id"] for r in data.get("requirements", []))

# In the collision check:
for fr in frs:
    valid = fr_to_reqs.get(fr, set())
    if req not in valid:
        # FR-663: skip if REQ belongs to a legacy capability
        if req in legacy_reqs:
            continue
        collisions.append(...)
```

## Acceptance Criteria

- [ ] AC-1: FRs claiming REQs from `fr: legacy` capabilities pass the cross-wiring test
- [ ] AC-2: Genuine cross-wiring (FR claiming a REQ from a non-legacy capability it doesn't own) still detected
- [ ] AC-3: FR-660 and FR-661 changelog fragments restored with their `req:` frontmatter

## Alternatives Considered

- **Add CAP entries for every FR**: Correct but noisy — creates hundreds of single-FR capabilities for incremental fixes
- **Skip `fr: legacy` capabilities entirely in the test**: Too permissive — would miss real cross-wiring between legacy REQs
- **Add `enhances: CAP-05` field to changelog frontmatter**: More explicit but invents new schema for a narrow problem

## Related

- FR-660: Agent tool unification (triggered this issue — had to omit `req: REQ-YG-018`)
- FR-661: Loop detector registration (same issue — had to omit `req: REQ-YG-218`)
- CAP-108: Changelog REQ cross-validation gate (FR-247)
- `tests/unit/test_changelog_req_cross_wiring.py`: The failing test
