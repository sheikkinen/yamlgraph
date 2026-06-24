# Feature Request: FR-584 Plot Modeller — L5 salience suppression + typed argument roles

**Priority:** HIGH
**Type:** Feature (prompt-architecture revision)
**Status:** Judged — Authority GRANTED (2026-06-24)
**Effort:** 1.5–2 days
**Requested:** 2026-06-24
**Predecessor:** FR-583 (L5 REVISE; Part 1 Jaccard KEEP, Part 2 vocab KILL)
**Blocks:** FR-579 (merge/pipeline)

## Summary

FR-583 left L5 at world recall ~0.60 (haiku) and killed the vocabulary-grounding
lever after a controlled A/B showed it regressed every metric. The post-spike
failure-mode dissection (FR-583 "L5 failure-mode analysis") proved the real
bottleneck is **not** token naming — it is **84 false positives vs 34 misses**,
dominated by location flooding (67% of FPs) and relation directionality. This FR
implements the C5-pre-registered alternative: **prompt-level reasoning-order
constraints** that guide the model to first assess *which* fluents are salient,
then fill *typed argument roles*, before naming tokens — all within the existing
single LLM call and output schema. Precision, not recall, is the primary target.

## Value statement

L5 precision is 0.16–0.30: the model emits 2.5× more wrong world-state predicates
than it omits true ones, and those false positives propagate into L6 causality as
phantom preconditions. Teaching the model to *suppress* non-salient fluents and to
*orient* asymmetric relations should lift precision toward ~0.5 and clear the 0.70
combined-recall confusion bar without a larger model — unblocking FR-579.

## Problem

The FR-583 confusion dump (no-vocab baseline, world recall 0.60) ranks the L5
failure modes by damage:

1. **Location flooding / salience blindness (precision killer).** 56 of 84 FPs
   (67%) are `at` predicates. The model snapshots every character's position at
   every beat; the ground truth records only the salient fluent the beat turns
   on. The model has no notion of *which* precondition a beat actually depends on.
2. **Relation directionality.** `rel(A, B)` is emitted as `rel(B, A)` (GT
   `rel(The Swarm, ARIA)=assimilated` → pred `rel(ARIA, The Swarm)`), and the
   wrong relatum is chosen (`rel(Jonas, The Swarm)` for truth `rel(Jonas, ARIA)`).
   9 `rel` misses + 15 `rel` FPs.
