# Feature Request: FR-435 Markdown Post-Edit Hygiene Hook

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-21

**Judge Verdict:** APPROVE with constraints — implement minimal hygiene parity only (trailing whitespace), keep behavior opt-in for mutation, and avoid overlapping responsibility with `fr-checks.sh`.

## Summary

Add a dedicated Markdown post-edit hook so `*.md` files receive immediate hygiene feedback (and optional auto-fix), instead of relying on commit-time hooks.

## Value Statement

Writers get fast feedback while editing docs, and commit-time churn is reduced when trailing whitespace or similar markdown hygiene issues are introduced.

## Problem

After FR-434 modularization, post-edit hooks cover:
- Python (`python-checks.sh`)
- YAML (`yaml-checks.sh`)
- feature-requests markdown semantics (`fr-checks.sh`)

A general markdown file like `examples/malformed/README.md` is intentionally ignored by python checks (`*.py` gate), so `POST_EDIT_AUTO_RUFF=1` does not mutate it. This is expected, but creates a behavior gap:

- post-edit stage: no markdown hygiene enforcement
- commit stage: `trim trailing whitespace` catches issues later

Also, Ruff is Python-focused and not a markdown formatter/linter, so "auto-ruff for md" is a category mismatch.

## Proposed Solution

Add a new modular hook script:
- `.github/hooks/scripts/checks/markdown-checks.sh`

Register it in:
- `.github/hooks/post-edit-checks.json`

### Behavior

- Relevance filter:
  - Edit tools only (`replace_string_in_file`, `create_file`, `multi_replace_string_in_file`, `apply_patch`)
  - Files ending in `.md`
  - Exclude `feature-requests/*.md` to preserve `fr-checks.sh` as the sole FR semantics owner
- Checks:
  - Detect trailing whitespace lines
  - Do not add tabs/newline policy checks in this FR (defer to follow-up FR)
- Optional auto-fix flag:
  - `POST_EDIT_AUTO_MD=1`
  - Remove trailing whitespace in-place
  - Preserve file contents otherwise
- Audit logging:
  - Log `markdown-autofix-applied` when mutations occur

### Out of Scope

- Running Ruff on markdown files
- Adding heavy markdown style policy (headings, line length, prose lint)

## Judgment Notes

- Root cause is boundary mismatch, not Ruff failure: markdown files never enter python check scope.
- Minimal fix is preferred: one markdown hygiene check (trailing whitespace) with optional mutation.
- Mutation must remain explicitly opt-in via env flag (`POST_EDIT_AUTO_MD=1`).
- Keep audit parity with existing hooks: log approve/feedback and explicit autofix reason when changed.

## Acceptance Criteria

- [x] New script exists: `markdown-checks.sh`
- [x] Hook JSON includes markdown check entry with timeout
- [x] Markdown edits receive post-edit feedback for trailing whitespace
- [x] `POST_EDIT_AUTO_MD=1` auto-fixes trailing whitespace in markdown files
- [x] `POST_EDIT_AUTO_RUFF` behavior remains unchanged and Python-only
- [x] `feature-requests/*.md` FSM checks remain in `fr-checks.sh`
- [x] Audit log records markdown auto-fix actions
- [x] Hook emits no output for non-edit tools and non-markdown files
- [x] Tests added for warning mode and auto-fix mode

## Test Plan

Add test file:
- `.github/hooks/tests/test_markdown_checks.py`

Cases:
1. Non-edit tool is ignored
2. Non-markdown file is ignored
3. Markdown trailing whitespace warns in default mode
4. Markdown trailing whitespace auto-fixes when `POST_EDIT_AUTO_MD=1`
5. `apply_patch` with mixed files only reports markdown targets
6. `feature-requests/*.md` remains ignored by markdown hook (owned by `fr-checks.sh`)
7. No regression in python/yaml/fr modular tests

## Alternatives Considered

- **Keep commit-time only hygiene**: Rejected. Feedback comes too late.
- **Use Ruff for markdown**: Rejected. Ruff does not target markdown formatting/linting directly.
- **Introduce full markdownlint stack now**: Deferred. This FR targets minimal hygiene parity first.

## Related

- `feature-requests/FR-433-post-edit-apply-patch-coverage-and-auto-ruff.md`
- `feature-requests/FR-434-hook-modular-refactor.md`
- `.github/hooks/scripts/checks/python-checks.sh`
- `.github/hooks/post-edit-checks.json`

## Implementation Notes

- Added `.github/hooks/scripts/checks/markdown-checks.sh` for markdown hygiene.
- Added hook registration in `.github/hooks/post-edit-checks.json` with timeout `5`.
- Implemented warning mode for trailing whitespace and optional mutation via `POST_EDIT_AUTO_MD=1`.
- Excluded `feature-requests/*.md` in markdown hook to preserve `fr-checks.sh` semantic ownership.
- Added test suite `.github/hooks/tests/test_markdown_checks.py` covering warning/autofix/apply_patch/mixed-target and exclusion behavior.
- Updated hook documentation in `.github/hooks/README.md`.

## Verification

- `pytest -q --no-cov .github/hooks/tests/test_markdown_checks.py .github/hooks/tests/test_python_checks.py .github/hooks/tests/test_yaml_checks.py .github/hooks/tests/test_fr_checks.py`
- Result: `24 passed`.
