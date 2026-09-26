# Feature Request: Retire `core-test` + Python 3.14 Ceiling

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — operator override of SPLIT (2026-09-26)
**Effort:** 0.5 days
**Requested:** 2026-09-26
**First consumer / first event:** every PR author at the first push
after merge (two unit-suite runs instead of three); the first Python
3.14 user running `pip install yamlgraph`, refused today by
`requires-python = ">=3.11,<3.14"`.
**Research:** in-body alternatives table below; 3.14 probe evidence in
Implementation Status. This is the follow-up FR-918 named ("re-widening
to `<3.15` is gated on a green 3.14 CI leg and verified wheels").
**Judgement:** [judgement](FR-1104-ci-dedup-core-test-and-python-314.judgement.md) — SPLIT,
overruled by the operator (see Operator Decisions).
**Prior art:** [FR-918](FR-918-ci-python-matrix-refresh.md) set the
3.11/3.13 bracket and `<3.14`; this moves the ceiling to 3.14.
[FR-756](FR-756-core-test-isolation.md) created `core-test`; its CI-run
claim is retired here, its collection-time lint is kept.
[FR-759](FR-759-otel-observability-boundary.md) gave `core-test` the
missing-`otel` claim; it moves to the 3.14 leg.
[FR-952](FR-952-optional-extras-must-skip-not-error.md) (Proposed)
planned to extend `core-test`; retargeted to the lean leg.
[FR-934](FR-934-merge-queue-on-main.md) merge queue is dormant (blocked
on a user-owned repo); no queue step here.

## Summary

Every code PR runs `tests/unit/` three times: `test (3.11)`,
`test (3.13)`, and `core-test` (3.13, `-m "not process"`, without the
`otel`/`vision` extras). `core-test` re-runs ~336 of 478 unit test
files already run by `test (3.13)` on the same interpreter. Delete
`core-test`, make the ceiling leg lean (no `otel`/`vision`) so it
carries FR-759's missing-extra claim, and move the ceiling to 3.14.

## Operator Decisions (2026-09-26)

1. **SPLIT overruled.** One FR, one PR. The judge's factual corrections
   (no active merge queue; `vision` omission is lean-install only) are
   folded below.
2. **FR-756 CI run retired.** The separate `-m "not process"` CI run is
   repealed. Kept: the collection-time boundary lint in
   `tests/conftest.py`, which fires on every collection. Accepted loss:
   CI no longer detects a core test that passes only because a process
   test ran first (test-isolation class, FR-1094 territory).
   `pytest tests/unit -m "not process"` stays the local command.

## Proposed Solution

1. **`.github/workflows/workflow.yml`**: delete `core-test`. `test`
   matrix `python-version: ['3.11', '3.14']` (contexts stay
   `test (<version>)`), with `include` adding a per-leg `extras` key:
   3.11 = all current extras incl. `otel,vision`; 3.14 = same minus
   `otel,vision`. Install step uses `.[${{ matrix.extras }}]`. `build`
   and `windows-encoding` stay on 3.13.
2. **`pyproject.toml`**: `requires-python = ">=3.11,<3.15"`; add the
   3.14 classifier.
3. **Tests**: new `tests/unit/test_fr1104_ci_matrix.py` pins the above;
   the 3.13 pins in `test_ci_hardening_consolidation.py` and
   `test_fr934_merge_queue_workflows.py` move to 3.14.
4. **Docs**: `reference/development-operations.md` required checks →
   `test (3.14)`; `reference/otel-observability.md` → the 3.14 leg;
   FR-952 one-line pointer.

### Branch-protection migration (operator, strict protection, no queue)

```bash
gh api repos/:owner/:repo/branches/main/protection/required_status_checks --jq '{strict, contexts}'
# just before squash-merging this PR (its checks emit test (3.11), test (3.14)):
gh api -X PATCH repos/:owner/:repo/branches/main/protection/required_status_checks \
  -F strict=true -f 'contexts[]=commitlint' -f 'contexts[]=test (3.11)' -f 'contexts[]=test (3.14)'
gh api repos/:owner/:repo/branches/main/protection/required_status_checks --jq '{strict, contexts}'
```

Open PRs still emitting `test (3.13)` must rebase (strict already
forces this). Nothing else merges between the PATCH and this merge.

## Acceptance Criteria

- [ ] AC-01: 3.14 probe — lean-leg extras install on Python 3.14,
      `pip check` clean, unit suite green; recorded in Implementation
      Status. A wheel gap or red suite blocks the FR (no extra dropped,
      no test skipped).
- [ ] AC-02: no `core-test` job; matrix emits exactly `test (3.11)`,
      `test (3.14)`.
- [ ] AC-03: 3.14 extras exclude `otel` and `vision`; 3.11 extras
      include both.
- [ ] AC-04: `requires-python = ">=3.11,<3.15"`; classifiers 3.11–3.14.
- [ ] AC-05: `tests/unit/test_fr1104_ci_matrix.py` RED then GREEN.
- [ ] AC-06: both CI legs green at the existing `--cov-fail-under=80`.
- [ ] AC-07: docs updated; FR-952 pointer added.
- [ ] AC-08: branch protection migrated; before/after readback recorded.
- [ ] AC-09: changelog fragment; diary entry.

Out of scope: the 3.11 floor, coverage threshold/flags, `-n auto`,
`constraints/dev-py312.txt`, other workflow pins, merge queue.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Shrink `core-test` to the two OTEL files | REJECTED — a third full install for two files; the lean leg carries the claim for free. |
| A2 | Keep `core-test`, move it to 3.14 | REJECTED — still three suite runs; 3.14 behind a non-required check. |
| A3 | Lean leg runs `not process` and `process` as two invocations | REJECTED by operator decision 2 (FR-756 CI run retired). |
| A4 | Three legs 3.11/3.13/3.14 | REJECTED — FR-918: +50% cost for a bracketed version. |
| A5 | Split into two FRs (judge verdict) | OVERRULED by operator decision 1. |

## Implementation Status

_In progress._
