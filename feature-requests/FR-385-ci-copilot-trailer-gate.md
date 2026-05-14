# Feature Request: FR-385 CI gate to block Copilot co-author trailers in commits and PR bodies

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-14
**Judged:** 2026-05-14

## Summary

Add a deterministic CI gate in `.github/workflows/commitlint.yml` that fails pull requests when Copilot `Co-authored-by` trailers appear in either PR commits or the PR body.

## Value Statement

Maintainers get merge-boundary enforcement against vendor-inserted Copilot trailers, preventing policy drift that local hooks alone cannot reliably stop.

## Problem

GitHub issue #388 reports a governance gap: Copilot co-author trailers can still reach PR surfaces despite local guardrails.

Research findings in this worktree:

1. `.github/workflows/commitlint.yml` has no job that scans commit messages or PR body text for `Co-authored-by` trailers.
2. Local pre-commit already blocks AI co-author trailers (`block-ai-coauthor`, `scripts/block_ai_coauthor.py`, CAP-82 / REQ-YG-215), but local hooks are not sufficient as merge-boundary enforcement.
3. Existing CI gate pattern is deterministic shell checks in `commitlint.yml` with unit tests validating workflow wiring and shell behavior (`tests/unit/test_ci_conflict_check.py`, `test_ci_demo_proof_gate.py`, `test_ci_diary_gate.py`).
4. Requested topic source `.chaplain/processing/gh-388.md` is not present in this worktree; canonical source used was GitHub issue #388.

## Objectives

1. Block Copilot trailer strings in all commits included in a PR.
2. Block Copilot trailer strings in PR body text.
3. Keep enforcement deterministic (grep/string match), with no LLM dependency.

## Constraints

1. Single responsibility: CI enforcement for Copilot trailer strings in commit messages and PR body only.
2. Preserve existing local `block-ai-coauthor` hook behavior and scope (no regressions, no broad refactor).
3. Preserve existing commitlint workflow jobs and triggers; add a focused, independent gate job.
4. Follow existing architecture traceability flow: add a new CAP + REQ entry and matching test markers.

## Proposed Solution

### In scope

1. Add a new `copilot-trailer-gate` job in `.github/workflows/commitlint.yml` on pull request events.
2. In that job, deterministically scan:
   - commit messages across `BASE_SHA..HEAD_SHA`
   - PR body text (`github.event.pull_request.body`)
3. Fail on either Copilot trailer form:
   - `Co-authored-by: Copilot`
   - `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
4. Add focused unit tests (workflow structure + shell behavior) in a new FR-scoped test file.
5. Add traceability entries:
   - new capability file (proposed `capabilities/CAP-148-ci-copilot-trailer-gate.yaml`)
   - new requirement row in `ARCHITECTURE.md` (proposed `REQ-YG-358`)
   - required status check mention in `CLAUDE.md` branch-protection section.

### Out of scope

1. Replacing or refactoring `scripts/block_ai_coauthor.py`.
2. Expanding CI gate to all AI trailer variants beyond Copilot in this FR.
3. Changing commit author metadata semantics outside trailer policy enforcement.

## Acceptance Criteria

- [x] **AC-01:** CI fails when any commit in the PR range contains `Co-authored-by: Copilot` (short form).
- [x] **AC-02:** CI fails when any commit in the PR range contains `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` (full email form).
- [x] **AC-03:** CI fails when PR body contains `Co-authored-by: Copilot` (short form).
- [x] **AC-04:** CI fails when PR body contains `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` (full email form).
- [x] **AC-05:** PRs without those trailers in commits/body pass unaffected by this new job.
- [x] **AC-06:** Unit tests validate both workflow wiring and shell behavior for AC-01..AC-05.
- [x] **AC-07:** `ARCHITECTURE.md`, capability registry, and `CLAUDE.md` required checks list are updated for the new CI gate.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`

Planned RED tests:

1. `test_ac01_workflow_has_copilot_trailer_gate_job`
2. `test_ac01_commit_scan_detects_short_form_copilot_trailer`
3. `test_ac02_commit_scan_detects_full_form_copilot_trailer`
4. `test_ac03_pr_body_scan_detects_short_form_copilot_trailer`
5. `test_ac04_pr_body_scan_detects_full_form_copilot_trailer`
6. `test_ac05_clean_commit_messages_and_pr_body_pass`
7. `test_ac06_workflow_step_uses_deterministic_grep_without_llm`
8. `test_ac07_architecture_and_capability_entries_reference_new_req`

RED command:

```bash
pytest tests/unit/test_fr385_ci_copilot_trailer_gate_red.py -q --no-cov
```

Additional RED evidence command (expected no match before implementation):

```bash
rg -n "copilot-trailer-gate|pull_request\\.body|BASE_SHA\\.\\.HEAD_SHA.*Co-authored-by" .github/workflows/commitlint.yml
```

## Alternatives Considered

1. **Rely on pre-commit only (CAP-82)**
   - Rejected: local hooks do not provide complete merge-boundary enforcement.

2. **Extend `block_ai_coauthor.py` and call it from CI**
   - Rejected for scope/minimality: still needs separate PR-body handling and adds coupling where inline deterministic CI logic is already the repo norm.

3. **Broaden to all AI trailer variants in CI now**
   - Rejected for single-responsibility: issue #388 requests Copilot-specific forms; broader policy can be a follow-up FR.

## Judgement Notes

- Scope: clear and minimal. Two scan surfaces (commit messages, PR body), two string forms, deterministic grep. Out-of-scope list explicit and sufficient.
- Traceability: REQ-YG-358 is the correct next sequential number; CAP-148 is the correct next sequential number. Both verified against current state.
- Pattern fit: **Framework primitive** — CI enforcement gate is a canonical pattern with 5+ existing precedents in `commitlint.yml` (`conflict-check`, `changelog-gate`, `diary-gate`, etc.). Implementation path is well-paved.
- Acceptance criteria: 7 ACs are measurable, map 1-to-1 to 8 planned tests. Test names in the RED plan are unambiguous.
- Implementation note: the `copilot-trailer-gate` job must include `fetch-depth: 0` in `actions/checkout` (required to resolve `BASE_SHA..HEAD_SHA` commit ranges), following the `changelog-gate` precedent. This is an implementation detail within the implementor's discretion.
- RED tests not written yet — correct pre-implementation state. First implementation step is to write the RED test file, then add the CI job, then add traceability entries.
- Authority granted. Proceed in order: RED → GREEN → traceability → diary.

## Related

- Issue #388: <https://github.com/sheikkinen/yamlgraph/issues/388>
- `.github/workflows/commitlint.yml`
- `.pre-commit-config.yaml` (`block-ai-coauthor`)
- `scripts/block_ai_coauthor.py`
- `tests/unit/test_precommit_hooks.py` (REQ-YG-215 local gate tests)
- `tests/unit/test_ci_conflict_check.py` (CI gate testing pattern)
- `tests/unit/test_ci_demo_proof_gate.py` (CI semantic gate testing pattern)
- `ARCHITECTURE.md` (CI gate requirement registry)
