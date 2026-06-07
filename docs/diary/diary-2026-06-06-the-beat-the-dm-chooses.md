# The Beat the DM Chooses — 2026-06-06 (FR-472)

## What happened

Phase C closed the DM web UI v2 redesign: a **Generate beat** button that weaves
one chosen beat on demand through a new stateless `weave-beat.yaml` graph, then
commits it on Accept with status flowing `planned → generated → committed`. The
three-phase arc (synopsis review → outline nav → beat generation) is complete and
the v1 eager, forward-only turn loop is gone from the web path entirely.

## The trap the judge caught before I could fall in

`commit_beat_tool` *looks* reusable — it writes a beat to a chapter file, exactly
what Accept needs. But it is welded to the turn loop: it advances `turn_number`,
`chapter_index`, and appends to `history`. Calling it to commit an **arbitrary
chosen beat** would corrupt that linear counter the moment the DM committed beat 3
before beat 1. The judgment (J1) named this and prescribed the cure: extract the
*pure* part — `append_beat_to_chapter(output_dir, chapter_index, title, prose)` —
and leave `commit_beat_tool` untouched but now delegating to it.

The lesson is the **framework_costume** trap inverted: a function that fits the
shape of the need (write prose to a file) but carries hidden linear state. The fix
wasn't to reuse it — it was to extract the 4 lines that were actually general and
let the linear tool keep them too. One helper, two callers, zero duplication, and
the random-access requirement falls out for free.

## The stateless-graph insight

`turn-loop.yaml` is a checkpointed FSM: it *resumes* to a position. A chosen-beat
generator must be **positionless** — a pure function of (chapter goal, windowed
history, the chosen stub). Splitting `plan_all → weave → normalize_beat` out of
the loop into `weave-beat.yaml` with no checkpointer, no interrupt, no edges back
made the graph a function: same inputs, same beat, callable for any (chapter, beat)
in any order. The checkpointer was never the feature; it was the *cost* of the
forward loop the DM didn't want.

## The reuse that mattered

`_recent_history` rebuilds the turn loop's `history[-3:]` window — but from the
**document's committed beats** instead of graph state, using tuple ordering
`(cj, bj) >= (ci, bi)` to stop at the chosen beat. The windowing *logic* was worth
reusing; the *state source* was not. Naming the difference (logic vs. source) is
what kept the stateless graph stateless.

## Seed

Per-beat status is now a flat string (`planned/generated/committed`) compared in
both Python and Jinja. The Phase B diary already asked whether this wants a real
state machine. Now there are two flags (`materialized` on chapters, `status` on
beats) and three transitions. **Seed:** at what point does a YAMLGraph FSM over the
beat lifecycle — with the transitions as data, not scattered string literals —
become clearer than the current imperative flips, and would modeling it expose
illegal transitions (e.g. committing an un-generated beat) the current code
silently permits?
