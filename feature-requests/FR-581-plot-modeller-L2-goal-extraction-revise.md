# Feature Request: FR-581 Plot Modeller — L2 goal extraction REVISE

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — Authority GRANTED (C1–C3 folded; 2026-06-24)
**Effort:** 0.5 day
**Requested:** 2026-06-24
**Predecessor:** FR-574 (L2 extract goals spike — verdict REVISE, 0.72 recall)
**Blocks:** FR-579 (merge/pipeline)
**Data dependency:** None new (same graph, prompt, evaluator)
**Scheduling dependency:** FR-574 (inherits its infrastructure)

## Summary

Revise the L2 goal extraction prompt and evaluation to raise goal recall from
0.72 to ≥ 0.80 (the GO gate). FR-574 measured two distinct failure modes —
wrong-object substitution on `holds` and blindness to `rel` / secondary-agent
`alive` goals — both traceable to prompt gaps, not architecture. No graph,
validator, or evaluator changes needed; this is a prompt-only revision with a
re-spike.

## Value statement

Goal extraction scopes the reachability check (Phase 4) and causality analysis
(L6). At 0.72 recall the pipeline misses ~1 goal per genre, which propagates
as a false-negative reachability gap downstream. Closing the two identified
error clusters brings recall above the GO gate without architecture changes.

## Problem

FR-574 spike measured goal recall 13/18 (0.72), precision 13/25 (0.52).
Verdict: REVISE. The error pattern is coherent and fixable:

### Per-genre miss reconciliation (C1)

| Genre | Recall | Missed GT goal | Failure mode |
|-------|--------|---------------|--------------|
| detective | 3/4 | `alive(Hagen, true)` — predicted `holds(Hagen, office, false)` instead | wrong-predicate substitution |
| historical | 2/3 | `holds(Naima, charter_letter, true)` — predicted `holds(Naima, charter letter, true)` | underscore/space mismatch |
| horror | 3/4 | `alive(Fen, true)` — not predicted at all | secondary-agent blindness |
| quest | 3/3 | — | — |
| scifi | 2/4 | `holds(ARIA, firmware_channel, false)` — predicted `holds(ARIA, phase_lock_control, false)`; `rel(Mara, Jonas, lovers)` — not predicted | wrong-object + rel blindness |

Total: 5 misses across 3 failure modes.

### Failure mode 1: wrong-object/predicate substitution (2 misses)

The model paraphrases object names or swaps predicates entirely:
- **scifi**: `firmware_channel` → `phase_lock_control` (wrong object)
- **detective**: `alive(Hagen)` → `holds(Hagen, office, false)` (wrong predicate)

**Root cause:** The prompt gives no instruction to use names **as they appear
in the synopsis text**. The model invents plausible but non-matching tokens.

### Failure mode 2: `rel` and secondary-agent blindness (2 misses)

- **scifi**: `rel(Mara, Jonas, lovers)` — no `rel` goal extracted at all
- **horror**: `alive(Fen)` — secondary protagonist survival dropped

**Root cause:** The prompt's example set shows only `alive`/`holds`/`at` goals.
The guidance says "survival + the main quest objective" which biases toward the
protagonist's survival and one `holds`/`at` objective, crowding out `rel` goals
and secondary-character survival. The "2–5 goals" ceiling compounds this: when
the model has budget for 3–4 goals, it picks the most salient ones and drops
`rel` and secondary `alive`.

### Failure mode 3: underscore/space normalization (1 miss)

- **historical**: GT `charter_letter` vs predicted `charter letter` (space).
  The evaluator's `_norm_args` does not equate underscores with spaces.

**Root cause:** dual — the model outputs `charter letter` (natural English)
where the GT uses `charter_letter` (identifier style), AND the evaluator lacks
underscore normalization. Fix both: prompt revision #1 helps anchor to
synopsis text, and a one-line evaluator tolerance fix normalizes underscores to
spaces in `_norm_args`.

