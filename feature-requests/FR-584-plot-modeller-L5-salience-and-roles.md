# Feature Request: FR-584 Plot Modeller — L5 salience suppression + typed argument roles

**Priority:** HIGH
**Type:** Feature (prompt-architecture revision)
**Status:** Draft (revision of FR-583 L5 REVISE)
**Effort:** 1 day
**Requested:** 2026-06-24
**Predecessor:** FR-583 (L5 REVISE; Part 1 Jaccard KEEP, Part 2 vocab KILL)
**Blocks:** FR-579 (merge/pipeline)

## Summary

FR-583 left L5 at world recall ~0.60 (haiku) and killed the vocabulary-grounding
lever after a controlled A/B showed it regressed every metric. The post-spike
failure-mode dissection (FR-583 "L5 failure-mode analysis") proved the real
bottleneck is **not** token naming — it is **84 false positives vs 34 misses**,
dominated by location flooding (67% of FPs) and relation directionality. This FR
implements the C5-pre-registered alternative: a **two-step decode** that first
constrains *which* fluents are salient, then fills *typed argument roles*, before
any token is named. Precision, not recall, is the primary target.

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

A single LLM node remains, but the prompt is restructured into a **two-pass
decode within one generation** (no second graph node — the model reasons in two
labelled stages in its YAML output, the validator checks the final stage):

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
(an object has a location) and the OBJECT of `holds`. Provide the artifact roster
(extracted mechanically from the gloss/agents — NOT from ground truth, to avoid
the FR-583 leakage trap).

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
