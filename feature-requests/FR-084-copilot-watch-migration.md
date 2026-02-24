# Feature Request: FR-084 Migrate watch.sh to YAMLGraph Copilot Graph

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-02-24

## Summary

Replace `.chaplain/watch.sh` (bash polling loop calling `copilot` CLI directly) with `yamlgraph graph run` invocations using the copilot node type (FR-081). The bash script becomes a thin polling wrapper; all workflow logic moves into a YAMLGraph graph.

## Problem

`watch.sh` duplicates the Plan→Judge workflow that `examples/copilot/graph.yaml` already models as a YAMLGraph pipeline. The shell script hard-codes prompts inline, bypasses YAMLGraph's structured execution (state, tracing, error handling), and cannot benefit from future graph improvements (checkpointing, retry, observability). Two implementations of the same workflow drift independently.

Specifically, the current `watch.sh`:
1. **Hard-codes prompts** as inline strings in `copilot -p "..."` calls
2. **Bypasses state management** — no structured `CopilotResult`, no `state_key`, no checkpointing
3. **Cannot be traced** via LangSmith or YAMLGraph observability
4. **Duplicates** what `examples/copilot/graph.yaml` already demonstrates

## Proposed Solution

### 1. Create `.chaplain/graph.yaml`

Copy and adapt `examples/copilot/graph.yaml` as the production chaplain workflow. Remove the `summarize` node (not needed for the watch loop). Keep the linear `plan→judge→END` flow — the AMEND retry loop is handled externally by the polling wrapper (Judge moves amended files back to `inbox/`, which the polling loop picks up on the next iteration).

```yaml
# .chaplain/graph.yaml
version: "1.0"
name: chaplain-plan-judge
description: Plan → Judge workflow for feature request creation

prompts_relative: true
prompts_dir: prompts

state:
  topic_file: str
  drafts_dir: str

nodes:
  plan:
    type: copilot
    prompt: plan
    backend: cli
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    variables:
      topic_file: "{state.topic_file}"
      drafts_dir: "{state.drafts_dir}"
    state_key: plan_result
    timeout: 300

  judge:
    type: copilot
    prompt: judge
    backend: cli
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    variables:
      drafts_dir: "{state.drafts_dir}"
    state_key: judge_result
    timeout: 300

edges:
  - from: START
    to: plan
  - from: plan
    to: judge
  - from: judge
    to: END
```

### 2. Simplify `watch.sh` to a thin polling wrapper

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

INBOX=".chaplain/inbox"
DRAFTS=".chaplain/drafts"
POLL=5

echo "👀 Watching $INBOX/"

while true; do
    topic_file=$(find "$INBOX" -name "*.md" -type f 2>/dev/null | head -1)
    [[ -z "$topic_file" ]] && { sleep "$POLL"; continue; }

    echo "📋 Processing: $topic_file"
    yamlgraph graph run .chaplain/graph.yaml \
        --var topic_file="$topic_file" \
        --var drafts_dir="$DRAFTS" \
        --full

    echo ""
done
```

The AMEND retry loop is external: Judge moves the file back to `inbox/`; the polling loop picks it up on the next iteration. This is the same mechanism used by the current `watch.sh` — no in-graph router is needed.

### 3. Copy and adapt prompts

Copy `examples/copilot/prompts/{plan,judge}.yaml` to `.chaplain/prompts/`. The Judge prompt already handles APPROVE/AMEND/REJECT with file moves.

### File structure after migration

```
.chaplain/
├── graph.yaml          # Production Plan→Judge graph
├── prompts/
│   ├── plan.yaml       # Adapted from examples/copilot
│   └── judge.yaml      # Adapted from examples/copilot
├── watch.sh            # Thin polling loop → yamlgraph graph run
├── inbox/              # Drop topics here
└── drafts/             # FR under review
```

### Flow

```
inbox/topic.md
    ↓ yamlgraph graph run .chaplain/graph.yaml
    ↓ plan node
drafts/XXX-slug.md
    ↓ judge node
    ├── APPROVE → feature-requests/XXX-slug.md (done)
    ├── AMEND   → inbox/XXX-slug.md (re-enters polling loop)
    └── REJECT  → feature-requests/XXX-slug.md (Status: Rejected)
```

## Implementation Steps

1. Create `.chaplain/prompts/` directory
2. Copy `examples/copilot/prompts/plan.yaml` → `.chaplain/prompts/plan.yaml`
3. Copy `examples/copilot/prompts/judge.yaml` → `.chaplain/prompts/judge.yaml`
4. Create `.chaplain/graph.yaml` (as specified above)
5. Replace `watch.sh` with the thin polling wrapper
6. Verify: `yamlgraph graph lint .chaplain/graph.yaml` passes
7. End-to-end test: drop a topic in inbox, confirm draft appears in drafts (manual)
8. Update `examples/copilot/README.md` with cross-reference to `.chaplain/` as production consumer

## Acceptance Criteria

- [x] `.chaplain/graph.yaml` exists and passes `yamlgraph graph lint`
- [x] `.chaplain/prompts/{plan,judge}.yaml` contain the Plan and Judge prompts
- [x] `watch.sh` calls `yamlgraph graph run .chaplain/graph.yaml` instead of raw `copilot` CLI
- [x] `watch.sh` remains a thin polling loop (no inline prompts, no file ops)
- [x] `examples/copilot/` is preserved as-is (it demonstrates the copilot node type)
- [ ] End-to-end test: dropping a topic in inbox produces a draft in drafts (manual)
- [x] Documentation updated in `examples/copilot/README.md` with cross-reference

## Alternatives Considered

1. **Keep watch.sh as-is** — Works, but two implementations of the same workflow diverge. The shell version misses structured state, tracing, and error handling.
2. **Delete examples/copilot/** — Loses the copilot node demo. Better to keep the example as a showcase and make `.chaplain/` the production consumer.
3. **Add file-watching to YAMLGraph itself** — Over-engineering. Polling loop in bash is fine; the graph handles the workflow logic.
4. **Add in-graph router for AMEND loop** — Unnecessary. The external polling loop already handles AMEND retries via the filesystem (Judge moves file back to inbox; polling picks it up). Adding a router would duplicate this mechanism.

## Related

- `068-chaplain-watch.md` — Original chaplain watch loop proposal
- `FR-081` — Copilot node type (enables this migration)
- `.chaplain/watch.sh` — Current implementation to migrate
- `examples/copilot/` — Source pattern to promote
