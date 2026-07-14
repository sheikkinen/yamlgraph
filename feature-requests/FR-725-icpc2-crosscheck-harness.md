# Feature Request: FR-725 ICPC-2 Labeled Crosscheck Harness (Phase 3)

**Priority:** MEDIUM
**Type:** Instrumentation
**Status:** In Progress
**Effort:** 1 day
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — scope frozen with 4 findings; raw-read gate satisfied by inheritance
**Parent:** FR-722 — see `examples/icpc-2-rfe/PLAN.md`
**Blocks:** FR-726 (verdict stability — may not be judged without this
harness's baseline numbers)

## Problem

Per-cluster verdicts vary run-to-run: before verdict discipline, three
HP-36 runs produced three different 0.98 primaries (A13/K86/K22); after
discipline the fixture stabilized, but nothing MEASURES stability or
correctness continuously. The per-run archive
(`logs/icpc2-rfe/*.result.json`) exists but has no consumer — drift is
only caught when a human happens to look (that is how every finding so
far was made). Measurement must precede mitigation
(read_raw_output_first; FR-711 precedent: instrument before verdict).

## Proposed Solution

- `examples/icpc-2-rfe/data/labeled/`: committed labeled fixtures —
  transcript + expected outcome (`primary_any_of`, `must_include`,
  `must_not_include`, `low_confidence_expected`), each label carrying a
  one-line rationale. Seed set: the FR-722 field-run transcripts
  (cough+fever, back pain+sick note, parking permit, tiredness+mood,
  diabetic glucose, HP-36) — labels encode phase-1 truth and flip with
  phase 2 (HP-36 label change is FR-724's acceptance evidence).
- `crosscheck.py` (python, LLM-free): evaluate archived result JSONs
  against labels → per-fixture pass/fail + drift report; `--runs N`
  mode invokes classify.sh N times and reports primary-agreement rate
  per fixture.
- Key-guarded slow pytest wrapper so CI can run the harness on demand,
  skipping cleanly without keys.

## Acceptance Criteria

- [ ] AC-01 Six labeled fixtures with rationales; harness passes on a
      fresh phase-1 run.
- [ ] AC-02 Agreement report: N-run primary/verdict agreement per
      fixture, machine-readable (JSON) + human summary.
- [ ] AC-03 Harness is LLM-free given existing archives (evaluation
      decoupled from generation); classifier behavior unchanged.
- [ ] AC-04 Baseline documented in the FR: agreement rates for the six
      fixtures at N≥5 — the numbers FR-726 must beat.
- [ ] AC-05 Fragment + diary + REQ under CAP-203.

## Constraints

1. No classifier changes — pure instrumentation.
2. Labels are synthetic/non-clinical, rank-tolerant (`primary_any_of`),
   never single-code brittle where the judgement was genuinely tied.

## Judgement (2026-07-14)

**Verdict: APPROVED.** This is a measurement FR, so the Scripture's
raw-read gate applies — and it is satisfied by inheritance: the six
seed fixtures ARE the FR-722 field runs (2–6, plus HP-36 runs 7–8),
each already read end-to-end with cited surprises (case-folded spans,
duplicate cluster votes, editing-by-omission, verdict inflation). The
labels encode those readings; no label may be written for a transcript
whose raw output has not been read — that rule extends to any future
fixture added to the set.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | Baseline cost unstated: 6 fixtures × N=5 runs × 33 clusters ≈ 990 LLM calls | Acknowledged and accepted (≈ 3–5 min, azure); `--runs N` is explicitly slow + key-guarded; default harness mode consumes EXISTING archives at zero LLM cost |
| F2 | Fixture→archive mapping relies on classify.sh's basename keying; stdin runs key as "stdin" and are unattributable | Labeled fixtures MUST be files under `data/labeled/`; the runner's basename convention is the join key; harness rejects (does not guess) archives it cannot attribute |
| F3 | "Statistically meaningful" (FR-726 AC-01) invites stats theatre at n=5 | The harness reports raw counts (k-of-n agreement per fixture) and refuses to compute significance; FR-726's judge interprets counts. No p-values on n=5 |
| F4 | Label freshness across phases: HP-36's phase-1 truth (low_confidence) flips when FR-724 lands | Labels carry a `valid_for_components` field; the harness skips (loudly, named) labels whose coverage assumption doesn't match the catalog's declared components — the FR-724/725 landing-order race resolves itself |

Additional pins: REQ under CAP-203 (id verified free at enforce);
fragment (feat) + diary; harness lives in `examples/icpc-2-rfe/`
(example-scoped tooling, not framework — no yamlgraph/ changes).

**Out of scope (purge list):** any classifier/prompt/reducer change,
significance testing, CI-blocking gates (advisory report only until a
future FR argues for a gate with data), clinical validity claims.
