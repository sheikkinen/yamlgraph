# The ignition key

**Date:** 2026-06-22
**FR:** FR-565 (DM v3 producer integration -- author & attach plot plan)

## What happened

Five milestones of typed infrastructure -- schema, projections, exclusion seam,
causal trio, affect closure, author, validate, realize -- sat dormant. Every
consumer seam was wired, every gate was tested, every dormancy invariant held.
But the pipeline never produced a plan. The entire v3 arc was a loaded gun with
no trigger.

The missing piece was `author_plot_plan`: one `async def` that runs the authoring
graph, parses through the tolerant boundary, and writes through the gated seam.
Thirty lines of glue between three already-tested components.

## The trap: infrastructure without activation

The strangler-fig pattern worked exactly as designed: each milestone added a seam,
tested its dormancy, and moved on. But the pattern has a blind spot -- when every
piece is individually correct and collectively inert, there is no failing test to
tell you the system doesn't work. The consumer seams pass because no plan is
attached. The author passes because no one calls it. The validator passes because
no plan reaches it in production.

The symptom was invisible: `generate_and_review.sh` ran successfully, produced
perfectly valid v2 books, and every test was green. The absence of a feature looks
exactly like the presence of a dormant feature when your tests are written to
prove dormancy.

## The insight: activation is a separate deliverable

The strangler-fig milestones M0-M4b built the parts. But "connect the parts" is
its own deliverable with its own acceptance criteria, not an afterthought.
Activation tests are different from unit tests: they prove the pipeline fires
end-to-end, not that each piece works in isolation.

## The serialization surprise

`write_plot_plan` stored a Pydantic model on the doc, but `story_doc.write` calls
`json.dumps`. The model is not JSON-serializable. The fix was two-sided:
`write_plot_plan` stores `plan.model_dump()` (a dict), and `attached_plot_plan`
reconstructs via `PlotPlan.model_validate(raw)`. The round-trip is now
value-equal, not identity-equal -- a pre-existing test that used `is` had to
become `==`.

This is the boundary normalization pattern: the write seam stores the portable
form, the read seam reconstructs the typed form, and the storage layer never sees
a Pydantic model. The `isinstance` guard in `attached_plot_plan` handles both the
in-memory path (model already attached) and the disk path (dict from JSON).

## Heuristic

**activation_as_deliverable:** When building a strangler-fig migration, schedule
"wire it up" as an explicit milestone with its own tests. The parts being correct
does not imply the whole is active. An integration test that proves the pipeline
fires end-to-end is the ignition key.

## Seed

The `--plot-plan` flag is opt-in. At what point does it become the default? When
the realize binding (FR-564) has proven stable across N generated books, the flag
should flip to opt-out (`--no-plot-plan`). But that transition needs a witness:
how many books have been generated with the flag on, and did their continuity
scores improve? The continuity witness (FR-530) could track this if it knew
whether a plan was attached.
