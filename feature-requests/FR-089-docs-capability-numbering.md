# Feature Request: Fix Capability Numbering Gap in ARCHITECTURE.md

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-24

## Summary

Remove the strikethrough capability row (~~29~~ Incaller Voice Demo) from the ARCHITECTURE.md capability table and annotate the resulting numbering gap to prevent reader confusion.

## Value Statement

Documentation readers get a clean capability table without confusing strikethrough entries, while preserving stable CAP-IDs that are cross-referenced across the codebase.

## Problem

The ARCHITECTURE.md capability table (lines 288–291) contains a gap:

| # | Capability | Status |
|---|-----------|--------|
| 28 | Graph-Level Thinking Budget | Active |
| ~~29~~ | ~~Incaller Voice Demo~~ | Strikethrough (consolidated into outcaller, OC-008) |
| 30 | Copilot Node | Active |

The strikethrough row is redundant — the consolidation is already documented in CAP-27's section note (line 545). The row clutters the table and confuses readers who expect sequential numbering.

## Proposed Solution

**Remove the strikethrough row** and **add a footnote** explaining that capability numbers are stable IDs (not renumbered when entries are retired).

### Before

```markdown
| 28 | Graph-Level Thinking Budget | ... | REQ-YG-083 |
| ~~29~~ | ~~Incaller Voice Demo~~ | ~~consolidated into outcaller (OC-008)~~ | IC-000, IC-001 |
| 30 | Copilot Node | ... | REQ-YG-087, REQ-YG-089 |
```

### After

```markdown
| 28 | Graph-Level Thinking Budget | ... | REQ-YG-083 |
| 30 | Copilot Node | ... | REQ-YG-087, REQ-YG-089 |

> Capability numbers are stable identifiers. Retired capabilities (e.g., CAP-29) are removed rather than renumbered to preserve cross-references.
```

## Acceptance Criteria

- [x] Strikethrough row ~~29~~ removed from capability table
- [x] Footnote added below capability table explaining stable numbering policy
- [x] No renumbering of existing capabilities (CAP-30 stays CAP-30)
- [x] All existing cross-references remain valid (`CAP-30` in `req_coverage.py`, `reference/graph-yaml.md`, `CHANGELOG.md`, etc.)
- [x] `python scripts/req_coverage.py` passes without changes
- [x] Documentation updated

## Alternatives Considered

### Option A: Renumber sequentially (30 → 29)

Renumber CAP-30 to CAP-29 so the table reads 27, 28, 29 without gaps.

**Rejected because:**
- CAP-30 is cross-referenced in **10+ files**: `scripts/req_coverage.py`, `reference/graph-yaml.md`, `CHANGELOG.md`, `feature-requests/FR-081-copilot-node.md`, `docs/diary.md` (7+ entries), `docs/diary-2026-02-23.md`
- Diary entries are historical records that should not be retroactively edited
- The churn-to-value ratio is high for a cosmetic change
- Future retirements would trigger the same cascade

### Option B: Keep strikethrough row as-is

Leave the ~~29~~ row in place.

**Rejected because:**
- The consolidation is already documented in CAP-27's section note (line 545)
- Strikethrough rows in tables are visually confusing and violate "kill entropy" (Commandment 8)
- The row serves no purpose that isn't already covered elsewhere

## Implementation

| File | Change |
|------|--------|
| `ARCHITECTURE.md` | Remove strikethrough row (line 290); add footnote after capability table |

### Estimated touch points

- 1 file, ~3 lines changed

## Related

- `ARCHITECTURE.md` lines 288–291 (capability table)
- `ARCHITECTURE.md` line 545 (CAP-27 section note documenting consolidation)
- `feature-requests/FR-078-relocate-project-tests.md` (removed CAP-29 from req_coverage.py)
- `scripts/req_coverage.py` line 175 (CAP-29 removal comment)
