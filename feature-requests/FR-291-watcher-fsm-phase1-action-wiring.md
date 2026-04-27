# Feature Request: Watcher-FSM Phase 1 — Action Wiring

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — APPROVED
**Effort:** 3 days
**Requested:** 2026-04-26

## Summary

Replace log-only action stubs in the Phase 0 FSM configs (`watcher-dispatcher.yaml` and `watcher-pipeline.yaml`) with real action handlers that execute the watcher2 pipeline: bash scripts, yamlgraph graphs, git operations, and pre-commit retry loops.

## Value Statement

The watcher2 daemon transitions from a 524-line implicit-FSM bash script to a declarative, crash-recoverable state machine — enabling audit trails, visual diagnostics, and a foundation for future parallelism — while preserving all existing bash library scripts and yamlgraph graphs.

## Problem

Phase 0 (FR-290) delivered two validated FSM configs with 33 states and correct transition topology, but every state action is a `type: log` stub. The configs cannot drive real work until actions are wired to the bash scripts (`lib/watcher/*.sh`), yamlgraph graphs (`graphs/watcher-plan/`, `graphs/watcher-enforce/`), and git operations that `watcher2.sh` currently orchestrates inline.

## Proposed Solution

Wire real actions into the Phase 0 configs using existing builtin action types where possible, and implement 4 new custom actions where no builtin fits.

### Strategy: Sequential Dispatcher, Maximize Builtins

Phase 1 uses a **sequential dispatcher** — one topic at a time — matching `watcher2.sh`'s current behavior exactly. This eliminates the job queue subsystem (`get_pending_jobs`, `claim_job`, `complete_job`, `pop_from_list`, `wait_for_jobs`, `start_fsm`) from Phase 1 scope. Parallel processing moves to Phase 3.

| Need | Builtin Available? | Action Type |
|---|---|---|
| Run shell commands | Yes — `bash_action` | `bash` with `{var}` templates |
| Run shell + capture JSON context | **No** — bash_action discards stdout | **New: `bash_context`** |
| Pick next inbox file | Yes — `bash_action` | `bash` (find + head) |
| Run yamlgraph pipeline | **No** — no builtin for yamlgraph CLI | **New: `yamlgraph_async`** |
| Git add + commit with lock | **No** — bash_action lacks flock + diff check | **New: `git_commit`** |
| Pre-commit retry loop | **No** — bash_action lacks attempt counter | **New: `precommit`** |

### 1. Dispatcher Config Updates (Sequential)

The Phase 0 dispatcher had 6 states for parallel batch processing. Phase 1 **simplifies to 3 states** matching `watcher2.sh`'s sequential model:

```yaml
# Simplified sequential dispatcher
metadata:
  name: "Watcher2 Dispatcher"
  machine_name: watcher2_dispatcher

initial_state: idle

states:
  - idle
  - syncing_inbox
  - processing_topic
  - stopped

events:
  - "timeout(10)"
  - sync_done
  - topic_found
  - no_topics
  - topic_done
  - stop

transitions:
  - { from: idle, to: syncing_inbox, event: "timeout(10)" }
  - { from: syncing_inbox, to: processing_topic, event: topic_found }
  - { from: syncing_inbox, to: idle, event: no_topics }
  - { from: processing_topic, to: idle, event: topic_done }
  - { from: "*", to: stopped, event: stop }

actions:
  syncing_inbox:
    - type: bash
      command: ".chaplain/lib/watcher/inbox_sync.sh"
    - type: bash_context
      command: |
        TOPIC=$(find .chaplain/inbox -name '*.md' -type f | head -1)
        if [ -z "$TOPIC" ]; then exit 1; fi
        BASENAME=$(basename "$TOPIC")
        mv "$TOPIC" ".chaplain/processing/$BASENAME"
        echo "{\"topic_file\": \".chaplain/processing/$BASENAME\"}"
      capture_keys: [topic_file]
      success: topic_found
      error: no_topics

  processing_topic:
    # Inline pipeline execution — runs all 27 pipeline states sequentially
    # Engine exits naturally at terminal state (completed/stopped/failed)
    - type: bash
      command: >-
        statemachine .chaplain/config/watcher-pipeline.yaml
        --machine-name watcher2_pipeline
        --initial-context '{"topic_file": "{topic_file}"}'
        --actions-dir .chaplain/actions
      success: topic_done
```

This removes `checking_queue`, `spawning_batch`, `waiting_for_batch` and all job queue builtins.

### 2. Pipeline Config Updates

Replace log stubs with real actions in `watcher-pipeline.yaml`. Key examples:

