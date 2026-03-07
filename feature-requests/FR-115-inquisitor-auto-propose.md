# Feature Request: Inquisitor Auto-Propose Fix Proposals for Persistent Violations

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-07

## Summary

Add a `--propose` flag to `.chaplain/inquisitor.sh` that detects violations persisting across ≥2 consecutive Inquisitor Audit entries in `docs/diary.md` and writes targeted fix proposals to `.chaplain/inbox/` for the Plan→Judge pipeline to process.

## Value Statement

Maintainers get automated remediation of recurring audit violations, closing the audit→action gap where repeated ✗ findings accumulate as ritual without driving change.

## Problem

The inquisitor (FR-076) audits recent commits against the Scripture and records findings in `docs/diary.md`. When a violation persists across multiple audits, it appears repeatedly but nothing converts the finding into an actionable fix. The audit becomes observation without correction.

Concrete evidence from the diary: two violations (ARCHITECTURE.md "7 providers" count and FR-112 "Status: Draft") persisted across 7 consecutive Inquisitor Audit entries, generating ~1,700 words of documentation. Each fix requires <1 minute of work. The process inverted — documenting the violation costs more than fixing it.

Today the only path from violation to fix is manual: a maintainer reads the diary, identifies the persistent violation, and writes a topic file to `.chaplain/inbox/`. This handoff never happens reliably.

The diary itself diagnosed this trap (Audit VII):
> *"A process that generates more entropy about a problem than the problem contains is not auditing — it is amplifying."*

## Proposed Solution

Add a second copilot call to `inquisitor.sh`, gated behind `--propose`. The existing audit call remains unchanged; the propose call runs after it.

### Shell changes

```bash
# .chaplain/inquisitor.sh — additions only
PROPOSE=""
if [[ "${1:-}" == "--propose" ]]; then
    PROPOSE="true"
fi

# ... existing audit copilot call (unchanged) ...

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

Each generated file in `.chaplain/inbox/` follows this structure:

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
| One file per violation type | Aligns with inbox processing (`watch.sh` processes one file at a time). Prevents proposal sprawl. |
| Filename-based dedup | Simple, filesystem-visible. No hidden state. Operator can clear inbox to re-trigger. |
| Copilot does all classification | Keeps shell thin. Violation classification requires semantic understanding of diary text. |

### What changes

| File | Change |
|------|--------|
| `.chaplain/inquisitor.sh` | Add `--propose` flag parsing and second copilot call |

### What does NOT change

- Audit behavior without `--propose` — identical to current implementation
- `.chaplain/watch.sh` — already processes any `.md` file in inbox
- `examples/copilot/graph.yaml` — Plan→Judge pipeline unchanged
- `docs/diary.md` format — proposal mode only reads it

## Acceptance Criteria

- [ ] `inquisitor.sh --propose` accepted without error
- [ ] `inquisitor.sh` without flag behaves identically to current implementation (46-line audit-only flow)
- [ ] Persistent violations (same ✗ item in ≥2 consecutive `## YYYY-MM-DD: Inquisitor Audit` entries) generate proposal files
- [ ] Proposals written to `.chaplain/inbox/` as markdown files
- [ ] Proposal filename follows pattern: `inquisitor-<violation-type>.md`
- [ ] No duplicate proposal written if `.chaplain/inbox/` already contains a same-named file
- [ ] Micro-fixes (status field, count, missing entry) propose direct change descriptions
- [ ] Structural gaps (missing REQ-YG-XXX, absent test tags) propose FR stubs
- [ ] Proposals are picked up by `watch.sh` on next poll cycle (no integration changes needed)
- [ ] Smoke test: run `--propose` against a diary with known repeated violations, verify proposal file created
- [ ] Documentation updated in `.chaplain/inquisitor.sh` header comments

## Alternatives Considered

1. **Merge propose logic into the audit copilot call** — Single call is simpler, but mixes read-only audit (writes diary) with write side-effects (writes inbox). Violates the principle that audit is observation. Rejected.

2. **Python extraction of violation patterns** — Could regex-parse diary for ✗ lines and compare across entries. More testable but duplicates the semantic understanding the copilot already has. Over-engineering for a thin-shell tool. Rejected.

3. **Automatic propose on every audit (no flag)** — Too aggressive. Every audit would potentially flood the inbox. The flag gives operators explicit control over when proposals are generated. Rejected.

4. **Cron-based separate script** — Would diverge from the existing chaplain tool family (`inquisitor.sh`, `watch.sh`). Adding a flag keeps the tool surface area small. Rejected.

## Judgement

**Verdict: APPROVE** — 2026-03-07

The FR is clear, minimal, and well-aligned with the chaplain tool family.

**Strengths:**
- Compelling evidence: 7 consecutive audits documented the same two violations (~1,700 words); each fix requires <1 minute. The process cost exceeds the problem cost — classic audit-as-ritual trap.
- Single Responsibility preserved: audit stays read-only, propose has write side-effects, separated by flag.
- Zero integration changes: inbox files are already processed by `watch.sh` → Plan→Judge pipeline.
- Thin-shell pattern maintained: semantic classification delegated to copilot, not regex.

**Implementation notes (non-blocking):**
1. **Filename determinism**: The `<violation-type>` slug is LLM-generated, making dedup fragile across runs. Add prompt guidance: "Use kebab-case, max 3 words, derived from the failing check name (e.g., `inquisitor-architecture-count.md`, `inquisitor-fr-status-draft.md`)."
2. **Edge case**: "Read the last 5 Inquisitor Audit entries" — say "up to 5" to handle diaries with fewer entries.
3. **Smoke test**: AC #10 should clarify this is a manual verification (no shell test infra exists). Consider documenting the test procedure in the script header.

Scope frozen. Authority granted.

## Related

- `.chaplain/inquisitor.sh` — The script to be extended
- `feature-requests/FR-076-chaplain-inquisitor.md` — Original inquisitor FR (implemented)
- `feature-requests/068-chaplain-watch.md` — Watch loop that processes inbox
- `feature-requests/FR-098-consolidate-watch-graph.md` — Consolidated watch graph (implemented)
- `examples/copilot/graph.yaml` — Plan→Judge pipeline that processes inbox proposals
- `docs/diary.md` — Source of audit history for persistence detection
