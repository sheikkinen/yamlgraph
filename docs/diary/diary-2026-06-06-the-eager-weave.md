# Diary — 2026-06-06 — The eager weave was the whole bug

## Context

FR-468 shipped a working DM web board, then I polished its UI four times. Each
polish made the *final beat* prettier. The user's verdict cut underneath all of
it: "current design tries to cut the process short and show the end result only.
that is not the point. journey to the story is." The fix was not another CSS
pass — it was deleting one line of orchestration: the eager `weave` that
`preplan()` ran before the DM saw anything.

## The trap: polishing the symptom of a design error

Four iterations refined the beat card while the real defect — *that there was a
beat at all, this early* — sat one function call up. I was sanding the surface of
a wall that was in the wrong place. The working system's inertia
(`working_system_inertia` in the Scripture graph) hid the misfit: because the app
*worked*, I kept improving its function instead of questioning its shape.

## What enforcement surfaced that the plan missed

Judging the three v2 FRs against the live code caught contradictions the plan
slept on — but the sharpest one only appeared at enforcement time:

- **The v1 tests asserted the exact opposite of v2.** CAP-169's witness tests
  demanded `"winds the great key"` *after preplan*; FR-470 demands no beat after
  preplan. Both cannot pass against one `preplan()`. A redesign that "supersedes
  the interaction model" silently un-implements the requirements that encoded the
  old model. I almost plowed through ~15 files before naming it; instead I stopped
  and asked, because retiring an *Implemented* capability is governance, not a
  refactor. `status: retired` on CAP-169 was the mechanical cure — the codebase
  had already paid for this primitive (CAP-163).

- **A node in `preplan.yaml` cannot be lazy.** FR-471 wanted "beat stubs lazily
  per chapter on first visit" *and* "a `beats` node in `preplan.yaml`." A graph
  node runs eagerly for every chapter at preplan time — the two clauses are
  contradictory. The cure: stubs come from a session-invoked prompt, not a graph
  node. The plan's own O2 ("lazy") refuted its own §5 ("add a node").

- **`commit_beat_tool` is not a commit primitive — it is a *loop step*.** It
  advances `turn_number`/`chapter_index`/`history`. Reusing it to commit an
  arbitrarily chosen beat would corrupt the linear counter. The journey model
  needs random-access commit, so the write had to be extracted into a pure
  `append_beat_to_chapter` helper (FR-472). The function's *name* said "commit a
  beat"; its *body* said "advance the loop." Read the body.

## Heuristic

When a redesign "supersedes the interaction model" of a shipped feature,
enumerate the **witness tests** of the old model first — they are the load-bearing
assertions that will invert, and they encode requirements that must be explicitly
*retired*, not silently broken. A green v1 suite is not neutral ground for v2; it
is the old contract, and contracts are ended on purpose.

## Seed

The four UI polishes were each a locally-correct TDD cycle that moved the product
*away* from its purpose. Could a "purpose drift" check exist — a periodic prompt
that re-reads the original problem statement against the current diff, so that a
streak of green iterations cannot quietly optimize the wrong objective? The
Judge validates execution; what validates that the execution still serves the
intent?
