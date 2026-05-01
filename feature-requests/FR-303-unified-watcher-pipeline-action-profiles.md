# Feature Request: FR-303 Unified Watcher Pipeline with Action Profiles

**Priority:** HIGH
**Type:** Enhancement
**Status:** AMEND — Conditionally Approved
**Effort:** 2 days (revised from 1)
**Requested:** 2026-05-01
**Judged:** 2026-05-01

## Summary

Eliminate the duplicated `integration-pipeline.yaml` by adopting the action-directory-swap pattern proven in `projects/ninchat_voice`. One canonical `watcher-pipeline.yaml` serves both production and integration — the `--actions-dir` flag selects between real actions (LLM calls) and stubs (instant echo + auto-approve).

## Value Statement

Watcher developers maintain one pipeline config instead of two, eliminating drift between integration and production while keeping deterministic no-LLM testing.

## Problem

FR-301 created `integration-pipeline.yaml` as a separate config with 18 states (vs production's 28). This works but introduces **config drift**: every time production adds a state, changes a transition, or renames an event, the integration config must be manually synced. FR-302 already required 7 bug-fix iterations partly because the two configs diverged on timeout values, terminal-state semantics, and merge flags.

The `projects/ninchat_voice` project solved this exact problem with **action directory swap**: one FSM config, four action directories (`real/`, `stubs/`, `timed_mocks/`, `e2e_bridge/`). Each directory contains the same filenames and class names with different implementations. The engine's `--actions-dir` flag selects the profile at startup. This pattern is production-proven across 6 FSM modes and 4 fidelity levels.

## Research Findings

### FSM Engine Capabilities (Verified)

1. **Action resolution:** `--actions-dir` discovers `*_action.py` files by naming convention. Custom actions shadow built-ins.
2. **Single directory:** Only ONE `--actions-dir` supported — stubs for `yamlgraph_async` require the stub dir to also contain (or symlink) the real `bash_context`, `git_commit`, and `precommit` actions.
3. **Extra config fields ignored:** Actions receive the full YAML block via `self.config`. Unknown fields like `profile:` are safely ignored.
4. **Fully extensible type system:** Any `type: foo` resolves to `foo_action.py` with `class FooAction(BaseAction)`. No enum validation.

### What Differs Between Integration and Production

| Category | States | Current Approach | Unified Approach |
|---|---|---|---|
| **LLM actions** (`yamlgraph_async`) | `planning`, `researching`, `judging`, `implementing`, `testing_demo`, `critiquing`, `remediating_ci`, `forensics` | Separate YAML with bash echo stubs | Stub `yamlgraph_async_action.py` in `actions-stub/` |
| **TDD verification** (`bash`) | `verifying_red` | Omitted from integration | Convert to `type: verify_red` custom action with stub |
| **Changelog generation** (`bash`) | `changelog_gen` | Omitted from integration | Convert to `type: changelog_gen` custom action with stub |
| **Merge flag** | `merging` | No `--delete-branch` in integration | Context variable `{delete_branch_flag}` or convert to custom action |
| **Failed cleanup** | `failed` | Simple cleanup in integration, forensics in production | Forensics is already `yamlgraph_async` — stub handles it |

### ninchat_voice Reference Pattern

```
actions/real/                    ← production (LLM, telephony, Ninchat)
actions/stubs/                   ← instant stubs (same filenames, same class names)
actions/timed_mocks/             ← stubs + asyncio.sleep (realistic timing)
actions/e2e_bridge/              ← Unix socket IPC for external test harness

config/voice_coordinator.yaml    ← ONE config per functional mode
start-fsm.sh --stub              ← --actions-dir swap via CLI flag
```

**Key invariant:** Every real action file has a stub counterpart with identical filename and class name. The engine doesn't know which profile it loaded.

## Proposed Solution

### Phase 1: Action Directory + Stub Actions

#### Directory Layout

```
.chaplain/actions/                          ← production (existing, unchanged)
  yamlgraph_async_action.py                 ← real LLM calls
  bash_context_action.py                    ← real bash with JSON capture
  git_commit_action.py                      ← real git operations
  precommit_action.py                       ← real pre-commit
  verify_red_action.py                      ← NEW: extracted from inline bash
  changelog_gen_action.py                   ← NEW: extracted from inline bash

.chaplain/actions-stub/                     ← integration stubs (NEW)
  yamlgraph_async_action.py                 ← echo + return success; judging auto-approves
  bash_context_action.py  → ../actions/     ← symlink to real
  git_commit_action.py    → ../actions/     ← symlink to real
  precommit_action.py     → ../actions/     ← symlink to real
  verify_red_action.py                      ← always succeeds (no pytest needed)
  changelog_gen_action.py                   ← generates minimal valid fragment
```

#### Stub yamlgraph_async Implementation

```python
"""Stub: yamlgraph_async — instant return, no LLM call.

Mirrors production interface: reads graph, vars, event_map, success from config.
Returns success event immediately. For judging state, always returns 'approve'.
"""
from statemachine_engine.actions.base import BaseAction

class YamlgraphAsyncAction(BaseAction):
    async def execute(self, context):
        event_map = self.get_config_value("event_map", {})
        if event_map:
            return "approve"  # judging: always approve in stub mode
        return self.get_config_value("success", "done")
```

#### New Custom Action Types

Extract `verifying_red` and `changelog_gen` from inline `type: bash` to custom action types so stubs can intercept them:

**Production `verify_red_action.py`:**
```python
class VerifyRedAction(BaseAction):
    async def execute(self, context):
        wt_dir = context.get("wt_dir", ".")
        # Run pytest, expect failure (RED state)
        result = await run_bash(f"cd {wt_dir} && python -m pytest tests/ --no-cov -x")
        if result.returncode != 0:
            return self.get_config_value("success", "red_verified")
        return self.get_config_value("error", "error")  # Tests passed = RED failed
```

**Stub `verify_red_action.py`:**
```python
class VerifyRedAction(BaseAction):
    async def execute(self, context):
        return self.get_config_value("success", "red_verified")
```

#### Pipeline YAML Changes

In `watcher-pipeline.yaml`, replace inline bash with custom types:

```yaml
# BEFORE
verifying_red:
  - type: bash
    command: "cd {wt_dir} && python -m pytest tests/ --no-cov -x 2>&1 | tail -5; test ${PIPESTATUS[0]} -ne 0"

# AFTER
verifying_red:
  - type: verify_red
    success: red_verified
    error: error
    description: "🔴 Verifying RED"
```

### Phase 2: Merge Flag Handling

The `merging` state uses `--delete-branch` in production but not in integration (worktree conflict). Two options:

**Option A (context variable):**
```yaml
merging:
  - type: bash
    command: "gh pr merge {pr_number} --squash {merge_flags}"
```
Pass `--initial-context '{"merge_flags": ""}'` for integration, `'{"merge_flags": "--delete-branch"}'` for production.

**Option B (custom action):** Extract to `type: merge_pr` custom action. Production adds `--delete-branch`, stub omits it.

Recommend Option A — minimal change, no new action type needed.

### Phase 3: Delete integration-pipeline.yaml

Once the unified pipeline works with both action directories:

1. Update `integration-dispatcher.yaml` to reference `watcher-pipeline.yaml` instead of `integration-pipeline.yaml`
2. Update `run-integration-test.sh` to pass `--actions-dir .chaplain/actions-stub/`
3. Delete `integration-pipeline.yaml`
4. Update unit tests in `test_fr301_integration_test.py`

### Phase 4: Run Script Update

```bash
# scripts/run-integration-test.sh
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions-stub \
  --initial-context "{\"inbox_dir\":\"$INBOX\", \"merge_flags\":\"\"}" \
  --debug > logs/integration-dispatcher-${TOPIC_SLUG}.log 2>&1 &
```

## Acceptance Criteria

- [ ] Single `watcher-pipeline.yaml` used by both production and integration
- [ ] `integration-pipeline.yaml` deleted
- [ ] `.chaplain/actions-stub/` directory with stub actions for all `yamlgraph_async`, `verify_red`, and `changelog_gen` types
- [ ] Symlinks for `bash_context`, `git_commit`, `precommit` actions in stub dir
- [ ] `verifying_red` and `changelog_gen` extracted to custom action types
- [ ] `run-integration-test.sh` passes with `--actions-dir .chaplain/actions-stub/`
- [ ] Production watcher still works with `--actions-dir .chaplain/actions/`
- [ ] Unit tests updated for unified config
- [ ] Integration test green: full pipeline preflight → completed

## Judgement

**Verdict: AMEND — Conditionally Approved**

The core idea (action-directory swap via `--actions-dir`) is **sound and proven**. The ninchat_voice reference validates the pattern across 4 fidelity profiles. Eliminating config drift is the right goal.

However, the FR as proposed covers only ~60% of the actual divergence. Six gaps must be addressed before implementation can proceed.

### Gap 1: Inline bash divergence (CRITICAL)

The FR only addresses the `yamlgraph_async` swap and proposes extracting `verifying_red` and `changelog_gen` to custom types. But **5 additional `type: bash`/`bash_context` states have different inline commands** between production and integration. Since `bash` is a built-in engine type, `--actions-dir` cannot intercept it.

| State | Production | Integration | Divergence |
|---|---|---|---|
| `merging` | `--squash --delete-branch` | `--squash` (no delete-branch) | FR addresses (Phase 2, context var) |
| `completed` | `post_merge.sh` | `echo` (no-op) | **UNADDRESSED** |
| `failed` | move topic to failed/, emit `analyze` → forensics | full cleanup: worktree teardown, branch delete, PR close, topic move | **UNADDRESSED** |
| `creating_pr` | `create_pr.sh --branch --dir` | `create_pr.sh --branch --dir --title "docs(integration): ..."` | **UNADDRESSED** |
| `committing_plan` | `add_paths: ["feature-requests/"]` | `add_paths: ["docs/"]` | **UNADDRESSED** |

**Required amendment:** Parameterize all 5 via context variables (the pattern FR already proposes for `merging`). Specifically:
- `completed`: `bash .chaplain/lib/watcher/post_merge.sh {post_merge_flags}` — integration passes `--dry-run` or `--skip`, or simply skip: `{post_merge_cmd}` with integration defaulting to `echo done`
- `failed`: Extract to `type: failure_cleanup` custom action. Production version: move topic only. Integration version: full cleanup (worktree, branch, PR, topic). The failure path differs structurally — production goes `failed → forensics → completed`, integration goes `failed → stopped`. Context variable insufficient here.
- `creating_pr`: `--title "{pr_title}"` with production defaulting to empty (create_pr.sh auto-generates) and integration set to `"docs(integration): smoke test"`
- `committing_plan`: `add_paths: ["{plan_commit_path}"]` — or use `["."]` universally (broader but safe)

### Gap 2: Stub file creation (CRITICAL)

Current integration stubs **create files and git-commit them inline**:
```bash
cd {wt_dir}
echo "## timestamp — planning" >> docs/watcher-integration.md
git add docs/watcher-integration.md
git commit -m "docs: integration — planning" --no-verify
```

The proposed yamlgraph_async stub just returns `"done"` — **no files created**. Then `committing_plan` (git_commit action) runs `git add feature-requests/` and tries to commit — but there's nothing to commit.

**Required amendment:** Either:
- **(A)** Stub yamlgraph_async creates a placeholder file in the worktree (like current stubs do), OR
- **(B)** git_commit action handles "nothing to commit" gracefully (--allow-empty or pre-check), OR
- **(C)** Symlink git_commit but also provide a stub git_commit that skips empty commits

Recommend **(A)** — it matches the current behavior and keeps git_commit unchanged. The stub should write to `docs/watcher-integration.md` (same as current stubs) and the unified config should use `add_paths: ["."]` for plan commit.

### Gap 3: Failure path structural divergence (MEDIUM)

Production transitions: `failed → forensics → completed`
Integration transitions: `failed → stopped` (via `job_done`)

With the unified config, integration failures would traverse forensics (yamlgraph_async stub returns instantly) → completed (runs `post_merge.sh`). This chain is functionally different from the current integration behavior where `failed` does full cleanup and halts.

**Required amendment:** This is actually acceptable IF:
1. The `failed` action in the unified config does sufficient cleanup (see Gap 1)
2. `completed` action is parameterized to skip `post_merge.sh` in integration (see Gap 1)
3. The forensics stub returns `forensics_done` instantly (already handled by yamlgraph_async stub)

### Gap 4: Error transitions missing from production (MINOR)

Integration has 14 explicit `from: X, to: failed, event: error` transitions. Production has none — only a global `from: "*" → stopped` on `stop`. If an action returns `"error"` in production, the event is unhandled (engine stays stuck or silently ignores).

**Required amendment:** Add per-state error transitions to the unified config. This is a production improvement, not just an integration concern. Both profiles benefit.

### Gap 5: Timeout divergence (MINOR)

Production: `timeout(600)` for all yamlgraph_async states.
Integration: `timeout(300)` for stubbed states, `timeout(660)` for waiting_ci.

With unified config, integration would use production's `timeout(600)`. Since stubs return instantly, these never fire — this is acceptable. The `waiting_ci` timeout is the same in both (660s). No amendment needed.

### Gap 6: Judging stub logic (MINOR)

The FR proposes:
```python
if event_map:
    return "approve"
```

The ninchat_voice reference uses the more flexible `_intent_sequence` pattern:
```python
intent_seq = context.get("_intent_sequence")
if intent_seq and isinstance(intent_seq, list) and len(intent_seq) > 0:
    return intent_seq.pop(0)
return params.get("success", "done")
```

**Required amendment:** Adopt the ninchat_voice `_intent_sequence` pattern. It allows tests to inject specific verdict sequences (`["approve"]`, `["reject", "approve"]`) rather than hardcoding auto-approve. For default behavior (no intent_sequence), use `params.get("success", "done")` which returns `approve` when `success: approve` is in the judging config.

### Revised Phase Plan

1. **Phase 0: Error transitions** — Add per-state `error → failed` transitions to `watcher-pipeline.yaml`. Production improvement.
2. **Phase 1: Custom action types** — Extract `verifying_red`, `changelog_gen`, and `failure_cleanup` to custom action types in `.chaplain/actions/`.
3. **Phase 2: Parameterize bash divergence** — Context variables for `merge_flags`, `pr_title`, `post_merge_cmd`. Universal `add_paths: ["."]` for plan commit.
4. **Phase 3: Stub directory** — Create `.chaplain/actions-stub/` with stub yamlgraph_async (file-creating, _intent_sequence-aware), stub verify_red, stub changelog_gen, stub failure_cleanup, and symlinks for real actions.
5. **Phase 4: Integration test update** — Point dispatcher at `watcher-pipeline.yaml`, pass `--actions-dir .chaplain/actions-stub/`, add context variables. Delete `integration-pipeline.yaml`.
6. **Phase 5: Verification** — Green integration test end-to-end with unified config.

### Effort Revision

1 day → **2 days**. The inline bash parameterization (Gap 1) and stub file creation (Gap 2) add ~half a day each. Error transitions (Gap 4) add 2 hours.

### Authority

**Granted conditionally.** Incorporate the 6 gaps into the proposed solution before beginning Phase 1. The revised phase plan above supersedes the original 4-phase plan.

## Alternatives Considered

### Option E: Generated Config (Rejected)

A Python script generates `integration-pipeline.yaml` from `watcher-pipeline.yaml` by stubbing LLM actions and removing production-only states. The generator detects config drift — if it fails, the configs have diverged.

**Rejected because:** The generator is ~100 lines of transformation logic that must be maintained alongside the pipeline. It's a second source of truth. The ninchat_voice pattern proves that action-directory swap is simpler, proven, and requires zero generation.

### Option D: Engine Profile Mechanism (Deferred)

Add `--profile integration` to the engine, with action blocks supporting `profile:` field filtering.

**Deferred because:** Requires FSM engine changes (separate package). The action-directory swap achieves the same result with zero engine changes. If the pattern proves insufficient, revisit as FSM engine FR.

### Keep Two Configs (Status Quo, Rejected)

**Rejected because:** FR-302 proved that config drift is a real maintenance cost (7 iterations, 3 timeout/terminal-state bugs traced to config divergence). The cost compounds with every production pipeline change.

## Related

- **FR-301** — Created the integration test with separate configs (the problem this FR solves)
- **FR-302** — Bug fixes from config drift between integration and production
- **ninchat_voice** — Reference implementation: `projects/ninchat_voice/actions/{real,stubs,timed_mocks,e2e_bridge}/`
- **Diary:** `docs/diary/2026-05-01-fr302-integration-test-convergence.md` — Documents terminal-state, timeout, and pipe-interleaving traps
