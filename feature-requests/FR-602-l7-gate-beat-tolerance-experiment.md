# Feature Request: FR-602 L7 Gate Beat-Tolerance Experiment (conditional)

**Priority:** LOW
**Type:** Enhancement (evaluator) — touches the FROZEN FR-578 gate; gated, separately judged
**Status:** CLOSED UNSTARTED (2026-06-26) — residual BEAT-OFF at +/-1 = 1 (< the >=3 evidentiary bar); exact-beat matching stays, frozen gate NOT loosened
**Effort:** ~0.5 day (parameterised re-score + before/after report; no model run)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-599 (probe), FR-600 (GT re-annotation)
**Gate (frozen):** FR-578 `affect_recall` — this FR is the ONLY successor permitted to
touch it, and only as a measured experiment behind a flag
**Lever this FR pulls:** evaluator beat-matching tolerance / GT granularity

## Summary

The FR-599 probe showed BEAT-OFF rising 2→5 and ABSENT falling 12→9 as the match window
widens ±1→±3 — i.e. ~3 "model-scale" misses are recoverable by relaxing the gate's
exact-beat-id requirement to ±1. This FR *measures* whether a ±1 tolerance is the honest
fix for the residual after FR-600, without committing to it: it is an experiment, not a
gate change.

## Value Statement

Decision-makers learn whether the residual beat-off misses are a gate-strictness artifact
(cheap to fix in the evaluator) or genuine model error (expensive to fix by scale) —
before anyone edits the frozen ruler or spends on a larger model.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, BLOCKED on FR-600.** This is the exemplary member of the
triad: it touches the frozen FR-578 ruler, and it does so *correctly* — a copy/flag that
never mutates canonical `main_l7`, a precision guard against admitting false matches, and
an outcome that is a *decision* (a separately-judged gate-change FR, or "exact matching
stays"), never a silent loosening. It refuses the `downstream_fix` trap by name and the
`mixed_commits_erode_auditability` trap by keeping the data fix (FR-600) and the ruler
experiment separate and ordered. Two corrections:

1. **Persist the post-FR-600 window sweep to a committed dump (PRIMARY — auditability).**
   The motivating sweep numbers (BEAT-OFF 2→5, ABSENT 12→9 across ±1→±3) are not on disk
   in any file I could find — only the 12-member (e) list is persisted. The "closed
   unstarted if residual BEAT-OFF ≈ 0" decision is only auditable if the re-run sweep is a
   committed artifact, not a console line. Make persisting the sweep the first AC.

2. **Hold the precision guard as load-bearing, not advisory (endorsed, reinforced).** A
   wider window that lifts recall while dropping precision is admitting wrong-beat (and,
   without correction, wrong-kind) neighbours — the exact failure that makes a looser ruler
   flatter the model. The verdict must report `affect_precision` at ±0 and ±1 side by side
   and treat any precision drop beyond noise as disqualifying, regardless of the recall
   gain. Carry forward FR-599 correction #4: a ±1 neighbour must match op+char+**kind** to
   count, or the tolerance silently admits kind-wrong neighbours.

**Endorsed:** BLOCKED until FR-600 is enforced; closed-unstarted if the residual is ~0;
canonical `main_l7` never mutated (diff-verified); decision-not-change outcome; REQ-YG-020
reuse, no new CAP; the anti-bundling and "set ±1 now" alternatives correctly refuted.

> **Predecessor update (FR-600 enforced 2026-06-26).** The blocker is cleared. FR-600's
> deterministic (e)=12 re-partition landed **0 BEAT-OFF** among the 12 re-classified members
> — but that is only the former-(e) subset, NOT the full miss set, so the "closed-unstarted if
> residual BEAT-OFF ≈ 0" test is **not** yet satisfied. The motivating window sweep (BEAT-OFF
> 2->5, ABSENT 12->9 across ±1->±3) was measured on the *pre*-FR-600 corpus. AC #1 stands:
> the full probe sweep must be re-run on the re-annotated GT and persisted to a committed
> dump before the close-unstarted-vs-proceed decision can be made.

