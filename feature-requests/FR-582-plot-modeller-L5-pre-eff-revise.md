# Feature Request: FR-582 Plot Modeller — L5 pre/eff assignment REVISE

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced — REVISE (0.55 Haiku flat, 0.51 Sonnet regressed; stop rule; escalate architectural; 2026-06-24)
**Effort:** 0.5 day
**Requested:** 2026-06-24
**Predecessor:** FR-576 (L5 assign pre/eff spike — verdict REVISE, 0.55 combined world recall)
**Blocks:** FR-579 (merge/pipeline)
**Data dependency:** None new (same graph, prompt, evaluator)
**Scheduling dependency:** FR-576 (inherits its infrastructure)

## Summary

Revise the L5 pre/eff prompt to raise combined world recall from 0.55 to
≥ 0.70 (the GO gate). FR-576 measured three distinct *fixable* failure modes —
open-label divergence on `rel`/`faction`, multi-word object-token paraphrase,
and departure under-modeling (dropped `=false` effects on location change) —
all traceable to prompt gaps, not architecture. No graph, validator, or
evaluator changes are required for the world gate; this is a prompt-only
revision with a re-spike. (A fourth measured mode, belief unrecoverability, is
**not** in scope — see "What this FR does NOT do".)

## Value statement

The pre/eff slice is the causal substrate the whole plan rests on: L6's
`enables` links read these predicates, and the Phase-4 causality SAT check
validates against them. At 0.55 combined world recall the model drops ~45% of
the world-state changes, which propagates as false open-condition flaws
downstream. Closing the three identified clusters brings recall above the GO
gate without architecture changes — the same prompt-only lever that FR-581
applies to L2.

## Problem

FR-576 spike measured combined world recall 47/85 (0.55), predicate precision
48/170 (0.28). Verdict: REVISE (J:N2 — borderline band, confusion pattern
confirms fixable). The error pattern is coherent and prompt-traceable.

### Per-genre reconciliation

| Genre | World recall | Dominant local failure |
|-------|--------------|------------------------|
| detective | 6/12 (0.50) | departure under-modeling (location moves) |
| historical | 6/9 (0.67) | object-token paraphrase (multi-word place names) |
| horror | 13/17 (0.76) | already near gate — thin residual |
| quest | 14/24 (0.58) | departure under-modeling (the journey arc is move-heavy) |
| scifi | 8/23 (0.35) | value-label divergence + token paraphrase compound |

The two move-heavy genres (detective, quest) and the label-heavy genre (scifi)
carry the deficit; horror is already at the gate.

### Failure mode 1: value-label divergence on `rel` / `faction` (open free-text)

- **scifi**: GT `rel(The Swarm, ARIA)=assimilated` vs predicted
  `rel(...)=synchronized`. The model invents a plausible synonym for the
  relationship label.

**Root cause:** `rel` and `faction` values are open free-text labels. The
current prompt *lists* example labels (`allied, hostile, assimilated,
entrained, estranged`) but frames them as examples, not as a vocabulary to
select from — so the model coins new synonyms the tolerant matcher cannot
bridge (an exact-ish value comparison on an open string set).

### Failure mode 2: multi-word object-token paraphrase

- **scifi**: GT `holds(ARIA, firmware_channel)` vs predicted
  `holds(ARIA, firmware update)`; GT `Vantari Labs` vs predicted `lab`.

**Root cause:** the **named dominant risk** carried forward from FR-576's spec.
The prompt already has a strong single-token NAMING anchor, but it fails on
*multi-word* tokens: the model compresses `Vantari Labs` → `lab` and rewrites
`firmware_channel` → `firmware update`. The anchor must explicitly forbid
shortening or re-spacing multi-word names, and the tolerant matcher cannot
(and should not) bridge a true paraphrase.

### Failure mode 3: departure under-modeling (dropped `=false` effects)

- **detective / quest**: GT models a location change as `at(X, old)=false` +
  `at(X, new)=true`; the model emits only the arrival (`at(X, new)=true`),
  dropping every departure.

**Root cause:** the prompt does not state that a location change produces
**both** a departure (`=false`) and an arrival (`=true`). Because half of every
move is silently dropped, the move-heavy genres (detective, quest) lose the
most recall. This is the single highest-yield fix: it converts a structural
omission into a one-rule instruction.

## Proposed solution

### Prompt revisions (`prompts/assign_pre_eff.yaml`) — prompt-only

