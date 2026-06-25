# Feature Request: FR-587 Plot Modeller — L5 snapshot-then-diff (comprehend / represent split)

**Priority:** HIGH
**Type:** Feature (architecture revision)
**Status:** Judged — Authority GRANTED (2026-06-25)
**Effort:** 1–2 days (spike-gated; the snapshot+diff spike is ~0.5 day and may KILL early)
**Requested:** 2026-06-24
**Predecessor:** FR-585 (L5 select→type split KILLed; deconfounded). See its Implementation section.
**Blocks:** FR-579 (merge/pipeline)

## Summary

FR-585 killed the *select-then-type* decomposition of L5: peeling typing off
salience-selection left precision flat at ~0.30 across three prompt architectures
(FR-584 monolith 0.30, open-vocab decode 0.14, closed-vocab decode 0.32). The
deconfounded Pass-2 run isolated the residual wound to a single mechanism —
**journey-waypoint over-tracking in `at`** (86 FPs, 88% of all FPs): the model now
correctly empties talk/decide beats but tracks *every leg* of *every journey* as
`at`-pairs, while the ground truth scores only the salient relocations.

FR-585's own post-enforce reflection named why all three architectures failed the
same way: **each fuses two cognitively distinct operations in a single LLM pass** —
*comprehension* (narrative prose → implied persistent world-state) and *encoding*
(closed-vocabulary typed predicate + slice + args + value + **salient-delta
judgment**). FR-585 split only *typing* off *selection*; both live on the encoding
side. The comprehension↔representation seam was never cut, so the flat 0.30 is a
ceiling for *single-operation encoding*, not a proven ceiling for the task.

This FR cuts the real seam. The LLM is asked only to **comprehend** — emit a
world-state **snapshot** after each beat (what is physically true *now*) — and
**code** computes the **change** by diffing consecutive snapshots and collapsing
non-salient intermediate movement. The model never judges "what changed" or "what
is salient"; it only describes the current scene, its strongest mode. The work is
**spike-gated**: the snapshot+diff path is built and measured against the FR-585
Pass-2 baseline first; if it does not move precision, the approach KILLs before any
further node is built and the FR-578 anti-scaling escalation (larger model for L5
only) is finally taken — now tested cleanly with comprehension and encoding loads
genuinely separated.

## Value statement

L5 precision rises toward ~0.5 — unblocking FR-579 — by asking the model only for
*state* (which it is good at) and delegating *change* and *salience* to
deterministic code (which never floods), so the journey-waypoint over-tracking that
caps precision is removed at its source rather than instructed against.

## Judgement (2026-06-25)

**Verdict: Authority GRANTED.** The FR is clear, minimal, and internally
consistent, and it executes the *exact* next lever FR-585's deconfounded KILL
named — cut the comprehend→represent seam (snapshot-not-delta), not reach for a
bigger model first. This is not invented here: FR-585's recorded status, its
Implementation section, and the repo memory all name snapshot+code-diff as the
follow-up's first lever and the bigger-model escalation as the fallback only after
this seam is tested. The discipline is sound throughout — spike-gated with a hard
tripwire, an explicit KILL path into the FR-578 escalation, clean A/B against the
frozen FR-585 Pass-2 baseline, the one-iteration rule (FR-584 fourth-iteration
lesson), and the dumb-adapter / no-GT-leakage constraints carried forward intact.
Moving *salience* and *change* into deterministic code while asking the LLM only to
**describe current state** is the correct structural fix for a missing-discrimination
defect (a faculty wording cannot install), and the `diff_snapshots` helper is
pure-function and unit-tested.

**Red Hat — is the pain real?** Yes, and rigorously isolated: the wound is a single
mechanism (`at` over-tracking, 86 FPs = 88% of all FPs, journey-waypoint flooding),
verified by reading raw output, not just aggregates. The snapshot bundles one
judgment where the delta prompt bundled three. Building a ~0.5-day spike to test it
before paying for scale is the cheaper, more diagnostic move.

