# Feature Request: FR-585 Plot Modeller — L5 salience-gate decode + deterministic bookkeeping

**Priority:** HIGH
**Type:** Feature (architecture revision)
**Status:** Enforced (2026-06-24) — Gate 1 FAILED (deconfounded); this FR's split (select→type) KILLed, but the real seam (comprehend→represent; snapshot-not-delta) is untested and is the follow-up's first lever, not a bigger model
**Effort:** 2–3 days (spike-gated; Node-A spike is ~0.5 day and may KILL early)
**Requested:** 2026-06-24
**Predecessor:** FR-584 (L5 prompt-only levers KILLed — salience/roles/subjects all net-negative)
**Blocks:** FR-579 (merge/pipeline)

## Summary

FR-584's controlled A/B proved the L5 precision wound (0.30) is **not** fixable by
prompt instruction at the haiku tier: a salience-suppression rule cut the `at`
flood but raised misses in lockstep (precision flat), one lever was dead, one was
counter-productive, and the levers introduced catastrophic 0-beat runs. The
diary's diagnosis — *"the flood and the miss are one gesture"* — is structural: the
single `assign` LLM call carries ~12 simultaneous cognitive jobs (vocabulary,
slice-splitting, salience discrimination, argument directionality, token-naming
fidelity, movement decomposition, kind priors, belief nesting, agent-membership,
hand-written nested YAML, self-correction). The discrimination tasks — the actual
wound — starve because they compete with bookkeeping.

This FR stops asking one call to do twelve things. It **(1) gives salience its own
LLM call with nothing else to do** (the FR-584 stop-rule's named escalation, a
two-node decode), and **(2) demotes the mechanical rules — movement-pair
emission, token-naming fidelity, YAML serialization — to deterministic code or
structured output**, so the model never spends attention on bookkeeping a parser
can do. The work is **spike-gated**: Node A alone is built and measured first; if
the salience gate in isolation does not move precision, the approach KILLs before
the rest is built.

## Value statement

L5 precision rises toward ~0.5 — unblocking FR-579 — by isolating the one judgement
the model is bad at (which fluents are salient) into a call where it is the *only*
judgement, and by removing from the prompt every rule a deterministic post-step
can enforce more reliably than a distracted generator.

## Problem

The current `graphs/assign_pre_eff.yaml` is a single `assign` LLM node feeding a
`validate_pre_eff` retry loop (3 attempts → empty on exhaustion). That one call,
over **all beats at once**, must simultaneously satisfy:

| # | Demand | Validator-enforced? |
|---|---|---|
| 1 | Map to 5 closed predicates (`VALID_PREDS`) | yes |
| 2 | Split into 4 slices (pre/eff × world/belief) | yes (shape) |
| 3 | **Salience: which facts are preconditions** | **no — the wound** |
| 4 | **Effect: which facts change** | **no** |
| 5 | **`rel` directionality (source/target)** | no |
| 6 | Token-naming fidelity (multi-word, underscores) | only agent-args |
| 7 | Movement → two `at` effects | no (pure prompt rule) |
| 8 | Kind→effect priors (6 of them) | no |
| 9 | Nested belief modeling (`Belief`) | yes |
| 10 | Every arg ∈ agents roster | yes — the loop-limit killer |
| 11 | Hand-write exact nested YAML | yes (parse) |
| 12 | Self-correct from flaw list | — |

