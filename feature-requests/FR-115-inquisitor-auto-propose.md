# Feature Request: Inquisitor Auto-Propose Fix Proposals for Persistent Violations

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-03-07

## Summary

Add a `--propose` flag to `.chaplain/inquisitor.sh` that detects violations persisting across ≥2 consecutive audits in `docs/diary.md` and automatically writes targeted fix proposals to `.chaplain/inbox/` for the Plan→Judge pipeline to process.

## Value Statement

Maintainers get automated remediation of recurring audit violations, closing the audit→action gap where repeated ✗ findings accumulate as ritual without driving change.

## Problem

The inquisitor (FR-076) audits recent commits against the Scripture and records findings in the diary. When a violation persists across multiple audits, it appears repeatedly (e.g., the same ✗ finding in 5+ consecutive entries) but nothing converts the finding into an actionable fix. The audit becomes observation without correction.

Today the only path from violation to fix is manual: a maintainer reads the diary, identifies the persistent violation, and either fixes it directly or writes a topic file to `.chaplain/inbox/`. This handoff never happens reliably.

## Proposed Solution

Extend `inquisitor.sh` to accept a `--propose` flag. When set, the copilot prompt is augmented with instructions to:

1. **Detect persistence** — Read the last 5 Inquisitor Audit entries from `docs/diary.md` and identify violations (✗ items) that appear in ≥2 consecutive audits.
2. **Classify severity** — Distinguish micro-fixes (status field corrections, missing count updates) from structural gaps (missing REQ-YG-XXX entries, absent test tags).
3. **Generate proposals** — Write one markdown file per persistent violation to `.chaplain/inbox/`, where `watch.sh` picks them up for Plan→Judge processing.
4. **Skip duplicates** — Before writing, check if `.chaplain/inbox/` already contains a file with the same name to prevent redundant proposals.

### Shell changes

```bash
# .chaplain/inquisitor.sh
PROPOSE=""
if [[ "${1:-}" == "--propose" ]]; then
    PROPOSE="true"
fi

# ... existing audit copilot call ...

if [[ -n "$PROPOSE" ]]; then
    copilot --allow-all-paths --allow-all-tools -p "**Propose.**
You are the Inquisitor in propose mode. Your duty: convert persistent violations into fix proposals.

**Step 1 — Read diary:** Read the last 5 'Inquisitor Audit' entries from docs/diary.md.
**Step 2 — Detect persistence:** Identify ✗ VIOLATION items appearing in ≥2 consecutive audits.
**Step 3 — Classify:** For each persistent violation:
  - Micro-fix (status field, count, missing entry): propose a direct fix description
  - Structural gap (missing REQ-YG-XXX, absent test tags): propose an FR stub
**Step 4 — Write proposals:** For each persistent violation, write a markdown file to .chaplain/inbox/:
  - Filename: inquisitor-<violation-type>.md (e.g., inquisitor-missing-changelog.md)
  - Skip if .chaplain/inbox/ already contains a file with the same name
  - Format: Brief title, problem description, suggested fix approach
**Step 5 — Report:** Print a summary of proposals written (or 'No persistent violations found')."
fi
```

### Proposal file format

```markdown
# Fix: [Brief violation description]

## Violation
[What the inquisitor found, which audits flagged it]

## Suggested Fix
[Concrete steps — for micro-fixes: the exact change; for structural gaps: an FR outline]
```

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| Separate copilot call (not merged into audit) | Audit stays read-only (diary only); proposal mode has write side-effects (inbox files). Single Responsibility. |
| Shell flag, not config file | Consistent with thin-shell pattern (FR-076). No new state mechanism needed. |
| ≥2 consecutive audits threshold | Avoids proposing fixes for one-off findings that may self-resolve (e.g., mid-work commits). |
| One file per violation type | Aligns with inbox processing (watch.sh processes one file at a time). Prevents proposal sprawl. |
| Filename-based dedup | Simple, filesystem-visible. No hidden state. Operator can clear inbox to re-trigger. |
| Copilot does all classification | Keeps shell thin. Violation classification requires semantic understanding of diary text. |

### What changes

| File | Change |
|------|--------|
| `.chaplain/inquisitor.sh` | Add `--propose` flag and second copilot call |

### What does NOT change

- Audit behavior without `--propose` — fully backward-compatible
- `watch.sh` — already processes any `.md` file in inbox
- `examples/copilot/graph.yaml` — Plan→Judge pipeline unchanged
- `docs/diary.md` — format unchanged; proposal mode only reads it

## Acceptance Criteria

- [ ] `inquisitor.sh --propose` accepted without error
- [ ] `inquisitor.sh` without flag behaves identically to current implementation
- [ ] Persistent violations (≥2 consecutive Inquisitor Audit entries with same ✗ item) generate proposal files
- [ ] Proposals written to `.chaplain/inbox/` as markdown files
- [ ] Proposal filename follows pattern: `inquisitor-<violation-type>.md`
- [ ] No duplicate proposal written if `.chaplain/inbox/` already contains a same-named file
- [ ] Micro-fixes propose direct change descriptions
- [ ] Structural gaps propose FR stubs
- [ ] Proposals are picked up by `watch.sh` on next poll cycle (no integration changes needed)
- [ ] Smoke test: run `--propose` against a diary with known repeated violations, verify proposal file created
- [ ] Documentation updated in `.chaplain/inquisitor.sh` header comments

## Alternatives Considered

1. **Merge propose logic into the audit copilot call**: Single call is simpler, but mixes read-only audit (writes diary) with write side-effects (writes inbox). Violates the principle that audit is observation. Rejected.

2. **Python extraction of violation patterns**: Could regex-parse diary for ✗ lines and compare across entries. More testable but duplicates the semantic understanding the copilot already has. Over-engineering for a thin-shell tool. Rejected.

3. **Automatic propose on every audit (no flag)**: Too aggressive — every audit would potentially flood the inbox. The flag gives operators explicit control over when proposals are generated. Rejected.

4. **Cron-based separate script**: Would diverge from the existing chaplain tool family (inquisitor.sh, watch.sh). Adding a flag keeps the tool surface area small. Rejected.

## Related

- `.chaplain/inquisitor.sh` — The script to be extended
- `feature-requests/FR-076-chaplain-inquisitor.md` — Original inquisitor FR (prerequisite, implemented)
- `feature-requests/068-chaplain-watch.md` — Watch loop that processes inbox
- `feature-requests/FR-098-consolidate-watch-graph.md` — Consolidated watch graph
- `examples/copilot/graph.yaml` — Plan→Judge pipeline that processes inbox proposals
- `docs/diary.md` — Source of audit history for persistence detection
