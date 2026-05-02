# Context: Watcher FSM Pipeline

## What It Is

The watcher is an **automated feature delivery pipeline** that watches `.chaplain/inbox/` for feature proposals (markdown files) and autonomously plans, judges, implements, tests, and merges them as PRs.

## Architecture: Two Nested FSMs

### 1. Dispatcher (`watcher-dispatcher.yaml`)

Simple polling loop — picks one topic at a time:

```
idle → (10s timeout) → syncing_inbox → topic_found → processing_topic → topic_done → idle
```

- Lives at `.chaplain/config/watcher-dispatcher.yaml`
- Calls `inbox_sync.sh` to pull GitHub issues into inbox
- Spawns the pipeline FSM as a subprocess per topic
- Sequential: one topic at a time

### 2. Pipeline Worker (`watcher-pipeline.yaml`)

The heavy worker — runs the full plan→judge→enforce→merge cycle for a single topic.

- Lives at `.chaplain/config/watcher-pipeline.yaml`
- Current version: 20+ states (being simplified via FR-305)
- Target version (v2): 5 operational states

## Key Directories

| Path | Purpose |
|------|---------|
| `.chaplain/config/` | FSM YAML configs (dispatcher + pipeline) |
| `.chaplain/actions/` | Python action classes for the FSM engine |
| `.chaplain/graphs/watcher-plan/` | YAMLGraph graphs for planning phase |
| `.chaplain/graphs/watcher-enforce/` | YAMLGraph graphs for enforcement phase |
| `.chaplain/graphs/watcher-forensic/` | Post-mortem analysis graph |
| `.chaplain/graphs/copilot/` | Main copilot workflow graph (session demo) |
| `.chaplain/lib/watcher/` | Shell scripts (preflight, worktree, PR, CI, cleanup) |
| `.chaplain/inbox/` | Incoming topics (markdown files) |
| `.chaplain/processing/` | Topic currently being processed |
| `.chaplain/failed/` | Topics that failed pipeline |
| `fsm/` | The statemachine-engine itself (separate project) |
| `fsm/src/statemachine_engine/core/engine.py` | Core async engine |
| `fsm/src/statemachine_engine/actions/` | Built-in action types |

## FSM Engine (`fsm/` subproject)

The `statemachine-engine` is a general-purpose YAML-driven FSM:
- Async event loop with Unix socket communication
- Pluggable action system (actions auto-discovered from directory)
- `context_map` on events to promote payload fields to durable context
- Real-time event emission for monitoring UI
- CLI: `statemachine <config.yaml> [--actions-dir DIR] [--initial-context JSON] [--machine-name NAME] [--debug]`

### Action Types Available

| Type | Class | Purpose |
|------|-------|---------|
| `bash` | Built-in | Run shell command, emit success/error event |
| `bash_context` | `bash_context_action.py` | Run shell, capture JSON output into context |
| `yamlgraph_async` | `yamlgraph_async_action.py` | Run `yamlgraph graph run` as subprocess, route via `event_map` |
| `git_commit` | `git_commit_action.py` | Stage + commit with message template |
| `precommit` | `precommit_action.py` | Run pre-commit with retry loop (max N) |

### Context Propagation

All action configs support `{placeholder}` interpolation from context dict. Key context fields:
- `topic_file` — path to the inbox markdown
- `fr_path` — path to the created feature request
- `wt_dir` — worktree directory
- `wt_branch` — worktree branch name
- `main_dir` — original repo directory
- `session_id` — copilot session for continuation

## Copilot Session Continuations (FR-105)

The `copilot` node type supports `resume: "{state.prev_result.session_id}"` to continue a previous session. This lets multiple nodes share the same LLM context window.

Key implementation:
- `yamlgraph/node_factory/copilot_node.py` — builds CLI command with `--resume <id>`
- `yamlgraph/models/schemas.py` — `CopilotResult.session_id` field
- Session ID extracted from `--share` file via regex (`SHARE_FILE_SESSION_PATTERN`)
- Graph example: `.chaplain/graphs/copilot/graph.yaml` (plan→research→judge sharing session)

## FR-305: Simplification Plan (In Progress)

Target: collapse 20+ states into 5:

```
plan → commit_plan → judge →(approve)→ enforce_session → done
                       ↑ revise              │ timeout
                       └────────┘            ▼
                                          failed
```

### Design Decisions

1. **Plan** — single copilot node doing worktree+FR+research+tests (new session)
2. **Commit plan** — `git_commit` action, one commit for all planning artifacts
3. **Judge** — copilot node with `resume: session_id`, routes APPROVE/REVISE/REJECT
4. **Enforce session** — single copilot node with `resume: session_id` + `allow_all_tools: true`. The implement→precommit→pytest→fix loop runs **inside one copilot invocation**. No FSM transitions for retries — the LLM iterates within its session.
5. **Done** — bash: push, create PR, wait CI, merge, cleanup

### Why Same-Session Enforce+Evaluate

The LLM retains full context of what it implemented, what errors occurred, and what it already tried. Each evaluate→fix cycle is a continuation, not a cold-start. This eliminates the primary failure mode of the current pipeline: context loss between subprocess invocations.

## Current `watcher2.sh` (Shell Implementation)

The shell-based watcher at `.chaplain/watcher2.sh` implements the same pipeline in bash with `yamlgraph graph run` calls chained by shell logic. It predates the FSM version and serves as the reference for expected behavior. Key differences from FSM:
- Uses `--export-state` / `--import-state` for inter-step state passing
- Manually commits between steps
- No retry loops for pre-commit (just fails)

## Running

### Production (full LLM pipeline)

```bash
# Start dispatcher + monitoring UI (port 3001)
.chaplain/scripts/start-system.sh

# Or manual single-run (no UI):
statemachine .chaplain/config/watcher-dispatcher.yaml \
  --actions-dir .chaplain/actions \
  --debug
```

### Integration test (no LLM, deterministic)

```bash
# Seeds a topic, runs full pipeline with bash stubs, reports pass/fail
scripts/run-integration-test.sh
```

Uses `.chaplain/actions-stub/` (echo stubs replacing all LLM steps). Tests the mechanical pipeline: git worktree, PR creation, CI polling, merge.

### Validation

```bash
# Validate FSM configs
statemachine-validate --strict .chaplain/config/watcher-dispatcher.yaml
statemachine-validate --strict .chaplain/config/watcher-pipeline.yaml

# Lint graphs
yamlgraph graph lint .chaplain/graphs/watcher-plan/*.yaml

# Unit tests
pytest tests/unit/test_fr291_watcher_fsm_phase1.py tests/unit/test_fr292_pipeline_path_alignment.py -v --no-cov
```

## Related FRs

| FR | Topic |
|----|-------|
| FR-105 | Copilot session continuations |
| FR-273 | Session chain with shell steps |
| FR-274 | Session ID extraction from share files |
| FR-290 | Watcher FSM Phase 0 configs |
| FR-291 | Phase 1 action wiring |
| FR-292 | Pipeline path alignment |
| FR-295 | Phase 2 single worker validation |
| FR-303 | Unified pipeline action profiles |
| FR-305 | Pipeline FSM simplification (this work) |