```yaml
# preflight — bash_context captures env vars
actions:
  on_enter:
    type: bash_context
    command: ".chaplain/lib/watcher/preflight.sh"
    success: preflight_done

# worktree_setup — bash_context captures wt_dir, wt_branch, main_dir
actions:
  on_enter:
    type: bash_context
    command: ".chaplain/lib/watcher/worktree_setup.sh --topic {topic_file}"
    capture_keys: [wt_dir, wt_branch, main_dir]
    success: worktree_ready

# planning — yamlgraph_async runs LLM pipeline
actions:
  on_enter:
    type: yamlgraph_async
    graph: graphs/watcher-plan/step-plan.yaml
    vars:
      topic_file: "{topic_file}"
    export_state: true
    cwd: "{wt_dir}"
    success: plan_done

# committing_plan — git_commit with context capture
actions:
  on_enter:
    type: git_commit
    message: "feat: FR plan — {topic_file}"
    add_paths: ["feature-requests/"]
    cwd: "{wt_dir}"
    capture_fr_path: true
    success: plan_committed

# judging — yamlgraph_async with event_map
actions:
  on_enter:
    type: yamlgraph_async
    graph: graphs/watcher-plan/step-judge.yaml
    vars:
      topic_file: "{topic_file}"
    import_state: true
    cwd: "{wt_dir}"
    event_map:
      APPROVE: approve
      REJECT: reject
      AMEND: amend
      SPLIT: split
    success: approve  # default if verdict not recognized

# finalizing — precommit with retry cap
actions:
  on_enter:
    type: precommit
    cwd: "{wt_dir}"
    max_attempts: 5
    success: finalize_done
    retry: precommit_retry

# creating_pr — bash_context captures pr_number, pr_url
actions:
  on_enter:
    type: bash_context
    command: ".chaplain/lib/watcher/create_pr.sh --branch {wt_branch} --dir {wt_dir}"
    capture_keys: [pr_number, pr_url]
    success: pr_created
```

### 3. New Custom Actions (4 modules)

All custom actions extend `BaseAction` from `statemachine_engine.actions.base`.

#### `bash_context_action.py`
- Executes shell command via subprocess
- On exit 0: parses last line of stdout as JSON, merges specified `capture_keys` into FSM context, returns `success` event
- On non-zero exit: returns `error` event (configurable event name)
- Empty/null `capture_keys` values treated as error (returns `error` event)
- Template substitution: `{var}` in command resolved from context

#### `yamlgraph_async_action.py`
- Executes `yamlgraph graph run <graph> --var key=val [--export-state] [--import-state]`
- Resolves graph path relative to `context["main_dir"]`
- Parses output for `event_map` routing (verdict extraction)
- Returns mapped event or default success event

#### `git_commit_action.py`
- Runs `git add <paths> && git diff --cached --quiet` — if nothing staged, returns `nothing_to_commit`
- Runs `git commit -m <message>`
- Optionally detects FR path from `git diff-tree` and captures `fr_path`/`fr_num` in context

#### `precommit_action.py`
- Runs `ruff check --fix && ruff format && pre-commit run --all-files` in `cwd`
- Reads `context["precommit_attempt"]`, increments
- If pre-commit fails and attempt < max_attempts: returns `retry` event (self-loop)
- If pre-commit fails and attempt >= max_attempts: returns `failed` event
- If pre-commit passes: stages fixes via `git add -A`, returns `success` event

### 4. Registration

Register custom actions in `statemachine_engine` action registry so the engine can load them by `type:` name:

```python
# In action registry (e.g., actions/__init__.py or plugin config)
ACTION_TYPES = {
    # ... existing builtins ...
    "bash_context": "statemachine_engine.actions.builtin.bash_context_action.BashContextAction",
    "yamlgraph_async": "statemachine_engine.actions.builtin.yamlgraph_async_action.YamlGraphAsyncAction",
    "git_commit": "statemachine_engine.actions.builtin.git_commit_action.GitCommitAction",
    "precommit": "statemachine_engine.actions.builtin.precommit_action.PrecommitAction",
}
```

### 5. Context Flow

Critical context variables and their lifecycle:

```
dispatcher bash_context (syncing_inbox)
  └─ captures: topic_file

dispatcher bash (processing_topic)
  └─ passes topic_file to pipeline via --initial-context

pipeline worktree_setup (bash_context)
  └─ captures: wt_dir, wt_branch, main_dir

pipeline committing_plan (git_commit)
  └─ captures: fr_path, fr_num

pipeline creating_pr (bash_context)
  └─ captures: pr_number, pr_url
```

All subsequent states can reference these via `{var}` interpolation. No job queue or `job_id` needed — sequential processing uses direct context passing.

### 6. What Is NOT in Scope

- **No logic changes to bash library scripts** — `lib/watcher/*.sh` get only JSON stdout appended (1 line each for `preflight.sh`, `worktree_setup.sh`, `create_pr.sh`, `wait_ci.sh`)
- **No changes to yamlgraph graphs** — `graphs/watcher-plan/`, `graphs/watcher-enforce/` are used as-is
- **No parallel processing** — sequential only; parallel moves to Phase 3
- **No job queue subsystem** — no `get_pending_jobs`, `claim_job`, `complete_job`, `pop_from_list`, `wait_for_jobs`, `start_fsm`; these move to Phase 3
- **No crash recovery implementation** — checkpointing is Phase 2
- **No dedup guard** — guard system is Phase 2
- **No changelog_gen action** — current `watcher2.sh` changelog logic (~lines 320-360) is simple enough to inline in a `bash` action; a dedicated action is premature until proven needed
- **No git flock** — single writer; flock added in Phase 3 when parallel workers introduced

