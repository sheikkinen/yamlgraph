# Feature Request: Round-trip skeleton P3 — coherence gate (dangling-open rate baseline)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-28

## Summary

Add `coherence_gate`, a leaf tool that reads the assembled `book` + `briefs` and emits the
scene_type-aware **affect-closure** number (`dangling_open_rate`, split by scene_type). This is
the phase that turns the skeleton from a demo into a test harness. Phase 3 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Every later thickening gets a number to move; without a gate the skeleton proves nothing and
the next lane to fix is chosen by intuition rather than measurement.

## Problem

A walking skeleton without a gradeable output is a demo. The field-wide gap (per the framework
survey) is exactly this: systems measure judge *outputs* but never close the loop with a
deterministic coherence check. The cheapest such check we already have logic for is affect
closure (opens that never close = dangling).

## Raw Output Read (measurement / metric-tooling FR)

> **Gate precondition (read_raw_output_first):** before the Judge grants authority, the author
> must read **K ≥ 5 assembled-book samples** produced by FR-612 (P2) and record, per sample,
> one concrete surprising detail about how affect opens and closes in the prose — *not* a
> description of the schema. The gate checks presence; this section must show substance. The
> raw artifact is the P2 `book`, dumped to `logs/p3-raw/` and read end-to-end before the
> `dangling_open_rate` aggregate is computed.

- **Samples read:** _TBD — link `logs/p3-raw/*.md` once P2 lands._
- **What I saw:** _TBD — one concrete per-sample detail (e.g. "reactive ch.3 opens guilt in
  dialogue and never names a close; the action-default close-op had nothing to match")._

## Proposed Solution

- `coherence_gate` (python leaf): reuse the open/close logic in `validators/affects.py`. Read
  `book` + `briefs`; report `{dangling_open_rate, opens, closes, by_scene_type}`. Start with
  this single validator; plan-exists / cast-consistency / entry-exit hand-off deferred.

## Acceptance Criteria

- [ ] One run yields a `dangling_open_rate` number split by `scene_type`.
- [ ] The Raw Output Read section is filled with K ≥ 5 real reads before authority is granted.
- [ ] The baseline (proactive vs reactive rate) is recorded in the phased plan's results log.
- [ ] Gate is a deterministic leaf tool; graph lints and runs end-to-end.

## Alternatives Considered

Skip the gate and eyeball coherence — rejected: that is the demo trap and gives no target for P4.

## Related

- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P3)
- Predecessor: FR-612 (P2). Successor: FR-614 (P4 close-op widening)
