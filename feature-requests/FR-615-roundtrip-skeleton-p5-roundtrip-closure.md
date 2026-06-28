# Feature Request: Round-trip skeleton P5 — round-trip closure (deferred)

**Priority:** LOW
**Type:** Feature
**Effort:** 2 days
**Requested:** 2026-06-28
**Status:** Re-judged after Decision fold — Authority SUSTAINED in principle; DEFERRED, now owns prose-vs-plan fidelity check (2026-06-28)

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

## Judgement (2026-06-28)

**Verdict: Authority GRANTED in PRINCIPLE; DEFERRED.** Gated on P0–P4 holding and on its own Raw
Output Read (K ≥ 5 synopsis pairs). Correctly LOW priority and off the critical path.

**Claims verified.** The L4b-classifier-**comparison-side-only** discipline is consistent with the
entire arc — `scene_type` is authored, so recognition is only ever a preservation check, never a
generation input. "Reconstruction is the gold" is the architecture's strongest deterministic,
judge-independent signal; approving the principle is sound.

**Correction 1 (secondary).** `roundtrip_diff`'s "deterministic preservation number" is **not**
deterministic if event alignment is done by an LLM. Specify the diff is over **structured extracted
events** (deterministic set/edge comparison), or it inherits the judge-taste it claims to escape —
contradicting the value statement.

**Correction 2 (secondary).** Hold the deferral firmly: do not let P5's reconstruction ambition
pull scope forward into the skeleton. P5 begins only after P3 yields a real baseline and P4 moves
it — and only after its Raw Output Read is filled from real (synopsis, synopsis′) pairs.

**Frozen scope.** Stays off the critical path. Authority to build conditioned on P0–P4 holding,
deterministic structured diff, and K ≥ 5 reconstruction-pair reads logged before commit.

## Decision fold (2026-06-28) — P5 owns the prose-vs-plan dangling check (option a consequence)

P3 ([FR-613](FR-613-roundtrip-skeleton-p3-coherence-gate.md)) measures closure **structurally over
the authored briefs** (option (a)). The prose-side question P3 deliberately rejected — *does the
generated prose actually deliver the authored close?* (the rejected option (b)) — lands **here**, on
the comparison side, alongside the L4b `scene_type` preservation check:

- Add `classify_affect_prose` (llm, comparison side only): extract affect opens/closes from the
  generated prose and diff them against the **authored** `eff_affect` arc. An authored close the
  prose never delivers is a *prose dangling* — the legitimate book-level signal P3's plan-level
  metric cannot see.
- This is also where P4's precision claim is independently audited: P4 hand-checks reactive closes
  against prose at Raw-Output-Read scale; P5 mechanizes that check across all chapters.

## Re-Judgement (2026-06-28)

**Authority SUSTAINED in principle; DEFERRED.** The fold gives P5 a sharper mandate: it now owns the
prose-vs-plan dangling check (`classify_affect_prose`, the rejected option (b)) AND mechanizes P4's
precision audit across all chapters. This is the correct home for both — the expensive prose-fidelity
check belongs off the skeleton's critical path.

Note the dependency this creates: P4's tautology guard is only manually spot-checked (K ≥ 5) until
P5 lands, so **P5 is not truly optional for the chain to make an honest fidelity claim** — it is the
mechanized proof that P4's number was not gamed by fiat. Keep it deferred for BUILD order, but it is
the fidelity-closure the skeleton's headline ultimately depends on. `roundtrip_diff` must remain a
deterministic structured-event diff (Correction 1, still binding). Sustained.

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
- `classify_affect_prose` (llm, comparison side only): extract affect opens/closes from the prose
  and diff against the authored `eff_affect` arc — the prose-vs-plan dangling check (option (b),
  routed here because P3 measures the plan, not the prose).
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
