# Feature Request: Round-trip skeleton P3 — coherence gate (dangling-open rate baseline)

**Priority:** HIGH
**Type:** Feature
**Effort:** 1 day
**Requested:** 2026-06-28
**Status:** Re-judged after Decision fold — option (a) declared, Authority SUSTAINED (design); FINAL authority WITHHELD pending Raw Output Read (2026-06-28)

## Summary

Add `coherence_gate`, a leaf tool that reads the **authored briefs' affect arc** and emits the
scene_type-aware **authored-closure** number (`authored_dangling_rate`, split by scene_type). It
measures the **plan's** closure deterministically, not the prose. This is the phase that turns the
skeleton from a demo into a test harness. Phase 3 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Every later thickening gets a number to move; without a gate the skeleton proves nothing and
the next lane to fix is chosen by intuition rather than measurement.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED for the gate DESIGN; FINAL authority WITHHELD until the Raw Output
Read is filled.** This is a measurement FR. Per the `read_raw_output_first` clause, authority to
commit the metric is withheld until **K ≥ 5 real P2 `book` samples** are read with one concrete
per-sample affect detail each. The FR correctly carries that precondition; it is TBD **by
construction** because P2 must land first. That is the dependency chain working as designed — not
a defect — but it means P3 cannot be *finalized* on the strength of this judgement alone.

**Claims verified.** `validators/affects.py` `check_affect_closure` (FR-571) is a real open/close
pop-walk that already surfaces dangling (unclosed) opens — genuine reusable logic.

**Correction 1 (PRIMARY — the crux of the P3/P4 boundary).** There is an unresolved architectural
inconsistency. `check_affect_closure(plan: PlotPlan, order)` operates on a **structured PlotPlan**
(affect deltas already extracted), **not on prose**. But P3's gate "reads `book` + `briefs`".
So either:
- **(a)** the gate checks the **authored briefs'** closure deterministically — then it measures the
  *plan*, not the generated prose, and "dangling opens in the book" is mislabeled; **or**
- **(b)** the gate runs an affect **classifier over the prose** to extract opens/closes — an LLM
  judge on the roundtrip path, shaped like `affect_throughline.yaml`.

Decide and **declare** which, because P4 depends on it. Under (b), the close-op P4 widens is the
prose classifier; under (a), there is no prose close-op to widen and P4 must instead change the
authored-brief closure logic. The chain cannot be enforced until this is resolved.

**Correction 2 (secondary).** `dangling_open_rate` split `by_scene_type` needs its denominator
**pre-registered** (opens-in-reactive-chapters vs all-opens), or P4's before/after is not
comparable. Fix the formula now, before the baseline is recorded.

**Frozen scope.** One `dangling_open_rate` number split by `scene_type`, baseline logged in the
plan's results table; structural-vs-prose closure decision declared; Raw Output Read filled with
K ≥ 5 real reads **before** the metric is committed.

## Decision fold (2026-06-28) — resolves Judge Correction 1: option (a), STRUCTURAL

**Closure is measured deterministically over the authored briefs, NOT over prose** (option (a)).
The gate reuses `check_affect_closure(PlotPlan, order)` on the per-chapter `eff_affect` ops that
P1 ([FR-611](FR-611-roundtrip-skeleton-p1-cast-briefs.md)) authors onto each brief — a deterministic
pop-walk, no LLM judge on the roundtrip path. Consequences:

- The metric is renamed `authored_dangling_rate` — it counts **unclosed authored opens**, not
  "dangling opens in the book." That book-level label was wrong under (a) and is corrected.
- The gate reads `briefs` (the authored arc), **not** `book`. Prose is read only in the Raw Output
  Read, to confirm the authored arc is faithful — not to compute the metric.
- **P4 ([FR-614](FR-614-roundtrip-skeleton-p4-scene-type-close-op.md)) is thereby unblocked**: with
  no prose close-op to widen, P4 edits the **authoring** rule (reactive chapters may author
  recognition/decision closes), never the shared `affect_throughline.yaml`.
- The **prose-vs-plan** dangling check (the rejected option (b) — does the prose deliver the
  authored close?) moves to P5 ([FR-615](FR-615-roundtrip-skeleton-p5-roundtrip-closure.md)).

**Resolving Judge Correction 2 (denominator pre-registration):** the reactive split is
`unclosed authored opens in reactive chapters / all authored opens in reactive chapters`; the
proactive split is the same over proactive chapters. Fixed before any baseline is recorded.

## Re-Judgement (2026-06-28)

**Authority SUSTAINED (design); the crux is resolved.** The fold declares option (a): closure is
measured structurally over the authored briefs' `eff_affect`, the metric is renamed
`authored_dangling_rate`, the gate reads `briefs` not `book`, and the denominator is pre-registered
(Correction 2 closed). Prose stays a side-witness in the Raw Output Read, never a metric input —
internally consistent.

One consequence the fold must carry into P4 (and the rename already half-does): under (a) the metric
reads what P1 authored and P4 edits the authoring rule, so `authored_dangling_rate` is **movable by
construction**. It proves authoring EMISSION, not story FIDELITY. Acceptable for a deterministic
first number ONLY because fidelity is routed to P5 — but the P3 baseline must be labelled
"authored-plan closure," never "the book's closure." The rename does this; hold the line. FINAL
authority remains gated on the K ≥ 5 raw read once P2 lands.

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

- `coherence_gate` (python leaf): reuse `check_affect_closure(PlotPlan, order)` from
  `validators/affects.py` (FR-571) over the **authored briefs' `eff_affect` ops** — a deterministic
  open/close pop-walk. Read `briefs` (not `book`); report
  `{authored_dangling_rate, opens, closes, by_scene_type}` with the pre-registered denominators.
  Start with this single validator; plan-exists / cast-consistency / entry-exit hand-off deferred.

## Acceptance Criteria

- [ ] One run yields an `authored_dangling_rate` number split by `scene_type` (pre-registered denominators).
- [ ] The gate reads the authored `briefs` arc deterministically (no LLM judge on the path).
- [ ] The Raw Output Read section is filled with K ≥ 5 real reads before authority is granted.
- [ ] The baseline (proactive vs reactive rate) is recorded in the phased plan's results log.
- [ ] Gate is a deterministic leaf tool; graph lints and runs end-to-end.

## Alternatives Considered

Skip the gate and eyeball coherence — rejected: that is the demo trap and gives no target for P4.

## Related

- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P3)
- Predecessor: FR-612 (P2). Successor: FR-614 (P4 close-op widening)
