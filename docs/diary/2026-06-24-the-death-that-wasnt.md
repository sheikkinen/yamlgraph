# 2026-06-24 — The death that wasn't, and the denominator that grew

## Context

Judged then enforced FR-576: the L5 spike asking whether a Haiku-class model can
assign world-state and belief preconditions/effects (`pre_world`, `eff_world`,
`pre_belief`, `eff_belief`) to classified beats. This is the first
**generative-within-constraint** layer — the model invents predicates, it does
not merely classify into a closed set.

It produced **47/85 (0.55)** — a borderline REVISE, exactly the "hardest layer"
the roadmap predicted.

But the number is not the lesson. The lesson is what I caught between writing the
spec and trusting it.

## The traps I walked into

### 1. I wrote a validator rule the corpus had already falsified (plausible_wrong_answer)

My draft baked a "coherence" check into the validator and the acceptance
criteria: *a `death` beat must produce `alive=false`*. It reads like obvious
domain sense. It passed my own first read. Then — judging my own draft as a
junior PR — I opened the two `death` beats in the ground truth:

- Horror (Fen): `eff_world: alive(Fen)=false` ✓ literal.
- Scifi (Jonas): `eff_world: rel(Jonas, ARIA)=assimilated` — **no `alive=false`**.
  A metaphorical, transformational death. "Jonas is gone," but his body lives.

My rule would have **rejected valid ground truth**. The validator would have
condemned the corpus it was built to measure against.

Heuristic (already in Scripture, paid for again): *a structural rule that reads
coherent is still a hypothesis until the boundary data confirms it.* The cure is
mechanical — `test_before_reading`: I made `test_death_as_relationship_change_is_valid`
a first-class test, so the absence of the rule is now guarded, not merely
remembered.

### 2. My denominator was a grep artifact (gate_checks_shape_not_substance, inverted)

The judged spec stated the gate denominator: pre_world 34, eff_world 23,
combined 57. I had counted with `grep -c 'pre_world:'` — *field headers*. But a
single `pre_world:` block holds several predicate list-items. The evaluator,
counting at the predicate level, found pre_world 42, eff_world 43, combined
**85**. My gate was off by nearly 50%.

The irony is exact: the spec's own J:C5 rule — *"denominators visible, never a
bare ratio"* — is what caught it. I had written the guard that exposed my own
error. The unit matters: **the predicate is the unit of measurement, not the
YAML field that contains predicates.** A field-level proxy undercounts an
incident-dense boundary, the same shape as `inventory_by_visibility`: I measured
what was easy to grep, not what the evaluator actually scores.

### 3. The threshold said KILL; the analysis said REVISE (unchallenged_premise)

The first run auto-flagged **KILL (0.46)** — but one genre had scored 0/9 because
validation hit the loop limit three times and wrote `null`. A transient. The
auto-verdict trusted the number; the number trusted a flaky run. A clean re-run
gave 0.55 → REVISE, and the confusion analysis confirmed it: every dominant miss
(value-label synonyms, object-token paraphrase, dropped departure effects) is a
**fixable prompt issue**, which the spec's own KILL rule explicitly excludes.

This is why `J:N2` ("thresholds trigger, analysis decides") is load-bearing. A
gate that auto-emits a verdict from a single noisy number is
`gate_checks_shape_not_substance` wearing a lab coat. The substance — *why* the
predicates miss — is what separates "revise the prompt" from "abandon the layer."

## The pattern across L2 and L5

FR-574 (L2 goals) revised down to a prompt FR (FR-581) because the model
paraphrased object tokens. FR-576 (L5 pre/eff) lands in the same place for the
same reason, one layer deeper. **Token substitution is not a per-layer bug; it
is the standing tax of letting an LLM invent identifiers it will later be scored
on by equality.** Every generative layer will pay it until the vocabulary is
either closed (a label set) or the matcher is made truly semantic. The tolerant
matcher (contains/prefix) is a down payment, not a solution.

## Heuristic to graduate (candidate)

*When a spike's evaluator counts at a finer grain than the spec's denominator
estimate, the evaluator wins and the spec is wrong — recompute the gate before
trusting the verdict. Field-level proxies systematically undercount
predicate-level truth.* This is the third denominator-reconciliation incident in
the plot_modeller arc (FR-572 self-derived denominators, FR-581 per-genre
reconciliation, FR-576 field-vs-predicate). If it recurs once more, it graduates
to a Scripture cure: `count_at_the_scoring_grain`.

## Seed

Three layers (L2, L5) now fail the same way: the LLM invents an identifier, then
equality punishes the variance. What if the pipeline never asked the model to
invent identifiers at all — what if L1 emitted a *closed token table* (every
object, location, relationship-label the story will use), and every downstream
layer could only *select* from it, never coin? Would constraining generation to
selection convert the standing token-substitution tax into a closed-set
classification problem the model already does at 0.80+ — and is the cost a
brittle L1 that must enumerate exhaustively up front?
