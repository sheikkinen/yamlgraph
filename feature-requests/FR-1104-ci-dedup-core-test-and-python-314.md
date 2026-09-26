# Feature Request: CI Dedup (Fold `core-test` into the Matrix) + Python 3.14 Ceiling

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-26
**First consumer / first event:** (1) every PR author, at the first
push after merge — CI runs the unit suite twice instead of three times;
(2) the first user on Python 3.14 who runs `pip install yamlgraph` and
today gets a resolver refusal from `requires-python = ">=3.11,<3.14"`.
**Research:** in-body dispositioned alternatives table below (FR-889 /
FR-918 style). This FR is the follow-up FR-918 named: "Re-widening to
`<3.15` is a follow-up FR gated on a green 3.14 CI leg and verified
dependency wheels."
**Prior art:**
[FR-918](FR-918-ci-python-matrix-refresh.md) — set the 3.11/3.13 bracket
and narrowed to `<3.14`; this FR moves the ceiling to 3.14 under the same
bracket policy and migration procedure.
[FR-917](FR-917-ci-python-matrix-and-doc-only-skip.md) — split parent;
its "add 3.14 as third leg" alternative was DEFERRED for install cost;
this FR replaces a leg rather than adding one.
[FR-756](FR-756-core-test-isolation.md) (Enforced) — created `core-test`;
this FR retires the job but keeps its mechanical enforcement (the
collection-time boundary lint), see Disposition of FR-756.
[FR-759](FR-759-otel-observability-boundary.md) (Enforced) — gave
`core-test` its missing-`otel`-extra claim; this FR moves that claim to
the 3.14 leg unchanged.
[FR-952](FR-952-optional-extras-must-skip-not-error.md) (Proposed) —
plans to extend `core-test` as the minimal-install gate; this FR
redirects that plan to the lean matrix leg, implements none of it.
[FR-934](FR-934-merge-queue-on-main.md) — merge queue; required contexts
must report on `merge_group`, which shapes the migration sequence.
[FR-919](FR-919-ci-doc-only-skip.md) — docs-only skip; the no-op step
pattern is preserved untouched.

## Summary

Every code PR runs `tests/unit/` three times: `test (3.11)`,
`test (3.13)`, and `core-test` (3.13, `-m "not process"`, no `otel` /
`vision` extras). `core-test` re-runs ~70% of `test (3.13)`'s files, on
the same interpreter, with nearly the same extras. The merge queue then
runs all three again. Separately, Python 3.14 (stable since 2025-10) is
install-refused.

Fold `core-test`'s one unique claim (tests pass with optional extras
absent) into the matrix by making the ceiling leg lean, delete the
`core-test` job, and move the ceiling from 3.13 to 3.14.

## Value Statement

PR authors get the same signal from roughly a quarter less unit-suite
compute per CI run (and per merge-queue run), and Python 3.14 users can
install yamlgraph.

## Problem

1. **Duplicate test set.** `.github/workflows/workflow.yml`:
   - `core-test`: py3.13, extras `dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master`,
     `pytest tests/unit -m "not process" -q --no-cov`.
   - `test (3.13)`: py3.13, same extras + `otel,vision`,
     `pytest tests/unit/ -v --cov=yamlgraph --cov-fail-under=80`.
   - `test (3.11)`: same as `test (3.13)` on 3.11.

   The `process` marker deselects 142 of 478 top-level unit test
   files (`rg -l 'pytest.mark.process' tests/unit`, 2026-09-26); the
   other ~336 run in `core-test` after already running in
   `test (3.13)` on the same interpreter. `core-test`'s only claims
   not already covered by
   `test (3.13)` are: (a) FR-759 — OTEL disabled/missing-extra tests
   collect and pass when `opentelemetry-sdk` is absent; (b) FR-756 —
   the core subset passes with process tests deselected.
2. **Merge queue multiplier.** FR-934's `merge_group` trigger
   short-circuits the change filter, so all three suites run again per
   queued PR — six unit-suite runs per merged code PR.
3. **3.14 refused.** `requires-python = ">=3.11,<3.14"` (FR-918 AC-06)
   makes `pip install yamlgraph` fail on 3.14, a year after its release
   and one month before 3.15. FR-918 made 3.14 support conditional on a
   green CI leg; nobody has filed that leg.

## Ideal Result

