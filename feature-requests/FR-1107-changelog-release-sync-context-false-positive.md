# Feature Request: Changelog release-sync gate matches diff context, not changes

**Priority:** LOW
**Type:** Bug
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-09-26
**First consumer / first event:** the next author who edits any
`pyproject.toml` line within three lines of `version =` (e.g.
`requires-python`, `description`) while `changelog/unreleased/` holds
fragments. FR-1104's GREEN commit (`68327573`) was the first recorded
event and needed an operator-authorized `SKIP=changelog-release-sync`.
**Research:** in-body; the defect is one line, read directly.
**Prior art:** [FR-192](FR-192-draconian-changelog-release-gate.md)
created the gate; this fixes its version-change detection, the freeze
rule is unchanged. [FR-441](FR-441-precommit-files-patterns.md) set the
hook's `files:` pattern; not touched.

## Summary

`scripts/check_changelog_release_sync.py` decides "version bumped" with
`'version = "' in diff_output`, where `diff_output` is the whole
`git diff --cached -- pyproject.toml`. Unified diff context includes the
unchanged `version = "0.6.0"` line whenever an edit lands on lines 4–10,
so a non-release commit is blocked as a release.

## Value Statement

For every author touching package metadata, removes a false block whose
only exits are freezing an unrelated release or skipping the gate — both
wrong.

## Problem

Witness (FR-1104): staged diff changed only `requires-python` (line 10)
and added a classifier; hunk `@@ -7,7 +7,7 @@` carried
` version = "0.6.0"` as context; the gate printed "Version bump detected".

## Ideal Result

The gate fires if and only if an added or removed line sets the
`[project]` `version`.

## Proposed Solution

Match only diff lines starting with `+`/`-` (excluding `+++`/`---`)
that match `^[+-]version\s*=\s*"`. No other behavior change.

## Acceptance Criteria

- [ ] AC-01: RED test in `tests/unit/test_changelog_release_sync.py`
      feeding a diff whose only `version = "` line is context → gate
      returns 0 with fragments present.
- [ ] AC-02: existing `test_blocks_version_bump_with_fragments` stays
      green (real `+version` / `-version` lines still block).
- [ ] AC-03: changelog fragment.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | `git diff --cached -U0` | REJECTED — `check()` also takes injected diffs; filtering changed lines fixes both paths. |
| A2 | Parse old/new `pyproject.toml` with `tomllib` and compare `project.version` | Viable, heavier; judge may prefer it. |

## Related

- FR-1104 — first event.
