# Feature Request: FR-424 block WIP commit subjects in main merge path

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-20

## Summary

Add an explicit WIP-subject gate so commit subjects containing the word `wip` (case-insensitive) are rejected in both local commit-msg flow on `main` and PR merge flow in CI.

## Value Statement

Maintainers get deterministic prevention of unfinished/WIP commit subjects landing through the normal merge ceremony, improving auditability of `main` history.

## Problem

Inquisitor audits repeatedly flagged commits like `chore: investigation of chaplain failures, wip` on `main` as doctrine violations/drift. The current policy stack has no dedicated check for `wip` in commit subjects:

1. `.pre-commit-config.yaml` has commit-msg gates for Conventional Commits, `feat`→`FR-XXX`, changelog fragment presence, and AI co-author trailers, but no WIP-subject guard.
2. `.github/workflows/commitlint.yml` has CI jobs for conflict markers, trailers, changelog, diary, and author identity, but no WIP-subject job.
3. This gap allows WIP-labeled commit subjects to pass the standard PR path unchecked.

## Research Findings

1. **Audit evidence exists and is recent.** `docs/diary/2026-05-19-inquisitor-audit-240.md`, `...-241.md`, and `...-242.md` flag WIP-labeled commits as drift/violation.
2. **Hook pattern already exists for subject/body gates.** `tests/unit/test_precommit_hooks.py` validates commit-msg hook entries with subprocess execution and message fixtures.
3. **CI gate pattern already exists for commit-range scans.** `tests/unit/test_fr410_ci_author_identity_gate_red.py` and `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py` execute workflow `run` scripts against temporary git ranges (`BASE_SHA..HEAD_SHA`).
4. **This FR must stay scoped.** `.chaplain/processing/inquisitor-direct-push-bypass.md` is a separate structural issue; direct-push bypass remediation is out of scope here.

## Objectives

1. Block commit subjects containing `wip` as a standalone word from the PR merge path to `main`.
2. Add a local commit-msg guard that blocks such subjects when committing on branch `main`.
3. Keep false positives low via word-boundary matching (e.g., allow `swipe`).

## Constraints

1. Single responsibility: WIP subject gating only.
2. No new dependencies.
3. Deterministic checks only (shell/grep), no LLM-based gate logic.
4. Preserve existing gate behavior for non-main branches and non-WIP subjects.

## Proposed Solution

### 1. Local gate: commit-msg hook

Add a new local commit-msg hook in `.pre-commit-config.yaml` that:

1. Reads commit **subject** (`head -n1 "$1"`).
2. Detects current branch (`git rev-parse --abbrev-ref HEAD`).
3. Fails only when branch is `main` and subject matches `\bwip\b` (case-insensitive).

### 2. CI gate: `wip-gate` job

Add a new job in `.github/workflows/commitlint.yml` that:

1. Runs for pull requests.
2. Reads commit **subjects** from `BASE_SHA..HEAD_SHA` using `git log --format=%s`.
3. Fails when any subject matches `\bwip\b` (case-insensitive).
4. Emits a clear error with offending subject lines.

### 3. Documentation update

Update `CLAUDE.md` branch-protection status-check list to include `wip-gate`.

## Out of Scope

1. Eliminating direct pushes to `main`.
2. Detecting duplicate commit subjects (audit seed item).
3. Blocking `wip` outside commit subject (body/footer scanning).

## Requirement Traceability Plan

1. Add capability entry: `CAP-156 WIP Commit Subject Gate` (proposed).
2. Add requirement: `REQ-YG-419` (proposed).
3. Add/extend ARCHITECTURE requirement row for `REQ-YG-419`.
4. Tag new acceptance tests with `@pytest.mark.req("REQ-YG-419")`.

## Acceptance Criteria

- [x] **AC-01:** `.pre-commit-config.yaml` defines a commit-msg hook that rejects `\bwip\b` (case-insensitive) in commit subject when branch is `main`.
- [x] **AC-02:** The local hook allows the same subject on non-`main` branches.
- [x] **AC-03:** The local hook does not reject non-word-boundary substrings (e.g., `swipe`).
- [x] **AC-04:** `.github/workflows/commitlint.yml` defines a `wip-gate` job that scans `BASE_SHA..HEAD_SHA` commit subjects.
- [x] **AC-05:** `wip-gate` fails when any commit subject in range contains `\bwip\b` (case-insensitive).
- [x] **AC-06:** `wip-gate` passes on clean commit ranges without WIP subjects.
- [x] **AC-07:** `CLAUDE.md` required status-check documentation includes `wip-gate`.
- [x] **AC-08:** Capability/architecture traceability is updated for `REQ-YG-419`.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr424_wip_main_gate_red.py`

Planned RED tests:

1. `test_ac01_precommit_hook_blocks_wip_subject_on_main`
2. `test_ac02_precommit_hook_allows_wip_subject_on_feature_branch`
3. `test_ac03_precommit_hook_uses_word_boundary_not_substring`
4. `test_ac04_commitlint_workflow_has_wip_gate_job`
5. `test_ac05_wip_gate_rejects_wip_subject_in_commit_range`
6. `test_ac06_wip_gate_allows_clean_commit_range`
7. `test_ac07_traceability_docs_reference_req_yg_411`

RED command:

```bash
pytest tests/unit/test_fr424_wip_main_gate_red.py -q --no-cov
```

## Alternatives Considered

1. **Local hook only** — rejected; can be bypassed and does not enforce PR merge boundary.
2. **CI gate only** — rejected; misses immediate local feedback on `main` commits.
3. **Block `wip` anywhere in full commit message** — rejected; higher false-positive risk than subject-only gating.
4. **Wait for direct-push-bypass fix first** — rejected; this gate is independently valuable and low-cost.

## Related

- `docs/diary/2026-05-19-inquisitor-audit-240.md`
- `docs/diary/2026-05-19-inquisitor-audit-241.md`
- `docs/diary/2026-05-19-inquisitor-audit-242.md`
- `.pre-commit-config.yaml`
- `.github/workflows/commitlint.yml`
- `tests/unit/test_precommit_hooks.py`
- `tests/unit/test_fr410_ci_author_identity_gate_red.py`
- `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`
- `ARCHITECTURE.md`
- `CLAUDE.md`