### Precision problem: over-generation (12 spurious goals)

The model adds 1–3 extra goals per genre not in ground truth — typically
negative-`holds` (villain loses power) and speculative `at` goals. The guidance
for `value: false` actively encourages this pattern ("villain loses power"
example).

## Proposed solution

### Prompt revisions (`prompts/extract_goals.yaml`)

1. **Anchor object names to the synopsis text.** Add explicit instruction:
   "Use object, location, and relationship names **exactly as they appear in the
   synopsis** — do not paraphrase or invent synonyms."

2. **Add `rel` goal to the example set.** The current example shows only
   `alive`/`holds`/`at`. Add a `rel` example:
   ```yaml
   - pred: rel
     args: [Hero, Ally]
     value: friends
   ```

3. **Broaden survival guidance.** Change "Include survival goals for
   protagonists whose survival is at stake" → "Include survival goals (`alive`)
   for **every character whose life is explicitly threatened or at risk** in
   the synopsis — protagonists AND secondary characters."

4. **Raise the goal ceiling and reframe.** Change "Most stories have 2–5
   goals" → "Most stories have 3–6 goals" and add: "Include **all** goals the
   synopsis drives toward, including relationship resolutions (`rel`) and group
   membership changes (`faction`). Do not omit a goal to stay under the count."

5. **Remove the villain-loses-power example.** The `value: false` example
   (`{pred: holds, args: [Villain, power], value: false}`) encourages
   speculative negative goals. Replace with a more constrained example:
   "Use `value: false` only when the synopsis explicitly frames the *removal*
   of something as a story objective."

### Evaluator tolerance fix (failure mode 3)

Add underscore-to-space normalization in `_norm_args` (`evaluate.py`). This
closes the `charter_letter` vs `charter letter` gap. One-line change + one
unit test.

### No changes needed

- **Graph** (`extract_goals.yaml`): same LLM-validator-retry structure.
- **Validator** (`validate_goals`): the validation rules are correct; the
  model's outputs pass validation but don't match ground truth.
- **Ground truth**: the GT goals are correct (verified during FR-574).

## Acceptance criteria

1. **Prompt updated.** All 5 revisions applied to `prompts/extract_goals.yaml`.
2. **Evaluator tolerance fix.** `_norm_args` in `evaluate.py` normalizes
   underscores to spaces (one-line fix for failure mode 3). Add a unit test
   for the normalization.
3. **Re-spike all 5 genres.** `run.py --mode extract-goals` produces new
   `results/l2/*.yaml` files.
4. **Goal recall ≥ 0.80.** `evaluate.py main_l2()` reports recall at or above
   the GO gate. Per J:N2, analysis decides — if recall is 0.78 with one
   remaining miss being a genuine edge case (not a prompt gap), that may still
   qualify as GO.
5. **Precision non-regression (C2).** Precision must not fall below FR-574's
   0.52. A drop must be justified and reported. A recall win bought purely by
   over-generation does not pass.
6. **Existing tests pass.** The 12 `test_l2_validator.py` tests and evaluator
   tests remain green.
7. **Verdict recorded.** Updated `results/evaluation/l2-summary.yaml` with new
   scores and GO/REVISE/KILL verdict.

## Stop rule (C3)

This is the **one permitted prompt-only revision pass**. If this re-spike does
not clear ≥ 0.80 (or a clean-edge-case 0.78 per J:N2), the next step is
**architectural** — two-step extraction, larger model, or accept L2 at its
ceiling and push the reachability check (Phase 4) to tolerate it. No third
prompt-only revision.

## Out of scope

- Ground-truth modifications (the GT goals are verified).
- Graph architecture changes (retry logic is working).
- Validator changes (validation catches real errors correctly).
- Evaluator changes beyond the underscore normalization in AC#2.

## Risks

- **Prompt changes may regress genres that already scored well.** Quest-adventure
  had perfect recall (3/3). Mitigation: re-spike all 5 genres and verify no
  genre drops below its FR-574 recall.