**Frozen scope:** parameterise the match window in a copy/flag (default ±0), score the
re-annotated FR-600 GT at ±0 and ±1 reporting recall AND precision with per-bucket shift
and a persisted sweep, read ≥3 residual genuine-±1 records (op+char+kind shared), and end
in a decision — a named gate-change FR or a recorded "exact matching stays." No mutation of
the canonical gate, no model run.

## Problem

The FR-578 gate matches affect on **exact beat id**. After FR-600 re-anchors the
displaced GT, some residual misses may still be one beat off — a model that reads the
feeling one beat early/late from the (now experiential) anchor. Whether to forgive that is
a *gate* question, and changing the gate to flatter the model is the `downstream_fix`
trap. The only safe path is to measure both numbers (±0 strict vs ±1 tolerant) against the
**re-annotated** GT and let the gap decide, with the change behind a flag so the canonical
gate stays strict until a Judgement promotes it.

## Raw Output Read (measurement / metric-tooling FRs only)

`read_raw_output_first` — this FR changes a scorer, so authority is withheld until this
section cites the BEAT-OFF residual *after FR-600*: ≥3 records where the model's predicted
delta matches op+char+kind on a beat exactly ±1 from the re-annotated GT anchor, read from
the (re-run) FR-599 dump. Each must show the predicted beat id, the GT beat id, and the
shared op/char/kind — proving these are true one-beat displacements, not loosened matches
that would also admit wrong-kind neighbours. If the residual BEAT-OFF count is ~0 after
FR-600, this FR is **closed unstarted** (the re-annotation already absorbed it).

## Proposed Solution

1. **Parameterise the match window** in a *copy* of the L7 scoring path (or a flag on the
   probe), defaulting to ±0 (canonical). Do **not** mutate the canonical `main_l7`.
2. **Score the re-annotated GT (FR-600) at ±0 and ±1**, reporting `affect_recall`,
   `affect_precision`, and the per-bucket shift. Precision must be watched: a wider window
   that lifts recall while dropping precision is admitting false matches, not forgiving
   real displacements.
3. **Decide and stop.** If ±1 lifts recall materially *without* a precision collapse and
   the read confirms genuine one-beat displacements → write a separate, Judged gate-change
   FR. If not → record that exact-beat matching is correct and close.

## Acceptance Criteria

- [x] BLOCKED until FR-600 is enforced; if FR-600 leaves BEAT-OFF residual ≈ 0, this FR is
      closed unstarted with that finding recorded.
- [x] The match window is parameterised in a copy/flag; canonical `main_l7` is **not**
      mutated (verified by diff).
- [x] `affect_recall` AND `affect_precision` reported at ±0 and ±1 on the re-annotated GT,
      with the per-bucket shift; the precision guard is explicit in the verdict.
- [x] ≥3 residual BEAT-OFF records read (predicted beat id, GT beat id, shared op/char/kind)
      proving genuine ±1 displacement before any tolerance is recommended.
      **(N/A — only 1 genuine ±1 displacement exists; the ≥3 bar cannot be met, which is
      precisely the close-unstarted trigger, not a gap.)**
- [x] The outcome is a *decision* — either a named gate-change FR (separately judged) or a
      recorded "exact matching stays" — never a silent loosening of the frozen gate.
      **Decision: exact-beat matching stays.**
- [x] No new CAP; REQ-YG-020 reused. Changelog fragment + diary reflection.

## Enforcement Outcome (2026-06-26)

**Verdict: CLOSED UNSTARTED — exact-beat matching stays; the frozen FR-578 gate is NOT
loosened.** The motivating residual the FR existed to measure has been absorbed by its two
predecessors (FR-600 re-annotation + FR-601 close-op discrimination cue): a +/-1 tolerance
recovers exactly **one** GT delta, far below the >=3 the AC requires before any loosening
may be recommended.

### Method (deterministic, no LLM, frozen gate untouched)

