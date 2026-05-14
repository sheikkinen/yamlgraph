# Feature Request: FR-373 Substance validation for diary-gate and changelog-gate

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-13

## Summary

Harden `diary-gate` and `changelog-gate` so they validate artifact substance (not just filename presence) before allowing feat/fix PRs to merge.

## Value Statement

Maintainers get merge gates that reject empty/meaningless compliance artifacts, reducing false-green CI outcomes and preserving traceability quality.

## Problem

Both gates currently validate shape only:

1. `changelog-gate` passes when any path under `changelog/unreleased/` appears in the PR diff, even if the fragment is empty or malformed.
2. `diary-gate` passes when any matching `docs/diary/*reflection*fr-NNN*` filename appears, even if the file has no substantive reflection content.

This allows compliance theatre: CI passes while the required artifact conveys no meaningful information.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Current CI scripts are presence-only.**
   - `.github/workflows/commitlint.yml` contains inline shell checks based on `git diff --name-only` + regex path match for both `changelog-gate` and `diary-gate`.
   - `tests/unit/test_ci_changelog_gate.py` and `tests/unit/test_ci_diary_gate.py` lock in this presence behavior today.
2. **There is proven prior art for semantic gate validation.**
   - FR-325 introduced `scripts/demo_log_semantics.sh` with `validate_demo_output_log_file()` and CI wiring via `source scripts/demo_log_semantics.sh`.
   - `tests/unit/test_fr325_demo_gate_log_content_validation.py` proves semantic checks through script-structure and behavior tests.
3. **Current local enforcement does not close the CI gap.**
   - `.pre-commit-config.yaml` `diary-reflection-check` only rejects known placeholder strings; it does not enforce minimum substance structure (size/header/Seed marker), and local hooks are bypassed by server-side squash merge.
4. **Recurring evidence of this exact failure mode exists.**
   - `docs/diary/2026-04-08-inquisitor-audit-162.md` and `...-163.md` explicitly identify existence-only gates as compliance theatre and propose minimum-content checks.
5. **Topic source discrepancy in this worktree.**
   - Requested source `.chaplain/processing/gh-373.md` is not present; canonical planning source used: GitHub issue #373.

## Objectives

1. Ensure `diary-gate` rejects empty or structurally invalid diary reflections.
2. Ensure `changelog-gate` rejects empty or structurally invalid changelog fragments.
3. Reuse the FR-325 semantic-validation pattern (shared shell validation function(s)) for maintainability and testability.

## Constraints

1. **Single responsibility:** only strengthen substance validation for existing `diary-gate` and `changelog-gate`.
2. Preserve existing gate trigger semantics (`feat`/`fix` PR titles, FR extraction behavior in `diary-gate`).
3. Preserve existing path contracts:
   - diary files still keyed by FR number in `docs/diary/`
   - changelog entries still in `changelog/unreleased/`
4. No expansion to unrelated gates (for example `demo-gate`).
5. Keep implementation shell-first and CI-local (no new external actions/services).

## Proposed Solution

### In scope

1. Add a shared shell semantic validator module for CI gate artifact checks (patterned after `scripts/demo_log_semantics.sh`), with:
   - `validate_diary_reflection_file <path> <label>`
   - `validate_changelog_fragment_file <path> <label>`
2. Update `changelog-gate` in `.github/workflows/commitlint.yml` to:
   - gather changed files under `changelog/unreleased/*.md`,
   - fail if none exist (existing behavior),
   - validate each matched fragment for substance:
     - contains non-whitespace content,
     - contains YAML front matter (`---` block) with `type:` field,
     - contains at least one Markdown list item (`- `) in the body section.
3. Update `diary-gate` in `.github/workflows/commitlint.yml` to:
   - keep FR-number-based matching logic,
   - validate matching diary file content for substance:
     - contains non-whitespace content,
     - contains at least one Markdown `##` header,
     - contains `Seed:` marker,
     - meets a minimum byte threshold (target: >100 bytes).
