# Watcher2 Merged-Branch Collision Guard Demo

**Feature:** FR-286 watcher2 merged-branch collision guard

This demo executes concrete checks against the live watcher2 scripts and README to prove the merged-branch collision guard is present and wired through the skip path.

## What It Verifies

1. `.chaplain/lib/watcher/worktree_setup.sh` performs merged-PR history checks with:
   - `gh pr list`
   - `--state merged`
   - `--head "$WT_BRANCH"`
   - dedicated `return 2` skip code
2. `.chaplain/watcher2.sh` handles skip code `2` as non-failure:
   - does not route to failure handler for this path
   - removes `"$TOPIC_FILE"` from processing
   - writes cycle metrics with skip outcome
3. `.chaplain/README.md` documents the merged-branch guard and merged-state query.

## Files

- `graph.yaml` - runnable verification graph (tool nodes only; no LLM needed)
- `prompts/context.yaml` - demo context prompt asset
- `demo-output.log` - proof captured from an actual demo run

## Run

```bash
yamlgraph graph lint .chaplain/demos/watcher2-merged-branch-collision-guard/graph.yaml

yamlgraph graph run .chaplain/demos/watcher2-merged-branch-collision-guard/graph.yaml \
  --full 2>&1 | tee .chaplain/demos/watcher2-merged-branch-collision-guard/demo-output.log
```
