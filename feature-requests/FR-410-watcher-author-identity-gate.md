# Feature Request: FR-410 enforce watcher git author identity and CI author gate

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-19
**Judged:** 2026-05-19

## Summary

Fix GitHub issue #407 by hardening watcher commit authorship at runtime and adding a CI gate that rejects PR commit ranges containing blocked placeholder identities (for example `Test <test@test.com>`).

## Value Statement

This closes a recurring provenance and auditability failure where automation-generated commits use placeholder identity and reach mainline history. The fix adds defense in depth:

1. Runtime boundary enforcement in watcher commit action.
2. Merge boundary enforcement in CI.

## Problem

Issue #407 reports that the watcher daemon commits with placeholder identity `Test <test@test.com>` instead of the operator's configured git identity.

Current gaps:

1. The watcher commit action does not explicitly source and enforce identity from repository git config before commit.
2. CI has no dedicated gate to block PRs containing commits from known placeholder identities.

## Objectives

1. Ensure watcher commit subprocess always uses canonical git identity from repo/worktree git config.
2. Fail fast when git identity is missing or blocklisted.
3. Add CI `author-identity-gate` to reject blocked identities in PR commit range.
4. Keep scope minimal and deterministic.

## Constraints

1. No fallback to synthetic/default identity.
2. Deterministic checks only (git config, git log, shell matching).
3. Preserve existing workflow topology; add one focused gate.
4. Avoid unrelated watcher pipeline refactors.

## Proposed Solution

### Runtime fix: watcher commit action

Update `.chaplain/actions/git_commit_action.py`:

1. Resolve `user.name` and `user.email` via git config in the target `cwd`.
2. Validate both values are present and non-empty.
3. Reject blocklisted identities (minimum initial set: `Test`, `test@test.com`).
4. Pass explicit environment to `git commit` subprocess:
   - `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`
   - `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`
5. Return configured error event when validation fails.

### Pipeline fix: CI author identity gate

Update `.github/workflows/commitlint.yml`:

1. Add job `author-identity-gate` for pull requests.
2. Scan `BASE_SHA..HEAD_SHA` using `git log --format='%an|%ae'`.
3. Fail when blocklisted author name/email is present.
4. Keep gate separate from `copilot-trailer-gate` for clear diagnostics.

## Acceptance Criteria

- [x] **AC-01:** Watcher commit action fails when git `user.name` is missing.
- [x] **AC-02:** Watcher commit action fails when git `user.email` is missing.
- [x] **AC-03:** Watcher commit action fails on blocklisted identity (`Test` / `test@test.com`).
- [x] **AC-04:** Valid identity is propagated to commit subprocess as author+committer env variables.
- [x] **AC-05:** `author-identity-gate` exists in `commitlint.yml` and scans `BASE_SHA..HEAD_SHA`.
- [x] **AC-06:** CI fails when PR commit range contains blocked author identity.
- [x] **AC-07:** CI passes when commit range contains no blocked identities.
- [x] **AC-08:** Unit tests cover AC-01 through AC-07.

## Test Plan (TDD)

### RED

1. Extend `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py` with identity validation and env-propagation tests.
2. Add `tests/unit/test_fr410_ci_author_identity_gate_red.py` for workflow gate behavior.

Planned RED tests:

1. `test_ac01_missing_user_name_fails_before_commit`
2. `test_ac02_missing_user_email_fails_before_commit`
3. `test_ac03_blocklisted_identity_fails_before_commit`
4. `test_ac04_valid_identity_sets_author_and_committer_env`
5. `test_ac05_workflow_contains_author_identity_gate`
6. `test_ac06_gate_rejects_blocklisted_identity_in_commit_range`
7. `test_ac07_gate_allows_clean_commit_range`

RED command:

```bash
pytest tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py tests/unit/test_fr410_ci_author_identity_gate_red.py -q --no-cov
```

### GREEN

1. Implement watcher identity enforcement.
2. Implement CI author identity gate.
3. Update and pass tests.

### Verification