4. Update tests to cover semantic behavior, not only path presence:
   - extend/add tests proving invalid-empty/malformed artifacts fail,
   - prove valid artifacts pass.
5. Update traceability text for the affected capability/requirement records to reflect semantic gate behavior:
   - `capabilities/CAP-50-ci-changelog-gate.yaml` (REQ-YG-148)
   - `capabilities/CAP-54-ci-diary-existence-gate.yaml` (REQ-YG-152)
   - `ARCHITECTURE.md` rows for REQ-YG-148 and REQ-YG-152.

### Out of scope

1. Rewriting historical diary/changelog files outside the current PR diff.
2. Changing pre-commit hooks (`diary-reflection-check`, `changelog-required`) in this FR.
3. Introducing a universal substance framework for all gates (can be a follow-up FR).

## Acceptance Criteria

- [x] **AC-01:** `changelog-gate` fails when a changed `changelog/unreleased/*.md` file is empty/whitespace-only.
- [x] **AC-02:** `changelog-gate` fails when a changed fragment lacks valid front matter with `type:` and/or lacks a body list item (`- `).
- [x] **AC-03:** `changelog-gate` passes when a changed fragment has non-empty content, valid front matter with `type:`, and at least one body list item.
- [x] **AC-04:** `diary-gate` fails when the FR-matching diary file is empty, below minimum size, missing `##` header, or missing `Seed:` marker.
- [x] **AC-05:** `diary-gate` passes when the FR-matching diary file satisfies all substance checks.
- [x] **AC-06:** Gate scripts use shared semantic validation function(s) (no duplicated validation logic inline in workflow).
- [x] **AC-07:** REQ/CAP architecture text for REQ-YG-148 and REQ-YG-152 describes substance validation semantics.

## Failing Acceptance Tests (RED plan)

RED test artifact:

- `tests/unit/test_fr373_gate_substance_validation_red.py`

Planned RED tests:

1. `test_ac01_changelog_gate_rejects_empty_fragment_content`
2. `test_ac02_changelog_gate_rejects_missing_type_or_body_list_item`
3. `test_ac03_changelog_gate_accepts_valid_fragment_structure`
4. `test_ac04_diary_gate_rejects_missing_header_seed_or_min_size`
5. `test_ac05_diary_gate_accepts_valid_reflection_structure`
6. `test_ac06_commitlint_gate_scripts_source_shared_semantics_module`
7. `test_ac07_reqyg148_and_reqyg152_text_mentions_substance_validation`

RED command:

```bash
pytest tests/unit/test_fr373_gate_substance_validation_red.py -q --no-cov
```

Targeted regression command (post-implementation):

```bash
pytest tests/unit/test_ci_changelog_gate.py tests/unit/test_ci_diary_gate.py -q --no-cov
```

## Alternatives Considered

1. **Keep presence-only CI checks**
   - Rejected: does not address the reported failure mode; empty files still pass.
2. **Rely only on local pre-commit hooks**
   - Rejected: server-side squash merge bypasses local hooks; CI must enforce merge boundary truth.
3. **Build one universal “substance gate” for all artifacts now**
   - Rejected for scope: useful direction, but broader than this issue’s single responsibility.

## Related

- Issue #373: <https://github.com/sheikkinen/yamlgraph/issues/373>
- `.github/workflows/commitlint.yml`
- `tests/unit/test_ci_changelog_gate.py`
- `tests/unit/test_ci_diary_gate.py`
- `scripts/demo_log_semantics.sh` (prior-art semantic validator pattern from FR-325)
- `feature-requests/FR-325-demo-gate-log-content-validation.md`
- `feature-requests/FR-149-ci-changelog-gate.md`
- `feature-requests/FR-158-diary-existence-ci-gate.md`
- `docs/diary/2026-04-08-inquisitor-audit-162.md`
- `docs/diary/2026-04-08-inquisitor-audit-163.md`