Added a read-only `--sweep` mode to `probe_l7_misses.py` — the copy/flag the Judge
mandated. It imports the frozen `_affect_matches` / `_l7_counts` **read-only** and adds a
windowed greedy matcher (`_windowed_match`, nearest-beat-first so an exact match is always
preferred and a neighbour is taken only when no exact match remains). Window 0 **ties out
to the frozen gate per genre** (asserted) before any wider window is trusted. Canonical
`evaluate.py` diff is **empty** (verified). Correction #4 holds for free: `_affect_matches`
requires op+char+**kind** (kind exact), so a +/-1 neighbour differing in kind is never
admitted. Reproduce: `cd examples/plot_modeller && ../../.venv/bin/python
probe_l7_misses.py --sweep`. Committed dump: `fixtures/affect-licensing/fr602-window-sweep.md`.

### Window sweep (post-FR-600 GT, post-FR-601 predictions; GT deltas=28, pred deltas=49)

| window | affect_recall | affect_precision | recall_hits |
|--------|---------------|------------------|-------------|
| ±0 (frozen) | 0.214 | 0.122 | 6 |
| ±1 | 0.250 | 0.143 | 7 |
| ±2 | 0.321 | 0.184 | 9 |
| ±3 | 0.357 | 0.204 | 10 |

- **BEAT-OFF recoverable at ±1** (recall_hits[1] − recall_hits[0]) = **1**.
- **Precision guard**: precision does NOT collapse at ±1 (0.122 → 0.143, +0.021) — but this
  is moot, because the recall gain is a single delta.

### The one residual ±1 displacement (read)

`historical-fiction-the-salt-road` **GT F1 → PRED F2** (off +1), `open Naima loss`:
- GT F1: "Moussa Keita ... announces a royal salt monopoly ... The small traders will be
  destroyed." (the loss *opens* at the announcement)
- PRED F2: "The council votes to comply. Naima has no leverage ... Everything her father
  built is being taken." (the model read the loss as crystallising one beat later, at the
  compliance vote)

A genuine one-beat-late read — op+char+kind all shared — but a sample of **one** is not
evidence that the gate is systematically too strict. It is the long tail of a 28-delta
corpus, not a fixable ruler artifact.

### Why close, not proceed

The pre-FR-600 sweep that motivated this FR showed BEAT-OFF rising 2→5 across ±1→±3 on the
**displaced** GT. FR-600 re-anchored that displacement at the data boundary (where it
belonged — the `downstream_fix` cure), and FR-601 converted the in-reach kind-confusions to
hits. What remained for FR-602 to forgive is a single tail displacement. Loosening the
frozen ruler to recover one delta would (a) admit wider-window false matches as the corpus
grows for a +0.036 recall gain, and (b) flatter the model against a ruler that is correct as
strict. The honest, Judge-endorsed outcome is to record the measurement and keep ±0.

**Frozen gate:** `evaluate.py` diff empty (verified). **REQ-YG-020** reused, no new CAP.
**Caveat:** predictions are the single post-FR-601 stochastic sample (temp 0.7); the
decision rests on the *structure* of the residual (1 tail displacement), which a different
sample would not change in kind.

## Alternatives Considered

- **Just set the gate to ±1 now.** Refuted: editing the frozen ruler before measuring
  precision impact is the `downstream_fix` trap — it could flatter the model by admitting
  wrong-beat matches. Measure behind a flag first.
- **Fold tolerance into FR-600 (re-annotate AND loosen together).** Refuted: bundling a
  data fix with a ruler change destroys attribution — you could not tell which moved the
  number (`mixed_commits_erode_auditability`). Keep them separate and ordered.
- **Skip — assume exact matching is right.** Refuted by the window-sweep evidence: ~3
  misses *do* shift to BEAT-OFF at ±3, so the question is real and worth one measurement,
  even if the answer is "stay strict."

## Related

- FR-599 probe (window sweep): `examples/plot_modeller/probe_l7_misses.py`
- Frozen gate: `examples/plot_modeller/evaluate.py` (`_match_count`, `_l7_counts`, `main_l7`)
- Predecessor (must run first): FR-600 (GT re-annotation)
