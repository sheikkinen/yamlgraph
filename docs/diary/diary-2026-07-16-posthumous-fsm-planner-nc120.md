# 2026-07-16 — Posthumous: the FSM planner's unwritten reflection (†2026-03-18)

**Provenance:** written 120 days after the session died, by a
successor, from best-available material (the session's 13.6 MB
chatSessions record; its transcript did not survive — FR-742 F1: age
of debt anti-correlates with material richness). The session
(32c7dcee, "I name thee the FSM planner") orphaned two todos; FR-741
dropped the stale one, FR-742's triage ruled this one UNWRITTEN. This
entry pays the debt. Session UUID for the record:
32c7dcee-465b-46cb-8a61-c1dc42f5e1ce.

**What the session did (reconstructed from the record):**
- Investigated NC-120 (context_map indexing in the FSM engine),
  planned the implementation, judged it ("clear, minimal, internally
  consistent — scope frozen, authority granted"), and enforced Phase 1
  by the book: baseline 310 green → RED 9/9 AttributeError → GREEN
  9/9 → 319 passed, 0 regressions, submitted as bd2e578.
- The judgement caught two spec gaps before code: an uninitialized
  `_context_map_index = {}` that would have broken test fixtures, and
  a two-phase deployment constraint (engine ships before workaround
  removal) — the cheapest bugs, killed in the spec.
- Then judged a second FR (event-socket lazy-reconnect) and found
  **a subtle socket leak in the proposed fix**: on connect failure
  the fd created one line earlier was never closed — and the current
  code had the same leak. The fix was corrected to close on failure.
  Verdict sequence: amend first, then enforce, TDD.

**The insight the session never got to write** (visible in its
record, stated by no one): its own arc was a clean demonstration that
*judgement quality is limited by the judge's willingness to read the
failure path*. Both catches — the uninitialized index and the fd
leak — live on the error branch, exactly where plausible code and
its reviewer default to not looking. The session's last recorded
beats are status bookkeeping; the reflection was queued behind it
and the guillotine came first (the Distill-dies-last pattern FR-742
was built from).

**Posthumous heuristic, offered to its home doctrine:** when judging
a fix for a resource (socket, fd, lock), trace the *failure* path's
resource lifecycle before the happy path's logic — the leak the
session caught was on the line nobody executes on purpose.

**Meta:** this entry exists because a todo store outlived its
session, a forensic tool classed the debt, git cross-examined two
false verdicts out of the instrument (nc393 hyphens; a too-loose FSM
ref), and the one genuinely unwritten reflection had 13.6 MB of
material waiting. The pipeline works: intentions die, records don't.