Each code PR runs the unit suite once per supported-bracket endpoint and
never twice on the same interpreter. The floor leg (3.11) installs every
extra and proves the enabled paths; the ceiling leg (3.14) installs the
extras minus `otel` and `vision` and proves the missing-extra paths.
`requires-python = ">=3.11,<3.15"`, classifiers 3.11–3.14, and branch
protection requires `test (3.11)` and `test (3.14)`.

## Proposed Solution

1. **`.github/workflows/workflow.yml`**
   - Delete the `core-test` job.
   - `test` matrix → `include`-based, same job name so contexts stay
     `test (<version>)`:

     ```yaml
     strategy:
       matrix:
         include:
           - python-version: '3.11'
             extras: dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master,otel,vision
           - python-version: '3.14'
             # FR-759: lean leg proves missing-extra paths (otel, vision absent)
             extras: dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master
     ```

     Install step: `pip install -e ".[${{ matrix.extras }}]"`. Test,
     lint, lock/unlock and docs-only no-op steps unchanged.
   - `build` (tags only) and `windows-encoding` stay on 3.13 —
     wheel is version-independent; the Windows job's claim is the codec,
     not the interpreter.
2. **`pyproject.toml`**: `requires-python = ">=3.11,<3.15"`; add
   classifier `Programming Language :: Python :: 3.14`. 3.12 and 3.13
   stay classified (bracketed, FR-918 policy).
3. **Docs**: `reference/development-operations.md` required-checks row
   → `commitlint`, `test (3.11)`, `test (3.14)`;
   `reference/otel-observability.md` `core-test` sentence → the 3.14
   lean leg.
4. **Changelog fragment** (`ci` scope) + diary.

### Disposition of FR-756 (`core-test` isolation)

FR-756's enforcement mechanism is the collection-time source scan in
`tests/conftest.py`, which fails any unmarked module referencing
`examples/`, `.chaplain/` or `scripts/`. It runs on every pytest
collection, so both remaining legs keep enforcing it. What is lost is
only a separate CI run proving the core subset passes when process tests
are deselected, i.e. that no core test depends on side effects of a
process test. That order-dependence class is FR-1094 / test-isolation
territory, and `pytest tests/unit -m "not process"` stays the documented
local command. If the Judge rules this claim must stay a CI gate, the
fallback is Alternative A3 below, not keeping the full duplicate job.

### Disposition of FR-952 (Proposed)

FR-952 AC-04 ("the `core-test` CI job runs the deselected suite") is
retargeted to the `test (3.14)` lean leg. FR-952 is not implemented
here; its FR text is amended with a one-line pointer only.

### Branch-protection migration (FR-918 procedure, adapted for FR-934)

With the merge queue, this PR cannot merge while `test (3.13)` is
required, because its own workflow no longer emits that context.
Operator-executed sequence (repo admin), preserving `strict`:

```bash
# 0. Record current state
gh api repos/:owner/:repo/branches/main/protection/required_status_checks --jq '{strict, contexts}'
# 1. Just before enqueue: drop test (3.13), keep strict
gh api -X PATCH repos/:owner/:repo/branches/main/protection/required_status_checks \
  -F strict=true -f 'contexts[]=commitlint' -f 'contexts[]=test (3.11)'
# 2. Enqueue / merge this PR (merge_group emits test (3.11), test (3.14))
# 3. Immediately after merge: add test (3.14)
gh api -X PATCH repos/:owner/:repo/branches/main/protection/required_status_checks \
  -F strict=true -f 'contexts[]=commitlint' -f 'contexts[]=test (3.11)' -f 'contexts[]=test (3.14)'
# 4. Verify and record BOTH strict and contexts in Implementation Status
gh api repos/:owner/:repo/branches/main/protection/required_status_checks --jq '{strict, contexts}'
```

The step-1→3 window requires only `commitlint` and `test (3.11)`. No
other PR may be enqueued during it. The workflow edit and the PATCH
are enforcement-infrastructure changes and need operator review. The
PATCH is run by the operator, not by an agent.

## Acceptance Criteria

- [ ] AC-01: **3.14 install probe before any workflow edit.** In a fresh
      Python 3.14 venv, `pip install -e ".[dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master]"`
      (with `requires-python` locally widened) succeeds, and
      `pytest tests/unit -q --no-cov -n auto` exits 0. The log is cited
      in Implementation Status. If any extra has no 3.14 wheel or the
      suite is red, stop and report the blocker; do not drop the extra
      or skip tests to get green.
- [ ] AC-02: `workflow.yml` has no `core-test` job; the `test` matrix
      emits exactly `test (3.11)` and `test (3.14)`.
