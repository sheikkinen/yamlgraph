# Feature Request: Round-trip skeleton P4 — scene_type-aware close-op (move the number)

**Priority:** HIGH
**Type:** Enhancement
**Effort:** 1 day
**Requested:** 2026-06-28
**Status:** Re-judged (pass 2) — tautology guard RESOLVED (now a binding AC); Authority SUSTAINED (design); FINAL authority WITHHELD pending Raw Output Read only (2026-06-28)

## Summary

Widen the **brief-authoring** rule so reactive chapters author a **reactive** close (a feeling
resolved by recognition/naming/decision), gated on the brief's authored `scene_type`, and prove it
moves the P3 baseline. Under decision (a) the close-op bug lives in the **authoring** prompt, not in
a prose classifier, so the fix is local to the roundtrip and never touches the shared
`affect_throughline.yaml`. This is the carried-over "cheapest first move" from
[plan-scene-typing.md](../examples/plot_modeller/docs/plan-scene-typing.md), now run inside the
skeleton harness rather than against an isolated layer. Phase 4 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Fixes the located root cause of L7's chronic AMBER-RED — the close-op is proactive-only — and
does it with a number that moves, not a layer graded in a vacuum.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED for the DESIGN; FINAL authority WITHHELD until the Raw Output Read is
filled AND the corrections below are bound.** This is the payoff phase and the riskiest in the
chain. Authority gate for Phase 4.

**Root cause CONFIRMED against source.** `prompts/affect_throughline.yaml` line 53–54 literally
reads *"A resolution beat shows a forceful or positive action that ENDS an earlier negative
feeling"* — action-resolution-only. A feeling resolved by recognition/naming/decision matches
nothing, so reactive chapters dangle by construction. The diagnosis is exactly right, and
`scene_type` as the missing **input** to the close-op (not a cosmetic tag) is the correct frame.

**Correction 1 (PRIMARY) — reactive PRECISION is unguarded.** The AC guards proactive stability
("no false-close inflation") but **not** reactive precision. A falling reactive
`dangling_open_rate` could be genuine closes **or** over-emission (closing opens that should
dangle) — the exact failure mode that has REFUTED prior close-op widenings in this lineage
(over-emission lowers the dangling rate *dishonestly*). Add a reactive-precision check: the new
reactive closes must match **real** reactive closes (a small hand-labeled set, or the witnessed
Raw Output Read sample), not merely lower the count. A number that moves the wrong way for the
right reason is the trap.

**Correction 2 (PRIMARY) — fork discipline.** `affect_throughline.yaml` is the **shared** L7
throughline classifier consumed by the prior affect arc's baselines. Editing it in place changes
the classifier for every earlier consumer and breaks the comparability the arc preserved by
**forking** (`affect_locate_goal`, `affect_locate_graph`). Confirmed: the frozen scorer
(`evaluate.py`) does **not** reference `affect_throughline`, so the *scorer* is safe — but the
classifier *baselines* are not. If the roundtrip gate uses a prose classifier (FR-613 corr-1
resolution (b)), P4 must widen a **roundtrip-local fork**, never the shared prompt.

**Correction 3 (secondary).** "(or the draft/gate path)" is an escape hatch that hides where the
close-op actually lives. Resolve FR-613 corr-1 **first**; P4 cannot name its edit site until P3
declares whether closure is structural or prose-classified. Blocked on FR-613's declaration.

**Frozen scope.** Reactive `dangling_open_rate` falls vs the P3 baseline **and** reactive closes
are precision-checked **and** proactive rate stable, all FR-598-safe (authored tag consumed, no
cross-beat inference smuggled in), edit applied to a roundtrip-local close-op — never the shared
`affect_throughline.yaml`. Raw Output Read (K ≥ 5 witnessed reactive dangling opens) filled before
the change.

## Decision fold (2026-06-28) — edit the AUTHORING rule (option a), Corrections 2 & 3 resolved

P3 ([FR-613](FR-613-roundtrip-skeleton-p3-coherence-gate.md)) declared **option (a)**: closure is
measured structurally over the **authored briefs**, not over prose. That resolves this FR's blocked
corrections and changes the edit site:

