# Diary: FR-175 Sequential Enforcement Mode

**Date:** 2026-03-09
**FR:** FR-175

## Cognitive Trap: Parallelism Theatre

The original `watch.sh` design spawned enforcement pipelines with `nohup ... &` — fire-and-forget parallelism that felt fast but violated the implicit contract of shared bookkeeping files.

**Trap name:** Parallelism Theatre
**Definition:** Concurrent execution that appears efficient but silently creates race conditions on shared state.

The symptom was obvious in hindsight: every second PR conflicted on ARCHITECTURE.md, CHANGELOG.md, and req_coverage.py. But the root cause — concurrent modification of sequential-by-nature bookkeeping — took multiple merge sessions to surface.

## Insight: Sequential Correctness Over Parallel Speed

The fix was trivially simple: remove `&` and `nohup`, run foreground, wait for exit. Total wall-clock time increases from T to N×T, but:

1. **Zero conflicts** — each PR merges to updated `main` before the next starts
2. **Clear error feedback** — exit codes visible immediately, not buried in logs
3. **Simpler mental model** — inbox = queue, not concurrent workload

The lesson generalizes: **when writes touch shared files, serialize at the orchestration layer**, not downstream in conflict resolution.

## Heuristic for Graduation

```yaml
parallelism_theatre:
  symptom: "Frequent merge conflicts on 'bookkeeping' files"
  cause: "Concurrent processes modifying sequential-by-nature state"
  cure: "Serialize at spawn point; accept linear wall-clock cost"
  test: "If 2+ processes can touch the same file, one must wait"
```

This pattern applies beyond git: database migrations, config file updates, any append-only logs.

## Seed

> What other "parallelism theatre" patterns exist in the codebase — places where we spawn concurrent work that implicitly depends on sequential completion?

Candidates to audit:
- `map` node parallel execution (do outputs ever share state keys?)
- MCP tool invocations (if multiple graphs call same tool simultaneously?)
- Checkpoint writes (concurrent state commits to same thread?)
