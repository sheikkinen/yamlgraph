# Feature Request: FR-585 Plot Modeller — L5 salience-gate decode + deterministic bookkeeping

**Priority:** HIGH
**Type:** Feature (architecture revision)
**Status:** Proposed
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
  fire, and never exhaust to empty.

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
      spike, type its flat output with a throwaway adapter so the existing
      evaluator can score it. Re-spike on haiku (verify `Creating LLM` log line),
      regenerate `results/l5`, report precision + `at`-FP via
      `analyze_l5_confusion.py`. **Tripwire:** if precision does not exceed the
      0.30 baseline by a clear margin (target ≥ 0.40) with no new catastrophic
      0-beat runs, KILL — do not build B/C; escalate to a larger model for L5 only.
- [ ] Node B added; final typed output validates through the unchanged
      `validate_pre_eff`; structured output used so YAML hand-writing (#11) is gone.
- [ ] Deterministic movement-pair helper added **only if** GT scores departures;
      otherwise the rule is dropped and that decision recorded.
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
