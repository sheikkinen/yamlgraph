# Watcher2 Deduplication Gate Demo

**Feature:** FR-287 watcher2 deduplication gate (skip already-completed FR topics)

This demo executes concrete checks and runtime scenarios to prove watcher2 now skips merged FR topics before preflight/worktree setup.

## What It Verifies

1. `.chaplain/lib/watcher/dedup_gate.sh`:
   - extracts `FR-[0-9]+` token,
   - queries merged PRs with `gh pr list --state merged --search "FR-XXX"`,
   - returns skip code `2` on merged hit,
   - degrades gracefully (`return 0` + warning) on `gh` failures.
2. Runtime behavior:
   - merged FR token returns skip code `2`,
   - no FR token returns `0` (pass-through),
   - `gh` query failure remains non-fatal.
3. `.chaplain/watcher2.sh`:
   - calls `dedup_gate` before preflight,
   - treats merged-hit as `CYCLE_OUTCOME="skipped"`,
   - consumes `"$TOPIC_FILE"` and writes cycle metrics.
4. `.chaplain/README.md` documents the dedup gate and merged-search contract.

## Files

- `graph.yaml` - runnable verification graph (tool nodes only; no LLM needed)
- `prompts/context.yaml` - context prompt asset
- `demo-output.log` - proof captured from an actual demo run

## Run

```bash
yamlgraph graph lint examples/demos/watcher2-deduplication-gate/graph.yaml

yamlgraph graph run examples/demos/watcher2-deduplication-gate/graph.yaml \
  --full 2>&1 | tee examples/demos/watcher2-deduplication-gate/demo-output.log
```
