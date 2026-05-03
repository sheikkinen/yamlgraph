# Feature Request: FR-317 `.chaplain/README.md` watcher2 FSM v2 accuracy refresh

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-03

## Summary

Update `.chaplain/README.md` so it documents the current watcher2 FSM v2 pipeline behavior (states, dispatcher loop, sanity-check stage, action types, model mapping, key scripts, and processing-dir hygiene) based on source-of-truth configs.

## Value Statement

Watcher2 operators and maintainers get an accurate runbook for the live FSM pipeline, reducing operational mistakes caused by stale documentation.

## Problem

GitHub issue #298 requests a refresh of `.chaplain/README.md` with current watcher2 FSM details. The current README still mixes older narrative flow with partial newer content and misses key v2 specifics.

Observed gaps in current `.chaplain/README.md`:

1. No explicit v2 state chain (`setup -> plan -> capture_fr -> judge -> enforce_session -> validate -> sanity_check -> precommit_check -> done`) plus terminal states.
2. No concrete dispatcher polling contract (`timeout(10)`) tied to `watcher-dispatcher.yaml` and `inbox_sync.sh`.
3. No explicit sanity-check placement/behavior (`validate -> sanity_check`, `warn` non-blocking to `precommit_check`).
4. No model mapping table for plan/judge/enforce/validate/sanity nodes.
5. No action-type view grounded in v2 config.
6. No explicit note that `.chaplain/processing/` can accumulate stale items and requires periodic manual cleanup.

Research also found two requested details that conflict with current code truth and must be handled explicitly in docs wording:

- `enforce-session` currently uses `gpt-5.3-codex` (not `claude-sonnet-4-6`).
- `failure_cleanup` action exists in `.chaplain/actions/` but is not wired in `watcher-pipeline-v2.yaml` (failed state currently uses `bash`).

## Objectives

1. Document watcher2 FSM v2 states and transitions accurately from `.chaplain/config/watcher-pipeline-v2.yaml`.
2. Document dispatcher poll/sync behavior from `.chaplain/config/watcher-dispatcher.yaml`.
3. Add a concise model mapping section tied to graph configs.
4. Clarify action types: active in v2 vs available action plugin (`failure_cleanup`) to avoid false claims.
5. Preserve and cross-reference existing retry/requeue guidance from FR-314.
6. Add acceptance tests that fail on current README and enforce the updated contract.

## Constraints

- Scope is docs + docs-tests only (`.chaplain/README.md` and `tests/unit/*`).
- Do not change FSM runtime behavior, graph configs, or model assignments.
- Keep single responsibility: README accuracy for watcher2 FSM v2 operations.
- Use repository configs/graphs as source of truth, not stale generated diagrams.

## Research Findings

### Source-of-truth artifacts

- Pipeline v2 states/transitions/actions: `.chaplain/config/watcher-pipeline-v2.yaml`
- Dispatcher poll loop and inbox sync: `.chaplain/config/watcher-dispatcher.yaml`
- Model assignments:
  - Plan: `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` (`gpt-5.3-codex`)
  - Judge: `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` (`claude-sonnet-4`)
  - Enforce: `.chaplain/graphs/watcher-enforce/enforce-session.yaml` (`gpt-5.3-codex`)
  - Validate: `.chaplain/graphs/watcher-enforce/validate-session.yaml` (`claude-sonnet-4-6`)
  - Sanity: `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml` (`claude-sonnet-4-6`)
- Action plugin inventory: `.chaplain/actions/` (includes `failure_cleanup_action.py`)

### Existing prior art in this codebase

- FR-314 already added retry/requeue runbook in `.chaplain/README.md` (keep and cross-reference).
- FR-316 introduced `sanity_check` state and non-blocking `warn` routing in FSM v2.
- `tests/unit/test_chaplain_readme_documentation.py` currently checks broad README presence/content but does not enforce FSM v2 specifics.

### Drift signal affecting approach

- Generated diagram docs under `.chaplain/docs/fsm-diagrams/` are not aligned with current v2 config naming/flow, so they should not be used as acceptance oracle for this FR.

## Proposed Solution

1. Add a focused section in `.chaplain/README.md` (near pipeline overview) titled along the lines of `Watcher2 FSM v2 (Current)`.
2. Document:
   - Operational and terminal states from `watcher-pipeline-v2.yaml`
   - Dispatcher loop from `watcher-dispatcher.yaml` including `timeout(10)` and `inbox_sync.sh` import behavior for labeled GitHub issues
   - Sanity-check insertion and non-blocking `WARN` path
