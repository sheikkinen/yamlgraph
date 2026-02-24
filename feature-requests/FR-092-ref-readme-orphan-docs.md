# Feature Request: FR-092 Link Orphan Reference Docs to Index

**Priority:** LOW
**Type:** Bug
**Status:** Implemented
**Effort:** 15 minutes
**Requested:** 2026-02-24

## Summary

Three reference documents (`expressions.md`, `intent-questionnaire-pattern.md`, `scheduling-agents.md`) exist in `reference/` but are not linked from `reference/README.md`, making them invisible to users navigating via the index.

## Value Statement

Users browsing the reference index discover all available documentation without needing to `ls` the directory.

## Problem

The reference index (`reference/README.md`) is the primary navigation for YAMLGraph documentation. Three files were added to `reference/` without corresponding entries in the index:

| File | Topic | Missing From |
|------|-------|--------------|
| `expressions.md` | Value & condition expression syntax | Core References |
| `intent-questionnaire-pattern.md` | Multi-graph session routing | Examples & Guides |
| `scheduling-agents.md` | Run graphs on schedule (launchd, cron, CI) | Advanced Features |

These docs are only discoverable via filesystem browsing — they are effectively invisible.

## Proposed Solution

Add one row to each of three existing tables in `reference/README.md`:

**Core References table** — after the "Common Patterns" row:
```markdown
| [Expressions](expressions.md) | Value and condition expression syntax |
```

**Advanced Features table** — after the "Contrib Utilities" row:
```markdown
| [Scheduling Agents](scheduling-agents.md) | Run graphs on schedule (launchd, cron, CI) |
```

**Examples & Guides table** — after the "Web UI & API" row:
```markdown
| [Intent + Questionnaire](intent-questionnaire-pattern.md) | Multi-graph routing with session registry |
```

No new files, no structural changes — three line insertions only.

## Acceptance Criteria

- [x] `expressions.md` linked in Core References table of `reference/README.md`
- [x] `scheduling-agents.md` linked in Advanced Features table of `reference/README.md`
- [x] `intent-questionnaire-pattern.md` linked in Examples & Guides table of `reference/README.md`
- [x] All three links resolve correctly (relative paths verified)
- [x] No other changes to `reference/README.md`

## Alternatives Considered

- **Auto-generated index**: A script could scan `reference/` and generate the README. Rejected — over-engineered for a 3-file gap; manual curation allows intentional ordering and descriptions.

## Related

- `reference/README.md` — the index to update
- `reference/expressions.md` — orphan doc (expression syntax)
- `reference/intent-questionnaire-pattern.md` — orphan doc (session routing)
- `reference/scheduling-agents.md` — orphan doc (scheduled execution)