- **Raising the ceiling may increase over-generation.** "3–6 goals" + "include
  all" could worsen precision. Mitigation: the "do not paraphrase" anchor and
  removal of the villain-power example should counterbalance.

## Dependencies

- **FR-574 (Enforced):** graph, prompt, validator, evaluator infrastructure.
- **FR-571 (Enforced):** Fluent/Belief schemas used by the validator.

## Judgement (2026-06-24)

**Verdict: GRANTED with conditions.** Predecessor verified — FR-574 is enforced
and returned REVISE 0.72, confirmed in
[l2-summary.yaml](../examples/plot_modeller/results/evaluation/l2-summary.yaml);
the five proposed prompt revisions each map to a real gap in
[extract_goals.yaml](../examples/plot_modeller/prompts/extract_goals.yaml)
(no "use names as they appear," example shape omits `rel`, the villain-power
`value:false` example, the "2–5 goals" ceiling). A prompt-only REVISE with a
re-spike is the right-sized response. Three conditions.

### C1 — the failure-mode table does not reconcile with the per-genre recall

The summary's per-genre misses are: detective 1, historical 1, horror 1,
quest 0, scifi 2 (= 5 total). The FR's evidence tables attribute: **scifi 3**
(two `holds` + one `rel`), detective 1, horror 1, **historical 0**. The grand
total coincidentally matches (5), but scifi is over-counted by one and
**historical-fiction's real miss (2/3) is undiagnosed** — it appears in neither
failure cluster. So the "two distinct failure modes, both prompt gaps" claim
does not actually cover all five misses. **Fold:** reconcile the table against
`l2-summary.yaml` per-genre before enforcing — identify the historical miss and
confirm scifi's true miss set. If the historical miss is a *third* pattern, the
five revisions may not move it, and the re-spike will land at 0.78 for a reason
the FR didn't predict. Diagnose all five, not four.

### C2 — hard recall gate, no precision floor, while the revisions trade one for the other

The revisions pull in opposite directions: revision 4 ("3–6 goals," "include
all," "do not omit") raises recall at precision's expense; revisions 1 and 5
(anchor names, drop villain-power) push precision back up. The FR gates hard on
recall (≥ 0.80) but sets **no precision floor** (AC#4: "no minimum threshold").
That asymmetry is a real risk, because the value statement's own logic cuts both
ways: a *missing* goal causes a false-negative reachability gap, but a
*spurious* goal (precision 0.52 → ~1 invented goal per genre) creates a
false-**positive** reachability *obligation* the merge node (Phase 4) must then
satisfy or flag. **Fold:** add a precision **non-regression** guard — precision
must not fall below FR-574's 0.52 — so a recall win bought purely by
over-generation does not silently pass. It need not be a hard GO gate, but it
must be reported and a drop must be justified.

### C3 — declare a stop rule: this is a REVISE of a REVISE

FR-574 was REVISE; this is the second pass. Without a stop rule, a 0.78 here
invites FR-582 (a third prompt tweak), then FR-583 — the diary's
`audit_as_ritual` trap (3+ iterations without structural change = ritual, not
process). **Fold:** state the exit explicitly — if this re-spike does not clear
≥ 0.80 (or a clean-edge-case 0.78 per J:N2), the next step is **architectural**
(two-step extraction, larger model, or accept L2 at its ceiling and push the
reachability check to tolerate it), **not** a third prompt revision. One more
prompt pass is the limit.

### Folded

C1 → reconcile the miss table with per-genre recall; diagnose the historical
miss. C2 → precision non-regression guard (≥ 0.52, reported). C3 → stop rule:
no third prompt-only pass. The prompt revisions themselves are well-grounded and
the no-architecture-change scope is correct. Proceed to Enforce — but resolve C1
first, because an undiagnosed miss means the re-spike target is not yet fully
understood.
