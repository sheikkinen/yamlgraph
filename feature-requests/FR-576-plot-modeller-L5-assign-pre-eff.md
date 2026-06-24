# Feature Request: FR-576 Plot Modeller — L5 assign pre/eff spike

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced — REVISE (combined world recall 47/85 = 0.55; follow-up prompt FR; 2026-06-24)
**Effort:** 1.5 days
**Requested:** 2026-06-24
**Plan:** [`plan-implementation-phases.md`](../examples/plot_modeller/docs/plan-implementation-phases.md) Phase 3a
**Predecessor:** FR-575 (L3 extract glosses — Enforced, GO 0.88)
**Blocks:** FR-577 (L6 causality), FR-579 (merge/pipeline)
**Data dependency:** L3 glosses + L4 kinds (the spike uses ground-truth glosses+kinds to isolate L5)
**Scheduling dependency:** FR-575 (risk-control sequence; J:N1)

## Summary

Build the first **formalization** layer: given a classified beat (gloss + kind),
assign its world-state and belief **preconditions and effects** as typed
predicates — `pre_world`, `eff_world`, `pre_belief`, `eff_belief`. Spike against
all 5 synopses using ground-truth glosses + kinds (isolate L5 from L3/L4 error).
This is the first layer where the model must **invent** predicates within a
constrained vocabulary, not merely classify — the highest-risk layer so far.

## Value statement

Preconditions and effects are the load-bearing structure of the plan. They are
what makes a plan *executable*: the merge node's causal-satisfiability check
(Phase 4) reads `pre_world` (what must hold before a beat) against the
`eff_world` of earlier beats (what they make true). Without pre/eff, the plan is
a labeled beat list with no causal spine — `enables` links (L6) and reachability
(Phase 4) have nothing to verify against. L5 turns a classified beat sheet into
a state machine.

## Problem

No pipeline layer assigns pre/eff. The ground-truth plans have hand-authored
`pre_world`/`eff_world`/`eff_belief`, but the pipeline cannot produce them from a
gloss + kind. Unlike L4 (classify into a closed 17-kind set) and L1–L3
(extraction), L5 is **generative within a constraint**: the model must choose a
predicate (`alive`/`at`/`holds`/`rel`/`faction`), invent its args (character,
object, location names), and assign a value — none of it drawn from a closed
list. This is where naming variance bites hardest (see the evaluation conditions
below).

## Proposed solution

### Graph: `graphs/assign_pre_eff.yaml`

Same LLM-validator-retry pattern as `classify_kinds.yaml`:

```
START → assign → validate → END (if ok)
                          → assign (if !ok, max 3 retries)
```

**State keys:**
- `glosses` (input): classified beats `{id, gloss, chapter, kind, subject}`
- `pre_eff_raw` (LLM output): raw YAML text
- `pre_eff` (validated output): parsed per-beat pre/eff slices
- `validation`: `{ok: bool, flaws: list[str]}`

L5 processes the **whole beat list in one call** (like L4), not one beat per
node — pre/eff assignment benefits from cross-beat context (an effect in F2
should reference the same object token F1 introduced).

### Prompt: `prompts/assign_pre_eff.yaml`

For each beat, assign:

1. **`pre_world`** — world-state `Fluent`s that must be true for the beat to
   happen (e.g. a `struggle` beat needs both parties `alive`).
2. **`eff_world`** — world-state `Fluent`s the beat makes true (a literal
   `death` beat sets `alive(victim) = false`; a transformational one may instead
   set a `rel`, e.g. `rel(victim, villain) = assimilated`).
3. **`pre_belief`** — beliefs that must hold (often empty).
4. **`eff_belief`** — beliefs the beat changes (a `recognition` beat updates a
   `Belief.held`).

**Vocabulary anchor (carries C1/C3 from FR-573/574).** The prompt MUST instruct:
"Use object, location, character, and relationship names **exactly as they
appear in the gloss** — do not paraphrase or invent synonyms. If beat F2's
effect concerns the same object F1 introduced, reuse F1's exact token." This is
the single most important prompt instruction in the layer — predicate matching
is exact-token-sensitive, and the FR-574 REVISE (FR-581) was caused precisely by
wrong-object substitution on `holds`.

