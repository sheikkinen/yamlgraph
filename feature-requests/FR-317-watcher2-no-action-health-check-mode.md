# Feature Request: FR-317 watcher2 no-action health check mode

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-03

## Summary

Add a watcher2 **health check mode** that runs the plan → judge → enforce → validate → sanity_check pipeline boundaries without creating feature/code artifacts or opening PRs.

## Value Statement

Watcher operators can verify end-to-end pipeline health after config/tooling changes in minutes, without polluting the repository with test branches and PR noise.

## Problem

Issue #297 asks for a lightweight way to confirm that the watcher pipeline still works after changes (e.g., sanity_check insertion), but today the only realistic proof is a full real cycle that creates commits and PRs.

Current behavior is heavy and side-effectful:

1. `.chaplain/lib/watcher/inbox_sync.sh` imports only `--label chaplain` topics.
2. `.chaplain/config/watcher-dispatcher.yaml` always invokes `.chaplain/config/watcher-pipeline-v2.yaml`.
3. `.chaplain/config/watcher-pipeline-v2.yaml` `done` action always performs `git push`, `gh pr create`, `wait_ci`, and merge.
4. Existing plan/validate/sanity prompts are implementation-focused and include write/commit responsibilities.

No first-class no-action mode exists.

## Objectives

1. Add a dedicated no-action health-check path for watcher2.
2. Exercise the same high-level pipeline stages (plan, judge, enforce, validate, sanity_check).
3. Guarantee zero git commits, zero pushes, and zero PR creation in health-check mode.
4. Keep default `chaplain` flow unchanged for normal feature topics.

## Constraints

- Scope is limited to watcher orchestration under `.chaplain/` and targeted unit tests.
- Do not change YAMLGraph runtime primitives.
- Do not alter existing normal pipeline semantics for standard topics.
- Health-check mode must be explicit (opt-in), not implicit.
- Requirement traceability must be preserved (new tests marked with the appropriate REQ id introduced for this capability).

## Research Findings

### Existing abstractions and prior art

- **Issue ingestion boundary exists:** `inbox_sync.sh` is already the single place where issue labels are queried and topic markdown files are generated.
- **Dispatcher routing boundary exists:** `watcher-dispatcher.yaml` already selects and launches the worker pipeline with context injection.
- **Pipeline boundaries already separated:** watcher v2 has distinct `plan`, `judge`, `enforce_session`, `validate`, and `sanity_check` states.
- **Non-blocking sanity precedent exists:** FR-316 established `sanity_check` with `PASS/WARN` routing.

### Gap check

- No `chaplain-check` label handling exists in `inbox_sync.sh`.
- No alternate worker pipeline is selectable from dispatcher context.
- No no-action prompt set exists for plan/judge/enforce/validate/sanity steps.
- Current done path is always PR-producing.

### Strategic alternatives reviewed

- Prior integration-profile ideas (FR-301/FR-303) are useful precedent but not present as active runnable config in this tree; they do not currently provide a dispatcher-triggered health-check mode.

## Proposed Solution

Implement an explicit label-driven health-check pipeline path.

### 1. Trigger and topic metadata

- Extend `.chaplain/lib/watcher/inbox_sync.sh` to import issues labeled `chaplain-check` (in addition to current `chaplain`).
- For `chaplain-check` imports, write a deterministic marker in topic file header:
  - `<!-- mode: health-check -->`
- Keep existing author allowlist/body truncation behavior unchanged.

### 2. Dispatcher routing

- Update `.chaplain/config/watcher-dispatcher.yaml` `processing_topic` action to:
  1. Read topic header mode marker.
  2. Select pipeline config:
     - default: `.chaplain/config/watcher-pipeline-v2.yaml`
     - health-check: `.chaplain/config/watcher-pipeline-health-check.yaml`
  3. Run `statemachine` with the selected config.

### 3. New health-check worker pipeline

Add `.chaplain/config/watcher-pipeline-health-check.yaml` with explicit no-action semantics:

```text
setup -> plan -> judge -> enforce_session -> validate -> sanity_check -> done -> completed
```

Rules:

