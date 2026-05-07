# Reflection: FR-350 Watcher2 Sanity Check

**Date:** 2026-05-07
**FR:** FR-350 — `agent-md` export with tool-scoped personas
**Phase:** Post-validate sanity review (watcher2)

## What Happened

Watcher2 ran an independent review of the FR-350 implementation on branch
`feat/watcher2-gh-350`. Scope reviewed: 14 changed files (+926 / -133), including
`skill_export.py`, `skill_export_writer.py`, `cli/__init__.py`, `cli/skill_commands.py`,
six acceptance tests in `test_fr350_agent_export_red.py`, and three reference docs.

All six acceptance tests pass cleanly in 0.16s. Every AC has a corresponding
`@pytest.mark.req` marker (REQ-YG-327–332). Assertions check behavioral output
(file existence, YAML-parsed frontmatter values, body section headings, error messages and
exit codes) — not implementation details.

## Trap

### `audit_as_ritual` — Judge Issues resolved but not verified by reviewer

The FR Judge raised four issues (file-vs-directory semantics, RED test pre-commit,
collision check scope, `model` key name). Each issue was resolved in the implementation.
The watcher2 risk is accepting the resolution claims without re-verifying each
independently. Verification performed:

- Issue 1: `SkillPackage.target_file: Path | None` confirmed; `_assert_target_file_is_safe`
  and `_resolve_target_file` exist as separate methods; collision check is `target_file.exists()`.
- Issue 2: `test_fr350_agent_export_red.py` committed with all 6 tests (exact names from FR).
- Issue 3: `FileExistsError` message is `"Output target file already exists: {target_file}"`
  — file path, not directory path.
- Issue 4: `model` key (singular) used in frontmatter, consistent with GitHub Copilot
  `.agent.md` spec.

No FSM pipeline log was found in `logs/`; the pipeline ran without log persistence.
This is a minor observability gap, not a correctness issue.

## Root Cause

The FR-348 directory-oriented export architecture created a semantic mismatch for the
`agent-md` single-file output. The Judge's Issue 1 identified this before implementation.
The implementation resolved it cleanly with minimal additions: one optional field on
`SkillPackage`, one new collision-check method, one new path-resolver method.

## What Worked

- Six behavioral acceptance tests with full req markers: trustworthy evidence trail.
- `write_agent_md_file` uses `open("x")` (exclusive create) as defense-in-depth behind
  the pre-check guard — double-fencing the collision boundary.
- CLI print updated to `package.target_file or package.target_dir` — callers get the
  useful path for both single-file and directory outputs without breaking existing formats.
- Docs updated across all three reference files (`cli.md`, `skills-export.md`, `README.md`)
  with explicit examples and layout tables.

## Verdict

**PASS** — proportionality, test quality, and FR/code alignment are acceptable.

## Seed

The `model` field is hardcoded to `"Claude Sonnet 4"`. A recurring pattern across export
formats is that defaults hardcoded at write time become stale without a mechanism to
detect drift. Could a CI-level check compare the hardcoded model identifier against a
registry of known-current Copilot model strings, failing the build when the default falls
outside the canonical set? This would turn a documentation maintenance task into an
enforcement gate.
