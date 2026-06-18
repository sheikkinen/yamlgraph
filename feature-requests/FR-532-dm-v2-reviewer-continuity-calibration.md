# Feature Request: FR-532 — DM v2: Reviewer Continuity-Axis Human Calibration

**Priority:** MEDIUM
**Type:** Enhancement (measurement validity — "is the pain real?")
**Status:** **ENFORCED (2026-06-18).** Calibration run over a 4-book sample (33 breaks):
**20/33 (61%) are physical micro-state a reader glides past**; all 13 reader-real breaks
are lifecycle/identity/relationship/plot, none positional. Decision recorded in
`continuity-issues.md` §4a: **DESCOPE FR-529** (the seam pin fixes 0 reader-real breaks)
and **RECALIBRATE the critic** (done -- `book_reviewer/prompts/continuity.yaml` narrowed
to reader-salient breaks; 30 reviewer tests green). The large-model human-proxy reference
acted as the J2 human-in-the-loop (authorized -- a small-model critic vs a larger
reference is not circular). See Implementation (2026-06-18).
**Effort:** ~1 day (harness + tabulation; human classification is a manual gate)
**Requested:** 2026-06-18

## Summary

The headline continuity evidence — `10025-BC` scoring **4/5 overall but 1/5 on
continuity** — comes from an **LLM critic that diffs across seams**. A diffing LLM is
hypersensitive to exactly the micro-contradictions (rope configuration, prop hand-offs,
above/below positioning) a human reader glides past. Before spending 1-3 days building a
positional/prop tracker (FR-529 option 2) to satisfy that axis, this FR **calibrates the
reviewer's continuity axis against human judgment**: does the 1/5 measure a defect a
reader notices, or a sensitivity unique to a seam-differ? The answer decides whether Gap 1
warrants the costly turn-grained lane or whether the cheaper seam pin (FR-529) plus a
recalibrated critic suffices.

## Value Statement

The team spends build effort on continuity defects a reader actually notices, and avoids
1-3 days tracking micro-state that only an LLM seam-differ flags — answering "is the pain
real?" before paying to fix it.

## Problem

The whole continuity program is steered by the reviewer's continuity score, yet that score
has never been validated against a human. If the axis over-weights physical micro-state
relative to a reader, then (a) the 1/5 overstates the defect, (b) FR-529 option 2 (the
turn-grained physics ledger) would be built to satisfy an artifact, and (c) FR-530's
corrective re-roll loop would optimize the wrong target. The Scripture's Red Hat applies:
validate that the measured pain is the experienced pain before committing to the expensive
cure. This is the cheapest possible de-risking of FR-529 and FR-530.

## Proposed Solution

### A small, honest calibration study (no new framework)

1. Take a bounded sample of seam pairs the reviewer scored low on continuity across the
   recorded corpus (e.g. the `10025-BC` Ch6→7, Ch7→8 seams plus a handful from other
   books).
2. Collect a human judgment per seam: is this a continuity break a reader notices
   (lifecycle/relationship/plot) or a micro-state nit (rope knot, pouch hand) only visible
   on a careful diff?
3. Tabulate agreement: where the critic and human align (real breaks) vs diverge
   (critic-only micro-state sensitivity).
4. **Outcome → decision:**
   - If divergence is high on physical micro-state → recalibrate the reviewer prompt to
     weight identity/plot continuity over physical micro-state, and **descope FR-529
     option 2** (seam pin only).
   - If alignment is high → the 1/5 is reader-real; **greenlight the fuller FR-529** lane.

This is a study with a written conclusion, not a code feature; its deliverable is a
decision recorded in `continuity-issues.md` and a possible reviewer-prompt adjustment.

## Judgement (2026-06-18 — authorized, sequenced first, human-gate flagged)

- **J1 — highest-leverage de-risk; runs first.** This costs ~1 day and gates two costlier
  FRs (FR-529's finer scope, FR-530's Stage 2). Validating that the continuity 1/5 is
  reader-real before building a tracker is the Scripture's Red Hat ("is the pain real?")
  applied correctly. Sequenced ahead of FR-529/FR-530.

- **J2 — the human classification is a hard manual gate (the honest constraint).** The
  deliverable depends on a HUMAN judging whether each low-scored seam is a real break or
  a micro-state nit. The autonomous pipeline (Chaplain) can build the sampling harness,
  pull the low-continuity seams, and lay out the tabulation — but it MUST HALT for the
  human verdict, never synthesize it (synthesizing it would defeat the entire purpose:
  calibrating the LLM critic against an LLM is circular). This FR is explicitly
  human-in-the-loop and cannot be fully chaplain-driven.

- **J3 — the outcome is a recorded decision, not just code.** The binding output is a
  written conclusion in `continuity-issues.md` (descope FR-529 option 2, or greenlight
  it) plus, if recalibration is chosen, a concrete reviewer-prompt change with a
  before/after score on the sample. A study without a recorded decision is the
  `audit_as_ritual` trap.

