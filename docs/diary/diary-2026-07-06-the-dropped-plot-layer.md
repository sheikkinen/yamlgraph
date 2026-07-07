# The Dropped Plot Layer

**Date:** 2026-07-06
**Context:** Story pipeline planning for novel_fandom. Operator: "earlier process was premise → synopsis → plot generation → timeline. plot generation asked for fleshed out 3-5 plots. reflect."
**Trap:** `ask_before_generate` violated at plan time — who solved this before? The answer was two directories away, in the project's own lineage.

## The Archaeology

Three generations of story pipeline exist in `~/Documents/src`, and each dropped something the previous one had:

**Gen 1 — `langgraph-poc-narrator/src_novel`** (premise → synopsis → plots → timeline):
- `SynopsisOutput` required **3–6 `PlotThread`s** as first-class objects at synopsis time
- `PlotElaboration` *required* `complications` and `turning_point` fields — the schema made it impossible to return a valid plot without naming opposition
- `PlotElaborationBeat.connections` — each beat cited *other threads it connects to*; each elaboration received the list of OTHER plots as context
- `Beat` had `act`, `sequence`, `plot_threads`, `importance` — a total order over beats, with thread interleaving

**Gen 2 — `dungeon_master/api/plot`**: formal `<initial state, agents, goals, functions, order>` plot model with a *mechanical validator*: world-truth vs. belief distinction, and the CLOSED AFFECT invariant — every emotional unit opened must be closed by a later beat or declared intentionally open, checked by Python, not by the model.

**Gen 3 — `novel_fandom`**: premise → synopsis → typed entity canon. **No plot object at all.** Events have `year` but no sequence. No thread, no beat, no affect ledger.

## The Diagnosis

Every defect diagnosed in the last two days maps to a field that existed in an ancestor and was dropped:

| Current defect | Ancestor's cure |
|---|---|
| De-escalation: tensions dissolve | Gen 1 `complications` — required field; Gen 2 CLOSED AFFECT — mechanical open/close balance |
| One plot line, so closing tension ends the story | Gen 1: 3–6 concurrent threads — one closes while another escalates; subplots are the *carriers* of sustained opposition |
| Horizontal silence: entities don't connect | Gen 1 `connections` / `thread_connections` — cross-thread references were schema-required |
| 19 events at year 0, unorderable | Gen 1 `Beat.sequence` + `act` — total order existed |
| Tension ledger proposed as a new idea | Gen 2 CLOSED AFFECT validator — already implemented, already tested (`test_plot_affect_closure.py`) |

The story pipeline plan spent an evaluation cycle *re-deriving* throughlines, sequence fields, and a mechanical tension gate — all reinventions of `PlotThread`, `Beat.sequence`, and the affect-closure validator. The plan was sound; it was also archaeology-blind.

## Why the Layer Was Dropped

Gen 3 optimized for *canon consistency* — 55 FRs of referential integrity, lane immutability, dedup gates. Entities are easy to gate: they either reference each other or they don't. Plots are hard to gate: a thread is a claim about *pressure over time*, not a lookup. The pipeline kept what was mechanically checkable and silently dropped what wasn't. This is `gate_checks_shape_not_substance` acting as a *selection force on architecture*: over generations, the layers that survive are the ones the gates can see. The plot layer had the most narrative value and the least gate-compatibility, so it went extinct.

## Heuristic

**Before planning a pipeline, excavate its ancestors.** When a project is the third generation of an idea, the first diagnostic is not analysis of the current artifact but a diff against the lineage: what fields, layers, and invariants existed before and are missing now? Dropped layers are not neutral — they were dropped because they resisted the previous generation's gates, which means they are *exactly* where the current generation's quality defect lives. `changelog_first_diagnostic`, applied across repositories instead of commits.

## Consequences for the Plan

The story pipeline plan should absorb, not reinvent:
- Step 1 throughlines ≈ per-character projection of Gen 1's multi-thread structure — but consider making plot threads first-class again (3–5 threads over the existing events), since character arcs and plot threads are different decompositions and the thread one is what fights de-escalation
- The `sequence: int` prerequisite FR is Gen 1's `Beat.sequence` — port, don't design
- The tension-ledger gate script should start from Gen 2's affect-closure validator (`dungeon_master/api/plot/validate.py`, `test_plot_affect_closure.py`) — the open/close-balance walk is the same algorithm

## Seed

The three generations form a selection experiment: gates shape which architectural layers survive. Could the capability registry record *dropped* capabilities alongside retired ones — a fossil record — so that generation N+1 can see what generation N-1 knew? A `CAP-*-extinct.yaml` with the reason for extinction would have surfaced `PlotThread` in one grep.
