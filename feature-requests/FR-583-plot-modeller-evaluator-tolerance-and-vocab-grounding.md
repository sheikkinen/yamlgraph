# Feature Request: FR-583 Plot Modeller — evaluator tolerance + L5 vocabulary grounding

**Priority:** HIGH
**Type:** Feature (architectural fix)
**Status:** Judged — Authority GRANTED with conditions (2026-06-24)
**Effort:** 1 day
**Requested:** 2026-06-24
**Judged:** 2026-06-24
**Predecessor:** FR-581 (L2 revise, stop rule hit), FR-582 (L5 revise, stop rule hit)
**Blocks:** FR-579 (merge/pipeline)

## Summary

Both L2 and L5 hit their stop rules after prompt-only revisions — L2 at recall
0.72 (gate 0.80), L5 at combined world recall 0.55 (gate 0.70). The remaining
misses share a structural root: the evaluator's string-matching rejects
legitimate multi-word partial matches (Part 1), and the L5 model paraphrases
world-state tokens because the prompt lacks an explicit vocabulary (Part 2).
This FR is the architectural escalation both stop rules point to.

## Value statement

Without this fix the pipeline stalls at two layers simultaneously: L2 misses
~28% of goals and L5 misses ~45% of world-state changes, both propagating as
false negatives into L6 causality and Phase-4 reachability. Part 1 (evaluator
tolerance) unblocks both layers with zero model changes; Part 2 (vocabulary
grounding) closes the dominant L5 failure mode at the prompt-information-
architecture level rather than the prompt-wording level.

## Problem

### Shared evaluator ceiling (L2 + L5)

The current `_norm_value` + contains/prefix matching works well for single-word
args but is too strict for multi-word arguments:
- `Seoul lab` vs `Seoul` — partial overlap, rejected (L5 location)
- `River road` vs `flooded river road` — superset, rejected (L5 location)
- `charter letter` vs `charter_letter` — fixed by FR-581 underscore norm, but
  the pattern repeats with new multi-word tokens

Single-word synonym pairs (`together` vs `lovers`, `synchronized` vs
`assimilated`) are genuine semantic gaps that no string metric bridges — these
are correctly rejected and not in scope.

### L5 token paraphrase (L5 only)

The L5 model consistently paraphrases tokens from the synopsis instead of
reusing `initial_world` atoms:
- `throne room` for `Capital` (location)
- `flooded gorge` for `Temple` (location)
- `firmware update` for `firmware_channel` (object)

FR-582's prompt anchoring ("copy verbatim") reduced but did not eliminate this.
The model has no access to the actual token vocabulary — it must guess which
tokens the ground truth uses.

## Proposed solution

### Part 1: args-level Jaccard tolerance in evaluator (L2 + L5)

Add a `_args_jaccard_match(predicted, expected, threshold=0.5)` helper to the
evaluator. The matching logic becomes:

1. **Single-word args:** exact match after existing normalization (lowercase,
   underscore→space, article stripping). No change from current behavior.
2. **Multi-word args:** tokenize both sides (split on whitespace), compute
   Jaccard similarity (`|intersection| / |union|`), accept if ≥ 0.5.

This bridges:
- `Seoul lab` ↔ `Seoul` — Jaccard 1/2 = 0.50, passes
- `River road` ↔ `flooded river road` — Jaccard 2/3 = 0.67, passes
- `firmware update` ↔ `firmware_channel` — after underscore norm: `firmware
  update` vs `firmware channel` — Jaccard 1/3 = 0.33, correctly rejected
  (genuinely different concept)

The helper slots into the existing per-arg comparison: when the current
exact/contains check fails on an arg, try Jaccard before rejecting. The actual
seams are `_fluent_matches` (L1/L5 world) and `_goal_matches` (L2) — both run
the same `pa != ta and pa not in ta and ta not in pa` per-arg loop over
`_norm_args` output. Extract that loop into one shared comparator, add the
Jaccard fallback there, and call it from both (one change, two layers, no
drift). There is **no** `_match_predicate` function (J:C1).

**Files changed:** `evaluate.py` — new `_args_jaccard_match` function folded
into the shared per-arg comparator called by `_fluent_matches` and
`_goal_matches`.

### Part 2: vocabulary grounding in L5 prompt (L5 only)

Inject a VOCABULARY section into `prompts/assign_pre_eff.yaml` that lists
every unique token from the synopsis's `initial_world` and `initial_belief`
blocks. The section is assembled at prompt-render time from the input data
(same mechanism the prompt already uses for `{initial_world}`).

Format in the prompt:

