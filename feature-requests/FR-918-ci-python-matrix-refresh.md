# Feature Request: CI Python Matrix Refresh (Floor + Ceiling Honesty)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the first user on Python 3.13 whose
interpreter is exercised by CI before the next release tag; concretely,
the first PR after merge runs `test (3.13)` instead of `test (3.12)`.
**Research:** split from [FR-917](FR-917-ci-python-matrix-and-doc-only-skip.md)
per its judgement
([FR-917 judgement](FR-917-ci-python-matrix-and-doc-only-skip.judgement.md),
D-1); in-body dispositioned alternatives table below.
**Prior art:** FR-917 is the split parent (superseded, no authority);
FR-919 is the sibling split covering the orthogonal doc-only-skip
concern — no overlap with this FR's matrix/support-claim scope. No
earlier FR touches the CI Python matrix or `requires-python`.

## Summary

The CI `test` matrix pins Python 3.11 and 3.12. The package classifier
list claims 3.13 support and `requires-python = ">=3.11,<3.15"` allows
3.14 installs — neither interpreter is ever tested. Refresh the matrix
to test the floor and ceiling of the declared range (bracket policy),
and narrow the declared range so no install-allowed interpreter sits
outside the tested bracket.

## Value Statement

CI directly tests the floor and ceiling of the declared support range;
classified intermediate versions (3.12) are supported by bracket
policy, and no install-allowed interpreter sits outside the tested
bracket — the support metadata stops being an untested claim
(detection_without_enforcement).

## Problem

1. `.github/workflows/workflow.yml` `test` matrix is `['3.11', '3.12']`;
   `core-test` and `security.yml` pin 3.12. Python 3.13 (stable since
   2024-10) is classified in `pyproject.toml` but never tested.
2. `requires-python = ">=3.11,<3.15"` permits installation on Python
   3.14, which has no classifier, no CI leg, and unverified dependency
   wheels — an install-allowed but untested envelope (FR-917 judgement
   R-2 contradiction).
3. Branch protection requires exactly `commitlint`, `test (3.11)`,
   `test (3.12)` (verified via API 2026-08-30). A matrix change orphans
   `test (3.12)` and PRs hang on an "Expected" check unless protection
   is migrated with an explicit, recorded procedure (judgement R-3).

## Ideal Result

The declared support contract is bounded by the tested bracket:
`requires-python = ">=3.11,<3.14"`, classifiers 3.11/3.12/3.13, matrix
legs 3.11 (floor) and 3.13 (ceiling), intermediate 3.12 supported by
bracket policy without a dedicated leg, single-version jobs on the
ceiling, and branch protection contexts matching the matrix — migrated
by the operator in a recorded, verified sequence.

## Support policy (resolves judgement R-2, option 2)

**Python 3.14 is unsupported until tested.** `requires-python` narrows
from `<3.15` to `<3.14` so untested interpreters are not
install-allowed. Re-widening to `<3.15` is a follow-up FR gated on a
green 3.14 CI leg and verified dependency wheels (langgraph,
pydantic-core).

Version-to-job mapping (judgement AC-04):

| Job | Version | Rationale |
|---|---|---|
| `test` matrix | 3.11, 3.13 | floor + ceiling of `requires-python` |
| `core-test` | 3.13 | ceiling; fast signal on the newest supported |
| `security` (pip-audit) | 3.13 | ceiling; matches the env users get |
| `build` (tag releases) | 3.13 | ceiling; wheel is version-independent |
| `constraints/dev-py312.txt` | unchanged | FR-761 artifact; py313 regeneration is a follow-up, not scoped |

3.12 remains classified and supported (inside the range) but loses its
dedicated leg: it is bracketed by tested 3.11 and 3.13, and the
constraints artifact still pins a reproducible 3.12 env.

## Proposed Solution

1. `.github/workflows/workflow.yml`: `test` matrix
   `['3.11', '3.12']` → `['3.11', '3.13']`; `core-test` python
   `3.12` → `3.13`; release `build` job python `3.12` → `3.13`
   (judgement R-2).
2. `.github/workflows/security.yml`: python `3.12` → `3.13`.
3. `pyproject.toml`: `requires-python = ">=3.11,<3.14"`.
4. `CLAUDE.md` Branch Protection table: `test (3.12)` → `test (3.13)`;
   Reproducible Dependency Governance section updated to state that
   `constraints/dev-py312.txt` remains the FR-761 Python 3.12
   reproducibility artifact (no longer the exact CI single-version
   env) and that a py313 constraints artifact is a follow-up, out of
   scope here (judgement R-4).
