# Feature Request: FR-316 watcher2 validate split (validate_fix + validate_gate)

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-03

## Summary

Split watcher2 post-enforce validation into two explicit states: `validate_fix` (LLM remediation) and `validate_gate` (deterministic CI-parity gate), so fixable issues are repaired or blocked before `done`.

## Value Statement

Watcher2 operators get earlier, deterministic failure detection for diary/commit-title/branch-sync contracts, reducing CI churn and failed PR cycles.

## Problem

Issue #316 identifies recurring failures that currently surface too late at `done`/CI:

1. Diary/changelog files created but not staged/committed.
2. Commit subject (used as PR title) violating commitlint rules.
3. Feature branch behind `origin/main` at push time.

Current flow:

```text
enforce_session -> validate -> sanity_check -> precommit_check -> done
```

Observed boundary gaps:

1. `validate` prompt focuses on lint/test remediation and does not explicitly own commit-title + branch-sync repair.
2. `precommit_check` only runs `pre-commit run --all-files`; it does not check commitlint parity or branch freshness.
3. `done` derives PR title from `git log -1 --format=%s` and pushes/opens PR; title and branch failures are found downstream.

## Research: Existing Patterns, Prior Art, and Scope Check

1. **Deterministic retry gate already exists:** `.chaplain/actions/precommit_action.py` provides `max_attempts`, `success`, `retry`, and `error` semantics.
2. **Remediation state already exists:** `.chaplain/graphs/watcher-enforce/validate-session.yaml` and prompt handle quality remediation (`ruff`/`pytest` + commit).
3. **PR title source-of-truth is explicit:** `.chaplain/config/watcher-pipeline-v2.yaml` `done` action sets `PR_TITLE=$(git log -1 --format=%s)`.
4. **CI parity rules are deterministic and testable:** `.github/workflows/commitlint.yml` defines title constraints (`feat` requires `FR-XXX`) and `diary-gate` diff checks.
5. **Not already solved in current v2 FSM:** no state before `done` performs all of: pre-commit + title contract + branch up-to-date + diary-in-diff checks.
6. **Topic file availability:** requested source `.chaplain/processing/gh-316.md` is not present in this worktree; canonical source used is GitHub issue #316.

## Objectives

1. Separate LLM repair from deterministic judgement with explicit state ownership.
2. Enforce CI-parity checks before `done`.
3. Preserve bounded retry behavior (`fix_needed` loop with attempt cap).
4. Keep `sanity_check` non-blocking `warn` routing semantics.

## Constraints

1. Scope limited to watcher2 artifacts under `.chaplain/` and focused tests under `tests/unit/`.
2. No YAMLGraph runtime changes under `yamlgraph/`.
3. No gate weakening; deterministic check failures must fail closed after retry cap.
4. Preserve `done` as publish/PR/CI/merge orchestration only.
5. Do not reuse `REQ-YG-316` (already allocated in `ARCHITECTURE.md`); allocate a new requirement ID during implementation.

## Proposed Solution

Refactor post-enforce flow to:

```text
enforce_session -> validate_fix -> sanity_check -> validate_gate -> done
                        ^                            |
                        +--------- fix_needed -------+
                              (max attempts -> error -> failed)
```

### 1. FSM changes (`.chaplain/config/watcher-pipeline-v2.yaml`)

1. Rename `validate` -> `validate_fix`.
2. Rename `precommit_check` -> `validate_gate`.
3. Route transitions:
   - `enforce_session --enforce_done--> validate_fix`
   - `validate_fix --validate_done--> sanity_check`
   - `sanity_check --pass--> validate_gate`
   - `sanity_check --warn--> validate_gate`
   - `validate_gate --pass--> done`
   - `validate_gate --fix_needed--> validate_fix`
   - `validate_gate --error--> failed`

### 2. `validate_fix` responsibilities (LLM remediation)

Extend prompt contract to repair:

