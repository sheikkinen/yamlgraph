# Feature Request: Value Statement Field in FR Template

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-24

## Summary

Add a mandatory **Value Statement** field to the feature request template — a single sentence declaring who benefits and how. Extend the Judge step to check for its presence before granting authority.

## Problem

Feature requests can pass all six Judge criteria (problem validity, minimality, duplication, testability, effort realism, Scripture compliance) yet still lose sight of _why_ the change matters to the user. Technical elegance without user benefit is entropy (Scripture, Commandment 8).

**Concrete evidence:** FR-082 (sampling backend) passed all technical checks and was implemented over two days with full Sermon compliance. The "does this add value?" question was asked only at teardown — the feature was deleted. Two days of technically correct work, zero user value delivered.

This pattern was documented in the diary entry "2026-02-24: The Lost Seed — Intent Dilution in Plan-Judge Loops": _a plan that cannot restate the original seed in one sentence has drifted from intent._ The current template has **Problem** and **Summary** fields, but neither requires an explicit, structured declaration of user value. The gap sits between "what problem exists" and "who gains what" — two different questions.

## Proposed Solution

### 1. Add Value Statement field to TEMPLATE.md

Insert a **Value Statement** section between **Summary** and **Problem**:

```markdown
## Value Statement

<!-- One sentence: Who benefits and how. -->
<!-- Example: "Graph authors get immediate feedback on broken edges, reducing debug time from minutes to seconds." -->
```

### 2. Add Judge criterion for Value Statement

Add a 7th criterion to `scripts/chaplain-prompts/judge.md`:

```markdown
7. **Value Clarity** — Does the FR contain a Value Statement that names who benefits and how? Reject if absent or vague ("improves things", "makes it better").
```

### 3. Graduate the heuristic to Scripture

Add `intent_drift` to the traps list in the Knowledge Graph (`.github/copilot-instructions.md`):

```yaml
traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
```

This captures the trap without introducing a naming contradiction with `the_one_law`.

## Acceptance Criteria

- [x] `feature-requests/TEMPLATE.md` contains a `## Value Statement` section with guidance comment
- [x] `scripts/chaplain-prompts/judge.md` includes criterion 7 (Value Clarity) in the evaluation list
- [x] Existing FRs are **not** retroactively modified (no churn)
- [x] The Knowledge Graph `traps` list includes `intent_drift`
- [x] `CHANGELOG.md` updated under Unreleased with the enhancement

## Alternatives Considered

1. **Merge into Problem section** — Rejected. The Problem field describes _what's wrong_; the Value Statement declares _who gains what_. Conflating them dilutes both signals.
2. **Automated lint check for Value Statement** — Deferred. The Judge prompt is the existing gatekeeper; adding a script would be scope creep for a 0.5-day task. Can be a follow-up FR if the field proves valuable.
3. **Make it optional** — Rejected. An optional field will be skipped under time pressure, defeating the purpose. The whole point is a forcing function.

## Related

- `docs/diary.md` (entry "2026-02-24: The Lost Seed") — originating seed
- `feature-requests/FR-082-*` — concrete evidence of the gap (deleted after implementation)
- `feature-requests/TEMPLATE.md` — template to modify
- `scripts/chaplain-prompts/judge.md` — Judge prompt to extend
- Scripture, Commandment 8: "Kill all entropy and false idols"

---

## Judgement — APPROVE

**Reviewed:** 2026-02-24
**Verdict:** APPROVE — All AMEND issues addressed. Authority granted.

### Issues Resolved

1. ~~Missing originating seed~~ — Fixed: Now references `docs/diary.md` entry "2026-02-24: The Lost Seed".
2. ~~Naming contradiction~~ — Fixed: Removed `the_value_law`, keeping only `intent_drift` trap.
3. ~~Acceptance criteria gap~~ — Fixed: Now that `the_value_law` is removed, criteria align with solution items.
4. ~~Weak evidence~~ — Fixed: FR-082 cited as concrete example (two days of work, deleted at teardown).

### Implementation

The FR is now minimal, testable, and grounded in observed failure. Proceed with Enforce phase.