3. **Ontological blindness to non-character entities.** Artifacts are never a
   fluent's subject: `at(Sunken Crown, Temple)` (missed ×4), `at(Charter letter,
   Djenné)`, `holds(Ferryman Ossa, passage)` all missed.
4. **Mortality bookkeeping.** 4 `alive` misses, ~0 correct; death beats are
   narrated as location/relation changes instead of `alive=false`.
5. **Abstraction drift on object tokens** (smallest gap, ~8 misses) — the only
   gap FR-583 Part 2 addressed, and the one it could not move.

A token list (FR-583 Part 2) attacks only #5 and *amplifies* #1 by giving the
model more tokens to dutifully place. The leverage is in #1 and #2.

## Proposed solution

A single LLM node remains with an unchanged YAML output schema (id, pre_world,
eff_world, pre_belief, eff_belief per beat). The prompt is restructured to guide
the model's **reasoning order** — assess salience before emitting predicates,
orient argument roles before writing `rel` — but the output the validator checks
is the same shape as today. If this prompt-reasoning-order approach stalls, the
stop rule escalates to a true two-node decode (separate salience-filter LLM call
feeding an argument-fill call).

### Lever A — salience suppression (targets #1, the precision killer)

Add an explicit suppression rule to `prompts/assign_pre_eff.yaml`:

> Emit a `pre_world` fluent ONLY if the beat would be *impossible* without it.
> Do NOT snapshot positions or restate standing state. If a character's location
> is not the thing this beat changes or depends on, do not mention it. Most beats
> have 0–2 preconditions, not one per character.

Acceptance signal: `at` false-positive count drops from 56 toward < 20; precision
rises from ~0.20 toward ~0.45+.

### Lever B — typed argument roles for `rel` (targets #2)

Require the model to fill named roles before emitting the predicate:

> For every `rel`, name the SOURCE (the agent who causes or holds the relation)
> and the TARGET (the agent it is directed at) explicitly, then write
> `rel(source, target)=label`. "The Swarm assimilates ARIA" → source=The Swarm,
> target=ARIA → `rel(The Swarm, ARIA)=assimilated`.

Acceptance signal: `rel` argument-order errors (swapped pairs) drop to near zero
on the scifi fixture.

### Lever C — non-character subject prompt (targets #3)

Add to the predicate guide: artifacts and objects can be the SUBJECT of `at`
(an object has a location) and the OBJECT of `holds`. The roster of such entities
is read by the model from the **beat text it is already given** — NOT from any
ground-truth structure.

**Source constraint (anti-leakage, ratified by C4 below):** The L5 node's state
is exactly `{glosses, agents}` (verified: `graphs/assign_pre_eff.yaml` has no
`initial_world` key; `run_assign_pre_eff` invokes with only those two). The GT
`initial_world` is the scored answer key and is forbidden as an input — reading it
would repeat the FR-583 Part 2 leakage KILL. The glosses already name objects and
places in the synopsis's own words (e.g. "firmware update" in F1, not the GT
token `firmware_channel`).

**Therefore Lever C is pure prompt language, no `run.py` change, no new template
variable, no roster injection:** instruct the model that any object or location
it reads in a beat may be the subject of `at` / `holds`. This fixes the
ontological-subject blindness (#3). It does NOT supply canonical tokens — that is
the #5 naming gap, which stays deferred and off-limits (the glosses carry only
paraphrased tokens, and the GT tokens are unreachable without leakage).

**Files changed:** `prompts/assign_pre_eff.yaml` only (prompt text).

### Out of scope (explicit)

- **No ground-truth vocabulary injection** (FR-583 Part 2 KILL; leakage + worse).
- **No larger model** as the first lever — haiku stays, per the FR-578
  anti-scaling lesson; escalate only if A+B+C stall.
- **No `alive` lever yet** (#4) — smallest, deferred; revisit if recall stalls
  after precision is fixed.
- **No evaluator changes** — Part 1 Jaccard tolerance stays; scoring is frozen so
  A/B is clean.

## Acceptance criteria

- [ ] Salience-suppression rule added; re-spike on haiku (verify `Creating LLM`
      log line) regenerates `results/l5`.
- [ ] `at` false-positive count and predicate precision reported before/after on
      every re-score (precision tripwire, inherited from FR-583 C3).
- [ ] Typed-role `rel` instruction added; scifi `rel` arg-swap count reported.
- [ ] Confusion analysis re-run (reuse the FR-583 dump method) — the dominant
      failure mode must *shift away from* location flooding for the lever to be
      judged working.
- [ ] **Controlled A/B (FR-583 lesson):** run the revised prompt AND a control
      (revised minus Lever A) at the same temp; compare precision delta and
      catastrophic-failure count, not a single noisy run.
- [ ] L5 verdict recorded by J:N2 (combined world recall ≥ 0.70 GO; 0.50–0.70
      REVISE; KILL only sub-0.50 with non-fixable confusion).
- [ ] Diary reflection added.

## Stop rule

If, after Levers A+B+C, precision stays ≤ 0.25 **and** location flooding remains
the dominant FP class, KILL the prompt-architecture approach and escalate to
either a true two-node decode (separate salience-filter node feeding an
argument-fill node) or a larger model — do NOT iterate prompt wording a fourth
time (FR-581/582/583 each hit a prompt-only stop rule; the fourth is ritual).

## Alternatives considered

- **Larger model first** — rejected as first lever (FR-578: scaling masks framing
  bugs; the failure is salience, which a bigger model emits *more* confidently).
- **Second vocab iteration** — rejected (FR-583 C5 KILL).
- **Relax evaluator precision** — rejected; precision is the true signal here, and
  loosening it would manufacture the win FR-583 Part 1 refused to fake.

## Related

- `feature-requests/FR-583-plot-modeller-evaluator-tolerance-and-vocab-grounding.md`
  (predecessor + failure-mode analysis)
- `examples/plot_modeller/prompts/assign_pre_eff.yaml` (Levers A/B/C land here)
- `examples/plot_modeller/evaluate.py` (frozen — scoring unchanged)
- `docs/diary/diary-2026-06-24-the-lever-that-taught-to-the-test.md`

## Judgement (2026-06-24)

**Verdict: Authority GRANTED — three conditions folded into spec above.**

FR-584 is the correct next step in the L5 progression: FR-582 hit the
prompt-wording stop rule, FR-583 Part 2 killed vocabulary grounding, and the
post-mortem failure analysis (84 FPs vs 34 misses, location flooding at 67%)
proved precision, not recall, is the wound. The three levers (salience
suppression, typed rel roles, non-character subjects) target failure modes
#1, #2, #3 by rank — the first FR in the L5 chain to attack the largest error
class first. The controlled A/B requirement (learned from FR-583) and the stop
rule (no fourth prompt iteration) are both sound.

### Conditions (folded)

**C1 — "Two-step decode" reframed as prompt-reasoning-order (folded into
Summary + Proposed solution).** The original text described "two labelled stages
in YAML output" but all three levers are prompt instructions — no output schema
change, no new YAML block, no validator modification. Reframed: the prompt
guides reasoning order (salience → roles → tokens) within the existing output
shape. The true two-node decode (separate salience-filter LLM call) is the
stop-rule escalation, not a deliverable of this FR.

**C2 — Lever C extraction rule specified (folded into Lever C).** Original said
"extracted mechanically from the gloss/agents" without naming the field, the
extraction logic, or the caller file. Now specifies: check whether `state.agents`
already includes non-character entities; scan `state.glosses` / `initial_world`
for artifact names; name `run.py` if a new template variable is needed.

**C3 — Effort revised to 1.5–2 days (folded into header).** Three prompt
levers + controlled A/B (two full 5-genre spikes minimum) + confusion
re-analysis + diary. FR-583 was estimated at 1 day and took a full session for
Part 1 alone. The mandatory A/B doubles the spike cost.

**C4 — Lever C leakage contradiction corrected (post-judgement check,
2026-06-24).** The first-pass judgement folded a C2 extraction rule that named
`initial_world` as a scan source and claimed it was "available to the prompt via
the synopsis input." Verification falsified both claims: the L5 graph state has
no `initial_world` key and `run_assign_pre_eff` passes only `{glosses, agents}`;
`initial_world` is exclusively a ground-truth fixture field — the scored answer
key. Using it would repeat the exact FR-583 Part 2 leakage that was KILLed. Lever
C is therefore re-scoped to **pure prompt language over the already-present beat
text** — no `run.py` change, no roster injection, no GT access. Lever C addresses
ontology (#3) only; canonical-token naming (#5) stays deferred and unreachable
without leakage. This correction tightens scope; it does not expand it.

**C5 — Confusion-dump tool is ephemeral (note for enforcement).** AC#4 says
"reuse the FR-583 dump method," but that script (`tmp_l5_confusion.py`) was
deleted, not committed. Enforcement must re-create it (or promote it to a small
committed analysis helper); it is not a standing artifact.

### Validated as correct (carried forward)

- Haiku-first, no model escalation (FR-578 anti-scaling lesson). Ratified.
- Evaluator frozen (Part 1 Jaccard stays, scoring unchanged). Clean A/B baseline.
- Out-of-scope list (no GT vocab, no alive lever, no evaluator loosening). All
  correct.
- Acceptance criteria AC#1–AC#7 cover the right signals: at-FP count, precision
  tripwire, rel arg-swap count, confusion shift, controlled A/B, J:N2 verdict.
- Stop rule: precision ≤ 0.25 AND location flooding dominant → KILL → true
  two-node decode or model escalation. Correct and non-ritual.

**Frozen scope:** Three prompt-instruction levers in `assign_pre_eff.yaml`
**and that file only** (salience suppression, typed rel roles, non-character
subjects over the existing beat text), unchanged output schema, no `run.py`
change, no ground-truth input, controlled A/B isolating Lever A, confusion
re-analysis, J:N2 verdict. Effort 1.5–2 days.
