# Feature Request: FR-726 ICPC-2 Verdict Stability (Phase 4)

**Priority:** LOW (blocked)
**Type:** Feature
**Status:** Judged (gated — mechanism judgement deferred)
**Effort:** 1-2 days
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — frame ratified; mechanism NOT judged
**Parent:** FR-722 — see `examples/icpc-2-rfe/PLAN.md`
**Blocked by:** FR-725 — this FR may not be judged until the crosscheck
harness has produced baseline agreement numbers (AC-04 there).

## Problem

Per-cluster LLM verdicts are nondeterministic even at temperature 0.1;
the deterministic reducer cannot repair variance in its inputs. Verdict
discipline (prompt) reduced but cannot eliminate flapping between
adjacent verdicts (match ↔ partial_match) on genuinely borderline
rubrics — observed as primary churn on HP-36 before discipline, and as
residual best-partial reordering after.

## Proposed Solution (to be judged against FR-725 baseline)

Per-cluster self-consistency voting: sample each cluster N times
(default N=3), aggregate per code — majority verdict, median
confidence, union of aligned evidence spans. Cost is N× LLM calls;
the judgement must weigh measured agreement gain against measured cost
(seed question from diary 2026-07-14: is 3× worth it, and should the
map node express repeat-sampling natively rather than the example
hand-rolling it?).

Alternatives the Judge must consider:
1. Reducer-side hysteresis over the run archive (no extra calls).
2. Native map-node `samples: N` + `aggregate:` primitive (framework
   feature — separate FR if chosen).
3. Do nothing: if FR-725 baseline shows ≥90% primary agreement after
   verdict discipline, close as not-worth-it.

## Acceptance Criteria

- [ ] AC-01 FR-725 harness shows a statistically meaningful agreement
      improvement at the judged N (before/after on the same fixtures).
- [ ] AC-02 Cost accounting: calls and wall-clock per transcript,
      before/after, in the FR.
- [ ] AC-03 Deterministic reducer contract unchanged; all phase-1/2
      witnesses green.
- [ ] AC-04 Explicit kill criterion honored: if baseline agreement is
      already ≥90%, this FR closes CONDEMNED with the numbers cited.

## Constraints

1. No calibration claims — voting changes verdict stability, not
   confidence meaning.
2. Fan-out × N must respect max_map_items or batch within the subnode.

## Judgement (2026-07-14)

**Verdict: APPROVED AS GATED — the frame is ratified, the mechanism is
deliberately unjudged.** Judging a mitigation before its baseline
exists would repeat the exact trap this ladder was built to avoid
(FR-711 precedent: the instrument measured a retired topology). What is
frozen NOW:

1. **The gate:** no mechanism judgement, no RED test, no enforcement
   until FR-725 AC-04 baseline numbers (k-of-n agreement per fixture,
   n≥5) are cited in this FR. Any enforce attempt before that is a
   doctrine violation, not an eagerness credit.
2. **The kill criterion is binding:** baseline primary agreement ≥ 90%
   across the labeled set closes this FR CONDEMNED with the numbers
   cited. Closing it is a success outcome, not a failure.
3. **The alternatives table is the judgement agenda**, in cost order:
   (a) do nothing (kill criterion), (b) reducer-side hysteresis over
   the archive (zero extra calls), (c) per-cluster self-consistency
   voting (N× calls), (d) native map `samples:`/`aggregate:` primitive
   (framework FR, separate judgement). The mechanism judge must reject
   (c) if (b) reaches comparable agreement, and must reject (d) unless
   a second example needs it (rule of two).
4. **Cost accounting (AC-02) is mandatory evidence**, measured by the
   FR-725 harness, not estimated.

**Out of scope until the gate opens:** everything else in this FR.

## Gate citation (2026-07-14): FR-725 baseline exists

Baseline (N=5 × 6 fixtures): primary agreement 5/5, 5/5, 5/5, 5/5, 3/5,
4/5 — ≈ 90%+ on four of six fixtures. **The kill criterion is in
reach, and more importantly the baseline shows the dominant defect is
BIAS, not variance**: cough-fever agrees 5/5 on the WRONG primary
(`-48`). Self-consistency voting amplifies a biased mode — it cannot
help. Mechanism judgement stays deferred until FR-727 (process-code
discipline) lands and a fresh baseline separates residual variance
from the now-dominant bias. Expected outcome: CONDEMNED per AC-04.
