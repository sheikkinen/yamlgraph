# Feature Request: Watcher-FSM Phase 0 — Declarative FSM Configs

**Priority:** HIGH
**Type:** Feature
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-04-26

## Summary

Create two declarative YAML state machine configs for the watcher2-FSM migration: a dispatcher (6 states) and a pipeline worker (27 states). Validate both with `statemachine-validate --strict` and generate Mermaid diagrams.

## Value Statement

The watcher2 pipeline gains a declarative, auditable FSM definition — enabling parallel workers, crash recovery, and visual state diagrams — without modifying any existing code.

## Problem

`watcher2.sh` is a 524-line hand-rolled FSM in bash. State transitions are implicit in control flow. There is no crash recovery, no parallelism, and no visual representation of the pipeline. Phase 0 establishes the declarative foundation that later phases will wire to actions.

## Proposed Solution

Two new YAML configs under `.chaplain/config/`, validated by `statemachine-engine` tooling:

### 1. Dispatcher: `.chaplain/config/watcher-dispatcher.yaml`

Controller that polls inbox and spawns one worker per topic.

**6 states:** `idle`, `syncing_inbox`, `checking_queue`, `spawning_batch`, `waiting_for_batch`, `stopped`

**Transitions:**
```yaml
transitions:
  - { from: idle, to: syncing_inbox, event: "timeout(10)" }
  - { from: syncing_inbox, to: checking_queue, event: sync_done }
  - { from: checking_queue, to: idle, event: no_jobs }
  - { from: checking_queue, to: spawning_batch, event: jobs_found }
  - { from: spawning_batch, to: spawning_batch, event: spawned }
  - { from: spawning_batch, to: waiting_for_batch, event: batch_empty }
  - { from: waiting_for_batch, to: waiting_for_batch, event: "timeout(30)" }
  - { from: waiting_for_batch, to: idle, event: batch_complete }
  - { from: "*", to: stopped, event: stop }
```

**Actions:**
- `syncing_inbox`: `bash` → `inbox_sync_wrapper.sh`
- `checking_queue`: `get_pending_jobs` with `machine_type: watcher2_pipeline`
- `spawning_batch`: `pop_from_list` + `claim_job` + `add_to_list` + `start_fsm`
- `waiting_for_batch`: `wait_for_jobs`

### 2. Pipeline Worker: `.chaplain/config/watcher-pipeline.yaml`

Runs the full plan→judge→enforce→merge cycle for a single topic.

**27 states:** `preflight`, `worktree_setup`, `planning`, `committing_plan`, `researching`, `committing_research`, `writing_tests`, `verifying_red`, `judging`, `splitting`, `implementing`, `committing_implementation`, `testing_demo`, `committing_tests`, `critiquing`, `changelog_gen`, `finalizing`, `pushing`, `creating_pr`, `waiting_ci`, `remediating_ci`, `merging`, `cleaning_up`, `completed`, `failed`, `forensics`, `stopped`

**Key patterns:**
- Events section MUST use dict format (not list) to support `context_map` (NC-120)
- `timeout(600)` on all 9 `yamlgraph_async` states → `failed`
- Judging verdict routing: `event_map: {approve→approve, reject→reject, amend→amend, split→split}`
- Retry loops: `finalizing` self-loop (capped at 5), `waiting_ci ↔ remediating_ci`
- Failure path: `failed → forensics → completed`
- Global stop: `from: "*", to: stopped, event: stop`
- Context maps: `worktree_ready` → `wt_dir`/`wt_branch`/`main_dir`, `pr_created` → `pr_number`/`pr_url`

### 3. Validation

Generate diagrams to `.chaplain/docs/fsm-diagrams/`.

**Note on action stubs:** Phase 0 configs may include action type/description stubs to document intent, but custom action modules (e.g., `yamlgraph_async`) don't need to exist yet. The validator checks transition coverage for known action types, not module imports. Alternatively, action sections can be left empty (transitions-only) — Phase 1 adds actions.

## Acceptance Criteria

- [ ] AC-01: `.chaplain/config/watcher-dispatcher.yaml` exists with 6 states and 9 transition rules
- [ ] AC-02: `.chaplain/config/watcher-pipeline.yaml` exists with 27 states
- [ ] AC-03: Both pass `statemachine-validate --strict`
- [ ] AC-04: Both pass `statemachine-lint`
- [ ] AC-05: Mermaid diagrams generated in `.chaplain/docs/fsm-diagrams/`
- [ ] AC-06: Dispatcher diagram shows idle polling loop and batch spawn/wait cycle
- [ ] AC-07: Pipeline diagram shows all 4 verdict paths from `judging`
- [ ] AC-08: Pipeline diagram shows `timeout(600)` on all `yamlgraph_async` states
- [ ] AC-09: Pipeline diagram shows `finalizing` retry self-loop
- [ ] AC-10: Pipeline diagram shows `waiting_ci ↔ remediating_ci` loop
- [ ] AC-11: Pipeline diagram shows `failed → forensics → completed` path
- [ ] AC-12: No orphaned or unreachable states in either config
- [ ] AC-13: No existing files modified (purely additive)

## Alternatives Considered

- Single monolithic config: rejected — dispatcher/worker separation enables parallelism and independent lifecycle
- Code-first FSM definition: rejected — YAML-first aligns with YAMLGraph philosophy and enables diagram generation

## Related

- Plan: `docs/plan-watcher-fsm.md` (Phase 0 section)
- Reference pattern: `examples/fsm-router/config/router.yaml`
- GitHub Issues: #238, #239, #240
- Depends on: `statemachine-engine` (`fsm/` subdirectory)
