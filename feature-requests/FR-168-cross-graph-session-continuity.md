# Feature Request: FR-168 Cross-Graph Session Continuity

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-03-09

## Summary

Thread the Copilot CLI session ID from the plan-judge pipeline (`examples/copilot/graph.yaml`) to the enforce pipeline (`examples/enforce/graph.yaml`) so the enforcer resumes the same session instead of starting from scratch.

## Value Statement

The enforce pipeline gains full conversation context from the plan-judge phase, eliminating redundant codebase exploration and FR re-reading at the start of implementation.

## Problem

The Chaplain pipeline executes as two separate graph runs:

1. **Plan-Judge** (`examples/copilot/graph.yaml`): plan → judge → summarize → write_diary
2. **Enforce** (`examples/enforce/graph.yaml`): implement → test_and_demo → precommit_check → submit_pr

Within each graph, session continuity already works (FR-105):
- Judge resumes plan's session via `resume: "{state.plan_result.session_id}"`
- Enforce phases 2–4 resume phase 1's session via `resume: "{state.implement_result.session_id}"`

But **between** the two graphs, context is lost. When `watch.sh` spawns the enforce pipeline, the `implement` node starts a brand-new Copilot CLI session. It must:
- Re-read the feature request file
- Re-discover the codebase structure
- Rebuild understanding of the problem, constraints, and judge's verdict

This is wasted work — the plan-judge session already holds all that context at `~/.copilot/session-state/<uuid>/`.

## Proposed Solution

Thread the session ID from plan-judge output through `watch.sh` to the enforce pipeline via file-based handoff.

### 1. Export session ID from plan-judge graph

Add a python tool node (or `exports:` config) to `copilot/graph.yaml` that writes `judge_result.session_id` to a well-known file:

```yaml
# examples/copilot/graph.yaml (new node after write_diary)
tools:
  write_session_id_tool:
    type: python
    module: examples.shared.session_handoff
    function: write_session_id

nodes:
  # ... existing nodes ...

  export_session:
    type: python
    tool: write_session_id_tool
    state_key: session_exported

edges:
  # ... existing edges, add before END ...
  - from: write_diary
    to: export_session
  - from: export_session
    to: END
```

The tool writes session ID to `tmp/last-plan-session-id`:

```python
# examples/shared/session_handoff.py
from pathlib import Path

def write_session_id(state: dict) -> dict:
    """Write judge session ID to tmp/ for cross-graph handoff."""
    session_id = None
    judge_result = state.get("judge_result")
    if judge_result and hasattr(judge_result, "session_id"):
        session_id = judge_result.session_id
    elif isinstance(judge_result, dict):
        session_id = judge_result.get("session_id")

    out = Path("tmp/last-plan-session-id")
    out.parent.mkdir(exist_ok=True)
    out.write_text(session_id or "")
    return {"session_exported": bool(session_id)}
```

### 2. Thread session ID through watch.sh

```bash
# .chaplain/watch.sh — after graph run
session_id=""
if [[ -f tmp/last-plan-session-id ]]; then
    session_id=$(cat tmp/last-plan-session-id)
    rm -f tmp/last-plan-session-id
fi

# Pass to enforce if available
if [[ -n "$new_fr" && -n "$session_id" ]]; then
    nohup scripts/enforce_worktree.sh "$new_fr" --session-id "$session_id" > "$LOG" 2>&1 &
elif [[ -n "$new_fr" ]]; then
    nohup scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 &
fi
```

### 3. Accept session ID in enforce_worktree.sh

```bash
# scripts/enforce_worktree.sh — new optional flag
SESSION_ID=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --session-id) SESSION_ID="$2"; shift 2 ;;
        *) FR_PATH="$1"; shift ;;
    esac
done

# Pass to graph run if available
yamlgraph graph run examples/enforce/graph.yaml \
    --var fr_path="$FR_PATH" \
    --var branch="$BRANCH" \
    ${SESSION_ID:+--var plan_session_id="$SESSION_ID"} \
    --full
```