**Claims verified against the codebase.** FR-585 status = *Gate 1 FAILED
(deconfounded), select→type KILLed, snapshot-not-delta is the follow-up's first
lever*; precision baseline 0.30 / closed-vocab 0.32 stable; `_type_triple` dumb
adapter (`spike_salience_gate.py`), `evaluate.main_l5`, `analyze_l5_confusion.py`,
and `assign_pre_eff_salience.yaml` all exist as referenced. `diff_snapshots` is
correctly new.

**Corrections required before enforce (clarifications, do not widen scope):**

1. **Resolve the Gate-1 tripwire's confound (primary correction).** The gate ANDs
   three conditions — `at`-FP 86→≤30, recall ≥ 0.50, precision ≥ 0.40 — but the
   spike types snapshots with the *dumb keyword adapter*, which FR-585's C1 showed
   **caps the absolute precision number** for adapter reasons unrelated to the seam.
   Pinning an absolute precision ≥ 0.40 gate on a dumb-adapter run risks a
   **false-KILL on an adapter artifact** — exactly the instrument-confounds-the-metric
   trap FR-585 was burned by. Make the decision rule explicit: **`at`-FP falling
   materially below 86 with recall holding (≥ 0.50, no catastrophic 0-beat run) is
   the GO/KILL decider** (the FR already calls this the "adapter-robust signal");
   absolute precision ≥ 0.40 is **corroborating, not gating**, on the dumb adapter.
   If `at`-FP drops but precision stays flat *because of the adapter*, that is a
   GO into the typed-node stage, not a KILL.

2. **Validate the waypoint-collapse on raw GT before reading the aggregate.** The
   collapse rule (intra-chapter `at`-run → net displacement) *is* the precision
   mechanism, so it must not be hill-climbed against the score. Per FR-585 lesson #1
   (read the raw output before declaring a measurement verdict), confirm the rule
   reproduces the 9 verified `at … value: false` departures by **inspecting the
   fixtures directly first**; if GT scores any intermediate leg as salient, narrow
   or drop the collapse rather than tuning it to the metric. The AC already states
   the guardrail — this fixes the *order of operations* so the rule is not
   self-validated through the number it produces.

3. **Pin the REQ-YG ID for the `diff_snapshots` tests (CI-blocking).** ADR-001 +
   `changelog-req-gate` require the unit tests to carry a valid `@pytest.mark.req`
   and the `feat` changelog fragment's `req:` to match. Reuse an existing
   plot_modeller / node-execution REQ rather than minting a new CAP for an example
   spike; name it before enforce so the gate does not block the PR. Diary reflection
   is already in the ACs (satisfies `diary-gate`).

**Minor note (not a correction):** `Blocks: FR-579` is a forward reference — FR-579
(merge/pipeline) is not yet drafted. Keep it aspirational; do not treat "unblock
FR-579" as a hard dependency of this FR's GO.

**Frozen scope:** Stage 1 (Node A snapshot prompt) + Stage 2 (`diff_snapshots`
deterministic helper) built and proven together as the spike; the wiring of
`graphs/assign_pre_eff.yaml` + `run.py` follows only on GO. Gate 1 decides the whole
FR. One snapshot-wording iteration only. No GT leakage, no evaluator change, no
belief-layer investment, no LLM in the diff, no larger model before the seam is
tested. The corrections above are clarifications within this scope, not additions.

## Problem

The L5 wound, isolated by FR-585 Pass-2, is a **delta-salience** failure. The
prompt asks, per beat, "what world facts does this beat *change*?" — which forces
the model to hold three things at once:

1. the **prior** world-state (what was true before this beat),
2. the **current** world-state (what is true after it), and
3. the **salience** of the difference (which flips matter vs which are incidental
   travel waypoints).

Salient deltas bundle three judgments; the model collapses under the load and
floods the cheapest predicate (`at`). Evidence (salt-road, Pass-2 closed-vocab):

```
F4  chg: at(Naima,Timbuktu)=false, at(Naima,river)=true        # GT scores this
F7  chg: at(Naima,river road)=false, at(Naima,dry country)=true # waypoint — GT silent
F8  chg: at(Naima,dry country)=false, at(Naima,Timbuktu)=true   # waypoint — GT silent
```