1. **Calibrate the relationship/faction label vocabulary.** Reframe the `rel`
   value list from examples to a *selection set*: "For `rel` and `faction`
   values, choose the closest label from this set:
   `allied, hostile, assimilated, entrained, estranged, captive, kin, rival`.
   Only coin a new label if none fits — and prefer the synopsis's own word."
   (Mirrors FR-581's calibrated-vocabulary revision for L2.)

2. **Strengthen the anchor for multi-word tokens.** Extend the existing
   CRITICAL — NAMING block: "This applies to **multi-word** names too. Do NOT
   shorten (`Vantari Labs` → `lab`), re-space, or re-style (`firmware_channel`
   → `firmware update`) any object, place, or character token. Copy the full
   token verbatim, including underscores and capitalization."

3. **Add a move-decomposition rule.** Add to the slice guidance: "When a beat
   moves a character from one place to another, `eff_world` must contain BOTH
   `at(character, origin)=false` AND `at(character, destination)=true`. A move
   is two effects, never one. If the origin is unknown, still emit the
   departure against the best-named prior location."

### No evaluator change

Unlike FR-581 (which added underscore normalization), the L5 matcher already
normalizes args and uses contains/prefix matching. The residual misses are
genuine paraphrases and genuine omissions — loosening the matcher further would
manufacture false positives (a plausible-wrong-answer hazard). The fix belongs
in generation, not in scoring.

## Re-spike and gate

Re-run L5 (Mode 1, ground-truth glosses + kinds) across all 5 synopses and
re-evaluate with the unchanged evaluator.

- Combined world recall ≥ 0.70 → **GO** (the gate FR-576 set)
- 0.50–0.70 → **REVISE** again (escalate per the stop rule below)
- < 0.50 → **KILL** the prompt-only approach

**Stop rule (inherited from FR-576's follow-up note):** if this second prompt
pass does not clear 0.70, the next step is **architectural** (two-step
pred-then-args generation, or a larger model), **not** a third prompt pass.
One revise, then escalate.

**J:N2 inheritance:** the threshold triggers; the confusion analysis carries
the verdict. A bare 0.71 with a new dominant failure mode is a REVISE, not a
GO; a 0.69 whose only residual is the (out-of-scope) belief slice is a GO.

## Acceptance criteria

1. `prompts/assign_pre_eff.yaml` revised with the three changes above; no
   graph, validator, or evaluator edits.
2. L5 re-run across all 5 synopses; `results/l5/*.yaml` regenerated.
3. `results/evaluation/l5-summary.yaml` regenerated with the new recall and a
   refreshed confusion block.
4. Combined world recall reported as `X/85` (denominator-visible, J:C5) with
   the verdict justified by confusion analysis, not the bare number.
5. Per-genre recall reported for all 5 genres; the move-heavy genres
   (detective, quest) show the expected lift from the move-decomposition rule.
6. The existing 12 L5 validator tests stay green (no validator change).
7. FR-582 updated with the re-spike verdict and, if still REVISE, the
   architectural escalation recorded (not a third prompt pass).

## What this FR does NOT do

- Does not raise `eff_belief` recall (1/17). That is J2 leakage — ground-truth
  beliefs encode full-plot dramatic irony a single-beat view cannot recover.
  It is excluded from the world gate (FR-576 J:C3) and is **informational**,
  not a defect. Belief modeling, if pursued, is a separate full-plot-context FR.
- Does not change the graph, validator, evaluator, or schema.
- Does not add a second formalization layer (L6 is FR-577) — this retires the
  L5 measurement debt before the chain advances, per the roadmap's risk-control
  serialization (one spike-and-measure at a time) and the review's R1
  (planning depth must not outrun evidence depth).
- Does not loosen the tolerant matcher — the residual misses are real
  paraphrases/omissions; bridging them in scoring would manufacture false
  positives.

## Judgement (2026-06-24)

**Verdict: Authority GRANTED.** A clean prompt-only REVISE mirroring the
FR-574→FR-581 arc one layer deeper. The scheduling rationale is correct —
retiring L5's measured debt before L6 (FR-577) honors the roadmap's N1
(layers are independent; serialization is risk-control) and the review's R1
(planning depth must not outrun evidence depth). Four conditions folded; all
are refinements, none a blocker.

### Verification against the data (what the judge checked, not assumed)

The spike artifacts were inspected directly, not taken on the FR's word:

- **Failure mode 3 (departure) is confirmed by hard data and is total.**
  Predicted `at(...)=false` count is **0 across all 5 genres**; ground truth
  has **9** (detective 2, quest 3, scifi 2, historical 1, horror 1). The model
  drops every departure effect. This is the single highest-yield, highest-
  confidence fix — up to ~9/85 (0.11) recall, which alone moves 0.55→0.66.
- **Failure mode 1 (label divergence) has the weakest evidence.** The diverged
  GT label `assimilated` is **already present** in the current prompt's `rel`
  example list, yet the model emitted `synchronized`. Reframing examples as a
  selection set may not address a *semantic preference* miss. Kept, but
  de-prioritized (C2).

### C1 — the per-genre failure-mode table over-localizes departure omission

The table attributes departure under-modeling to detective/quest specifically.
The data shows it is **universal**: all 5 genres dropped 100% of their
departures. The directional claim (move-heavy genres lose *more* recall to it)
holds because they have more departures (quest 3, detective 2), but the
attribution must read "universal omission, weighted by move-density," not a
genre-local defect. Fold: relabel the table column accordingly when enforcing.

### C2 — fix #1 (label vocabulary) is the lowest-confidence lever; do not over-invest

`assimilated` was already offered and not selected, so a bigger/forced label
list is unlikely to be the cure. The operative clause is **"prefer the
synopsis's own word"** — lead with that, treat the enumerated set as a fallback,
and spend the revision budget on C3/mode-3 (the high-yield fix). If the
re-spike still shows label divergence, that residual is a *value-comparison*
problem for a later FR, not a third prompt pass.

### C3 — the move-decomposition "guess the origin" sub-clause must be constrained

The draft says "if the origin is unknown, still emit the departure against the
best-named prior location." Telling the model to **guess** an origin can
hallucinate `at(X, wrong)=false`, hurting precision (already 0.28) and
contradicting this FR's own anti-false-positive stance for the evaluator. Fold:
emit the departure **only** when the origin is named in the gloss OR established
by a prior beat's `at(X, ·)=true`. No speculative origins. A move whose origin
is genuinely unstated yields arrival-only — and that is correct, not a miss.

### C4 — AC#5 must not presuppose the outcome

"The move-heavy genres show the expected lift" bakes the hypothesis into the
gate. If overall recall clears 0.70 but the lift lands differently, that is
still a GO. Fold: reword AC#5 to **report** per-genre recall and **analyze**
whether the move rule produced the predicted lift — observational, not gating.

### Carried forward unchanged (validated as correct)

- Gate (≥ 0.70 combined world, X/85 denominator-visible), stop rule (one revise
  then escalate to architectural), and J:N2 (confusion analysis carries the
  verdict) are sound and correctly inherited from FR-576.
- Excluding `eff_belief` (1/17, J2 leakage) from the world gate is correct.
- Prompt-only with no evaluator loosening is the right call — the residuals are
  genuine generation defects, and loosening the matcher would manufacture false
  positives (a plausible-wrong-answer hazard).

**Frozen scope:** three prompt revisions (with C2/C3 constraints), re-spike,
re-evaluate, record verdict. No graph/validator/evaluator/schema changes. One
revise, then escalate.

## Implementation Status (2026-06-24)

**Verdict: REVISE → escalate to architectural.** The three judged prompt
revisions were applied verbatim (C2: "prefer the synopsis's own word" leading,
enumerated set as fallback; C3: departure emitted only when origin is named or
prior-established, no speculative origins; mode-2 multi-word anchor). The clean
re-spike measured **47/85 (0.55) combined world recall — exactly flat against
the FR-576 baseline.** The prompt-only lever is exhausted; per the stop rule,
the next step is architectural, not a third prompt pass.

### Built (prompt-only, as judged)

- `prompts/assign_pre_eff.yaml` — three revisions applied (label-vocabulary
  reframe with synopsis-word preference; multi-word NAMING anchor; constrained
  move-decomposition rule).
- No graph, validator, evaluator, or schema edits — scope held.

### Boundary bug discovered and fixed (separate concern, RED+GREEN)

The first two re-spikes returned **historical-fiction 0/9** via a recurring
`assign` loop-limit transient. Diagnosis (Mode-1 single-genre re-run) traced it
to a **code-fence parse crash**: at temp 0.7 the model sporadically wraps its
YAML in a ```` ```yaml ... ``` ```` block; the raw backtick crashes
`yaml.safe_load` → validator fails → retry → loop limit → 0 beats written. This
is a boundary-normalization gap, not an L5 capability ceiling. Fixed by a shared
`_strip_code_fences` helper applied at **all five** validator parse sites
(kinds, agents, goals, glosses, pre/eff), with two RED-first tests
(`test_code_fenced_output_is_parsed`, `test_bare_code_fence_is_parsed`). After
the fix, historical parsed cleanly (10 beats, 4/9). The 14 L5 validator tests
stay green (AC#6 honored — no behavioral validator change beyond fence input
normalization).

### Per-genre results (clean run, fence fix in place)

| Genre | FR-576 baseline | FR-582 clean | Δ | Note |
|-------|-----------------|--------------|---|------|
| detective | 6/12 (0.50) | 7/12 (0.58) | +1 | departure rule emits some `=false` |
| historical | 6/9 (0.67) | 4/9 (0.44) | −2 | temp-0.7 noise (was 0/9 transient pre-fix) |
| horror | 13/17 (0.76) | 13/17 (0.76) | 0 | at gate, flat |
| quest | 14/24 (0.58) | 16/24 (0.67) | +2 | **move rule working — departures emitted** |
| scifi | 8/23 (0.35) | 7/23 (0.30) | −1 | label divergence + token paraphrase persist |
| **overall** | **47/85 (0.55)** | **47/85 (0.55)** | **0** | flat |

Slice detail: `eff_world 28/43 (0.65)` (the move-rule half, the stronger slice)
vs `pre_world 19/42 (0.45)` (the drag). `eff_belief 1/17 (0.06)` — out of scope
(J2 leakage). Predicate precision `48/178 (0.27)`.

### Analysis (J:N2 — confusion carries the verdict, not the bare number)

- **The move-decomposition rule works** (AC#5, observational): quest +2 and
  detective +1 are the move-heavy genres, and `at(...)=false` departures are now
  emitted where the gloss names or prior-establishes the origin — confirmed by
  direct result-file inspection (the grep counter undercounts due to multi-line
  `args:` blocks; the departures are present at e.g. quest lines 52/62).
- **But the gains are offset by genre-level temp-0.7 noise** (historical −2,
  scifi −1) so overall lands flat at 0.55. Across three runs (0.48 with
  transient, 0.53 with transient, 0.55 clean) the signal clusters at ~0.55.
- **The two non-move residuals persist and are not prompt-fixable here:** label
  divergence (`assimilated` was already offered, model still emits
  `synchronized` — a *semantic preference* miss, C2 predicted this) and
  multi-word token paraphrase. Both are value-comparison problems for the
  matcher/architecture, not generation-instruction problems.

### Escalation (AC#7 — not a third prompt pass)

Per the stop rule, the prompt-only approach is retired at 0.55. The next lever
is **architectural**, recorded here for the successor FR:

1. **Two-step pred-then-args generation** — generate the predicate skeleton
   first (which fluents change), then fill args in a second constrained pass.
   This isolates the move-decomposition success (structural) from the
   token/label residuals (lexical), letting each be optimized independently.
2. **Larger model for the assign node** — the label-preference and paraphrase
   misses are the kind of lexical-fidelity gap a stronger model closes; the
   structural move rule already lands on haiku.

The L5 measurement debt is now **retired with a clean, transient-free number**;
the chain may advance to L6 (FR-577) with 0.55 as the honest pre/eff baseline
and the architectural levers documented for a future L5 hardening FR.

### Sonnet 4.6 re-spike (2026-06-24, second run)

A second re-spike with `claude-sonnet-4-6` (upgraded from Haiku) measured
**43/85 (0.51) combined world recall** — a further regression from the 0.55
Haiku baseline, confirming the prompt-only lever is exhausted.

| Genre | FR-576 (Haiku) | FR-582 (Haiku) | FR-582 (Sonnet) |
|-------|---------------|----------------|-----------------|
| detective | 6/12 (0.50) | 7/12 (0.58) | 8/12 (0.67) |
| historical | 6/9 (0.67) | 4/9 (0.44) | 8/9 (0.89) |
| horror | 13/17 (0.76) | 13/17 (0.76) | 13/17 (0.76) |
| quest | 14/24 (0.58) | 16/24 (0.67) | 10/24 (0.42) |
| scifi | 8/23 (0.35) | 7/23 (0.30) | 4/23 (0.17) |
| **overall** | **47/85 (0.55)** | **47/85 (0.55)** | **43/85 (0.51)** |

Precision: 45/239 (0.19), down from 48/178 (0.27).

**Regression drivers (Sonnet-specific):**

- **Quest (-6 vs Haiku FR-582): location token drift.** Sonnet invented
  descriptive location names — "throne room" for "Capital", "flooded gorge"
  for "Temple", "enemy territory" for "Capital" on return. The
  move-decomposition rule fired correctly (structural win) but with wrong
  tokens, costing 2 fluents per beat across the entire move chain.
- **Scifi (-3 vs Haiku FR-582): persistent `rel` → `faction` predicate swap.**
  The label vocabulary revision pushed Sonnet to systematically use
  `faction(X, ARIA)=synchronized` where GT uses `rel(X, ARIA)=assimilated`.
  Self-reinforcing across 7 beats (wrong eff feeds wrong pre).

**Conclusion:** a larger model did not help — it amplified the token-vocabulary
grounding problem. The architectural escalation (two-step pred-then-args, or
explicit vocabulary grounding via initial_world atoms) is confirmed as the
correct next step.
