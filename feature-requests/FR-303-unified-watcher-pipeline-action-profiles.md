# Feature Request: FR-303 Unified Watcher Pipeline with Action Profiles

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-05-01
**Judged:** 2026-05-01
**Amended:** 2026-05-01

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

## Proposed Solution (Amended)

Six phases. Each phase is independently committable and testable.

### Phase 0: Error Transitions (production improvement)

Add per-state `error → failed` transitions to `watcher-pipeline.yaml`. Currently only integration has these; production has none — an action returning `"error"` leaves the engine stuck.

```yaml
# Add to watcher-pipeline.yaml transitions:
- from: preflight
  to: failed
  event: error
- from: worktree_setup
  to: failed
  event: error
- from: planning
  to: failed
  event: error
- from: committing_plan
  to: failed
  event: error
- from: researching
  to: failed
  event: error
- from: committing_research
  to: failed
  event: error
- from: writing_tests
  to: failed
  event: error
- from: judging
  to: failed
  event: error
- from: implementing
  to: failed
  event: error
- from: committing_implementation
  to: failed
  event: error
- from: testing_demo
  to: failed
  event: error
- from: critiquing
  to: failed
  event: error
- from: changelog_gen
  to: failed
  event: error
- from: finalizing
  to: failed
  event: error
- from: pushing
  to: failed
  event: error
- from: creating_pr
  to: failed
  event: error
- from: merging
  to: failed
  event: error
- from: cleaning_up
  to: failed
  event: error
```

Also add the `error` event to the events block and add missing `timeout(660)` for `waiting_ci`.

### Phase 1: Custom Action Types

Extract 3 inline `type: bash` states to custom action types so stubs can intercept them.

#### 1a. `verify_red_action.py` (production)

```python
"""VerifyRed — run pytest and expect failure (RED state in TDD)."""
import asyncio
from statemachine_engine.actions.base import BaseAction

class VerifyRedAction(BaseAction):
    async def execute(self, context):
        wt_dir = context.get("wt_dir", ".")
        cmd = f"cd {wt_dir} && python -m pytest tests/ --no-cov -x 2>&1 | tail -5; test ${{PIPESTATUS[0]}} -ne 0"
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if proc.returncode == 0:
            return self.get_config_value("success", "red_verified")
        return self.get_config_value("error", "error")
```

#### 1b. `changelog_gen_action.py` (production)

Wraps the existing inline bash (the 12-line fragment generator) in a custom action. No logic change — just move from inline YAML to Python file.

#### 1c. `failure_cleanup_action.py` (production)

```python
"""FailureCleanup — move topic to failed/ directory."""
import asyncio
from statemachine_engine.actions.base import BaseAction

class FailureCleanupAction(BaseAction):
    async def execute(self, context):
        topic_file = context.get("topic_file", "")
        cmd = f'''mkdir -p .chaplain/failed
if [ -n "{topic_file}" ] && [ -f "{topic_file}" ]; then
  mv "{topic_file}" .chaplain/failed/
fi'''
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return self.get_config_value("success", "analyze")
```

#### Pipeline YAML changes

```yaml
# BEFORE                                          # AFTER
verifying_red:                                     verifying_red:
  - type: bash                                       - type: verify_red
    command: "cd {wt_dir} && ..."                        success: red_verified
    success: red_verified                                error: error
                                                         description: "🔴 Verifying RED"

changelog_gen:                                     changelog_gen:
  - type: bash                                       - type: changelog_gen
    command: |                                           success: changelog_done
      FR_NUM=...                                         error: error
                                                         description: "📋 Generating changelog"

failed:                                            failed:
  - type: bash                                       - type: failure_cleanup
    command: |                                           success: analyze
      mkdir -p .chaplain/failed                          description: "❌ Pipeline failed"
      ...
```

### Phase 2: Parameterize Bash Divergence

Four inline `type: bash`/`bash_context` states need context variables to handle production vs integration differences.

#### 2a. `merging` — merge flags

```yaml
merging:
  - type: bash
    command: "gh pr merge {pr_number} --squash {merge_flags}"
    success: merged
    error: error
```

- **Production context:** `merge_flags: "--delete-branch"`
- **Integration context:** `merge_flags: ""`

#### 2b. `creating_pr` — PR title override