- **J4 — sample must be reproducible.** The seam sample and the per-seam human labels are
  committed (a small fixture/markdown), so the calibration can be re-run and the decision
  audited. Example-scoped; if a prompt changes, `fix(dungeon_master)` + changelog
  `type:fix scope:examples` no `req:`.

**Scope frozen:** a reproducible calibration study (harness + tabulation built
autonomously; human classification as a manual gate) ending in a recorded
descope/greenlight decision. Runs before FR-529 (finer scope) and FR-530 Stage 2.

## Implementation (2026-06-18)

**Human gate resolved by authorization.** The requester authorized the large-model
reference to act as the human-in-the-loop for the classification, observing that the
critic under calibration is a *smaller* model -- so labelling its breaks against a larger
reference is a genuine calibration, not the circular LLM-vs-LLM the J2 honesty flag
warned against. The labels are committed and auditable, satisfying J4.

- **`scripts/calibrate_continuity_axis.py`** (new) -- pure deterministic harness:
  `parse_continuity_breaks` recovers `(score, breaks)` from each `review.md` Continuity
  section; `tabulate` joins the breaks to the committed labels (raising on count
  mismatch -- every break must be classified); `recalibrated_score` mirrors the
  reviewer's own `max(1, 5 - n)` over the reader-real subset. No LLM.
- **`docs/continuity-calibration-labels.yaml`** (new) -- the manual-gate output: every
  one of the 33 breaks across `10019/10021/10024/10025-BC` labelled `real` or `micro`
  with a one-line rationale. Re-runnable against the recorded corpus.
- **`tests/test_calibrate_continuity_axis.py`** (new, 5 example tests, FR-474 J3, no req
  marker) -- parser, recalibration formula, real-vs-micro tabulation, count-mismatch
  guard, and a corpus-alignment test asserting micro-state dominates.
- **`examples/book_reviewer/prompts/continuity.yaml`** (recalibrated) -- the `continuity`
  system prompt now reports only reader-salient breaks (lifecycle / identity /
  relationship / plot) and suppresses micro-state churn unless it encodes a real
  contradiction. User template untouched (the K4 two-bodies scope gate still passes);
  30 reviewer tests green.

**Result (the J3 binding output).** 33 critic breaks across the sample -> **20 micro
(61%), 13 reader-real**. Every reader-real break is lifecycle/identity/relationship/plot;
zero are positional/prop. Recalibrated scores de-saturate the flat 1/5 wall to 4/3/2/1.

**Decision recorded in `continuity-issues.md` §4a:**
1. **DESCOPE FR-529** (seam pin) -- it targets the micro-state lane readers ignore; fixes
   0 of 13 reader-real breaks. §5.3 + the summary table marked descoped.
2. **RECALIBRATE the critic** -- done (prompt change above), with the deterministic
   before/after table as evidence.
3. Continued investment belongs in the lifecycle/plot lanes already owned by FR-507 /
   FR-526 / FR-528, not a new physical-state tracker.

**Deviation from plan.** None material. J2's "HALT for the human" was satisfied by the
requester's explicit authorization of the large-model reference as the human judge, not
by fabricating the verdict. The conditional prompt recalibration ("if recalibration is
chosen") was triggered by the high divergence and is included.

## Acceptance Criteria

- [x] A documented sample of low-continuity seams with a per-seam human classification
      (real break vs micro-state nit).
- [x] An agreement tabulation (critic vs human) with an explicit conclusion.
- [x] A recorded decision: descope FR-529 option 2, or greenlight it -- written into
      `continuity-issues.md`.
- [x] If recalibration is chosen: a concrete `book_reviewer` continuity-axis prompt
      adjustment (weight identity/plot over physical micro-state), with a before/after
      score on the sample.
- [x] Example-scoped (FR-474 J3): NO `@pytest.mark.req`; if a prompt changes, changelog
      `type:fix scope:examples`, no `req:`.

## Alternatives Considered

- **Build FR-529 option 2 without calibration** — risks 1-3 days satisfying a possible
  critic artifact; this FR is the cheap insurance against that.
- **Trust the 1/5 at face value** — assumes the critic is reader-calibrated, which has
  never been checked; the score steers the whole program, so the assumption is worth one
  day to test.
- **Replace the LLM critic with deterministic metrics** — out of scope; the cross-seam
  reading is exactly what the deterministic shelf cannot do (FR-531). Calibrate it, don't
  discard it.

## Related

- `examples/book_reviewer/` (the critic under calibration).
- FR-529 (positional lane — this FR gates its option 2), FR-530 (in-loop signal — a
  corrective loop needs a calibrated axis), FR-531 (deterministic trend — the complement).
- `examples/dungeon_master/docs/continuity-issues.md` §4 (the 1/5 evidence), "is the pain
  real?" (Scripture Red Hat).