3. Add a model mapping table sourced from graph YAML files (including enforce model as currently configured).
4. Add an action-type subsection:
   - Active in v2 config: `yamlgraph_async`, `bash_context`, `precommit`, `bash`
   - Available plugin note: `failure_cleanup` exists in action library but is not currently wired in v2
5. Keep existing retry/requeue section and add cross-reference from FSM overview.
6. Add a short maintenance note that `.chaplain/processing/` may contain stale files and can be periodically cleaned by operators.
7. Add/extend a documentation contract test file to enforce these README sections.

## Acceptance Criteria

- [x] **AC-01:** `.chaplain/README.md` contains a dedicated watcher2 FSM v2 section with the full operational path `setup -> plan -> capture_fr -> judge -> enforce_session -> validate -> sanity_check -> precommit_check -> done`.
- [x] **AC-02:** README explicitly lists terminal states `completed`, `failed`, and `stopped`.
- [x] **AC-03:** README documents dispatcher polling behavior with `timeout(10)` and `inbox_sync.sh` GitHub-label sync context.
- [x] **AC-04:** README describes sanity-check behavior between `validate` and `precommit_check`, including non-blocking `WARN`.
- [x] **AC-05:** README includes model mapping for plan/judge/enforce/validate/sanity and matches graph config values.
- [x] **AC-06:** README documents action types active in v2 config and explicitly clarifies `failure_cleanup` availability vs wiring status.
- [x] **AC-07:** README includes/retains key script references: `start-system.sh`, `inbox_sync.sh`, `wait_ci.sh`, `merge_pr.sh`, `worktree_teardown.sh`, `post_merge.sh`.
- [x] **AC-08:** README includes a stale-processing maintenance note for `.chaplain/processing/`.
- [x] **AC-09:** Documentation tests enforce AC-01..AC-08 and fail on current state before implementation.

## Failing Acceptance Tests (RED)

Current failing checks in this worktree:

```bash
rg -n 'setup -> plan -> capture_fr -> judge -> enforce_session -> validate -> sanity_check -> precommit_check -> done' .chaplain/README.md
# exits 1 (v2 state chain missing)

rg -n 'timeout\(10\)' .chaplain/README.md
# exits 1 (dispatcher polling contract missing)

rg -n 'claude-sonnet-4-6|gpt-5.3-codex|claude-sonnet-4' .chaplain/README.md
# exits 1 (model mapping section missing)

python - <<'PY'
from pathlib import Path
text = Path(".chaplain/README.md").read_text()
required = [
    "setup -> plan -> capture_fr -> judge -> enforce_session -> validate -> sanity_check -> precommit_check -> done",
    "completed",
    "failed",
    "stopped",
    "timeout(10)",
    "yamlgraph_async",
    "bash_context",
    "precommit",
    "failure_cleanup",
    "gpt-5.3-codex",
    "claude-sonnet-4",
    "claude-sonnet-4-6",
    "start-system.sh",
    "processing/",
]
missing = [item for item in required if item not in text]
assert not missing, f"missing watcher2 FSM README details: {missing}"
PY
# exits 1 (multiple required items missing)
```

Planned RED test command after adding a dedicated docs contract test:

```bash
pytest tests/unit/test_chaplain_readme_documentation.py -q --no-cov -k "watcher2_fsm_v2 or dispatcher_polling or model_mapping or action_types"
```

## Alternatives Considered

1. **Mirror issue bullets verbatim even when they conflict with config reality** — Rejected. This would keep README inaccurate.
2. **Expand scope to change runtime model assignments/actions to match requested bullets** — Rejected. This FR is documentation-accuracy only.
3. **Use generated FSM diagram markdown as source-of-truth** — Rejected. Current generated docs are drifted relative to v2 config.

## Related

- Topic source requested: `.chaplain/processing/gh-298.md` (not present in this worktree)
- Canonical source used: GitHub issue #298 (`https://github.com/sheikkinen/yamlgraph/issues/298`)
- Target doc: `.chaplain/README.md`
- Source-of-truth configs and graphs:
  - `.chaplain/config/watcher-pipeline-v2.yaml`
  - `.chaplain/config/watcher-dispatcher.yaml`
  - `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`
  - `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`
  - `.chaplain/graphs/watcher-enforce/enforce-session.yaml`
  - `.chaplain/graphs/watcher-enforce/validate-session.yaml`
  - `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml`
- Prior FRs:
  - `feature-requests/FR-314-chaplain-readme-retry-requeue-workflow.md`
  - `feature-requests/FR-316-watcher2-sanity-check-state.md`
- Existing docs-test baseline:
  - `tests/unit/test_chaplain_readme_documentation.py`