```
## VOCABULARY — use these tokens exactly

Locations: Capital, Temple, Outpost, Seoul
Objects: firmware_channel, charter_letter, phase_lock_control
Agents: ARIA, Mara, Jonas, Hagen
Relationships: allied, hostile, assimilated, entrained

Use ONLY these tokens for existing entities. For genuinely new entities
introduced by the beat (not present in initial_world), you may coin a new
token — but prefer the synopsis's own word.
```

The token list is extracted mechanically from `initial_world` + `initial_belief`
by collecting unique values from predicate arguments and values. This is a
prompt-information-architecture change: it changes what the model *sees*, not
how it is *told to behave*.

**Files changed:** `prompts/assign_pre_eff.yaml` — add VOCABULARY block with
template variables; `run.py` (the caller) — extract the unique token set from
each synopsis's `initial_world` + `initial_belief` predicate args/values and
pass it as a template variable (J:C4).

## Acceptance criteria

1. **RED tests for Jaccard tolerance.** Unit tests in `test_evaluator.py` that
   assert multi-word args are matched by Jaccard ≥ 0.5 and single-word args
   require exact match, covering **both** the `_fluent_matches` (L5) and
   `_goal_matches` (L2) seams (J:C1). Tests fail before implementation.
2. **`_args_jaccard_match` implemented** in the shared per-arg comparator called
   by `_fluent_matches` and `_goal_matches`. GREEN on the new unit tests.
3. **L2 re-evaluated with new tolerance.** No re-spike needed — same L2 results
   from FR-581, re-scored with the updated evaluator. Report new recall **and
   precision** (J:C3 false-positive tripwire); expect improvement from
   multi-word arg matches. Target: recall ≥ 0.80.
4. **L5 re-spiked with vocabulary grounding.** New prompt with VOCABULARY
   section, re-run across all 5 synopses. `results/l5/*.yaml` regenerated.
5. **L5 re-evaluated with new tolerance.** Report combined world recall **and
   precision** with both fixes active. Target: measurable improvement over 0.55
   (not a hard gate — this is the first architectural pass).
6. **Per-genre breakdown reported** for both L2 and L5, with confusion analysis
   justifying the verdict per J:N2. The confusion analysis inspects the
   newly-admitted Jaccard matches to confirm they are legitimate partials, not
   manufactured positives (J:C3).
7. **Existing evaluator and validator tests stay green.** The Jaccard helper is
   additive; no existing match behavior changes for single-word args.
8. **Two commits** (J:C2): commit 1 = Jaccard helper + RED/GREEN tests + L2/L5
   re-score; commit 2 = VOCABULARY prompt block + `run.py` token extraction +
   L5 re-spike.

## Gate

- **L2:** recall ≥ 0.80 → GO. Below 0.80 with only genuine semantic misses
  (not multi-word partial matches) → still GO per J:N2 confusion analysis.
- **L5:** combined world recall improvement over 0.55. No hard numeric gate —
  this is the first architectural pass. Verdict by confusion analysis: if the
  dominant failure mode shifts from token paraphrase to a new category, the
  fix worked and the next FR targets the new mode.

**L5 stop rule (J:C5).** This is one architectural pass, not an open loop. If
L5 stays flat at ~0.55 with token-paraphrase STILL the dominant failure mode
despite vocabulary injection, that is a KILL for the vocab-grounding lever — the
next step is two-step pred-then-args generation or a larger model, NOT a second
vocabulary iteration.

## Out of scope

- **Semantic embedding similarity** for value matching. Adds a model dependency
  to the evaluator; the Jaccard approach is stateless and deterministic.
- **LLM-as-judge evaluation.** Same concern — non-deterministic, expensive,
  and the current evaluator's failure modes are well-characterized.
- **Belief recall** (L5 `eff_belief`). Remains informational per FR-576 J:C3.
- **Third prompt-only pass** for either layer. Both stop rules expired; this
  FR is the architectural escalation.

## Judgement (2026-06-24)

**Verdict: Authority GRANTED with conditions — split into two landings.**
FR-583 is the architectural escalation both stop rules (FR-581 L2, FR-582 L5)
correctly point to, and the two parts attack the right seams: scoring tolerance
for multi-word args (Part 1, L2+L5) and prompt information-architecture for
token vocabulary (Part 2, L5). But the FR names an integration point that does
not exist, bundles two separable concerns, and re-scores an already-verdicted
layer — each needs a binding condition before scope freezes. Six conditions
folded.

### Verification against the data (checked, not assumed)

- **`_match_predicate` does not exist.** The evaluator's actual arg-comparison
  seams are `_fluent_matches` (L1/L5 world, ~line 243) and `_goal_matches`
  (L2, ~line 510), both consuming `_norm_args` and a per-arg contains/prefix
  loop. The Jaccard helper must slot into BOTH, or into a shared per-arg
  comparator the two call. Fold C1.