- Keep state names aligned with v2 stage boundaries to prove those boundaries fire.
- Reuse existing failure/stop terminal handling pattern.
- `done` performs only safe cleanup/logging (e.g., worktree teardown/topic archival) and **must not** run push/PR/merge commands.

### 4. No-write graph/prompt set for health-check mode

Add dedicated health-check graphs/prompts under `.chaplain/graphs/watcher-check/`:

- `plan-health-check.yaml`
- `judge-health-check.yaml`
- `enforce-health-check.yaml`
- `validate-health-check.yaml`
- `sanity-check-health-check.yaml`

Prompt contracts:

- Read-only diagnostics only (tool availability, command execution viability, graph invocation health).
- Explicitly forbid writing files/commits/PR operations.
- Return deterministic routing tokens (e.g., `APPROVE`, `PASS`, `WARN`) so FSM transitions are machine-verifiable.

## Acceptance Criteria

- [x] **AC-01:** `inbox_sync.sh` supports importing `chaplain-check` issues and tags imported topic files with `mode: health-check`.
- [x] **AC-02:** Standard `chaplain` topics remain on existing default worker pipeline path.
- [x] **AC-03:** Dispatcher can select health-check pipeline config based on topic metadata.
- [x] **AC-04:** `.chaplain/config/watcher-pipeline-health-check.yaml` exists and includes states for `plan`, `judge`, `enforce_session`, `validate`, and `sanity_check`.
- [x] **AC-05:** Health-check pipeline contains no `git push`, `gh pr create`, or `gh pr merge` commands.
- [x] **AC-06:** Health-check pipeline `done` state is side-effect-safe (cleanup/logging only).
- [x] **AC-07:** Dedicated health-check graphs/prompts exist for all five stage boundaries.
- [x] **AC-08:** Health-check prompts explicitly prohibit write operations (file edits, git commit/push, PR operations, diary generation).
- [x] **AC-09:** `sanity_check` still routes with `PASS/WARN` semantics in health-check mode, and `WARN` remains non-blocking.
- [x] **AC-10:** Acceptance tests fail on current implementation and pass after implementation.

## Failing Acceptance Tests (RED)

Create `tests/unit/test_fr317_watcher2_no_action_health_check_mode.py`:

1. `test_ac01_inbox_sync_imports_chaplain_check_and_tags_health_mode`
2. `test_ac02_standard_chaplain_topics_keep_default_pipeline`
3. `test_ac03_dispatcher_selects_health_check_pipeline_from_topic_mode`
4. `test_ac04_health_pipeline_has_required_stage_states`
5. `test_ac05_health_pipeline_has_no_push_or_pr_commands`
6. `test_ac06_health_pipeline_done_is_cleanup_only`
7. `test_ac07_health_check_graphs_and_prompts_exist`
8. `test_ac08_health_check_prompts_forbid_write_side_effects`
9. `test_ac09_health_sanity_check_warn_path_is_non_blocking`

RED command:

```bash
pytest tests/unit/test_fr317_watcher2_no_action_health_check_mode.py -q --no-cov
```

## Alternatives Considered

1. **Add `yamlgraph watcher check` CLI command**
   Rejected for this FR: touches CLI surface and expands scope beyond watcher2 pipeline orchestration.
2. **Run normal pipeline then auto-delete PR/branch**
   Rejected: still creates external side effects and repository noise.
3. **Reuse existing plan/enforce/sanity prompts with flags**
   Rejected: current prompt contracts are write-oriented; a dedicated no-write prompt boundary is clearer and safer.

## Related

- GitHub issue #297: <https://github.com/sheikkinen/yamlgraph/issues/297>
- Requested topic path: `.chaplain/processing/gh-297.md` (not present in this worktree)
- `.chaplain/lib/watcher/inbox_sync.sh`
- `.chaplain/config/watcher-dispatcher.yaml`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `feature-requests/FR-316-watcher2-sanity-check-state.md`
- `feature-requests/FR-301-watcher-fsm-integration-test.md`
- `feature-requests/FR-303-unified-watcher-pipeline-action-profiles.md`
