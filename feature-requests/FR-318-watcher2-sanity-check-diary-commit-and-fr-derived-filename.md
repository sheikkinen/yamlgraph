# Feature Request: FR-318 watcher2 sanity_check diary commit and FR-derived filename

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-03

## Summary

Fix `sanity-check-session` prompt drift so it (1) commits the diary reflection it creates and (2) derives the diary filename from `{{ fr_path }}` instead of hardcoding `fr-316`.

## Value Statement

Watcher2 maintainers get diary-gate-compliant PRs from the sanity-check stage without manual cleanup, eliminating repeat CI failures caused by untracked or misnamed diary files.

## Problem

GitHub issue #305 reports repeated watcher pipeline CI failures caused by `sanity_check` prompt behavior:

1. `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml` instructs diary creation with a hardcoded filename:
   - `docs/diary/YYYY-MM-DD-reflection-fr-316-watcher2-sanity-check-state.md`
2. The same prompt does not instruct staging/committing the new diary file.

Impact:

- `diary-gate` checks PR diff for a diary reflection file matching the FR number from title.
- A hardcoded `fr-316` filename mismatches non-316 FRs.
- An uncommitted diary file does not appear in PR diff, so gate fails.

## Research: Existing Patterns and Prior Art

1. **Commit-step pattern already exists in watcher prompts**
   `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml` has an explicit `STAGE + COMMIT` step for remediation outputs.

2. **Diary filename contracts are enforced mechanically**
   - `.github/workflows/commitlint.yml` (`diary-gate`) requires diary reflection in PR diff for FR number referenced by PR title.
   - `.pre-commit-config.yaml` (`diary-filename-check`) enforces `docs/diary/...reflection...fr-NNN...` naming.

3. **FR-path-derived naming exists elsewhere**
   `.chaplain/lib/finalize_lib.sh` and `.chaplain/actions/changelog_gen_action.py` extract FR metadata from `fr_path`/FR filename rather than hardcoding identifiers.

4. **Current tests miss this boundary**
   `tests/unit/test_fr316_watcher2_sanity_check_state.py` verifies diary presence in prompt but does not verify commit instruction or FR-derived diary filename.

## Objectives

1. Ensure sanity-check prompt commits the diary artifact it creates.
2. Ensure diary filename is derived from `{{ fr_path }}` (FR under execution), not fixed to FR-316.
3. Preserve current routing semantics (`PASS`/`WARN`) and single responsibility of `sanity_check`.

## Constraints

1. Scope limited to sanity-check prompt contract and directly coupled tests.
2. No FSM transition changes in `.chaplain/config/watcher-pipeline-v2.yaml`.
3. No changes to validate/enforce ownership boundaries beyond this diary artifact contract.
4. No CI gate relaxation; fix behavior at prompt boundary.

## Proposed Solution

1. Update `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml` step sequence:
   - Replace hardcoded FR-316 diary filename instruction with FR-derived naming based on `{{ fr_path }}`.
   - Add explicit `git add` + `git commit` instruction after diary creation (matching validate-session commit pattern).

2. Add focused RED/GREEN unit tests for the prompt contract to enforce:
   - No hardcoded FR-316 diary filename string.
   - Explicit FR-path-derived diary naming instruction.
   - Explicit stage+commit instruction after diary creation.
   - Existing PASS/WARN output contract remains intact.

## Acceptance Criteria

- [x] **AC-01:** `sanity-check-session` prompt no longer contains hardcoded `fr-316` diary filename text.
- [x] **AC-02:** Prompt explicitly instructs deriving diary filename from `{{ fr_path }}`.
- [x] **AC-03:** Prompt explicitly instructs staging and committing the created diary file.
- [x] **AC-04:** Prompt still returns exactly `PASS` or `WARN` for FSM routing.
- [x] **AC-05:** Unit tests are added to lock AC-01..AC-04 against regressions.

## Failing Acceptance Tests (RED)

Create `tests/unit/test_fr318_watcher2_sanity_check_diary_contract.py`:

1. `test_ac01_no_hardcoded_fr316_diary_filename`
2. `test_ac02_diary_filename_is_derived_from_fr_path_instruction`
3. `test_ac03_prompt_requires_stage_and_commit_for_diary`
4. `test_ac04_prompt_keeps_pass_warn_output_contract`

RED command:

```bash
pytest tests/unit/test_fr318_watcher2_sanity_check_diary_contract.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
! rg -n 'fr-316-watcher2-sanity-check-state' .chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml
rg -n 'STAGE \+ COMMIT|git add|git commit' .chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml
```

## Alternatives Considered

1. **Patch in `done`/finalize stage to auto-create or auto-commit diary**
   Rejected: fixes symptom downstream; diary ownership belongs to sanity-check boundary.

2. **Keep hardcoded filename and only add commit instruction**
   Rejected: still fails FR-specific diary-gate matching for non-316 FRs.

3. **Relax diary-gate matching rules**
   Rejected: weakens enforcement instead of fixing prompt contract defect.

## Related

- GitHub issue #305: <https://github.com/sheikkinen/yamlgraph/issues/305>
- `.chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`
- `.github/workflows/commitlint.yml` (`diary-gate`)
- `.pre-commit-config.yaml` (`diary-filename-check`)
- `tests/unit/test_fr316_watcher2_sanity_check_state.py`
- Topic source requested: `.chaplain/processing/gh-305.md` (not present in this worktree)
- Canonical source used: GitHub issue #305