## Design Decision: Sequential over Parallel

`watcher2.sh` processes one topic at a time (`while true; pick one; process; loop`). Phase 1 preserves this behavior exactly. This eliminates:

| Eliminated Component | Why Not Needed |
|---|---|
| `spawning_batch` self-loop | No batch — one topic at a time |
| `waiting_for_batch` polling | No workers to wait for |
| `start_fsm` action | Pipeline runs inline via subprocess |
| SQLite job queue | No job coordination needed |
| `pop_from_list` | No queue to pop from |
| Git flock contention | Single writer — no contention |

The dispatcher collapses from **6 states + 5 builtins** to **4 states (3 active + stopped) + 2 actions**. The pipeline config (27 states) is unchanged.

## Acceptance Criteria

- [ ] AC-01: `watcher-dispatcher.yaml` simplified to 4 states (`idle`, `syncing_inbox`, `processing_topic`, `stopped`) with real action types — no `type: log` stubs
- [ ] AC-02: `watcher-pipeline.yaml` has zero `type: log` stubs — all states have real action types
- [ ] AC-03: Both configs pass `statemachine-validate --strict`
- [ ] AC-04: Both configs pass `statemachine-lint` (0 errors)
- [ ] AC-05: `BashContextAction` exists, extends `BaseAction`, passes unit tests
- [ ] AC-06: `YamlGraphAsyncAction` exists, extends `BaseAction`, passes unit tests
- [ ] AC-07: `GitCommitAction` exists, extends `BaseAction`, passes unit tests
- [ ] AC-08: `PrecommitAction` exists, extends `BaseAction`, passes unit tests
- [ ] AC-09: All 4 custom actions are registered in the action registry
- [ ] AC-10: `BashContextAction.execute()` runs subprocess, parses JSON stdout, merges keys into context
- [ ] AC-11: `YamlGraphAsyncAction.execute()` invokes `yamlgraph graph run`, resolves paths via `main_dir`, routes via `event_map`
- [ ] AC-12: `GitCommitAction.execute()` checks diff, commits, optionally captures `fr_path`
- [ ] AC-13: `PrecommitAction.execute()` retries up to `max_attempts`, returns `retry`/`failed`/`success`
- [ ] AC-14: Context propagation test: `topic_file` → `wt_dir` → `fr_path` → `pr_number` chain verified
- [ ] AC-15: Dispatcher can be started with `statemachine .chaplain/config/watcher-dispatcher.yaml` (smoke test)
- [ ] AC-16: Pipeline can be started with `statemachine .chaplain/config/watcher-pipeline.yaml --initial-context '{"topic_file": "test.md"}'` (smoke test — fails at preflight, but engine loads and enters first state)
- [ ] AC-17: Existing bash library scripts modified only by appending JSON stdout lines (no logic changes)
- [ ] AC-18: No existing yamlgraph graphs modified
- [ ] AC-19: Dispatcher uses no job queue builtins (`get_pending_jobs`, `claim_job`, `complete_job`, `pop_from_list`, `wait_for_jobs`, `start_fsm`)
- [ ] AC-20: Topic file moved from `inbox/` to `processing/` before pipeline starts (prevents re-pick on failure)
- [ ] AC-21: Pipeline `cleaning_up` state removes topic file from `processing/`; `failed` state moves it to `.chaplain/failed/`

## Alternatives Considered

- **Parallel dispatcher from Phase 1:** Rejected — `watcher2.sh` is already sequential; adding job queue, `start_fsm`, `wait_for_jobs` triples dispatcher complexity without behavior change. Parallel deferred to Phase 3.
- **Inline all bash logic in YAML actions:** Rejected — preserves existing tested scripts, reduces blast radius
- **Single `watcher_action.py` mega-module:** Rejected — violates single responsibility; each action is independently testable
- **Skip custom actions, use bash_action for everything:** Rejected — bash_action discards stdout, can't capture context; pre-commit retry logic becomes bash spaghetti
- **Implement changelog_gen as custom action:** Deferred — simple enough for `bash` action until pattern recurs

## Related

- Phase 0: FR-290 (merged PR #245) — declarative configs with log stubs
- Plan: `docs/plan-watcher-fsm.md`
- Action base class: `fsm/src/statemachine_engine/actions/base.py`
- Existing builtins: `fsm/src/statemachine_engine/actions/builtin/`
- Current watcher: `.chaplain/watcher2.sh`
- GitHub Issues: #238, #239, #240
