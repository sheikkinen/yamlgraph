# 2026-05-01: FR-303 Unified Watcher Pipeline — Action Profile Swap

## Trap: Stale Process Interference

During integration testing, an old dispatcher process (from 9:43AM) had already consumed the inbox topic before the new dispatcher (7:57PM) started. The new dispatcher spun indefinitely on an empty inbox. The symptom — "waiting forever" — pointed downstream, but the root cause was an orphaned process from a previous test run.

**Heuristic:** Before starting any integration test that uses background daemons, kill all stale instances of the same process. The run script already cleans up worktrees and branches but didn't kill stale dispatcher PIDs. Process cleanup belongs at the same boundary as file cleanup.

## Trap: Glob Escaping in Zsh

`rm -f .chaplain/processing/smoke-*.md` fails in zsh when no files match — zsh treats unmatched globs as errors (unlike bash). The fix: either `setopt null_glob` or redirect stderr. This bit twice in the same session.

**Heuristic:** When writing cleanup commands that use globs in zsh, always guard against no-match: `rm -f pattern 2>/dev/null` or use `find -delete`.

## Insight: Action Directory Swap as Configuration Algebra

The core insight of FR-303 is that the difference between production and integration is not in the pipeline graph topology — it's in the *implementations* of a few nodes. Extracting `verify_red`, `changelog_gen`, and `failure_cleanup` into custom action types created interception points. The stub directory provides alternative implementations. Context variables handle the remaining bash divergence.

This is configuration algebra: one graph × two action sets × two context vectors = two complete pipelines from a single source of truth.

## Insight: Error Transitions as Safety Net

Adding `error → failed` transitions for all 18 non-terminal states (Phase 0) proved immediately useful — the integration test's git_commit step failed (expected, since stubs don't create real commits), and the pipeline gracefully recovered through `failed → forensics → completed` instead of hanging.

## Seed

Could the action-directory-swap pattern generalize beyond testing? Consider: `actions-dry-run/` for plan-only execution, `actions-audit/` for logging without side effects, `actions-replay/` for deterministic replay from recorded outputs. If three profiles emerge, the pattern graduates from testing trick to architectural primitive.