### 4. Resume in enforce graph

```yaml
# examples/enforce/graph.yaml
state:
  fr_path: str
  branch: str
  plan_session_id: str   # Optional: session ID from plan-judge pipeline
  # ... existing state keys ...

nodes:
  implement:
    type: copilot
    prompt: enforce-implement
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.plan_session_id}"  # Resume plan-judge session if available
    variables:
      fr_path: "{state.fr_path}"
      branch: "{state.branch}"
    state_key: implement_result
    timeout: 3600
```

When `plan_session_id` is empty/None, the `resume` expression resolves to a falsy value and the copilot node starts a fresh session (existing FR-105 behavior: `if resume:` guard in `_execute_cli`).

## Acceptance Criteria

- [x] Plan-judge graph exports `judge_result.session_id` to `tmp/last-plan-session-id`
- [x] `watch.sh` reads session ID file and passes to `enforce_worktree.sh`
- [x] `enforce_worktree.sh` accepts optional `--session-id` flag
- [x] Enforce graph's `implement` node resumes plan-judge session when session ID is provided
- [x] Enforce pipeline still works when no session ID is provided (graceful degradation — fresh session)
- [x] Session ID file is cleaned up after consumption (no stale state)
- [x] Unit test: session handoff tool writes and reads correctly
- [x] Integration test: enforce graph accepts `plan_session_id` variable and passes `--resume` flag
- [x] Documentation updated in `reference/graph-yaml.md` (cross-graph session pattern)

## Constraints

1. **Copilot sessions are global** (`~/.copilot/session-state/<uuid>/`), not per-directory. Resuming from a worktree (different CWD) should work, but the copilot CLI's working directory context changes. The `enforce-implement` prompt must re-orient the session to the worktree path.
2. **Session expiry**: Copilot CLI sessions may expire or be garbage-collected (FR-138). The resume must handle a stale/missing session gracefully — if `--resume` fails, the CLI may start a fresh session or error. The `on_error` handling should cover this.
3. **No silent fallback** (FR-165): If a session ID is provided but resume fails, the node should raise, not silently start fresh. This is already the copilot CLI's behavior.
4. **File-based handoff** is chosen over stdout parsing for robustness. The session ID file is an explicit contract, not a fragile grep on human-readable output.

## Alternatives Considered

### A. Unified single graph
Merge plan-judge-enforce into one graph. Rejected because:
- Enforce runs in a git worktree (different directory) requiring shell-level orchestration
- Enforce is spawned asynchronously with `nohup`
- Plan-judge and enforce have fundamentally different lifecycles and failure modes

### B. Parse session ID from `--full` output
Grep `session_id:` from `yamlgraph graph run --full` stdout. Rejected because:
- Output format is human-readable, not machine-parseable
- Fragile if output format changes
- Violates "no silent fallback" — grep failure would silently skip session threading

### C. Add `--output-json` CLI flag
New CLI feature to emit final state as JSON. Would be useful generally but is a larger scope change (separate FR). The file-based handoff solves the immediate need without framework changes.

### D. LangGraph checkpointer-based state sharing
Use `--thread` flag and shared checkpointer to persist state across runs. Rejected because:
- Copilot CLI session ID is external to LangGraph state persistence
- Would require configuring a persistent checkpointer (SQLite/Redis) for the chaplain pipeline
- Overengineered for passing a single string value

## Related

- **FR-081**: Copilot node type (foundation)
- **FR-105**: Copilot session continuations (within a single graph — this FR extends it across graphs)
- **FR-138**: Copilot session cleanup (session lifecycle management)
- **FR-106**: Enforce pipeline via git worktree (the enforce architecture)
- **FR-128**: YAMLGraphication of enforcer (enforce graph YAML)
- **Files**: `examples/copilot/graph.yaml`, `examples/enforce/graph.yaml`, `.chaplain/watch.sh`, `scripts/enforce_worktree.sh`, `yamlgraph/node_factory/copilot_node.py`
