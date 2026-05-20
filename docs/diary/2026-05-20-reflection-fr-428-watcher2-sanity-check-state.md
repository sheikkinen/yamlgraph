## 2026-05-20: FR-428 — Watcher2 post-validate sanity check reflection

**Date:** 2026-05-20
**FR:** FR-428 (missing diary reflections for FR-423 and FR-424)
**Reviewer:** watcher2 post-validate sanity pass

## What Happened

FR-428 adds retrospective diary reflections and witness tests for two FRs (FR-423 and
FR-424) that were merged without their required Distill artifacts. The implementation
is structurally correct: both diary files exist with `> 200` bytes of content, named
traps, `**Seed:**` markers, and proper YYYY-MM-DD-reflection-fr-NNN.md naming. All 10
witness tests pass.

## Trap

*gate_checks_shape_not_substance* — the witness tests validate presence, length, named
traps, and `**Seed:**` markers, but not content relevance to the actual FR. The FR-424
diary reflection describes "Changelog req frontmatter enforcement retrospective" while
the canonical FR-424 feature request (`FR-424-session-timeline-join-script.md`) and the
inquisitor topic file both identify FR-424's primary commit as `feat(hooks): FR-424
session timeline join script`. The reflection is therefore semantically misaligned: it
documents a different aspect of the FR-424 umbrella (the changelog enforcement work)
rather than the session timeline join script work flagged by the inquisitor.

FR-423's reflection is correctly aligned with its scope (watcher plan/judge convergence
stabilization).

## Root Cause

FR-424 was an umbrella FR whose commits spanned changelog enforcement, CI gates, and the
session timeline join script. When writing the retrospective reflection, the implementer
chose the changelog-enforcement facet — likely the most impactful from a governance
standpoint — rather than the facet explicitly flagged by the inquisitor. The tests
enforce structure, not semantic relevance; the mismatch slipped through all automated
gates.

## What Worked

- Established remediation pattern (FR-152, FR-161) followed exactly.
- `> 200` non-stub threshold applied consistently with precedent per judge note.
- No watcher2 FSM, CI gate, or inquisitor cadence logic was changed.
- Scope is proportional: 5 files, 273 lines, purely additive.
- Pipeline log shows FSM reached `stopped` state cleanly; prior failure was unrelated
  (a push rejection on a separate worktree/PR).

## Seed

Should the diary-gate validate that reflection content mentions the FR's canonical slug
or scope keyword (extracted from the FR file or commit subject), so that a reflection
about the wrong aspect of an umbrella FR is caught at merge time rather than at the
next inquisitor cycle?
