# The Duplication That Only a Future Feature Could See

**Date:** 2026-06-15
**FR:** FR-489 (DM v2 `session.py` refactor — compose dedup + navigation extraction)
**Commits:** `240a47e5` (Phase 1), `e40d6697` (Phase 2)

## What happened

`session.py` had grown to 485 lines. Asked to "check for *real* refactoring
opportunities," I found two — but they were not equal, and the difference is the
lesson.

**The compose dedup (Phase 1)** was a verbatim four-branch dispatch duplicated
across `weave` and `_autodraft`. It had sat there, harmless, through FR-477,
FR-484, FR-485, FR-487 — four features that each *added a branch to both copies*
and nobody flinched. What made it suddenly worth fixing was not its present cost
but its *future* cost: FR-488 (book-scope chapters) would force a fifth lockstep
edit. The duplication was invisible until a pending feature gave it a price.

**The navigation extraction (Phase 2)** was the size lever. The cluster
(`_can_visit`, `_accept_target`, `_next_unreviewed_char`) was pure tree reasoning
wearing the costume of session methods — `self.`-bound only because that is where
it happened to be written, not because it needed the session. The proof: once
moved, the only coupling was a *single line* (`_accept_target` calling
`_expand_roster`), and the new module needed no `DMSession`, no `TestClient`, no
filesystem to test. The methods were never really methods.

## The trap I nearly stepped in

When I judged Phase 2, the FR I had written left an open question: "move
`accept_target` whole (callback for roster expansion) or only the two pure
functions — start with two, measure, then decide." That hedge *felt* prudent. It
was indecision dressed as caution. Judging my own plan, I read the code instead of
the prose and saw the entanglement was one line — so the "measure then decide"
was a way to defer a decision the code had already made. A callback threading a
graph-invoking side-effect through a module whose entire value proposition is
*purity* would have been a self-inflicted wound. The Judge's job was to kill the
open question, not to bless it.

## The heuristic

**Duplication's cost is denominated in future edits, not present lines.** A block
copied in two places is free until the N+1th feature has to touch both. The signal
to deduplicate is not "this looks repeated" (it always has) but "the next planned
change edits every copy." Let the roadmap, not the line count, schedule the
refactor.

**Corollary (purity smell):** a method that is `self.`-bound but touches `self`
only through one incidental call is not a method — it is a pure function with a
costume. The tell is the test: if extracting it lets the test drop the whole
fixture stack (`DMSession`, `TestClient`, filesystem), it was never coupled.
Extract it and let the side-effect stay home.

## What held

Splitting into two one-concern commits (safe pure dedup; then the boundary move)
meant each diff was separately revertable and each ran green against the existing
45-test contract before the next began. The 11 new navigation tests are the first
in this example that need *nothing* but a dict — the extraction paid for itself in
test legibility, not just line count. A purity guard (`doc` byte-for-byte
unchanged) pins the J3 refinement so a future hand cannot quietly reintroduce the
`setdefault` side-effect the old session-bound version had.

## Seed

If the *trigger* for a refactor is "the next planned feature edits every copy,"
could the FR template carry a one-line **"Refactor-before" field** — naming the
duplication or coupling a feature will aggravate — so the cleanup is scheduled
*with* the feature that prices it, not discovered mid-implementation? FR-488 priced
FR-489; would the chapters FR have been cheaper if it had said so up front?