The model emits a correct *itinerary*; the GT wants only *net salient relocation*.
A **snapshot** bundles one judgment (current state). Diffing snapshots and
collapsing intra-chapter `at`-runs to net displacement is a deterministic operation
code does reliably and the model does not.

## Proposed solution

Two stages. Build and prove **Stage 1+2 together** (the snapshot+diff spike); the
rest follows only if the gate works.

### Stage 1 — comprehension (the LLM's only job)

**Node A — world-state snapshot.** For each beat, emit the full set of currently-
true world facts *after* that beat, in the five L5 predicates, as a **snapshot**,
not a delta:

> After this beat, list every world fact that is now true: where each named
> character is, what they hold, who is alive, allegiances, and standing relations.
> List the complete current state, not what changed — repeat facts that are still
> true from before.

Output is a **per-beat typed snapshot** (`{id, world: [fluent, …]}`). Encoding a
snapshot still uses the closed vocabulary (so the dumb adapter / structured output
applies), but it requires **no prior-state reasoning and no salience judgment** —
the two loads that broke the delta prompt. "Repeat facts still true" is the
explicit instruction that lets code, not the model, find the changes.

### Stage 2 — representation (deterministic code, no LLM)

**`diff_snapshots` helper (`nodes/tools.py`).** Given the ordered per-beat
snapshots:

- `eff_world[i]` = fluents that **flipped** between snapshot `i-1` and `i`
  (appeared, disappeared, or changed value).
- `pre_world[i]` = the subset of snapshot `i-1` that the flipped fluents reference
  (the preconditions the change acts on).
- **Waypoint collapse:** within a single chapter, a run of single-character
  `at`-transitions for the same character collapses to **net displacement** —
  emit only the departure from the run's origin and the arrival at the run's
  terminus, dropping intermediate legs. This is the deterministic salience rule the
  model was failing to apply. **Guardrail:** the collapse must be validated against
  GT semantics (the 9 `at … value: false` departures FR-585 verified) — if GT
  scores intermediate legs, narrow or drop the collapse; if it scores only net
  displacement, the collapse is the precision win.

Belief slices stay empty for the spike (FR-585: belief is not the wound).

### Files

- `prompts/assign_pre_eff_snapshot.yaml` — new Node A prompt (snapshot only).
- `examples/plot_modeller/spike_snapshot_diff.py` — spike harness: run Node A per
  fixture → type snapshots (reuse FR-585 dumb adapter `_type_triple` for the gate,
  J:C1 carries over) → `diff_snapshots` → write `results/l5/<genre>.yaml` →
  `evaluate.main_l5`.
- `nodes/tools.py` — `diff_snapshots` deterministic helper (+ unit-testable).
- `evaluate.py` — frozen (Part 1 Jaccard stays; scoring unchanged for clean A/B).
- On GO: `graphs/assign_pre_eff.yaml`, `run.py` wire the snapshot node + diff step.

## Acceptance criteria

- [ ] **Gate 1 — snapshot+diff spike (decides the whole FR).** Build Node A
      (snapshot) + `diff_snapshots` only; type snapshots with the FR-585 dumb
      keyword adapter (NOT an LLM — J:C1 carries over). Re-spike on haiku (verify
      `Creating LLM: anthropic/claude-haiku-4-5`), regenerate `results/l5`, report
      precision + `at`-FP via `analyze_l5_confusion.py`. **Tripwire:** PASS
      requires `at`-FP to fall from the FR-585 Pass-2 baseline **86 toward ≤ 30**
      *with recall holding* (≥ 0.50, no catastrophic 0-beat run), AND overall
      precision trending **≥ 0.40**. The `at`-FP absolute count is the primary
      adapter-robust signal (it depends on the diff+collapse suppressing waypoints,
      which passes through any adapter quality). If `at`-FP does not fall materially
      below 86 → snapshot+diff does not beat single-operation delta → KILL, take the
      FR-578 escalation (larger model for L5, snapshot prompt as input), do not
      iterate further.
