# Watcher2-FSM: Migration Plan

> Replace the 524-line bash orchestration script with a declarative FSM that is visible, resumable, parallelizable, and self-monitoring.

## Problem

`watcher2.sh` is a hand-rolled finite state machine in bash. Its states are implicit in control flow (`if/continue`), its context lives in shell variables (lost on crash), it processes one topic at a time, and observability is `tail -f logs/*.log`. The script works, but it cannot:

- Resume after a crash (topic goes to `.chaplain/failed/`)
- Process multiple topics in parallel
- Show live pipeline state in a UI
- Be diagrammed or validated statically

## End State

A **declarative FSM system** using `statemachine-engine`:

- **Dispatcher** (controller): polls inbox, processes one topic at a time (Phase 1: sequential; Phase 3: parallel workers)
- **Pipeline worker** (per topic): runs the full plan→judge→enforce→merge cycle
- **Web UI**: live Mermaid diagram + Kanban board at `localhost:3001` (Phase 3)
- **Startup**: two commands replace the entire bash script

```bash
# Phase 1: sequential
statemachine .chaplain/config/watcher-dispatcher.yaml \
  --machine-name watcher2_dispatcher \
  --actions-dir .chaplain/actions

# Phase 3: + parallel workers + UI
statemachine-ui --port 3001 --project-root . &
```

## Architecture

### Phase 1: Sequential Dispatcher ✅ COMPLETED (FR-291, PR #246)

```
┌─────────────────────────────────────────────────────┐
│        watcher2-dispatcher (sequential)           │
│                                                     │
│  idle ─timeout(10)─► syncing_inbox                   │
│   ▲                       │                            │
│   │              ┌────────┤                            │
│   │    no_topics │  topic_found                     │
│   │              │        │                            │
│   │              │        ▼                            │
│   │              │  processing_topic                 │
│   │              │   (statemachine pipeline           │
│   │              │    subprocess, blocks until done)  │
│   │              │        │                            │
│   └──────────────┴────────┘                            │
│                   topic_done                        │
│                                                     │
│  from "*" ─► stopped (event: stop)                   │
└─────────────────────────────────────────────────────┘
                    │ statemachine subprocess
                    ▼
```

