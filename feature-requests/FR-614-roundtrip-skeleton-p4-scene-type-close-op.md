# Feature Request: Round-trip skeleton P4 — scene_type-aware close-op (move the number)

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-28

## Summary

Widen the L7 affect close-op to recognise **reactive** closure (a feeling resolved by
recognition/naming/decision in dialogue or thought), gated on the brief's authored
`scene_type`, and prove it moves the P3 baseline. This is the carried-over "cheapest first
move" from [plan-scene-typing.md](../examples/plot_modeller/docs/plan-scene-typing.md), now run
inside the skeleton harness rather than against an isolated layer. Phase 4 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Fixes the located root cause of L7's chronic AMBER-RED — the close-op is proactive-only — and
does it with a number that moves, not a layer graded in a vacuum.

## Problem

`prompts/affect_throughline.yaml` defines the close-op in purely ACTION terms ("a resolution
beat shows a forceful or positive action that ENDS an earlier negative feeling"). A feeling
resolved by recognition/decision in dialogue matches nothing → emits no close → the open
dangles. Reactive chapters therefore dangle by construction. scene_type is the missing INPUT to
the close-op decision, not a cosmetic tag.

## Raw Output Read (measurement / metric-tooling FR)

> **Gate precondition (read_raw_output_first):** before authority, read the P3 per-sample
> close-op emissions on **reactive** chapters (K ≥ 5) and confirm, per sample, that the
> dangling open is a recognition/decision close the action rubric could not match — the
> mechanism, witnessed, not inferred.

- **Samples read:** _TBD — link `logs/p4-raw/*.md`._
- **What I saw:** _TBD — one concrete per-sample dangling-open with its unmatched reactive
  close (e.g. "ch.3 'she finally lets herself believe him' — a naming close; action rubric
  emits nothing")._

## Proposed Solution

- Record the P3 baseline (RED): `dangling_open_rate` on reactive vs proactive chapters.
- Add a **reactive close branch** to `prompts/affect_throughline.yaml` (or the gate path): a
  feeling resolved by recognition/naming/decision **closes** an open, applied only when the
  chapter's authored `scene_type == reactive`.
- Re-measure (GREEN): reactive `dangling_open_rate` drops; proactive rate stays stable (no new
  false-closes).

## Acceptance Criteria

- [ ] RED baseline recorded before the change (failing/high reactive dangling rate).
- [ ] Reactive `dangling_open_rate` falls measurably vs the P3 baseline.
- [ ] Proactive `dangling_open_rate` unchanged within noise (no false-close inflation).
- [ ] Before/after numbers recorded in the phased plan's results log.
- [ ] Change gated on authored `scene_type`; no cross-beat inference smuggled in (FR-598-safe).

## Alternatives Considered

Infer scene_type inside affect_throughline while also doing cross-beat close inference —
rejected: overloads one node with recognition + cross-beat inference (the AMBER-RED part). The
tag is authored upstream and merely consumed here.

## Related

- [plan-scene-typing.md](../examples/plot_modeller/docs/plan-scene-typing.md) (cheap first move)
- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P4)
- Predecessor: FR-613 (P3). Successor: FR-615 (P5 round-trip closure)