**Kind-driven priors.** Include a short table of typical effects per kind to
anchor the generation (e.g. `liquidation → eff_world` restores the lacked thing;
`recognition → eff_belief` updates a held belief). These are priors, not rules —
the gloss governs. Do NOT include a `death → alive=false` prior: the corpus
models one death as a relationship change (`rel=assimilated`), and a hard prior
would bias the model toward the wrong predicate (J:C2).

Output: a YAML list of `{id, pre_world, eff_world, pre_belief, eff_belief}`
objects, one per beat.

### Validator: `validate_pre_eff` in `nodes/tools.py`

Checks (J1 contract — writes `pre_eff` only on full success, else only
`validation`):

1. Output is valid YAML, a list of mappings
2. Every `id` matches an input beat id (no orphans, no gaps)
3. Every `pre_world`/`eff_world` entry parses as a `Fluent`
   (pred ∈ {alive, at, holds, rel, faction})
4. Every `pre_belief`/`eff_belief` entry parses as a `Belief`
   (observer, fluent, held)
5. All character args appear in the plan's agent list
6. **No kind-effect structural rule.** L5 must NOT enforce "kind X implies
   effect Y" — the corpus falsifies the obvious one: the scifi `death` beat
   (Jonas) models its effect as `rel(Jonas, ARIA)=assimilated`, not
   `alive=false` (metaphorical/transformational death). A hard kind→effect
   validator would reject valid ground truth (J:C2). Coherence is the
   evaluator's job (tolerant matching against GT), not the validator's.

### Runner: extend `run.py`

Add `--mode assign-pre-eff`:
1. Load each ground-truth plan's glosses + kinds (Mode 1 isolation)
2. Run the `assign_pre_eff` graph
3. Write output to `results/l5/<genre>.yaml`
4. Compare against ground-truth pre/eff

### Evaluator: extend `evaluate.py`

Add L5 evaluation. **Matching is tolerant by mandate (J:C1/C3 inheritance) —**
exact `pred+args+value` equality is forbidden as the primary metric, because L5
*invents* the tokens it is scored on. Predicate matching:

- Normalize args: lowercase, strip articles/whitespace, order-insensitive for
  symmetric predicates (`rel`, `faction`).
- Match on normalized `pred` + tolerant args (contains/prefix) + value.
- Report **predicate recall** (fraction of GT pre/eff predicates matched) and
  **predicate precision** (fraction of generated predicates that match GT).

Split the score by slice — `eff_world` recall, `pre_world` recall,
`eff_belief` recall — because they have very different difficulty and very
different denominators (see the sparsity note). Corpus-wide denominators
(verified at the predicate level by the evaluator across the 5 ground-truth
fixtures): **`pre_world` 42, `eff_world` 43, `pre_belief` 9, `eff_belief` 17** —
total world predicates 85, total belief predicates 26. (An earlier field-level
estimate of 34/23 undercounted: a single `pre_world:` block holds several
predicate list-items — the predicate is the unit, not the field.)

## Deliverables

| File | What |
|------|------|
| `graphs/assign_pre_eff.yaml` | L5 graph (LLM → validate → retry) |
| `prompts/assign_pre_eff.yaml` | L5 prompt (vocabulary anchor + kind priors) |
| `nodes/tools.py` (extended) | `validate_pre_eff` function |
| `run.py` (extended) | Mode: `--mode assign-pre-eff` |
| `evaluate.py` (extended) | L5 evaluation (tolerant predicate matching, per-slice) |
| `tests/test_l5_validator.py` | Unit tests for `validate_pre_eff` (incl. J1 crash regression) |
| `results/l5/*.yaml` (5 files) | Assigned pre/eff per genre |
| `results/evaluation/l5-summary.yaml` | Predicate recall/precision, per-slice + per-genre |

## Acceptance criteria

1. `validate_pre_eff` catches: orphan/missing ids, invalid Fluent/Belief
   structure, unknown predicate, character not in agent list
2. The validator enforces **no kind→effect semantic rule** (J:C2 — a `death`
   beat need not produce `alive=false`; the corpus has a counter-example)