FR-584 demonstrated the consequence: under this load the model cannot tell a
salient precondition from an incidental snapshot, so it floods (`at` FPs = 67% of
all FPs) **and** misses true preconditions in the same proportion. Sterner wording
(#3 as an instruction) moved both together and precision not at all. The defect is
a missing *discrimination capability*, and the cure for a missing capability is
architecture, not adjectives.

The catastrophic 0-beat runs trace to #10/#11: when the all-in-one output fails the
agent-membership or parse check three times, the loop exhausts to empty. Demanding
naming/serialization perfection *during* generation is fragile; enforcing it
*after* generation (snap + structured output) removes the failure surface.

## Proposed solution

Three buckets. Build and prove **Bucket 2 Node A first**; the rest follows only if
the gate works.

### Bucket 2 — split the LLM work (the salience-gate decode)

**Node A — salience gate (the hypothesis-bearing call).** One question per beat,
nothing else:

> For this beat, list (a) the world facts that must already be TRUE for it to
> happen, and (b) the world facts it CHANGES. Name each as a short phrase
> ("Hagen holds the relic", "Marren is hostile to Hagen"). Most beats have 0–2 of
> each. If a fact is just where someone happens to be standing and the beat
> neither needs it nor changes it, leave it out.

Output is a **flat minimal list per beat** — no predicate typing, no slice schema,
no belief nesting, no YAML acrobatics. This is the only place precision is won, and
it now gets the model's whole attention. **This node is built and measured against
the no-lever baseline before anything else in this FR is written.**

**Node B — typing / argument-fill.** Takes Node A's selected phrases and renders
each into the typed schema: predicate ∈ {alive, at, holds, rel, faction}, ordered
args (source first for `rel`), value, and the pre/eff slice it belongs to. This is
near-mechanical and a good fit for **structured output / function-calling** (#11
disappears). Belief facts route here too, or to Node C.

**Node C — belief pass (conditional, optional).** Only beats whose kind is
recognition / exposure / mediation get a belief call; all others skip it (the
current prompt already concedes belief slices are "often empty"). Deferred until A
and B land — belief is not the precision wound.

### Bucket 1 — remove from the LLM (deterministic code)

- **#7 movement-pair emission.** A pure rule: if an `eff` contains
  `at(c, dest)=true` and a known `at(c, origin)=true` is in scope, code emits the
  `at(c, origin)=false` departure. Delete CRITICAL — MOVEMENT from the prompt.
  **First measure** whether GT even scores departures; if `=false` fluents are
  rare in ground truth, drop the rule entirely rather than reimplement it.
- **#6 token-naming snap.** Post-process each arg token to the nearest roster
  entry (agents + objects/locations mined from the glosses) by normalized/fuzzy
  match, *capped* so it only corrects near-misses (e.g. case, spacing,
  underscores) and never rewrites a token to a different referent. This attacks
  the #10 loop-limit deaths after generation instead of demanding perfection
  during it. Deletes most of CRITICAL — NAMING. **Guardrail:** the snap must be
  measured for false-merges (does it ever collapse two distinct objects?); if it
  does, narrow or drop it. The evaluator already does tolerant matching, so the
  snap must beat "do nothing" on precision to justify existing.

### Bucket 3 — keep but demote

- **#8 kind priors** become light hints inside Node A, or are dropped if they
  compete with the gloss text (FR-578 anti-prior lesson).
- **#12 retry loop** stays, but each node now has a small, single-purpose contract
  that is far cheaper to satisfy than the 12-job monolith — the loop should rarely
  fire, and never exhaust to empty. **The retry target for the multi-node flow
  must be specified before Node B is wired** (J:C2): when `validate_pre_eff`
  rejects Node B's output, does Node B retry alone (A's selection cached —
  cheaper, tighter contract) or does the pipeline restart from Node A (handles
  malformed A output)? The answer determines the graph YAML structure and whether
  the loop-limit-death failure mode (FR-583 Part 2, FR-584 Lever A) is resolved
  or inherited.

### Files

- `graphs/assign_pre_eff.yaml` — add Node A (and later B/C) nodes + edges.
- `prompts/assign_pre_eff_salience.yaml` — new Node A prompt (salience only).
- `prompts/assign_pre_eff_type.yaml` — new Node B prompt (typing/arg-fill), later.
- `nodes/tools.py` — deterministic movement + naming-snap helpers; existing
  `validate_pre_eff` contract unchanged (it still validates the final typed list).
- `run.py` — wire the multi-node flow; state stays `{glosses, agents}` in, typed
  `pre_eff` list out. **No ground-truth input** (FR-583 leakage KILL stands).
- `evaluate.py` — frozen (Part 1 Jaccard stays; scoring unchanged for clean A/B).

## Acceptance criteria

