# Feature Request: Round-trip skeleton P5 — round-trip closure (deferred)

**Priority:** LOW
**Type:** Feature
**Status:** Proposed (deferred — gated on FR-610..614)
**Effort:** 2 days
**Requested:** 2026-06-28

## Summary

Close the generative round-trip: re-derive a synopsis′ from the typed structure and diff it
against the input synopsis ("the reconstruction is the gold"), and add an L4b classifier that
recognises `scene_type` *back out* of generated prose — on the **comparison side only**, to
check the authored tag was preserved. Phase 5 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md). Not
required for the skeleton to be useful; build only after P0–P4 hold.

## Value Statement

Turns the skeleton into the full round-trip the architecture targets — synopsis → typed
structure → synopsis′ — where reconstruction fidelity becomes a deterministic coherence signal
independent of any judge's taste.

## Problem

The skeleton (P0–P4) proves the generative path and the affect-closure gate, but does not yet
verify that the typed structure *preserves* the source — the field-wide missing piece. And the
authored `scene_type` is never checked for preservation, because recognition was deliberately
kept off the generative critical path.

## Raw Output Read (measurement / metric-tooling FR)

> **Gate precondition (read_raw_output_first):** before authority, read K ≥ 5 (synopsis,
> synopsis′) pairs end-to-end and record, per pair, one concrete divergence the diff metric
> must capture (a dropped reversal, a collapsed cause). The validator is authored from
> witnessed divergences, not imagined ones — and validators are not trustworthy by
> construction, so the read is what grounds them.

- **Samples read:** _TBD — link `logs/p5-raw/*.md`._
- **What I saw:** _TBD — one concrete per-pair divergence._

## Proposed Solution

- `reconstruct_synopsis` (llm): typed structure (briefs + cast + closed affect arc) → synopsis′.
- `roundtrip_diff` (python leaf): deterministic comparison synopsis vs synopsis′ →
  preservation report (events kept/dropped, cause edges preserved).
- `classify_scene_type` (L4b, llm): recognise scene_type from each generated chapter's prose;
  **comparison side only** — compare against the authored brief `scene_type` to score
  preservation. Never inserted on the generative path.
- Optional additional gate validators: plan-exists, cast-consistency, entry/exit-state
  hand-off continuity.

## Acceptance Criteria

- [ ] synopsis′ is reconstructed from the typed structure via `yamlgraph graph run` (no runner).
- [ ] `roundtrip_diff` emits a deterministic preservation number.
- [ ] L4b classifier runs only on the comparison side; authored vs recognised scene_type
      agreement is reported.
- [ ] Raw Output Read filled with K ≥ 5 real (synopsis, synopsis′) reads before authority.
- [ ] Graph lints and runs end-to-end.

## Alternatives Considered

Put the L4b classifier on the generative path — rejected throughout this arc: scene_type is
authored, so recognition is only ever a preservation check, not a generation input.

## Related

- [plan-generative-roundtrip.md](../examples/plot_modeller/docs/plan-generative-roundtrip.md) (architecture)
- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P5)
- Predecessor: FR-614 (P4)
