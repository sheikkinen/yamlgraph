# Watcher2 Post-Merge Inbox Consumption Demo

**Feature:** FR-289 watcher2 post-merge inbox consumption for matching FR items

This demo executes concrete script-contract checks and runtime scenarios against `.chaplain/lib/watcher/post_merge.sh` to prove stale inbox duplicates are consumed after merge.

## What It Verifies

1. `.chaplain/lib/watcher/post_merge.sh`:
   - resolves `FR-[0-9]+` from `PR_NUMBER` (`gh pr view`) with `PR_TITLE` and `TOPIC_FILE` fallbacks,
   - scans `.chaplain/inbox/*.md` for matching token,
   - moves matches to `.chaplain/done/`,
   - creates `.chaplain/done/` when absent,
   - appends timestamp suffix on destination collision,
   - logs explicit no-token no-op and consumed counts.
2. Runtime behavior:
   - PR metadata token resolution consumes only matching inbox files,
   - PR title fallback works and preserves existing done file on collision,
   - no-token path leaves inbox untouched and returns success.
3. `.chaplain/README.md` documents post-merge token cleanup and done-queue semantics.

## Files

- `graph.yaml` - runnable verification graph (tool nodes only; no LLM needed)
- `prompts/context.yaml` - demo context prompt asset
- `demo-output.log` - proof captured from an actual demo run

## Run

```bash
yamlgraph graph lint .chaplain/demos/watcher2-post-merge-inbox-consumption/graph.yaml

yamlgraph graph run .chaplain/demos/watcher2-post-merge-inbox-consumption/graph.yaml \
  --full 2>&1 | tee .chaplain/demos/watcher2-post-merge-inbox-consumption/demo-output.log
```
