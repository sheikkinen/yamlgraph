# The string that closed the loop

**Date:** 2026-06-22
**FR:** FR-564 (DM v3 M4b -- realize, beat-driven turn instruction)

## What happened

The design §6b sketched a `to_turn_request(fn, plan) -> TurnRequest` builder that
constructed the entire request from a single `Function`. It looked plausible -- the
types aligned, the fields were named suggestively. But the sketch was a category
error: a `Function` is ONE beat; a `TurnRequest` runs the WHOLE cast for one turn.
The sketch also invented fields (`protected=`, `belief_context=`) that do not exist
on `TurnRequest`, whose `protected` lives inside `TurnExtras`.

## The trap: design-as-type-level-fiction

The design described how the realize binding *should* work at the type level, but the
actual engine's entry point for caller intent is `TurnRequest.instruction: str = ""`.
That's it -- one string. The entire v2 stage→turn boundary flows through that field.
If you try to bypass it with phantom fields, you fight the engine; if you feed it,
the engine cooperates.

The cure was `beat_instruction(plan, chapter) -> str` -- a pure function that renders
the authored beat(s) into the one field the engine already exposes. No schema change,
no `TurnRequest` widening, no import inversion. The additive merge inside
`invoke_turn` mirrors the exclusion seam's additive union: gated on
`attached_plot_plan(doc)`, passthrough when absent.

## The insight: a leaf can steer a trunk through its existing aperture

The plot model is a leaf package (A1 architecture). It cannot import `turn_ops` or
`turn_engine`. But it doesn't need to -- it produces a string, and the trunk
(`invoke_turn`) reads it through the one aperture it already exposes. The constraint
that seemed limiting (leaf cannot import trunk) turned out to be the design pressure
that found the correct shape.

## Heuristic

**aperture_over_schema:** When a leaf needs to steer a trunk, find the trunk's
existing aperture (the field, the parameter, the callback) instead of widening the
trunk's schema. A new field on a shared contract is a coordination cost; a value
through an existing field is a leaf decision.

## Seed

If the turn engine's single `instruction` string carries both stage intent and beat
intent (concatenated), can the turn LLM reliably distinguish them? Or does a richer
instruction schema (structured sections, not just a string) become necessary at
scale? The current additive merge works for one-beat and two-beat chapters, but a
saga with five beats per chapter might need structured delimitation.