- [ ] `diff_snapshots` has unit tests (pure function): appearance, disappearance,
      value-flip, and intra-chapter `at`-run collapse to net displacement, each
      tagged `@pytest.mark.req`.
- [ ] Waypoint-collapse validated against GT: confirm the rule reproduces the 9
      verified `at … value: false` departures without inventing departures GT does
      not score. Drop or narrow the collapse if it regresses precision.
- [ ] Confusion re-analysis: the dominant FP class must shift away from `at`
      flooding for the decode to be judged working (`analyze_l5_confusion.py`).
- [ ] Controlled comparison: snapshot+diff vs FR-585 Pass-2 closed-vocab vs FR-584
      no-lever baseline, same temp; report precision, recall, `at`-FP, catastrophic
      count.
- [ ] L5 verdict: combined world recall ≥ 0.70 GO; 0.50–0.70 REVISE; KILL sub-0.50
      with non-fixable confusion. Precision is the primary signal.
- [ ] Diary reflection added.

## Stop rule

If the snapshot+diff path (Gate 1) does not move `at`-FP materially below the
Pass-2 86 with recall holding, the *comprehend/represent split with deterministic
salience* is falsified at this tier — KILL and take the FR-578 escalation (larger
model for the L5 node only, snapshot prompt as its input). This is the honest
escalation point: prompt-wording (FR-581/582), prompt-architecture (FR-584),
select-type decomposition (FR-585), and now comprehend-represent decomposition
(FR-587) will all have failed, so single-tier framing is exhausted and scaling is
tested cleanly. Do **not** iterate the snapshot wording more than once (FR-584
fourth-iteration-ritual lesson).

## Out of scope (explicit)

- **No ground-truth input** of any kind (FR-583 Part 2 leakage KILL stands;
  snapshots are derived from `{glosses, agents}` only).
- **No evaluator changes** (Part 1 Jaccard tolerance frozen; clean A/B).
- **No belief-layer investment** until the world snapshot proves out.
- **No larger model as the first lever** — it is the stop-rule escalation, now
  reached only after the comprehend/represent seam is tested, not before it.
- **No LLM in the diff** — Stage 2 is deterministic code; an LLM diff would refuse
  the whole point (re-fusing change/salience into a model judgment).

## Alternatives considered

- **Larger model directly on the FR-585 Pass-2 prompt** — rejected as first lever:
  it leaves comprehension and encoding fused, so a GO would not reveal *why* it
  worked and a NO-GO would not be clean. Snapshot+diff is the cheaper, more
  diagnostic test and is the FR-585 reflection's named next lever.
- **Prose snapshot → second LLM typing pass → diff** (three stages) — deferred:
  adds an LLM call and a parse surface; the two-stage typed-snapshot+code-diff is
  the minimal test of the core hypothesis (state is easier than salient delta).
- **Few-shot salient-vs-waypoint pairs in the delta prompt** — rejected: it teaches
  salience by example but keeps the three-judgment load in one pass; the structural
  fix (move salience to code) dominates the instructional one.
- **Keep the delta prompt, add a deterministic `at`-run collapse post-step** —
  partially folded in (the collapse *is* Stage 2's salience rule), but without the
  snapshot the model still over-emits non-`at` predicates under delta load; the
  snapshot removes the prior-state reasoning that the collapse alone does not.

## Related

- `feature-requests/FR-585-plot-modeller-L5-salience-gate-decode.md` (predecessor; select→type KILL, deconfounded; Implementation section names this seam)
- `feature-requests/FR-584-plot-modeller-L5-salience-and-roles.md` (prompt-only KILL; "the flood and the miss are one gesture")
- `feature-requests/FR-586-prompt-monolith-linter-check.md` (detects the single-operation overload this FR resolves for L5)
- `docs/diary/diary-2026-06-24-the-flood-that-only-changed-its-name.md` (the comprehend/represent reflection this FR acts on)
- `examples/plot_modeller/prompts/assign_pre_eff_salience.yaml` (FR-585 Pass-2 encoding baseline), `spike_salience_gate.py` (dumb adapter `_type_triple`, reused), `analyze_l5_confusion.py` (measurement witness)