```bash
pytest tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py tests/unit/test_fr410_ci_author_identity_gate_red.py -q --no-cov
pytest tests/unit/test_commitlint_workflow.py -q --no-cov
```

## Files Expected to Change

1. `.chaplain/actions/git_commit_action.py`
2. `.github/workflows/commitlint.yml`
3. `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py`
4. `tests/unit/test_fr410_ci_author_identity_gate_red.py` (new)
5. `changelog/unreleased/*.md` fragment for this fix
6. `docs/diary/*` reflection entry

## Risks and Mitigations

1. **Risk:** Overbroad matching blocks valid authors.
   **Mitigation:** Start with exact blocked values and add tests for clean pass.
2. **Risk:** Runtime checks fail on misconfigured local repos.
   **Mitigation:** Fail fast with explicit error message and remediation hint.
3. **Risk:** Policy overlap confusion with trailer gate.
   **Mitigation:** Keep separate gate names and error reasons.

## Alternatives Considered

1. **Runtime-only fix**
   Rejected: merge-boundary bypass remains possible.
2. **CI-only fix**
   Rejected: invalid commits still get created locally by watcher.
3. **Fallback default identity**
   Rejected: recreates the core defect pattern.

## Implementation Checklist

- [x] Add RED tests for runtime identity enforcement
- [x] Add RED tests for CI author identity gate
- [x] Implement runtime fix (GREEN)
- [x] Implement CI gate (GREEN)
- [x] Run targeted tests
- [x] Add changelog fragment
- [x] Add diary reflection with Seed

## Related

1. GitHub issue #407: <https://github.com/sheikkinen/yamlgraph/issues/407>
2. Existing watcher commit retry tests: `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py`
3. CI workflow: `.github/workflows/commitlint.yml`
4. Prior related gate work: `feature-requests/FR-409-ci-coauthored-by-gate-generalization.md`

## Judgement

**Verdict: APPROVED WITH AMENDMENTS**

The problem is real, recurrent, and already evidenced in repository history. The proposed two-boundary design (runtime + CI) is minimal, deterministic, and aligned with doctrine.

Required amendments before implementation:

1. **Blocklist contract must be explicit and exact-match first.**
   Define exact blocked values for this FR (`name == "Test"`, `email == "test@test.com"`) and avoid broad substring matching in v1.
2. **Runtime failure must include actionable remediation text.**
   When identity is missing/blocked, return error output that tells operator exactly which git config commands to run.
3. **CI gate must validate commit range only, not PR body.**
   This FR targets author identity in commit metadata; keep trailer/body policy in FR-409 scope.
4. **Test assertion for env propagation must be strict.**
   Validate both author and committer env vars are present and equal to resolved git config values.

Scope freeze:

1. In scope: `.chaplain/actions/git_commit_action.py`, `.github/workflows/commitlint.yml`, targeted tests, changelog fragment, diary reflection.
2. Out of scope: generalized identity policy expansion, commit-msg hook redesign, unrelated watcher pipeline refactors.

Authority granted to implement RED -> GREEN under this FR.

## Implementation Notes

Implemented in worktree `feat/watcher2-gh-407`:

1. Added strict runtime identity resolution and validation in `.chaplain/actions/git_commit_action.py`.
2. Added explicit author+committer env propagation on `git commit` subprocess calls.
3. Added CI job `author-identity-gate` in `.github/workflows/commitlint.yml` using exact-match blocked identity check on `BASE_SHA..HEAD_SHA` commit range.
4. Extended runtime tests in `tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py` for missing name/email, blocklisted identity, and env propagation.
5. Added CI gate acceptance tests in `tests/unit/test_fr410_ci_author_identity_gate_red.py`.

Verification evidence:

1. `pytest tests/unit/test_fr311_watcher2_git_commit_hook_fix_retry.py tests/unit/test_fr410_ci_author_identity_gate_red.py -q --no-cov` -> `10 passed`
2. `pytest tests/unit/test_commitlint_workflow.py -q --no-cov` -> `13 passed`