### Phase 3: Parallel Dispatcher (future)
┌─────────────────────────────────────────────────────────────────────┐
│                    watcher2-dispatcher (always running)              │
│                                                                     │
│  idle ─timeout(10)─► syncing_inbox ─► checking_queue                │
│   ▲                                      │                          │
│   │                           ┌──────────┤                          │
│   │                 no_jobs   │    jobs_found                       │
│   │                           │          │                          │
│   │                           │          ▼                          │
│   │                           │    spawning_batch                   │
│   │                           │     (pop_from_list → start_fsm      │
│   │                           │      → loop until batch_empty)      │
│   │                           │          │                          │
│   │                           │          ▼                          │
│   │                           │    waiting_for_batch                │
│   │                           │     (wait_for_jobs, timeout(30))    │
│   │                           │          │                          │
│   └───────────────────────────┴──────────┘                          │
│                                                                     │
│  from "*" ──► stopped (event: stop)                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ start_fsm (one per topic)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              watcher2-pipeline-{topic_id} (per topic)               │
│                                                                     │
│  ┌─── PLANNING PHASE ──────────────────────────────────────────┐    │
│  │                                                              │    │
│  │  preflight ─► worktree_setup ─► planning ─► committing_plan │    │
│  │                                                  │           │    │
│  │                                    researching ◄─┘           │    │
│  │                                        │                     │    │
│  │                                  committing_research         │    │
│  │                                        │                     │    │
│  │                                  writing_tests               │    │
│  │                                        │                     │    │
│  │                                  verifying_red               │    │
│  │                                        │                     │    │
│  │                                     judging                  │    │
│  │                               ┌────┼────┬───┐                │    │
│  │                        reject │  amend  │ split │ approve   │    │
│  └───────────────────────────┼───┼─────────┼──────┼────────────┘    │
│                              │   │         │      │                  │
│                              │   │   ┌─────┘      │                  │
│                              │   │   │ (re-queue   │                  │
│                              │   │   │  sub-topics │                  │
│                              │   │   ▼  as new     │                  │
│                              │   │ splitting       │                  │
│                              │   │   │  jobs)       │                  │
│                              ▼   ▼   ▼              ▼                  │
│                            failed  failed       implementing           │
│                                                      │                 │
│  ┌─── ENFORCEMENT PHASE ────────────────────────────────────────┐     │
│  │                                                               │     │
│  │                         implementing                          │     │
│  │                              │                                │     │
│  │                   committing_implementation                   │     │
│  │                              │                                │     │
│  │                        testing_demo                           │     │
│  │                              │                                │     │
│  │                     committing_tests                          │     │
│  │                              │                                │     │
│  │                         critiquing                            │     │
│  │                              │                              │     │
│  │                        changelog_gen                         │     │
│  │                              │                              │     │
│  │                     finalizing ◄── precommit_retry           │     │
│  │                              │                              │     │
│  │                          pushing                            │     │
│  │                              │                              │     │
│  │                        creating_pr                          │     │
│  │                              │                              │     │
│  │                  waiting_ci ◄──── remediating_ci             │     │
│  │                      │                                      │     │
│  │                   merging                                   │     │
│  │                      │                                      │     │
│  │                  cleaning_up                                │     │
│  └──────────────────────┼──────────────────────────────────────┘     │
│                         │                                            │
│                     completed                                        │
│                                                                      │
│  failed ─► forensics ─► completed                                    │
│  from "*" ─► stopped (event: stop)                                   │
└──────────────────────────────────────────────────────────────────────┘
```

## State-to-Action Mapping

Every watcher2 step maps to either a `bash` action or a `yamlgraph_async` action.

### Dispatcher (Phase 1: Sequential) ✅

| State | Action Type | What It Does | Success Event |
|---|---|---|---|
| `syncing_inbox` | `bash_context` | Runs `inbox_sync.sh`, finds next topic file, moves to `processing/` | `topic_found` / `no_topics` |
| `processing_topic` | `bash` | Runs pipeline via `statemachine` subprocess | `topic_done` |

### Pipeline Worker

| State | Action Type | Source | Success Event |
|---|---|---|---|
| `preflight` | `bash_context` | `lib/watcher/preflight.sh` | `preflight_ok` |
| `worktree_setup` | `bash_context` | `lib/watcher/worktree_setup.sh` → captures `wt_dir`, `wt_branch`, `main_dir` | `worktree_ready` |
| `planning` | `yamlgraph_async` | `graphs/watcher-plan/step-plan.yaml` | `plan_done` |
| `committing_plan` | `bash` | `git add feature-requests/ && git commit` | `committed` |
| `researching` | `yamlgraph_async` | `graphs/watcher-plan/step-research.yaml` | `research_done` |
| `committing_research` | `bash` | `git add && git commit` | `committed` |
| `writing_tests` | `yamlgraph_async` | `graphs/watcher-plan/step-acceptance.yaml` | `tests_written` |
| `verifying_red` | `bash` | `pytest $TEST_FILES -x --no-cov -q` | `red_verified` |
| `judging` | `yamlgraph_async` | `graphs/watcher-plan/step-judge.yaml` | `approve` / `reject` / `amend` / `split` |
| `splitting` | `bash` | Commits judged FR, queues sub-topics as new jobs via `statemachine-db add-job` | `split_done` → `failed` (current cycle ends; sub-topics re-enter as new inbox items) |
| `implementing` | `yamlgraph_async` | `graphs/watcher-enforce/step-implement.yaml` | `implement_done` |
| `committing_implementation` | `bash` | `git add -A && git commit -m "feat: watcher2 — implementation"` | `committed` |
| `testing_demo` | `yamlgraph_async` | `graphs/watcher-enforce/step-test-demo.yaml` | `test_done` |
| `committing_tests` | `bash` | `git add -A && git commit -m "test: watcher2 — tests and demos"` | `committed` |
| `critiquing` | `yamlgraph_async` | `graphs/watcher-enforce/step-critique.yaml` | `critique_done` |
| `changelog_gen` | `bash` | FR-283 fragment generation script | `changelog_done` |
| `finalizing` | `bash` | `ruff check --fix && pre-commit run --all-files` | `finalize_done` / `precommit_retry` |
| `pushing` | `bash` | `git push origin {wt_branch}` | `push_done` |
| `creating_pr` | `bash_context` | `lib/watcher/create_pr.sh` → captures `pr_number`, `pr_url` | `pr_created` |
| `waiting_ci` | `bash_context` | `lib/watcher/wait_ci.sh` → captures `ci_result` | `ci_passed` / `ci_failed` |
| `remediating_ci` | `yamlgraph_async` | `graphs/watcher-enforce/step-ci-remediate.yaml` | `remediated` / `failed` |
| `merging` | `bash` | `gh pr merge` | `merged` |
| `cleaning_up` | `bash` | `lib/watcher/worktree_teardown.sh` + `lib/watcher/post_merge.sh` | `cleanup_done` |
| `forensics` | `yamlgraph_async` | `graphs/watcher-forensic/graph.yaml` | `forensics_done` |

## Context Variables (Pipeline Worker)

Passed from dispatcher via `--initial-context`, then accumulated through the pipeline:

| Variable | Set By | Used By |
|---|---|---|
| `topic_file` | dispatcher (--initial-context) | planning |
| `topic_basename` | dispatcher (--initial-context) | logging |
| `wt_dir` | worktree_setup | all subsequent states (working directory) |
| `wt_branch` | worktree_setup | pushing, creating_pr, waiting_ci |
| `fr_path` | committing_plan | implementing, critiquing, finalizing |
| `fr_num` | committing_plan | changelog_gen |
| `pr_number` | creating_pr | remediating_ci |
| `pr_url` | creating_pr | logging |
| `ci_attempt` | remediating_ci | loop counter (max 2) |
| `precommit_attempt` | finalizing | retry counter (max 5) |
| `verdict` | judging (yamlgraph_async event_map) | splitting (determines sub-topic creation) |

## File Structure

```
.chaplain/
├── config/
│   ├── watcher-dispatcher.yaml       # Controller FSM — Phase 1: 4 states (idle, syncing_inbox, processing_topic, stopped); Phase 3: 6 states (parallel)
│   └── watcher-pipeline.yaml         # Worker FSM — 27 states, all actions wired
├── actions/
│   ├── yamlgraph_async_action.py     # Copied from examples/fsm-router, adapted path resolution ✅
│   ├── bash_context_action.py        # Bash + stdout JSON → context capture ✅
│   ├── git_commit_action.py          # git add + commit, no --no-verify ✅; flock added in Phase 3
│   └── precommit_action.py           # pre-commit with retry counter ✅
├── scripts/
│   ├── inbox_sync_wrapper.sh         # Phase 3: calls inbox_sync.sh then inserts jobs
│   ├── validate-fsm-single.sh        # Phase 2 validation (NEW)
│   ├── validate-fsm-parallel.sh      # Phase 3 validation (NEW)
│   └── stress-test-git-locks.sh      # Phase 3 git lock stress test (NEW)
├── graphs/                           # YAMLGraph LLM pipelines (EXIST — used by watcher2.sh)
│   ├── watcher-plan/                 # step-plan, step-research, step-acceptance, step-judge ✅
│   ├── watcher-enforce/              # step-implement, step-test-demo, step-critique, step-ci-remediate, step-finalize ✅
│   └── watcher-forensic/             # graph.yaml + prompts/ ✅
├── lib/watcher/                      # Called by bash/bash_context actions
│   ├── inbox_sync.sh                 # UNCHANGED (wrapper calls it)
│   ├── preflight.sh                  # +1 line: stdout JSON on success ✅
│   ├── worktree_setup.sh             # +1 line: stdout JSON with wt_dir/wt_branch/main_dir ✅
│   ├── worktree_teardown.sh          # UNCHANGED
│   ├── create_pr.sh                  # +1 line: stdout JSON with pr_number/pr_url ✅
│   ├── wait_ci.sh                    # +1 line: stdout JSON with ci_result ✅
│   ├── merge_pr.sh                   # UNCHANGED
│   ├── post_merge.sh                 # UNCHANGED
│   └── metrics.sh                    # UNCHANGED — called at cleanup; DB metrics supplement
├── docs/fsm-diagrams/                # Generated Mermaid diagrams (NEW)
└── watcher2.sh                       # Phase 4: replaced by FSM launcher
```

## What Changes at Each Layer

| Layer | Before (watcher2.sh) | After (watcher-fsm) |
|---|---|---|
| Orchestration | 524-line bash script with implicit FSM | Two YAML configs (~100 lines total) |
| State | Implicit in control flow + bash vars | Explicit FSM states in SQLite |
| Concurrency | Serial — one topic at a time | Phase 1: sequential (same); Phase 3: parallel via `start_fsm` |
| Failure | `handle_failure()` + `.chaplain/failed/` | `failed` state → forensics → `completed` |
| Resumability | None — crash = restart from scratch | SQLite persists state; restart = resume |
| Visibility | `tail -f logs/*.log` | Live Web UI: Mermaid diagram + Kanban board |
| CI remediation | Nested `for ci_attempt in 1 2` | `waiting_ci ↔ remediating_ci` loop with counter in context |
| Metrics | `write_cycle_metrics` in bash | DB job lifecycle provides timing automatically; `metrics.sh` still called at `cleaning_up` for existing log-based metrics. DB metrics supplement (not replace) the current format during migration; Phase 4 evaluates whether log metrics can be dropped. |
| Inbox polling | `find "$INBOX" -name "*.md" \| head -1` | `bash_context` find + head (Phase 1); `check_database_queue` with priority ordering (Phase 3) |
| GitHub sync | `inbox_sync.sh` populates filesystem | Phase 1: `bash` calls original `inbox_sync.sh` directly; Phase 3: `inbox_sync_wrapper.sh` adds `statemachine-db add-job` |

## Web UI Experience

Open `http://localhost:3001`:

- **Left panel**: live Mermaid diagram of the dispatcher. The `spawning_batch` node pulses.
- **Kanban columns**: `planning` (1 topic), `implementing` (1 topic), `waiting_ci` (1 topic). Three cards moving in parallel.
- **Click a worker card**: drills into that pipeline's Mermaid diagram. Shows current state `critiquing`. Context panel shows `fr_path`, `pr_number`, `wt_branch`.
- **Activity log**: scrolling real-time entries — `[watcher2_pipeline_47] planning → researching`, `[watcher2_pipeline_45] waiting_ci → merging`.
- **Failed card**: topic enters `failed` → forensic analysis runs → card turns red → read the generated diary entry, decide whether to re-queue.

## Migration Phases

### Phase 0: Config Only ✅ COMPLETED (FR-290, PR #245)
- Write `watcher-dispatcher.yaml` and `watcher-pipeline.yaml`
- Validate with `statemachine-validate` and `statemachine-lint`
- Generate diagrams with `statemachine-diagrams`
- Deliverable: validated YAML configs + Mermaid diagrams

### Phase 1: Action Scripts (Sequential) ✅ COMPLETED (FR-291, PR #246)
- Simplified `watcher-dispatcher.yaml` to 4 states (idle, syncing_inbox, processing_topic, stopped)
- Copied `yamlgraph_async_action.py` from `examples/fsm-router/actions/`
- Wrote 4 custom actions: `bash_context`, `git_commit`, `precommit`, `yamlgraph_async`
- Wired all 27 pipeline states with real action types
- Existing lib scripts augmented with JSON stdout for `bash_context` capture
- 50 unit tests in `tests/unit/test_fr291_watcher_fsm_phase1.py` (CI-safe with skip markers)
- No `changelog_gen_action.py` — changelog generation uses `yamlgraph_async` action instead
- Deliverable: all actions runnable, individually testable, sequential end-to-end

### Phase 1.5: Pipeline Config Path Alignment ✅ COMPLETED (FR-292, PR #247)
Fixed all 9 graph path references. Removed 2 unreachable states (`splitting`, `committing_tests`). Converted `changelog_gen` to bash. Pipeline version 0.2.0, 25 states.

**Path corrections needed in `watcher-pipeline.yaml`:**

| Config references | Actual path | Fix |
|---|---|---|
| `graphs/watcher-plan/step-plan.yaml` | `.chaplain/graphs/watcher-plan/step-plan.yaml` | Prefix with `.chaplain/` |
| `graphs/watcher-plan/step-research.yaml` | `.chaplain/graphs/watcher-plan/step-research.yaml` | Prefix with `.chaplain/` |
| `graphs/watcher-plan/step-tests.yaml` | `.chaplain/graphs/watcher-plan/step-acceptance.yaml` | Fix path + rename to `step-acceptance` |
| `graphs/watcher-plan/step-judge.yaml` | `.chaplain/graphs/watcher-plan/step-judge.yaml` | Prefix with `.chaplain/` |
| `graphs/watcher-plan/step-split.yaml` | **DOES NOT EXIST** | Create or handle split via bash (watcher2.sh does it inline) |
| `graphs/watcher-plan/step-implement.yaml` | `.chaplain/graphs/watcher-enforce/step-implement.yaml` | Fix directory: `watcher-enforce/` not `watcher-plan/` |
| `graphs/watcher-plan/step-test-demo.yaml` | `.chaplain/graphs/watcher-enforce/step-test-demo.yaml` | Fix directory |
| `graphs/watcher-plan/step-critique.yaml` | `.chaplain/graphs/watcher-enforce/step-critique.yaml` | Fix directory |
| `graphs/watcher-plan/step-changelog.yaml` | **DOES NOT EXIST** | Create (watcher2.sh generates changelog fragments via bash, not LLM) |
| `graphs/watcher-plan/step-remediate.yaml` | `.chaplain/graphs/watcher-enforce/step-ci-remediate.yaml` | Fix directory + rename |
| `graphs/watcher-plan/step-forensics.yaml` | `.chaplain/graphs/watcher-forensic/graph.yaml` | Fix directory + rename |

**Missing graphs to create or convert to bash:**
- `step-split.yaml` — rare case; could be a bash action that splits the FR and re-queues sub-topics
- `step-changelog.yaml` — watcher2.sh generates fragments via bash script, not LLM; convert `changelog_gen` action to `bash` type or create a simple LLM graph

**Note on `yamlgraph_async` path resolution:** The `yamlgraph_async_action.py` resolves graph paths relative to `context['main_dir']`. When the pipeline runs inside a worktree, `main_dir` points to the project root. All graph paths must be relative to project root.

- Deliverable: pipeline config references match actual graph files; `statemachine-validate --strict` still passes

### Phase 2: Single-Worker Validation ← NEXT
- **Prerequisite**: Phase 1.5 path alignment ✅
- **Coexistence**: `watcher2.sh` remains functional and is the production fallback throughout Phase 2–3. The FSM dispatcher runs on a separate test inbox (`.chaplain/inbox-fsm/`). Both systems can operate simultaneously without conflict.
- Run dispatcher + single pipeline worker end-to-end on a test topic
- Verify: state transitions match watcher2.sh behavior exactly
- Verify: worktree lifecycle (setup/teardown) survives all exit paths
- Verify: forensics runs on failure states
- Verify: SPLIT verdict creates sub-topic jobs and terminates the current worker
- Verify: all 4 verdict paths (APPROVE, REJECT, AMEND, SPLIT) produce correct transitions
- **Rollback**: if validation fails, stop the FSM dispatcher. `watcher2.sh` continues processing the production inbox. Debug forward on the FSM config using the test inbox. No data loss possible — FSM uses its own job queue, watcher2.sh uses its own filesystem inbox.
- Deliverable: one topic processed through FSM, PR merged

### Phase 3: Parallel + UI
- Enable `spawning_batch` to spawn multiple workers
- Add `statemachine-ui` to launcher
- Verify: concurrent worktree isolation (separate branches, separate dirs)
- Verify: git lock contention handled (worktrees share `.git`)
- **Enhancement: amend self-correction loop.** Add `amend` → `planning` transition with the judge's feedback injected as context (`judge_feedback` variable). This turns a dead-end into a self-correcting cycle — the FSM's resumability makes this safe (cap at 2 amend loops via `amend_attempt` counter, then → `failed`). Not in initial scope because it changes behavior vs. watcher2.sh, but the FSM architecture makes it trivial to add.
- Deliverable: 3 topics processed in parallel, visible in Kanban UI

### Phase 4: Retire watcher2.sh
- Replace `watcher2.sh` with launcher script:
  ```bash
  #!/bin/bash
  statemachine .chaplain/config/watcher-dispatcher.yaml \
    --machine-name watcher2_dispatcher \
    --actions-dir .chaplain/actions &
  statemachine-ui --port 3001 --project-root . &
  wait
  ```
- Archive `watcher2.sh` to `docs/archive/`
- Deliverable: old script retired, FSM is production

## Risks

| Risk | Mitigation |
|---|---|
| Git lock contention with parallel worktrees (Phase 3 only) | Not applicable in Phase 1 (sequential = single writer). Phase 3: (1) All git write operations acquire `flock /tmp/yamlgraph-git.lock`. (2) `git gc --auto=0` in worker worktrees. (3) Dispatcher runs `git fetch` once per cycle. (4) Phase 3 stress test: 3 workers for 10 cycles. |
| Context lost on process crash | SQLite `machine_state` persists; statemachine-engine resumes from last committed state |
| `yamlgraph_async` socket dispatch from worktree dir | Resolve graph paths relative to project root, not cwd |
| Inbox sync race (dispatcher polls while sync writes) | Phase 1: not possible (sequential — sync completes before topic pick). Phase 3: `claim_job` atomicity prevents double-processing |
| Pre-commit retry loop as FSM self-transition | Cap with `precommit_attempt` counter in context; `failed` after 5 |
| CI poll as blocking wait | `timeout(30)` event drives polling loop; non-blocking |
| LLM step hangs (no response) | All `yamlgraph_async` pipeline states (`planning`, `researching`, `implementing`, `critiquing`, etc.) have a `timeout(600)` (10 min) transition to `failed`. Prevents zombie workers. |
| Verdict extraction from LLM output | The `yamlgraph_async` action's `event_map` parameter maps LLM output values to FSM events. The judge graph returns a `judge_result` field with structured output containing a verdict string. The action config specifies: `event_key: judge_result`, `event_map: { approve: approve, reject: reject, amend: amend, split: split }`. The `_extract_event()` helper in `yamlgraph_async_action.py` handles both plain strings and Pydantic model fields. Fallback: if no verdict matches, `success` event fires (defaults to `approve` — same as current watcher2.sh `UNKNOWN` handling). |

## What Stays Unchanged

- All YAMLGraph graphs (`.chaplain/graphs/`) — the LLM intelligence layer ✅ confirmed: all graphs exist and are used by watcher2.sh
- Bash lib scripts (`.chaplain/lib/watcher/`) — the leaf operations (JSON stdout lines added ✅; originals untouched)
- The inbox format (markdown files in `.chaplain/inbox/`)
- GitHub issue sync (remote inbox via `chaplain` label)
- The feature request workflow (plan → judge → enforce)
- Pre-commit hooks and CI gates

## What Changed (Phase 0–1)

- `watcher-dispatcher.yaml` — created (4-state sequential dispatcher)
- `watcher-pipeline.yaml` — created (27-state pipeline worker with all actions wired)
- 4 custom actions in `.chaplain/actions/` — `bash_context`, `yamlgraph_async`, `git_commit`, `precommit`
- Lib scripts — `preflight.sh`, `worktree_setup.sh`, `create_pr.sh`, `wait_ci.sh` got JSON stdout lines
- 50 unit tests in `tests/unit/test_fr291_watcher_fsm_phase1.py`

## What Still Needs to Change (Phase 1.5+)

- `watcher-pipeline.yaml` — graph path references need alignment to actual `.chaplain/graphs/` locations
- `splitting` and `changelog_gen` actions — convert from `yamlgraph_async` to `bash` (no LLM graphs exist for these)
- `inbox_sync.sh` — Phase 3: wrapped by `inbox_sync_wrapper.sh` that adds `statemachine-db add-job` after sync
- `watcher2.sh` — Phase 4: replaced by FSM launcher (archived to `docs/archive/`)
- `metrics.sh` — still called, but DB metrics provide additional timing data

---

## Phased Implementation Plan

File-level actions for each phase. New files marked **(NEW)**, changed files marked **(CHANGED)**.

### Phase 0: FSM Configs + Validation ✅ COMPLETED (FR-290, PR #245)

Delivered: Two validated YAML configs. Dispatcher (6-state parallel design) and pipeline (27-state worker). Both pass `statemachine-validate --strict`. Mermaid diagrams generated.

---

### Phase 1: Action Scripts (Sequential) ✅ COMPLETED (FR-291, PR #246)

Delivered:
- Dispatcher simplified to 4 states (idle, syncing_inbox, processing_topic, stopped)
- 4 custom actions: `bash_context_action.py`, `yamlgraph_async_action.py`, `git_commit_action.py`, `precommit_action.py`
- All 27 pipeline states wired with real action types (bash, bash_context, yamlgraph_async, git_commit, precommit)
- Lib scripts (`preflight.sh`, `worktree_setup.sh`, `create_pr.sh`, `wait_ci.sh`) augmented with JSON stdout
- `syncing_inbox` merged into single `bash_context` action (inbox sync + topic find + mv)
- Dispatcher uses `statemachine` subprocess (not `statemachine-run`) for pipeline
- ActionLoader class naming: uses `capitalize()` per `_`-separated word (e.g., `YamlgraphAsyncAction` not `YamlGraphAsyncAction`)
- 50 unit tests in `tests/unit/test_fr291_watcher_fsm_phase1.py` with CI skip markers (`requires_fsm_engine`, `requires_fsm_cli`)
- Linter limitation: `statemachine-lint` hardcodes known action types — custom types trigger E008; tests use `--select E001,...,E007`

**Key decisions recorded:**
- No `changelog_gen_action.py` — changelog generation uses `yamlgraph_async` action instead
- No `inbox_sync_wrapper.sh` in Phase 1 — bash action calls `inbox_sync.sh` directly
- Re-generate diagrams

---

### Phase 1.5: Pipeline Config Path Alignment ✅ COMPLETED (FR-292, PR #247)

Delivered: All 9 graph path references fixed. 2 states removed (`splitting` — no graph exists, route to `failed`; `committing_tests` — redundant, route `test_demo_done` → `critiquing`). `changelog_gen` converted from `yamlgraph_async` to `bash` (inline script). 14 acceptance tests. Pipeline version 0.2.0 (25 states, down from 27).

#### `.chaplain/config/watcher-pipeline.yaml` **(CHANGED)**
Fix graph paths in all `yamlgraph_async` action blocks:
- Planning phase: `graphs/watcher-plan/` → `.chaplain/graphs/watcher-plan/`
- `step-tests.yaml` → `step-acceptance.yaml` (filename mismatch)
- Enforcement phase: `graphs/watcher-plan/` → `.chaplain/graphs/watcher-enforce/`
- `step-remediate.yaml` → `step-ci-remediate.yaml` (filename mismatch)
- `step-forensics.yaml` → `.chaplain/graphs/watcher-forensic/graph.yaml` (dir + filename mismatch)

#### Missing graph decisions:
- `step-split.yaml`: Convert `splitting` action from `yamlgraph_async` to `bash` (watcher2.sh handles split inline — commits judged FR, creates sub-topic files in inbox)
- `step-changelog.yaml`: Convert `changelog_gen` action from `yamlgraph_async` to `bash` (watcher2.sh generates changelog fragments via shell script, not LLM)

#### Validation
- Run `statemachine-validate --strict .chaplain/config/watcher-pipeline.yaml`
- Verify each referenced graph file exists on disk

---

### Phase 2: Single-Worker Validation ← NEXT

**Goal**: One topic processed through the full FSM pipeline, producing a merged PR. watcher2.sh remains the production fallback.

**Prerequisite**: Phase 1.5 path alignment ✅.

#### Setup
- Create `.chaplain/inbox-fsm/` test inbox directory
- Configure dispatcher to use `inbox-fsm/` (via `--initial-context '{"inbox_dir":".chaplain/inbox-fsm/"}'`)
- Write a simple test topic: `.chaplain/inbox-fsm/test-fsm-migration.md` with a trivial feature request

#### Validation script: `.chaplain/scripts/validate-fsm-single.sh` **(NEW)**
- Start dispatcher in foreground (single cycle, not loop): process one topic then stop
- Monitor state transitions via `statemachine-events --machine watcher2_pipeline_* --format compact`
- Assert: all expected states visited in order (preflight → ... → cleaning_up → completed)
- Assert: PR created and merged on GitHub
- Assert: worktree cleaned up (no stale dirs in `tmp/worktrees/`)
- Assert: metrics written (both `metrics.sh` JSON and DB job record)

#### Test scenarios (run manually, one at a time)
1. **Happy path**: approve verdict → full enforcement → PR merged
2. **Reject path**: craft a topic that the judge will reject → verify `judging → failed → forensics → completed`
3. **Preflight failure**: run without being on main branch → verify `preflight → failed → forensics → completed`
4. **LLM timeout**: set `timeout(10)` on planning step temporarily → verify timeout → failed transition
5. **Pre-commit failure**: introduce a ruff violation → verify `finalizing → precommit_retry → finalizing` loop, then fix

---

### Phase 3: Parallel + UI + Amend Loop

**Goal**: Multiple topics processing simultaneously, visible in Web UI.

#### `.chaplain/config/watcher-dispatcher.yaml` **(CHANGED — expand to parallel)**
- Replace 3-state sequential dispatcher with 6-state parallel dispatcher
- Add states: `checking_queue`, `spawning_batch`, `waiting_for_batch`
- Add job queue builtins: `get_pending_jobs`, `claim_job`, `complete_job`, `pop_from_list`, `wait_for_jobs`
- Add `start_fsm` action to spawn pipeline workers as subprocesses
- Write `inbox_sync_wrapper.sh` to bridge inbox files → job queue

#### `.chaplain/config/watcher-pipeline.yaml` **(CHANGED)**
- Add `amend` → `planning` transition with `amend_attempt` counter
- Add `amend_attempt` context variable (set by `set_context` action in `judging` state on amend event)
- Add guard: if `amend_attempt >= 2` → `failed` (requires a custom action or conditional logic)

#### `.chaplain/config/watcher-dispatcher.yaml` **(CHANGED)**
- Verify `spawning_batch` self-loop handles 3+ topics correctly
- Add `set_context` action to initialize `active_jobs` list before spawning

#### Validation script: `.chaplain/scripts/validate-fsm-parallel.sh` **(NEW)**
- Queue 3 test topics simultaneously in `.chaplain/inbox-fsm/`
- Start dispatcher
- Monitor via `statemachine-events` that 3 workers spawn
- Assert: all 3 reach `completed` (or specific expected outcomes)
- Assert: no git lock errors in logs
- Assert: worktree dirs are unique and correctly isolated

#### `.chaplain/scripts/stress-test-git-locks.sh` **(NEW)**
- Spawn 3 workers that each do 10 rapid `git add/commit` cycles
- Verify: no lock contention errors, no corrupted commits
- Verify: `flock` serialization works correctly

#### Launcher: `.chaplain/watcher2-fsm.sh` **(NEW)**
- Coexistence launcher — runs FSM dispatcher alongside (separate inbox)
- Starts `statemachine-ui` on port 3001
- Cleanup trap for graceful shutdown

---

### Phase 4: Retire watcher2.sh

**Goal**: FSM is production. Old script archived.

#### `.chaplain/watcher2.sh` **(CHANGED → launcher)**
- Replace entire content with:
  ```bash
  #!/bin/bash
  set -euo pipefail
  cd "$(dirname "$0")/.."
  statemachine .chaplain/config/watcher-dispatcher.yaml \
    --machine-name watcher2_dispatcher \
    --actions-dir .chaplain/actions &
  statemachine-ui --port 3001 --project-root . &
  trap 'kill $(jobs -p) 2>/dev/null' SIGINT SIGTERM
  wait
  ```

#### `docs/archive/watcher2-bash.sh` **(NEW)**
- Archive of the original 524-line watcher2.sh for reference

#### `.chaplain/config/watcher-dispatcher.yaml` **(CHANGED)**
- Switch inbox from test (`inbox-fsm/`) to production (`.chaplain/inbox/`)

#### Cleanup
- Remove `.chaplain/inbox-fsm/` test inbox
- Remove validation scripts (or move to `docs/archive/`)
- Update `CLAUDE.md` to reference FSM config instead of watcher2.sh
- Update `.github/copilot-instructions.md` "Submitting Proposals" section
