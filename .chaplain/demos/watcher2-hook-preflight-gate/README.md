# Watcher2 Hook Preflight Gate Demo

**Feature:** FR-288 watcher2 hook preflight gate (fail-closed enforcement infrastructure check)

This demo executes concrete runtime scenarios proving watcher2 preflight now blocks cycles when git hook enforcement is disabled or broken.

## What It Verifies

1. `.chaplain/lib/watcher/preflight.sh` contract:
   - reads local `core.hooksPath`,
   - enforces policy: unset or `.git/hooks` only,
   - requires executable `.git/hooks/pre-commit` and `.git/hooks/commit-msg`,
   - logs explicit remediation commands.
2. Runtime matrix:
   - empty `core.hooksPath` fails,
   - non-default `core.hooksPath` fails,
   - missing required hook fails,
   - non-executable required hook fails,
   - healthy default hooks pass.
3. `.chaplain/watcher2.sh` boundary:
   - `if ! preflight; then` guard runs before `Step 1/4: Plan`.
4. `.chaplain/README.md` documents enforced hook preflight contract.

## Files

- `graph.yaml` - runnable verification graph (tool nodes only; no LLM needed)
- `prompts/context.yaml` - context prompt asset
- `demo-output.log` - proof captured from an actual demo run

## Run

```bash
yamlgraph graph lint .chaplain/demos/watcher2-hook-preflight-gate/graph.yaml

yamlgraph graph run .chaplain/demos/watcher2-hook-preflight-gate/graph.yaml \
  --full 2>&1 | tee .chaplain/demos/watcher2-hook-preflight-gate/demo-output.log
```
