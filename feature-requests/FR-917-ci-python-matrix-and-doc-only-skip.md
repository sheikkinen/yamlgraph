# Feature Request: CI Python Matrix Refresh + Doc-Only PR Test Skip

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Split — superseded by [FR-918](FR-918-ci-python-matrix-refresh.md) (matrix/support-claim) and [FR-919](FR-919-ci-doc-only-skip.md) (doc-only skip), per [judgement](FR-917-ci-python-matrix-and-doc-only-skip.judgement.md) D-1/D-2. No implementation authority under this FR.
**Prior art:** FR-918 and FR-919 are this FR's own split children (judgement D-1/D-2), not competing precedent; no earlier FR addresses CI path filtering or the Python matrix.
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the next doc-only PR (diary entry, FR
edit, changelog fragment) — its `test` matrix jobs skip instead of
burning ~2× full-suite minutes; and the first user on Python 3.13 whose
interpreter is finally exercised by CI before release.
**Research:** in-body dispositioned alternatives table (FR-889 style), below.

## Summary

The CI `test` matrix pins Python 3.11 and 3.12 — both old (3.13 has been
stable since 2024-10; 3.14 since 2025-10). The newest interpreter the
package *claims* to support (classifier `3.13`, `requires-python <3.15`)
is never tested. Separately, every PR — including doc-only PRs — runs
`core-test`, two full matrix `test` jobs, and `security`, though no
Python file changed.

## Value Statement

CI validates the interpreters users actually run, and doc-only PRs
(the majority under the diary/FR/changelog gates) stop paying ~3 full
test-job installs per push.

## Problem

1. **Stale matrix.** `.github/workflows/workflow.yml` `test` job:
   `python-version: ['3.11', '3.12']`. `pyproject.toml` declares
   `requires-python = ">=3.11,<3.15"` and a `3.13` classifier. CI never
   runs 3.13 — the classifier is an untested claim (Commandment 6:
   detection_without_enforcement — remove the claim or gate it).
2. **No path awareness.** `workflow.yml` triggers on all `pull_request`
   events with no path conditions. A PR touching only `docs/diary/*.md`
   installs the full extras set three times (core-test + 2 matrix legs)
   plus `security`'s pip-audit env.
3. **Branch protection coupling.** Required contexts are exactly
   `commitlint`, `test (3.11)`, `test (3.12)` (verified via API
   2026-08-30). Any matrix change silently orphans the old contexts and
   PRs hang on "Expected" checks unless protection is updated in the
   same motion.

## Ideal Result

CI tests the floor and the ceiling of the declared support range
(3.11 and 3.13), the classifier list is honest, doc-only PRs complete
their required checks in seconds via job-level skips that branch
protection counts as passing, and branch protection contexts match the
matrix — updated atomically with the merge.

## Proposed Solution

### 1. Matrix refresh (floor + ceiling)

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.13']
```

- 3.11 stays: it is the `requires-python` floor; dropping it is a
  support-contract change out of scope here.
- 3.12 → 3.13: test the newest *declared* interpreter. 3.14 is allowed
  by `<3.15` but has no classifier and unverified dependency wheels
  (langgraph/pydantic-core); deferred — see Alternatives.
- `core-test` bumps `3.12` → `3.13` for the same reason.
- `security.yml` bumps to `3.13` (matches the env users get).
- `constraints/dev-py312.txt` (FR-761) stays as-is this FR; a follow-up
  may add a `dev-py313.txt` regeneration — noted, not scoped.

### 2. Doc-only skip via job-level `if` (not workflow `paths-ignore`)

Workflow-level `paths-ignore` leaves required checks stuck in
"Expected" and blocks automation PRs. Job-level skip reports
`skipped`, which branch protection treats as passing.

Add a cheap first job to `workflow.yml`:

```yaml
changes:
  runs-on: ubuntu-latest
  outputs:
    code: ${{ steps.filter.outputs.code }}
  steps:
    - uses: actions/checkout@v4
    - uses: dorny/paths-filter@v3
      id: filter
      with:
        filters: |
          code:
            - '!(**/*.md)'
            - '!docs/**'
            - '!changelog/**'
            - '!feature-requests/**'
```

Then gate the expensive jobs:

```yaml
core-test:
  needs: changes
  if: needs.changes.outputs.code == 'true'
test:
  needs: changes
  if: needs.changes.outputs.code == 'true'
```

Conservative allowlist: only `*.md`, `docs/`, `changelog/`,
`feature-requests/` count as docs. `prompts/*.yaml`, `graphs/*.yaml`,
`capabilities/*.yaml`, workflows, and scripts are all code — any such
file in the diff runs the full suite. `security.yml` gets the same
gate (pip-audit output is a pure function of `pyproject.toml`).

### 3. Branch protection update (same motion as merge)

```bash
gh api -X PATCH repos/:owner/:repo/branches/main/protection/required_status_checks \
  -f 'contexts[]=commitlint' -f 'contexts[]=test (3.11)' -f 'contexts[]=test (3.13)'
```

Executed by the operator/admin immediately after merge; documented in
the FR implementation status.

## Acceptance Criteria

- [ ] `test` matrix is `['3.11', '3.13']`; `core-test` and
      `security.yml` use 3.13.
- [ ] Doc-only PR (fixture: a PR touching only a `docs/diary/*.md`
      file) shows `core-test`, both `test` legs, and `security` as
      *skipped*, and branch protection reports the PR mergeable.
- [ ] Mixed PR (md + py) runs the full suite — witness run cited.
- [ ] Required status check contexts updated to `test (3.11)`,
      `test (3.13)`; verified via API and recorded in this FR.
- [ ] Changelog fragment added (`ci` scope).
- [ ] Diary reflection added.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Workflow-level `paths-ignore` | REJECTED — required checks stay "Expected", blocking automation (non-admin) PRs; job-level skip is the only shape branch protection counts as passing. |
| Matrix `['3.12', '3.14']`, drop 3.11 | REJECTED here — raising the floor changes `requires-python`, a user-facing support contract; separate FR if desired. |
| Add 3.14 as third leg | DEFERRED — allowed by `<3.15` but no classifier and unverified dependency wheels; adds a third install cost. Candidate follow-up once deps are verified. |
| `git diff` shell step instead of `dorny/paths-filter` | REJECTED — hand-rolled base-ref resolution for PR/push/tag events reimplements what the action does; the action is pinned and widely audited. |
| Skip via commit-message tag (`[skip ci]`) | REJECTED — pushes the decision to authors; path facts are mechanical (substance_over_presence). |

## Related

- [.github/workflows/workflow.yml](../.github/workflows/workflow.yml)
- [.github/workflows/security.yml](../.github/workflows/security.yml)
- `pyproject.toml` `requires-python = ">=3.11,<3.15"`
- FR-761 (constraints artifact — py312 pin untouched this FR)
- CLAUDE.md § Branch Protection (required contexts table needs the
  same update)

## Judgement (date)