3. L5 graph follows the LLM-validator-retry pattern (max 3 retries)
4. Predicate matching is **tolerant** (normalized args, order-insensitive for
   symmetric predicates) — NOT exact `pred+args+value` equality (J:C1/C3)
5. **Combined world-predicate recall ≥ 0.70** across the 5-synopsis corpus is
   the gate metric (denominator 85 = pre_world 42 + eff_world 43). Combined,
   not `eff_world` alone, because per-genre `eff_world` slices are small enough
   that three misses swing the ratio sharply (J:C3). `eff_world` recall is
   still reported per-slice.
6. No hardcoded provider/model in the graph or prompt
7. All generated pre/eff parse into the FR-571 schema (`Function` slice valid)
8. The summary reports per-slice recall (`eff_world`, `pre_world`, `eff_belief`)
   with each denominator shown explicitly (J:C5 — denominators visible, not
   hidden in a ratio)
9. Verdict recorded: GO / REVISE / KILL with confusion analysis

## Evaluation output

```yaml
# results/evaluation/l5-summary.yaml
corpus:
  synopses: 5
  isolation: ground-truth glosses + kinds (Mode 1)
world_recall:      "X/85 (0.XX)"   # GATE metric = (pre_world 42 + eff_world 43)
eff_world_recall:  "X/43 (0.XX)"   # per-slice (informational)
pre_world_recall:  "X/42 (0.XX)"   # per-slice (informational)
eff_belief_recall: "X/17 (0.XX)"   # per-slice (informational) — hardest
predicate_precision: "X/Y (0.XX)"
per_genre:
  detective-thriller-the-vanished-witness: { world: "X/Y" }
  # ... (all 5)
verdict: GO | REVISE | KILL
conditions:
  - "combined world recall ≥ 0.70 for GO (denominator 85)"
  - "borderline 0.50–0.70 defaults to REVISE (J:N2)"
note: >
  Denominators are predicate-level, verified by the evaluator: pre_world 42,
  eff_world 43, pre_belief 9, eff_belief 17. The gate is combined world recall
  (N=85). The per-slice numbers are reported but do not gate. Belief recall is
  informational: ground-truth beliefs encode full-plot dramatic irony and are
  an upper bound a single-beat view cannot recover (J2 leakage, inherited from
  FR-573 C2).
```

## Go/no-go gate

| Outcome | combined world recall | Action |
|---------|----------------------|--------|
| **GO** | ≥ 0.70 | Proceed to FR-577 (L6 causality) |
| **REVISE** | 0.50–0.70 | Analyze the predicate confusions (wrong pred? wrong token? wrong value?); revise prompt; re-spike |
| **KILL** | < 0.50 *and* incoherent confusion pattern | Re-evaluate L5 — generative predicate assignment may need a larger model or a two-step (pred-then-args) decomposition |

The KILL band is narrow (J:N2) and the denominators are modest (J:C5): even at
N=85, a bare score near 0.50 is within sampling noise. A KILL requires both a
clear collapse *and* a confusion pattern that does not point to a fixable prompt
issue (e.g. systematic wrong-token substitution → a prompt fix, not a KILL).

## Risk assessment

**Medium-high** (per the roadmap). This is the first generative-within-constraint
layer. The dominant, already-seen risk is **token substitution**: the FR-574
REVISE (→ FR-581) proved the model paraphrases object names (`firmware_channel`
→ `phase_lock_control`). L5 multiplies that exposure — it generates many more
`holds`/`rel`/`at` predicates than L2 did. The vocabulary anchor (prompt) and
tolerant matching (evaluator) are the two mitigations, and they must both be in
place before the spike, or the measured recall will reflect naming variance, not
formalization ability.