- [ ] AC-03: The 3.14 leg's install line contains neither `otel` nor
      `vision`; the 3.11 leg's contains both.
- [ ] AC-04: FR-759 witness preserved. On the 3.14 leg,
      `tests/unit/test_otel_observability.py` disabled/missing-extra
      tests run and pass (not skip). Cited from the CI log.
- [ ] AC-05: Both legs pass `--cov-fail-under=80`. If the lean leg falls
      below it, stop and report; the threshold is not lowered in this FR.
- [ ] AC-06: `pyproject.toml`: `requires-python = ">=3.11,<3.15"`;
      classifiers 3.11, 3.12, 3.13, 3.14.
- [ ] AC-07: The FR-756 collection-time boundary lint is unchanged, and a
      synthetic unmarked module referencing `.chaplain/` still fails
      collection (existing FR-756 test green on both legs).
- [ ] AC-08: `reference/development-operations.md` and
      `reference/otel-observability.md` updated; no remaining doc claims
      a `core-test` CI job (`rg -n 'core-test' reference/ CLAUDE.md` is
      empty or history-only).
- [ ] AC-09: Branch protection migrated per the sequence above; step-0
      and step-4 outputs (both `strict` and `contexts`) recorded in
      Implementation Status.
- [ ] AC-10: The first post-merge PR shows green `test (3.11)` and
      `test (3.14)` and no `core-test` check. Run link cited.
- [ ] AC-11: FR-952 carries a one-line pointer retargeting AC-04 to the
      lean leg.
- [ ] AC-12: Changelog fragment in `changelog/unreleased/`; diary entry.

## Constraints

| # | Constraint | Kind |
|---|---|---|
| C-1 | Do not raise or drop the 3.11 floor. | GATE |
| C-2 | Do not change `--cov-fail-under`, add `-n auto`, or drop `-v`. These are separate CI-speed/threshold concerns (80 vs 85 addopts mismatch noted, not fixed). | GATE |
| C-3 | Do not regenerate or rename `constraints/dev-py312.txt` (FR-918 C-5 carried). | GATE |
| C-4 | Do not change `build`, `windows-encoding`, `security.yml`, or `commitlint.yml` interpreter pins. | GATE |
| C-5 | Branch-protection PATCH is operator-executed with recorded before/after output. | GATE |
| C-6 | No extra is dropped from the 3.14 leg except `otel` and `vision` (the FR-759/FR-781 missing-extra claim). A 3.14 wheel gap blocks the FR; it is not absorbed. | GATE |

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Keep `core-test`, restrict it to `tests/unit/test_otel_observability.py` + `test_fr363_per_node_otel_scoping_red.py` | REJECTED. Removes the duplication, but keeps a third install (~full dependency resolve) for 2 files, and drops the missing-`vision` angle. The lean leg gives the same claim at zero extra install. |
| A2 | Keep `core-test` unchanged, move it to 3.14 as the 3.14 probe; matrix stays 3.11/3.13 | REJECTED. Still three full-suite runs per PR (the user's complaint), and 3.14 would sit behind a non-required check while being claimed as supported. |
| A3 | Lean 3.14 leg runs two pytest invocations: `-m "not process"` then `-m process` with `--cov-append` | FALLBACK only if the Judge requires FR-756's deselected-run claim in CI. Each test still runs once per leg; the cost is workflow complexity. |
| A4 | Matrix `['3.11','3.13','3.14']` | REJECTED. FR-918 A-row (three legs = +50% cost for a bracketed version). |
| A5 | Drop 3.11, matrix `['3.13','3.14']` | REJECTED. Support-contract change; 3.11 is upstream-supported until 2027-10 (FR-918, FR-917 precedent). |
| A6 | Skip the merge-queue re-run | OUT OF SCOPE. The queue tests the merged result, and FR-934 requires that. |
| A7 | Make the 3.11 leg lean instead of 3.14 | REJECTED. The ceiling leg is where new-interpreter wheel gaps appear. A lean leg with fewer compiled extras is less fragile there, and the fully-extras leg stays on the best-supported interpreter. |

## Related

- `.github/workflows/workflow.yml` — `core-test`, `test` jobs
- `pyproject.toml` — `requires-python`, classifiers
- `tests/conftest.py` — FR-756 boundary lint
- `reference/development-operations.md` — required checks table
- `reference/otel-observability.md` — `core-test` reference