- **Corr 3 (was: blocked on FR-613's declaration) — RESOLVED.** The edit site is the
  roundtrip-local **brief/affect-authoring** prompt (`prompts/roundtrip/outline_briefs.yaml`, or a
  dedicated affect-authoring node), where the `eff_affect` ops are authored. There is no prose
  close-op; the "(or the draft/gate path)" escape hatch is removed.
- **Corr 2 (fork discipline) — RESOLVED by construction.** We never touch the shared
  `affect_throughline.yaml`, so the prior affect-arc baselines are untouched. No fork needed.
- **Corr 1 (reactive precision) — STILL BINDING, inverted to PRIMARY.** A falling
  `authored_dangling_rate` could be honest reactive closes **or** over-emitted balance (the author
  closing opens that should dangle). Under option (a) P4 edits the rule that authors the metric, so
  the rate falls **by fiat** — it proves EMISSION, not FIDELITY. The binding success criterion is the
  **paired** result, recorded *both or neither*: the rate falls **AND** every new reactive close is
  witnessed deliverable in the prose at the K≥5 raw read. A bare rate win is forbidden.
- The metric is `authored_dangling_rate` (per FR-613), not "dangling opens in the book."

## Re-Judgement (2026-06-28)

**Authority SUSTAINED (design); Corrections 2 & 3 closed, Correction 1 SHARPENED to a PRIMARY
blocker.** The fold resolves edit-site and fork discipline cleanly: P4 edits the roundtrip-local
authoring rule (`prompts/roundtrip/outline_briefs.yaml`), never the shared `affect_throughline.yaml`;
the prior affect-arc baselines are untouched by construction; the "(or the draft/gate path)" escape
hatch is removed. Good.

**Correction 1 — the tautology guard (now PRIMARY).** Under option (a) the metric P4 moves
(`authored_dangling_rate`) is computed from the authored briefs, and P4 edits the rule that authors
them. The number therefore drops **by fiat**: instruct the author to emit reactive closes and the
dangling rate falls whether or not the prose delivers a single one. `authored_dangling_rate ↓`
proves EMISSION, not FIDELITY — a textbook plausible-wrong-answer (passes the shape check,
semantically empty). The fold's prose cross-check is the only real signal, yet the GREEN DoD (plan
line 117) reads the rate drop as the headline and the cross-check as a parenthetical
"(+ precision check)". **Invert that.** P4's binding success criterion is the PAIRED result —
reactive rate ↓ AND every new reactive close witnessed *deliverable in the prose* at the K ≥ 5 raw
read — recorded both or neither. A bare `authored_dangling_rate` win is forbidden; it is the number
moving for the wrong reason. P5 mechanizes this across all chapters, but P5 is deferred, so at
P4-completion the K ≥ 5 manual cross-check is the **sole** guard and must be HARD, not advisory.

**Frozen scope (re-affirmed).** Reactive `authored_dangling_rate` falls AND each authored reactive
close is witnessed in prose (K ≥ 5) AND proactive rate stable AND shared `affect_throughline.yaml`
untouched. Emission without witnessed fidelity is not a pass.

## Re-Judgement (pass 2 — 2026-06-28)

**Tautology guard RESOLVED; Authority SUSTAINED (design).** The PRIMARY blocker is now folded into
the contract, not left as advice: the Acceptance Criteria carry the **PAIRED pass (both or neither)**
— reactive rate falls AND every new reactive close is witnessed deliverable in prose (K ≥ 5) — and
explicitly **forbid a bare rate win** ("emission without witnessed fidelity is not a pass"), with
both results recorded together. That is the inversion I demanded, now enforceable at the AC level
rather than parenthetical in a DoD. The design-of-record [architecture-walking-skeleton.md](../docs/architecture-walking-skeleton.md)
§4 carries the same guard verbatim and §6 P5 is named "not truly optional" — consistent across
plan, doc, and FR.

No open corrections remain on the **design**. FINAL authority is still WITHHELD on the single
standing gate every measurement FR carries: the K ≥ 5 Raw Output Read, fillable only once P3 emits
real per-sample reactive close-op emissions. That is the dependency chain, not a defect.

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

- Record the P3 baseline (RED): `authored_dangling_rate` on reactive vs proactive chapters.
- Add a **reactive close branch** to the roundtrip-local brief/affect-authoring prompt
  (`prompts/roundtrip/outline_briefs.yaml` or a dedicated affect-authoring node): for
  `scene_type == reactive`, author a `close` op when a feeling is resolved by
  recognition/naming/decision. **Never edit the shared `affect_throughline.yaml`.**
- Re-measure (GREEN = the PAIRED result, both or neither): reactive `authored_dangling_rate` drops
  AND every new reactive close is witnessed deliverable in the prose (K≥5); proactive rate stays
  stable (no new false-closes). A bare rate drop is **not a pass** — the rate is movable by fiat, so
  emission without witnessed fidelity is forbidden. Until P5 mechanizes the cross-check, the manual
  K≥5 read is the sole, HARD guard.

## Acceptance Criteria

- [ ] RED baseline recorded before the change (failing/high reactive authored-dangling rate).
- [ ] **PAIRED pass (both or neither):** reactive `authored_dangling_rate` falls measurably vs the P3
      baseline **AND** every new reactive close is witnessed deliverable in the prose (K≥5 raw read).
- [ ] A bare rate win is **forbidden** — emission without witnessed fidelity is not a pass.
- [ ] Proactive `authored_dangling_rate` unchanged within noise (no false-close inflation).
- [ ] Both results (rate + prose-witness) recorded together in the phased plan's results log.
- [ ] Edit applied to the roundtrip-local authoring prompt; shared `affect_throughline.yaml` untouched.
- [ ] Change gated on authored `scene_type`; no cross-beat inference smuggled in (FR-598-safe).

## Alternatives Considered

Infer scene_type inside affect_throughline while also doing cross-beat close inference —
rejected: overloads one node with recognition + cross-beat inference (the AMBER-RED part). The
tag is authored upstream and merely consumed here.

## Related

- [plan-scene-typing.md](../examples/plot_modeller/docs/plan-scene-typing.md) (cheap first move)
- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P4)
- Predecessor: FR-613 (P3). Successor: FR-615 (P5 round-trip closure)