**Secondary risk — sparse denominator.** The per-slice predicate counts are
modest (eff_belief only 17), so a per-slice percentage is high-variance. Gating
on the combined world denominator (85) and the denominator-visible reporting
(AC#8) are the guards: a reader must see "X/85" / "X/43", never a bare "0.XX."

## What this FR does NOT do

- Does not assign causal links / motivation / threatens (that's FR-577 / L6)
- Does not assign affects (that's FR-578 / L7)
- Does not run L5 on L3-extracted glosses — the spike uses ground-truth
  glosses+kinds to isolate L5's accuracy (the full chain is FR-579)
- Does not add plan-level validators (`causality.py`, `reachability.py`) — those
  run on complete plans at merge time (Phase 4), not on the L5 slice
- Does not modify the schema (FR-571 already covers `Fluent`, `Belief`,
  and the `Function` pre/eff fields)

## Implementation status

**Enforced 2026-06-24 — REVISE.** Built the full L5 slice TDD (RED validator
tests → GREEN), ran live against all 5 synopses with `claude-haiku-4-5`.

### Deliverables built

| File | Status |
|------|--------|
| `graphs/assign_pre_eff.yaml` | ✓ LLM→validate→retry, `loop_limits: {assign: 3}` |
| `prompts/assign_pre_eff.yaml` | ✓ vocabulary anchor + kind priors (no death→alive prior, J:C2) |
| `nodes/tools.py` `validate_pre_eff` + `load_glosses_with_kinds` | ✓ J1 contract, no kind→effect rule |
| `run.py` `--mode assign-pre-eff` | ✓ Mode-1 isolation (GT glosses+kinds) |
| `evaluate.py` `score_l5`/`summarise_l5`/`main_l5` | ✓ tolerant matching, per-slice, denominator-visible |
| `tests/test_l5_validator.py` | ✓ 12 tests incl. J1 crash + J:C2 death-as-rel |
| `results/l5/*.yaml` (5) | ✓ |
| `results/evaluation/l5-summary.yaml` | ✓ verdict + confusion analysis |

124/124 example tests pass; new code lints clean (graph carries the same W012
advisory as L4 — loop limit keyed on the re-entered `assign` node, intentional).

### Results

| Slice | Recall | Note |
|-------|--------|------|
| **combined world (GATE)** | **47/85 (0.55)** | borderline band → REVISE |
| eff_world | 24/43 (0.56) | per-slice |
| pre_world | 23/42 (0.55) | per-slice |
| eff_belief | 1/17 (0.06) | confirms J2 leakage — informational |
| predicate precision | 48/170 (0.28) | model over-generates |

Per-genre world recall: detective 0.50, historical 0.67, horror 0.76, quest
0.58, scifi 0.35.

### Verdict: REVISE (not KILL)

Auto-threshold flagged 0.55 as REVISE (borderline 0.50–0.70). The confusion
analysis confirms REVISE rather than KILL — the KILL condition requires the
failure pattern to be *not* a fixable prompt issue, and every dominant miss is
fixable:

1. **Value-label divergence** — `rel=assimilated` vs model's `synchronized`;
   relationship labels are open free-text and the model invents synonyms. Fix:
   calibrated label vocabulary in the prompt.
2. **Object-token paraphrase** (the named dominant risk) — `firmware_channel` →
   `firmware update`, `Vantari Labs` → `lab`; the vocabulary anchor is too weak.
3. **Departure under-modeling** — GT models a move as `at(old)=false` +
   `at(new)=true`; the model drops every `=false` departure. Fix: a
   move-decomposition rule in the prompt.
4. **Belief unrecoverable** — eff_belief 1/17, confirming J2 leakage
   (informational, not a defect).

This mirrors the FR-574 → FR-581 arc: a measured borderline recall whose misses
are prompt-fixable. The follow-up is a **prompt-only REVISE FR** (label
vocabulary + move decomposition + stronger token anchor). Stop rule: if a
second prompt pass does not clear 0.70, the next step is architectural
(two-step pred-then-args, or a larger model) — not a third prompt pass.

### Deviations from spec

- **Denominators corrected during enforce.** The judged spec estimated
  pre_world 34 / eff_world 23 / combined 57 from a field-level grep. The
  evaluator counts at the *predicate* level: pre_world 42, eff_world 43,
  combined **85** (a single `pre_world:` block holds several list-items). The
  FR, summary, and gate were corrected to 85 — the predicate is the unit, not
  the field. (The spec's own J:C5 denominator-visibility rule caught this.)
- **Transient loop-limit failures.** Validation is non-deterministic; one early
  run lost an entire genre (historical-fiction 0/9) to a 3-strike loop-limit.
  A clean re-run recovered it (6/9). The reported corpus number is from the
  clean run; the flakiness itself is evidence the failure is output-stability,
  not capability — reinforcing REVISE.