```yaml
creating_pr:
  - type: bash_context
    command: "bash .chaplain/lib/watcher/create_pr.sh --branch {wt_branch} --dir {wt_dir} {pr_title_flag}"
    capture_keys: [pr_number, pr_url]
    success: pr_created
    error: error
```

- **Production context:** `pr_title_flag: ""` (auto-generated from FR)
- **Integration context:** `pr_title_flag: '--title "docs(integration): smoke test"'`

#### 2c. `completed` — post-merge command

```yaml
completed:
  - type: bash
    command: "{post_merge_cmd}"
    description: "✅ Pipeline completed"
```

- **Production context:** `post_merge_cmd: "bash .chaplain/lib/watcher/post_merge.sh 2>/dev/null || true"`
- **Integration context:** `post_merge_cmd: "echo done"`

#### 2d. `committing_plan` — add paths

```yaml
committing_plan:
  - type: git_commit
    message: "{plan_commit_msg}"
    add_paths: ["."]
    capture_fr_path: true
    success: plan_committed
    error: error
```

Use `add_paths: ["."]` universally (broader but safe — pre-commit catches unwanted files). Both production and integration benefit from not having to maintain path lists. The commit message varies:
- **Production context:** `plan_commit_msg: "feat: FR plan — {topic_file}"`
- **Integration context:** `plan_commit_msg: "docs: integration plan — {topic_file}"`

### Phase 3: Stub Directory

Create `.chaplain/actions-stub/` with stubs for all custom action types and symlinks for real actions.

#### Directory layout

```
.chaplain/actions-stub/
  yamlgraph_async_action.py          ← stub (file-creating, _intent_sequence-aware)
  verify_red_action.py               ← stub (always succeeds)
  changelog_gen_action.py            ← stub (generates minimal valid fragment)
  failure_cleanup_action.py          ← stub (full cleanup: worktree, branch, PR, topic)
  bash_context_action.py → ../actions/bash_context_action.py     ← symlink
  git_commit_action.py   → ../actions/git_commit_action.py       ← symlink
  precommit_action.py    → ../actions/precommit_action.py        ← symlink
```

#### Stub `yamlgraph_async_action.py`

Adopts ninchat_voice `_intent_sequence` pattern. Creates a placeholder file in the worktree so downstream `git_commit` has something to commit.

```python
"""Stub: yamlgraph_async — instant return, no LLM call.

Creates a placeholder file in the worktree (so git_commit has content)
and returns the success event. Supports _intent_sequence for injecting
specific verdict sequences in tests.
"""
import os
from datetime import datetime, timezone
from statemachine_engine.actions.base import BaseAction


class YamlgraphAsyncAction(BaseAction):
    async def execute(self, context):
        current_state = context.get("current_state", "unknown")

        # Hold support (same as ninchat_voice)
        if context.get(f"_hold_yamlgraph_async_{current_state}"):
            return None

        # Intent sequence override: pop next intent if available
        intent_seq = context.get("_intent_sequence")
        if intent_seq and isinstance(intent_seq, list) and len(intent_seq) > 0:
            return intent_seq.pop(0)

        # Create placeholder file in worktree (stub content for git_commit)
        wt_dir = context.get("wt_dir", ".")
        if os.path.isdir(wt_dir):
            docs_dir = os.path.join(wt_dir, "docs")
            os.makedirs(docs_dir, exist_ok=True)
            stub_file = os.path.join(docs_dir, "watcher-integration.md")
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            with open(stub_file, "a") as f:
                f.write(f"## {ts} — {current_state}\n\n")

        return self.get_config_value("success", "done")
```

#### Stub `verify_red_action.py`

```python
class VerifyRedAction(BaseAction):
    async def execute(self, context):
        return self.get_config_value("success", "red_verified")
```

#### Stub `changelog_gen_action.py`

```python
"""Stub: generates a minimal valid changelog fragment."""
import os
from statemachine_engine.actions.base import BaseAction

class ChangelogGenAction(BaseAction):
    async def execute(self, context):
        # Create minimal fragment so changelog-gate passes
        wt_dir = context.get("wt_dir", ".")
        frag_dir = os.path.join(wt_dir, "changelog", "unreleased")
        os.makedirs(frag_dir, exist_ok=True)
        frag = os.path.join(frag_dir, "integration-stub.md")
        if not os.path.exists(frag):
            with open(frag, "w") as f:
                f.write("---\ntype: feat\nscope: integration\n---\n")
                f.write("- **Integration**: stub changelog fragment.\n")
        return self.get_config_value("success", "changelog_done")
```

