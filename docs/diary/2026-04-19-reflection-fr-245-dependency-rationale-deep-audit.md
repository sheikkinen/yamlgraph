# Diary: FR-245 Dependency Rationale Deep Audit

**Date:** 2026-04-19
**FR:** FR-245
**Phase:** Enforce

## Cognitive Process

The feature itself was straightforward — add `find_orphaned()` and `find_stale_modules()` to complement the existing one-direction audit. The real challenge emerged during pre-commit: the stale-module check flagged three paths that were "stale" only in a worktree context.

## Trap: Filesystem as Truth vs Intent as Truth

The initial `find_stale_modules()` used `Path.exists()` which returns `False` for broken symlinks. But `fsm/` is a deliberate symlink to an external project — its presence *is* the documentation of intent, even when the target is unreachable. The fix: check `is_symlink()` as a parallel escape hatch.

For `projects/outcaller/` the path was genuinely stale — never tracked in git, gitignored, and absent. The rationale registry silently referenced a phantom directory. This is exactly the drift FR-245 was designed to catch.

## Insight

Module-path validation must distinguish three states:
1. **Exists** — path resolves to a real file/directory
2. **Symlink** — developer placed an intentional reference (tolerate)
3. **Missing** — no trace on disk or in git (report as stale)

`Path.exists()` collapses states 2 and 3 into the same `False`. The one-line fix (`not resolved.exists() and not resolved.is_symlink()`) restores the distinction.

## Heuristic

> When validating filesystem paths, distinguish "broken reference" (symlink to missing target) from "no reference" (nothing on disk). A broken symlink is documentation of intent; a missing path is drift.

## Seed

Could the rationale registry include a `scope: external | tracked` field to explicitly declare whether a module path is expected to exist in all environments (tracked) or only in development setups with external project symlinks (external)? This would make the validation context-aware rather than relying on symlink detection as a proxy.