1. Unstaged/untracked required artifacts (diary/changelog) via stage + amend workflow.
2. Commit subject/type alignment with CI commitlint contract.
3. Branch divergence from `origin/main` (rebase/refresh).
4. Lint/test failures (`ruff`, `pytest`).

### 3. `validate_gate` responsibilities (deterministic gate)

Implement deterministic gate action (new action class or deterministic wrapper) with retry contract:

1. Run `pre-commit run --all-files`.
2. Validate commit subject from `git log -1 --format=%s` against CI commitlint expectations.
3. Verify feature branch is up-to-date with `origin/main`.
4. Verify diary artifact presence in diff for `feat`/`fix` FR PRs (CI-parity behavior).

On failure, persist structured diagnostics in context (for example `validate_gate_output`) and emit `fix_needed`; emit `error` on attempt exhaustion.

### 4. Source-of-truth alignment

`validate_gate` title validation must use the same title source as `done` (`git log -1 --format=%s`) to avoid local/CI drift.

## Acceptance Criteria

- [x] **AC-01:** `watcher-pipeline-v2.yaml` defines `validate_fix` and `validate_gate` states.
- [x] **AC-02:** Legacy state names are removed from transitions (`validate`, `precommit_check`) in post-enforce path.
- [x] **AC-03:** Happy path is `enforce_session -> validate_fix -> sanity_check -> validate_gate -> done`.
- [x] **AC-04:** `validate_gate` loops `fix_needed -> validate_fix` and routes `error -> failed` on retry exhaustion.
- [x] **AC-05:** `sanity_check` retains non-blocking `warn` routing to `validate_gate`.
- [x] **AC-06:** `validate_gate` is deterministic and configured with retry semantics (`max_attempts`, success, retry, error events).
- [x] **AC-07:** `validate_gate` performs all four checks: pre-commit, commit-title contract, branch freshness, diary-in-diff parity.
- [x] **AC-08:** `validate_fix` prompt explicitly covers artifact staging/amend, commit-type correction, branch refresh/rebase, and lint/test remediation.
- [x] **AC-09:** `done` still derives PR title from `git log -1 --format=%s`.
- [x] **AC-10:** RED acceptance tests are added for AC-01..AC-09.

## Failing Acceptance Tests (RED)

Planned RED test module:

- `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py`

Planned tests:

1. `test_ac01_adds_validate_fix_and_validate_gate_states`
2. `test_ac02_removes_legacy_validate_and_precommit_check_states`
3. `test_ac03_routes_enforce_validatefix_sanity_validategate_done`
4. `test_ac04_validate_gate_loops_fix_needed_and_errors_to_failed`
5. `test_ac05_sanity_warn_routes_to_validate_gate`
6. `test_ac06_validate_gate_has_deterministic_retry_contract`
7. `test_ac07_validate_gate_checks_ci_parity_rules`
8. `test_ac08_validate_fix_prompt_covers_mechanical_repairs`
9. `test_ac09_done_pr_title_source_remains_latest_commit_subject`

Marker requirement (placeholder until registry update):

- `@pytest.mark.req("REQ-YG-318")`

RED commands:

```bash
pytest tests/unit/test_fr316_watcher2_validate_split_fix_gate.py -q --no-cov
rg -n "validate_fix|validate_gate" .chaplain/config/watcher-pipeline-v2.yaml
```

## Alternatives Considered

1. Keep `validate` + `precommit_check` as-is and rely on CI rejection.
   Rejected: failures are discovered too late and cause repeated pipeline churn.
2. Expand only `precommit_check` without splitting remediation/gate ownership.
   Rejected: conflates LLM repair and deterministic judgement boundaries.
3. Move these checks into `done`.
   Rejected: violates boundary-first normalization and keeps failures downstream.

## Related

- GitHub issue #316: <https://github.com/sheikkinen/yamlgraph/issues/316>
- Supersedes issue note: gh-312 (git add before precommit_check)
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/actions/validate_gate_action.py`
- `.chaplain/graphs/watcher-enforce/validate-session.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`
- `.github/workflows/commitlint.yml`