#### Stub `failure_cleanup_action.py`

Full cleanup for integration (worktree teardown, remote branch delete, PR close, topic move):

```python
"""Stub: full integration failure cleanup."""
import asyncio
from statemachine_engine.actions.base import BaseAction

class FailureCleanupAction(BaseAction):
    async def execute(self, context):
        wt_dir = context.get("wt_dir", "")
        wt_branch = context.get("wt_branch", "")
        pr_number = context.get("pr_number", "")
        topic_file = context.get("topic_file", "")

        cmds = []
        if wt_dir:
            cmds.append(f"bash .chaplain/lib/watcher/worktree_teardown.sh --dir {wt_dir} || true")
        if wt_branch:
            cmds.append(f"git push origin --delete {wt_branch} 2>/dev/null || true")
        if pr_number:
            cmds.append(f"gh pr close {pr_number} 2>/dev/null || true")
        cmds.append("mkdir -p .chaplain/failed")
        if topic_file:
            cmds.append(f'[ -f "{topic_file}" ] && mv "{topic_file}" .chaplain/failed/ || true')

        cmd = " && ".join(cmds)
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return self.get_config_value("success", "analyze")
```

### Phase 4: Integration Test Update

1. Update `integration-dispatcher.yaml` — change pipeline reference from `integration-pipeline.yaml` to `watcher-pipeline.yaml` and pass `--actions-dir .chaplain/actions-stub`
2. Update `run-integration-test.sh` — pass context variables for integration profile:

```bash
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions-stub \
  --initial-context "{
    \"inbox_dir\":\"$INBOX\",
    \"merge_flags\":\"\",
    \"pr_title_flag\":\"--title \\\"docs(integration): smoke test\\\"\",
    \"post_merge_cmd\":\"echo done\",
    \"plan_commit_msg\":\"docs: integration plan — {topic_file}\"
  }" \
  --debug > logs/integration-dispatcher-${TOPIC_SLUG}.log 2>&1 &
```

3. Delete `integration-pipeline.yaml`
4. Update unit tests in `test_fr301_integration_test.py` to reflect unified config

### Phase 5: Verification

- Green integration test end-to-end: `bash scripts/run-integration-test.sh` → exit 0
- Production watcher still works: `bash .chaplain/watcher2.sh` with real actions
- Unit tests pass: `pytest tests/unit/test_fr301_integration_test.py -v --no-cov`

## Acceptance Criteria

- [ ] Per-state `error → failed` transitions added to `watcher-pipeline.yaml` (Phase 0)
- [ ] `verifying_red`, `changelog_gen`, `failed` extracted to custom action types in `.chaplain/actions/` (Phase 1)
- [ ] Inline bash parameterized with context variables: `merge_flags`, `pr_title_flag`, `post_merge_cmd`, `plan_commit_msg` (Phase 2)
- [ ] `.chaplain/actions-stub/` directory with stub actions for `yamlgraph_async`, `verify_red`, `changelog_gen`, `failure_cleanup` (Phase 3)
- [ ] Stub yamlgraph_async creates placeholder files in worktree and supports `_intent_sequence` (Phase 3)
- [ ] Symlinks for `bash_context`, `git_commit`, `precommit` actions in stub dir (Phase 3)
- [ ] `integration-dispatcher.yaml` references `watcher-pipeline.yaml` with `--actions-dir .chaplain/actions-stub` (Phase 4)
- [ ] `integration-pipeline.yaml` deleted (Phase 4)
- [ ] `run-integration-test.sh` passes context variables for integration profile (Phase 4)
- [ ] Unit tests updated for unified config (Phase 4)
- [ ] Integration test green: full pipeline preflight → completed (Phase 5)
- [ ] Production watcher still works with `--actions-dir .chaplain/actions/` (Phase 5)

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

**Granted.** All 6 gaps have been incorporated into the amended Proposed Solution. The revised 6-phase plan is the implementation contract. Proceed to Phase 0.

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
