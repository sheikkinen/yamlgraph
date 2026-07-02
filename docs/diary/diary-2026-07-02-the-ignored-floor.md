# Diary: The Ignored Floor

**Date:** 2026-07-02
**FRs:** FR-651, FR-652, FR-653, FR-654
**Commit:** b290689e

## What happened

Four worldgen quality fixes batched together. After observing pipeline output:
only 3/8 characters had temporal fields, role fields were freetext gibberish,
2/3 reflect loops lost all output to schema mismatch, seed characters stayed
thin while new skeletons got all the attention.

## Trap: `git_clean_insufficient_for_gitignored`

`git clean -fd` does not remove gitignored files. The novel_fandom pipeline
writes dynamic pages into gitignored subdirectories (by design — FR-650).
After a pipeline run, `git clean -fd` leaves these behind, polluting the test
fixture that reads all canon files via rglob. Required `git clean -fdX` to
remove only ignored files.

This is a variant of `workspace_is_not_boundary` — the working tree visible
to git status is not the same as the directory tree visible to `find` or
`rglob`. The test was correct; the cleanup command was incomplete.

## Trap: `confession_line_drift`

Pre-commit hooks validate noqa confessions by file:line. After ruff auto-fixes
(import sorting, whitespace), line numbers shift. CONF-050 was written for
line 27 but ruff moved the code to line 26. The noqa hook catches this —
but the drift happens silently between the "write confession" step and the
"commit" step. Mitigation: always verify line numbers after ruff runs, or
accept that confession line refs are approximate.

## Insight: `batch_boundary_normalization`

Four FRs enforced in ~15 minutes because they all follow the same pattern:
normalize at the boundary where LLM output enters. FR-652 (role enum),
FR-653 (flat dict), FR-654 (depth bonus) — each is a 3-line fix at the
persist/select boundary. The one-law of Scripture proves itself again:
normalize at entry, not downstream.

## Seed

Can the gitignore-vs-git-clean gap be made a pre-commit check? A hook that
warns when gitignored files exist in directories that contain test fixtures
would prevent test pollution from pipeline runs. Or should the test fixture
itself filter to tracked-only files via `git ls-files`?