- [ ] **Gate 1 — Node A spike (decides the whole FR).** Build Node A only; for the
      spike, type its flat output with a **dumb throwaway adapter** (keyword/regex
      mapping, NOT another LLM call — J:C1) so the existing evaluator can score
      it. Re-spike on haiku (verify `Creating LLM` log line), regenerate
      `results/l5`, report precision + `at`-FP via `analyze_l5_confusion.py`.
      The adapter may add noise to recall, but the `at`-FP count (the primary
      precision signal) depends on Node A *not selecting* non-salient facts — that
      signal passes through any adapter quality. **Tripwire (dual — keyed on the
      adapter-robust count first):** PASS requires `at`-FP to drop from the
      baseline **56 to < 30** *with recall holding* (no new catastrophic 0-beat
      run), AND the precision ratio trending **≥ 0.40**. The absolute `at`-FP
      count is the gate; the ratio is fragile under a dumb adapter (it can starve
      the true-positive numerator), so a halved `at`-FP with a *flat* precision
      ratio means recall fell too (adapter starvation, not a Node-A failure) —
      investigate the adapter before KILL. If `at`-FP does not fall materially,
      KILL — do not build B/C; escalate to a larger model for L5 only.
- [ ] Node B added; final typed output validates through the unchanged
      `validate_pre_eff`; structured output used so YAML hand-writing (#11) is gone.
- [ ] Deterministic movement-pair helper: GT scores **9 `at … value: false`
      departures** across the 5 fixtures (verified 2026-06-24, ~10% of `at`
      fluents), so the helper is **in scope** — build it and confirm it lifts
      `at` recall without adding `at`-FP. Drop only if it measurably regresses
      precision.
- [ ] Naming-snap helper added **only if** it beats "do nothing" on precision with
      zero measured false-merges; otherwise dropped and recorded.
- [ ] Confusion re-analysis: the dominant FP class must shift away from `at`
      flooding for the decode to be judged working (`analyze_l5_confusion.py`).
- [ ] Controlled comparison: full decode vs the FR-584 no-lever baseline at the
      same temp; report precision, recall, `at`-FP, and catastrophic-failure count.
- [ ] L5 verdict by J:N2 (combined world recall ≥ 0.70 GO; 0.50–0.70 REVISE; KILL
      sub-0.50 with non-fixable confusion). Precision is the primary signal.
- [ ] Diary reflection added.

## Stop rule

If the Node A salience gate (Gate 1) does not lift precision clearly above the 0.30
baseline, the *decomposition* hypothesis is falsified at this model tier — KILL and
escalate to a larger model for the L5 node only (the FR-578 anti-scaling lesson is
spent once prompt-architecture *and* call-decomposition have both failed; scaling
is then the honest next lever, not the lazy first one). Do **not** iterate Node A
wording more than once — that is the fourth-iteration ritual FR-584 already named.

## Out of scope (explicit)

- **No ground-truth input** of any kind (FR-583 Part 2 leakage KILL stands).
- **No evaluator changes** (Part 1 Jaccard tolerance frozen; clean A/B).
- **No belief-layer investment** until A and B prove out (#9 is not the wound).
- **No larger model as the first lever** — it is the *stop-rule escalation*, not a
  deliverable of the happy path.

## Alternatives considered

- **A fourth prompt-wording pass** — rejected (FR-581/582/583/584 each hit the
  prompt-only stop rule; the fifth is ritual).
- **Larger model first** — rejected as first lever (FR-578: scaling masks framing
  bugs; here the framing bug is task-overload, which decomposition tests directly
  and cheaply before spending on a bigger model).
- **One call with structured output but no decomposition** — rejected: structured
  output fixes #11 (serialization) but not #3/#4 (discrimination under load); the
  wound is attention budget, not output format.

## Related

- `feature-requests/FR-584-plot-modeller-L5-salience-and-roles.md` (predecessor; prompt-only KILL)
- `feature-requests/FR-583-plot-modeller-evaluator-tolerance-and-vocab-grounding.md` (leakage KILL; failure-mode analysis)
- `docs/diary/diary-2026-06-24-the-flood-and-the-miss-are-one-gesture.md` (the structural diagnosis this FR acts on)
- `examples/plot_modeller/graphs/assign_pre_eff.yaml`, `prompts/assign_pre_eff.yaml`, `nodes/tools.py` (`validate_pre_eff`), `analyze_l5_confusion.py` (measurement witness)

## Judgement (2026-06-24)

**Verdict: Authority GRANTED — spike-gated, two conditions folded into spec.**

FR-585 is the correct architectural escalation. The predecessor chain is clean
and each step is the right escalation from the previous failure:

| FR | Lever | Outcome |
|----|-------|---------|
| FR-581/582 | Prompt wording (×2) | Stop rule: next step architectural |
| FR-583 P1 | Evaluator Jaccard tolerance | KEEP (null result, no harm) |
| FR-583 P2 | Vocabulary grounding | KILL (leakage + net-negative) |
| FR-584 | Prompt reasoning-order (×3 levers) | KILL (precision flat at 0.30) |
| **FR-585** | **Task decomposition (two-node decode)** | **Named stop-rule escalation** |

The core hypothesis — "salience discrimination starves because it competes with
11 other cognitive jobs in one LLM call" — is credible and directly supported by
FR-584's evidence: the salience rule moved the `at` flood directionally but
precision stayed flat because misses rose in lockstep (*"the flood and the miss
are one gesture"*). Isolating salience into its own call is the minimal
architectural test of whether the problem is attention competition.

The spike-gated design (build and measure Node A before B/C/deterministic
helpers) is the right discipline. Gate 1's tripwire (precision ≥ 0.40 vs 0.30
baseline) is a 33% relative lift — large enough to distinguish from stochastic
noise across the 5-genre corpus.

### Verification against the data (checked, not assumed)

- **FR-584 KILL confirmed.** Status: "Enforced (2026-06-24) — Verdict
  REVISE/KILL prompt-only levers; all three reverted." The stop rule's named
  escalation was "a true two-node decode or a larger model." FR-585 implements
  the first option.
- **Current graph structure verified.** `assign_pre_eff.yaml` is a single
  LLM→validate→retry graph (lines 38–67), state keys `{glosses, agents}` in /
  `{pre_eff_raw, pre_eff, validation}` internal. Runner (`run.py:252–257`)
  passes only `{glosses, agents}` — no GT `initial_world` (leakage constraint
  holds).
- **`analyze_l5_confusion.py` exists** (122 lines, committed `2bc5ab69` per
  FR-584 C5). Measurement witness is standing infrastructure.
- **Precision baseline is stable.** 0.30 across FR-583 (no-vocab) and FR-584
  (all levers). Not a single-point reference.
- **GT scores movement departures (resolves AC#3's deferred conditional).** The
  ground-truth fixtures contain **9 `at … value: false` fluents** (~10% of all
  `at` predicates), so the movement-pair helper is in scope rather than a
  drop-candidate. Checked 2026-06-24; the conditional in AC#3 now governs only
  whether the helper nets a recall gain, not whether departures exist.

### Conditions (folded into spec)

**C1 — Gate 1 adapter must be dumb (folded into AC#1).** Node A outputs
natural-language phrases. The throwaway adapter mapping these to typed predicates
for evaluator scoring must be keyword/regex-based, NOT another LLM call. If the
adapter is smart (an LLM typing call), Gate 1 tests decomposition + typing
together and cannot distinguish whether precision gains come from better salience
selection or better typing. The `at`-FP count depends on Node A *not selecting*
non-salient facts — that signal passes through any adapter quality.

**C2 — Retry architecture specified before Node B (folded into Bucket 3 #12).**
The current graph retries the single `assign` node (max 3, loop-limit → END).
With Node A → Node B → validate, the retry target is ambiguous. Must be settled
before Node B is wired: retry B only (A cached) or restart from A. Determines
graph YAML structure and whether loop-limit-death is resolved or inherited.

**C3 — Gate 1 tripwire hardened + movement conditional resolved (post-judgement
verification pass, 2026-06-24).** Two tightenings from an independent re-check:
(a) AC#1 named `at`-FP as the adapter-robust signal but keyed the tripwire on the
precision *ratio*, which a dumb adapter can destabilise by starving the
true-positive numerator. The tripwire is now dual and keyed on the absolute
`at`-FP count first (56 → < 30 with recall holding), ratio ≥ 0.40 as
corroboration. (b) AC#3's deferred "does GT score departures?" was answered by
inspection — 9 `at = false` fluents exist in the GT fixtures — so the movement
helper is in scope, not a drop-candidate. Both fold tighter scope, not wider.

### Validated as correct (carried forward)

- **Spike-gated design.** Gate 1 → full pipeline only if passes → KILL if not.
  Correct and capital-efficient.
- **Stop rule.** "Do not iterate Node A wording more than once." Prevents
  fourth-iteration ritual. "Escalate to larger model for L5 only." FR-578
  anti-scaling lesson is validly spent once prompt-wording, prompt-architecture,
  AND call-decomposition have all failed.
- **Deterministic demotion guardrails.** Movement-pair only if GT scores
  departures; naming-snap only if it beats "do nothing" with zero false-merges.

## Implementation — Gate 1 outcome (2026-06-24)

**Verdict: Gate 1 FAILED (deconfounded). KILL per the stop rule — do not build
Node B/C; escalate L5 to a larger model.** The KILL was reached in two passes: a
first pass that was *confounded by prompt defects in the spike itself*, and a
second pass that *removed those defects and still failed on the primary signal*.
The two-pass record is kept because the deconfounding is the honest part.

### What was built (the spike, as judged)

- `prompts/assign_pre_eff_salience.yaml` — Node A salience gate. Per beat: the
  world facts the beat *requires* (must already hold) and the facts it *changes*,
  each as a `subject | relation | object` triple. No slice schema, no belief
  nesting, no YAML acrobatics.
- `examples/plot_modeller/spike_salience_gate.py` — throwaway measurement harness.
  Runs Node A per GT fixture → a **deliberately dumb keyword adapter**
  (`_type_triple`, no LLM, J:C1) types each triple → writes `results/l5/<genre>.yaml`
  → scores via the unchanged evaluator. Validator/retry bypassed on purpose to
  isolate Node A's selection.

### Pass 1 — confounded (open-vocabulary prompt)

| Metric | Baseline | Pass 1 |
|---|---|---|
| World recall | 0.60 | 0.27 |
| Precision | 0.30 | 0.14 |
| `at`-FP | 56 | 33 |
| `rel`-FP | ~15 | **88** |
| MISS total | 34 | 62 |

Per C3 I investigated before declaring KILL. Dumping the 88 `rel`-FPs revealed
they were **action verbs** ("traveling to", "pursuing", "announces", "threatens")
and **belief facts** ("aware of", "knows") — *not* an adapter artifact. **Root
cause traced to three defects in my own spike prompt, not in the decomposition
hypothesis:** (a) the vocabulary was never closed, so the model invented free-form
relations; (b) the DIRECTION example literally demonstrated an action verb as a
relation (`The Swarm | assimilates | ARIA`), teaching the flood; (c) the prompt
anchored "most beats have 0–2 facts" when the GT truth is *most beats change
nothing*. A KILL on a confounded prompt is not an honest falsification, so the
stop-rule's single permitted Node-A iteration was spent fixing the prompt.

### Pass 2 — deconfounded (closed-vocabulary prompt, the decisive run)

Closed the relation set to the five L5 predicates, deleted the action-verb
example, re-anchored on "most beats change nothing — empty lists are expected."

| Metric | Baseline | Pass 1 | **Pass 2** |
|---|---|---|---|
| World recall | 0.60 | 0.27 | **0.54** |
| Precision | 0.30 | 0.14 | **0.32** |
| `at`-FP | 56 | 33 | **86** |
| `rel`-FP | ~15 | 88 | **0** |
| MISS total | 34 | 62 | 39 |

The deconfounding worked where it could: `rel`-flood **88 → 0**, recall recovered
**0.27 → 0.54**, and talk/announce/decide beats now correctly emit **empty** lists
(salt-road F1–F3 went from 2–3 spurious triples each to `[]`, matching GT `None`).
That is genuine new discrimination the cleaner prompt unlocked.

**But the wound itself did not move: precision 0.32 ≈ 0.30 baseline** (within
noise). The over-emission did not disappear — once action-verbs and beliefs were
forbidden, it **funneled into `at`** (56 → 86 FPs, now 88% of all FPs). The model
now empties talk-beats correctly but tracks **every leg of every journey** as
`at`-pairs (salt-road F5–F10 emit a full caravan itinerary: Djenné → river road →
dry country → Timbuktu), while the GT scores only the *salient* relocations. It
cannot distinguish a salient arrival from a travel waypoint, so `at`-recall is
good and `at`-precision is bad **in the same gesture** — the exact FR-584
mechanism, now isolated to one predicate.

**Tripwire (dual):** PASS required `at`-FP < 30 with recall holding. Pass 2:
`at`-FP = 86 (worse than baseline), precision flat. **Hard fail.**

### Conclusion

Three prompt architectures now land at the same precision: FR-584 monolith (0.30),
Pass-1 open-vocab decode (0.14, confounded), Pass-2 closed-vocab decode (0.32). The
Gate-1 KILL of *this FR's specific split* (Node A salience-select → Node B type)
**stands** — peeling typing off selection does not move precision.

**But the conclusion must not over-reach (post-enforce reflection, 2026-06-24).**
All three architectures — including this FR's "decomposition" — share one
**unexamined fusion**: each asks the model, in a single operation, to *comprehend*
the narrative (abstract prose → implied persistent world-state) **and** *encode*
the result (closed-vocabulary typed predicate, correct slice/args/value, salient
delta). FR-585 split *typing* off *selection*; both are on the encoding side. The
comprehension↔representation seam was never cut. So the flat 0.30 is a ceiling for
**single-operation world-encoding**, not a proven ceiling for the task — concluding
"haiku model ceiling, escalate to a bigger model" repeats, one level up, the Pass-1
error of inferring a verdict from an architecture that shares an unexamined flaw.

The `at`-waypoint flood is specifically a **delta-salience** failure: "what does
this beat *change*" forces the model to hold prior state, current state, and
salience at once. The honest next lever is therefore **not** a bigger model first —
it is the untested seam:

1. **Snapshot, don't delta.** Ask the model only to *comprehend* — emit a plain
   world-state **snapshot** after each beat (its easiest mode, "describe the
   scene"), with no vocabulary or slices. Then let **code** diff consecutive
   snapshots into typed deltas and collapse intra-chapter `at`-runs to net
   displacement. Snapshots bundle one hard judgment; salient deltas bundle three.
2. **Then** type the diffed deltas (mechanical) and, only if the snapshot seam
   still underperforms, escalate to a larger model — now with the comprehension
   and encoding loads genuinely separated, so the scaling test is clean.

Node B/C and the deterministic helpers are **not** built — Gate 1 closed this FR's
split. The Pass-2 prompt and spike harness are retained as measurement artifacts
(FR-584 C5).

**Handoff for the follow-up FR:** the residual wound is narrow and legible —
*journey-waypoint over-tracking in `at`* (86 FPs, 88%), with talk-beat and `rel`
over-emission already solved by the Pass-2 prompt. The follow-up's **first** lever
is the snapshot-then-deterministic-diff seam above (comprehension/representation
split), using the Pass-2 prompt only as the encoding baseline; a larger model is
the *fallback*, not the first move (FR-578 anti-scaling still applies — the real
framing alternative is untested). No GT input; evaluator frozen. **Drafted as
`feature-requests/FR-587-plot-modeller-L5-snapshot-then-diff.md`.**
- **No GT input** (FR-583 leakage KILL stands). Verified: `run_assign_pre_eff`
  passes only `{glosses, agents}`.
- **Evaluator frozen.** Clean A/B baseline.
- **Effort 2–3 days (spike-gated).** 0.5 day Node A spike (may KILL early),
  1.5–2 days full pipeline if Gate 1 passes.
- **Out-of-scope exclusions** (no GT vocab, no evaluator changes, no belief
  investment, no larger model as first lever). All correct.

**Frozen scope:** Spike-gated two-node decode. Gate 1: Node A + dumb adapter,
precision vs 0.30 baseline (target ≥ 0.40); KILL if flat. Post-Gate-1: Node B
(structured output), deterministic helpers (only if measured beneficial), retry
architecture specified, controlled comparison, J:N2 verdict. Effort 0.5–3 days
depending on Gate 1.