5. Changelog fragment (`ci` scope), diary reflection.

### Branch-protection migration (judgement R-3, C-2)

Actor: the operator (repo admin). Timing: immediately after the change
lands on `main` (admin direct push — the default single-dev flow;
`enforce_admins` is off, so the orphaned context cannot block the
landing itself).

```bash
# 1. Land the matrix change on main (admin push).
# 2. Read current strict value (read-modify-write; preserve strict):
gh api repos/:owner/:repo/branches/main/protection/required_status_checks --jq '{strict, contexts}'
# 3. Migrate contexts, explicitly preserving strict=true:
gh api -X PATCH repos/:owner/:repo/branches/main/protection/required_status_checks \
  -F strict=true \
  -f 'contexts[]=commitlint' -f 'contexts[]=test (3.11)' -f 'contexts[]=test (3.13)'
# 4. Verify and record BOTH strict and contexts:
gh api repos/:owner/:repo/branches/main/protection/required_status_checks --jq '{strict, contexts}'
```

The step-4 output (containing both `strict` and `contexts`) is pasted
into this FR's implementation status (judgement R-3). Open
automation PRs still emit `test (3.12)` from their stale merge refs;
the existing strict up-to-date rule already forces them to update with
`main`, after which they emit `test (3.13)` and satisfy the new
contexts. No overlap window is needed.

### Human review gate (judgement R-6, C-4)

CI workflow edits and the branch-protection mutation are
enforcement-infrastructure changes: both require explicit operator
review before landing. The `gh api PATCH` is executed by the operator,
not by automation.

## Acceptance Criteria

- [ ] `test` matrix is `['3.11', '3.13']`; `core-test`, `security.yml`,
      and the release `build` job use 3.13.
- [ ] `pyproject.toml` `requires-python = ">=3.11,<3.14"`; classifiers
      unchanged (3.11/3.12/3.13) — every classified version is inside
      the tested bracket (3.12 supported by bracket policy, no
      dedicated leg).
- [ ] Python 3.14 status stated explicitly: unsupported until a green
      CI leg exists (this section); no `<3.15` claim survives.
- [ ] Version-to-job mapping table present (AC-04) and matches the
      workflows byte-for-byte.
- [ ] Required contexts migrated to `commitlint`, `test (3.11)`,
      `test (3.13)` by the operator via read-modify-write preserving
      `strict: true`; verification output recording both `strict` and
      `contexts` pasted into this FR.
- [ ] `CLAUDE.md` Branch Protection table updated; Reproducible
      Dependency Governance prose corrected re: py312 constraints
      artifact scope (judgement R-4).
- [ ] Witness: first post-merge PR shows green `test (3.11)` and
      `test (3.13)` checks; run link cited.
- [ ] Operator has explicitly reviewed the workflow diff and executed
      the protection PATCH (human review gate).
- [ ] Changelog fragment + diary reflection.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Test 3.14, keep `<3.15` (R-2 option 1) | DEFERRED — no classifier, unverified dependency wheels, third install cost; follow-up FR once wheels verified. |
| Keep `<3.15` as "allowed but non-classified envelope" (R-2 option 3) | REJECTED — install-allowed-but-untested is exactly the untested-claim shape this FR exists to remove. |
| Matrix `['3.12', '3.14']`, drop 3.11 | REJECTED — raising the floor is a user-facing support-contract change; separate FR. |
| Three-leg matrix `['3.11','3.12','3.13']` | REJECTED — 3.12 is bracketed by tested floor and ceiling; a third leg buys marginal signal for +50% matrix cost. |
| Pre-merge protection PATCH | REJECTED — removing `test (3.12)` before the workflow change lands would strand open PRs that still emit it; post-land migration with the strict up-to-date rule needs no overlap. |

## Related

- [FR-917](FR-917-ci-python-matrix-and-doc-only-skip.md) (parent, split)
- [FR-917 judgement](FR-917-ci-python-matrix-and-doc-only-skip.judgement.md) (R-2, R-3, R-6, AC-02–AC-04)
- FR-919 (sibling: doc-only skip)
- FR-761 (constraints artifact)
- [.github/workflows/workflow.yml](../.github/workflows/workflow.yml),
  [.github/workflows/security.yml](../.github/workflows/security.yml)

## Judgement (date)