- **The Jaccard worked examples check out** against `_norm_args` (which already
  lowercases, strips articles, maps `_`→space): `firmware update` vs
  `firmware_channel`→`firmware channel` = 1/3 = 0.33, correctly rejected;
  `Seoul lab` vs `Seoul` = 1/2 = 0.50, accepted; `River road` vs
  `flooded river road` = 2/3, accepted. The token-paraphrase L5 misses
  (`throne room`/`Capital`, `flooded gorge`/`Temple`) share zero tokens → 0,
  still rejected. The loosening admits only literal-subset multi-word overlaps,
  not "fuzzy matching."
- **Part 2's token source is real.** `initial_world` + `initial_belief` are
  present per genre and already injected as `{initial_world}` in the prompt, so
  mechanical token extraction has a concrete source.

### C1 — pin the real integration seams (not `_match_predicate`)

Rewrite Part 1 to target `_fluent_matches` and `_goal_matches` explicitly.
**Preferred:** extract the per-arg comparison (currently duplicated as the
`pa != ta and pa not in ta and ta not in pa` loop in both functions) into one
helper, add the Jaccard fallback there, and call it from both — one change, two
layers, no drift. AC#2 must name both functions (or the shared helper) as
covered by the RED tests.

### C2 — land Part 1 and Part 2 as separate commits

Part 1 (evaluator + unit tests, no model call) and Part 2 (prompt + re-spike,
model calls) are independent concerns with different blast radii. Per
one-concern-per-commit, they land separately even under this single FR:
commit 1 = Jaccard helper + RED/GREEN tests + L2/L5 re-score; commit 2 =
VOCABULARY prompt block + run.py token extraction + L5 re-spike. This keeps the
L2 re-score auditable in isolation from the L5 generation change.

### C3 — Part 1 re-scores an already-verdicted layer; precision is the tripwire

Loosening multi-word matching retroactively changes L2's score (FR-581) and
L5's (FR-582). The plausible-wrong-answer hazard applies directly: `Seoul lab`
↔ `Seoul` now passes, and a lab-in-Seoul may be a genuine granularity
distinction the GT intends. **Binding:** every re-score under the Jaccard
matcher MUST report precision alongside recall, and the confusion analysis MUST
inspect the newly-admitted matches to confirm they are legitimate partials, not
manufactured positives. If precision drops materially, 0.5 is too loose and
must rise.

### C4 — name run.py as a changed file for Part 2

The FR lists only `prompts/assign_pre_eff.yaml`, but the VOCABULARY token set is
extracted from input data by the caller and passed as a template variable — that
logic lives in `run.py` (or the graph node), not the prompt. The deliverables
MUST name the caller change and the extraction rule (unique values from
`initial_world`+`initial_belief` predicate args/values), or Part 2 is
under-specified.

### C5 — state the stop rule for THIS architectural pass (L5)

FR-582's stop rule ("one revise, then escalate to architectural") brought us
here; FR-583 must declare its own exit. If L5 stays flat at 0.55 with
token-paraphrase STILL the dominant mode despite vocabulary injection, that is a
KILL for the vocab-grounding lever → next step is two-step pred-then-args
generation or a larger model, NOT a second vocabulary iteration. If the dominant
failure mode shifts (the FR's stated success signal), the fix worked and the
next FR targets the new mode. Make this explicit so a flat re-spike does not
invite an unbounded third architectural guess.

### C6 — the L5 soft gate is correct; the L2 gate stays hard

No hard numeric gate for L5 (first architectural pass, verdict by confusion
analysis) is the right call and consistent with J:N2. L2 keeps its hard ≥ 0.80
gate, with the J:N2 escape (genuine semantic misses — not multi-word partials —
still GO). Ratified.

### Carried forward unchanged (validated as correct)

- Out-of-scope exclusions (embedding similarity, LLM-as-judge, belief recall,
  third prompt-only pass) are all correct — they preserve the evaluator's
  deterministic, well-characterized failure modes.
- RED-first for the Jaccard helper (AC#1), additive helper leaving single-word
  matching exact (AC#7), per-genre breakdown with confusion analysis (AC#6) —
  all sound.

**Frozen scope:** Part 1 (Jaccard helper at the real
`_fluent_matches`/`_goal_matches` seams, RED-first, precision reported on
re-score) and Part 2 (VOCABULARY prompt block + run.py token extraction, L5
re-spike), landed as two commits, with the explicit L5 stop rule (C5). No
embedding/LLM-judge, no belief gate, no third prompt-only pass.
