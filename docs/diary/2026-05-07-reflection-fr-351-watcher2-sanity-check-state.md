# Reflection: FR-351 Watcher2 Sanity Check

**Date:** 2026-05-07
**FR:** FR-351 — Agent export `.agent.md` for tool-scoped Copilot modes
**Reviewer:** watcher2 post-validate sanity check

## Trap

`partial_remediation`: earlier iteration (FR-350) split the collision guard into two
separate methods (`_assert_target_file_is_safe`, `_assert_target_dir_is_safe`) and
retained a `target_file` field on `SkillPackage`. The refactor collapsed both into a
single `_assert_target_is_safe` dispatch — addressing the symptom at the right boundary
rather than papering over it with an extra model field.

## What Happened

FR-351 replaced FR-350 artifacts cleanly: old test file, FR doc, diary entry, changelog
fragment, and capability file were all removed; new counterparts added. The implementation
made targeted changes to three files (`skill_export.py`, `skill_export_writer.py`,
`skill_commands.py`) and added one new test file with five acceptance tests.

All five acceptance tests pass (0.15 s). Each test maps to exactly one REQ-YG-3xx ID and
asserts observable behavior: file path existence, frontmatter content, error type on
collision, and doc string membership.

## Root Cause (of prior complexity)

The original split between `target_file` and `target_dir` leaked the format distinction
into `SkillPackage` — a data model that should be format-agnostic. Resolving the path
fully inside `_resolve_target_dir` (now misnamed but functionally unified) removed the
leak. One residual cosmetic mismatch: `SkillPackage.target_dir` holds a file path for
`agent-md` format; this is visible in the CLI output line `✓ Skill exported: <file>`,
which is correct, but the field name is misleading.

## What Worked

- Unified collision guard (`_assert_target_is_safe`) dispatches on format before
  checking existence — normalizing at the boundary, not downstream.
- `write_agent_markdown` is a pure function: no side-effectful staging, no temp dirs;
  appropriate for a single-file artifact.
- Reference docs (`reference/cli.md`, `reference/skills-export.md`) were updated in the
  same diff, satisfying AC-06 without a follow-up commit.
- No pipeline logs available for this run; timing evidence not present but not required
  for a clean GREEN run.

## Seed

If `SkillPackage.target_dir` semantically holds either a directory or a file depending on
format, should `SkillPackage` be split into format-specific result types (or carry a
`target_path: Path` instead), and would that make the CLI output line self-evident
without reading the format field?
