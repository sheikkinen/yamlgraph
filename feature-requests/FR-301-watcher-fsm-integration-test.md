# Feature Request: FR-301 Watcher FSM Integration Test (No-LLM End-to-End)

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-04-30

## Summary

Create isolated FSM configs (`integration-dispatcher.yaml`, `integration-pipeline.yaml`) that run the full watcher pipeline end-to-end — preflight, worktree, commit, push, PR, CI, merge, teardown — with every LLM step replaced by a bash stub that appends a timestamped entry to `docs/watcher-integration.md`.

## Value Statement

Watcher developers get a deterministic, repeatable integration test that proves all bash tools, git operations, and GitHub interactions work correctly without spending LLM tokens or waiting for AI responses.

## Problem

The current watcher pipeline (`watcher-pipeline.yaml`) depends on 8 `yamlgraph_async` LLM steps (planning, researching, writing_tests, judging, implementing, testing_demo, critiquing, remediating_ci). This makes it impossible to test the mechanical pipeline (git worktree, PR creation, CI polling, merge) in isolation. When a bash tool bug breaks the pipeline (e.g., the "function defined but never called" bug found in all watcher scripts), debugging requires full LLM runs that take minutes and cost tokens.

## Constraints

1. No LLM calls — all AI steps replaced with bash stubs.
2. Separate config files — production configs unchanged.
3. CI-safe — only `docs/` and `changelog/` changes; PR uses `docs:` commit type to avoid diary-gate, demo-gate, and changelog-req-gate.
4. Uses real bash tools: `preflight.sh`, `worktree_setup.sh`, `create_pr.sh`, `wait_ci.sh`, `worktree_teardown.sh`.
5. Changelog fragment uses `type: docs` (not `feat`) to avoid requirement cross-validation.

## Proposed Solution

### New Files

| File | Purpose |
|------|---------|
| `.chaplain/config/integration-dispatcher.yaml` | Dispatcher FSM polling `.chaplain/inbox-integration/` |
| `.chaplain/config/integration-pipeline.yaml` | Pipeline FSM with bash stubs replacing all LLM steps |
| `.chaplain/inbox-integration/` | Isolated inbox directory for test topics |
| `scripts/run-integration-test.sh` | One-command wrapper: seed → run → report (A4) |

### State Mapping (A5)

The integration pipeline maps every production state to one of three categories:

```
# ── STATE MAPPING (production → integration) ──────────────────────
# REAL (same action type as production):
#   preflight         bash_context   — real preflight.sh
#   worktree_setup    bash_context   — real worktree_setup.sh
#   committing_plan   git_commit     — real git_commit action (A1)
#   committing_research git_commit   — real git_commit action (A1)
#   committing_implementation git_commit — real git_commit action (A1)
#   changelog_gen     bash           — real changelog fragment generation
#   finalizing        precommit      — real pre-commit run
#   pushing           bash           — real git push
#   creating_pr       bash_context   — real create_pr.sh
#   waiting_ci        bash_context   — real wait_ci.sh
#   merging           bash           — real gh pr merge
#   cleaning_up       bash           — real worktree_teardown.sh
#
# STUBBED (yamlgraph_async → bash echo):
#   planning          bash           — echo timestamp to docs/watcher-integration.md
#   researching       bash           — echo timestamp to docs/watcher-integration.md
#   judging           bash           — echo timestamp, always emits "approve"
#   implementing      bash           — echo timestamp to docs/watcher-integration.md
#
# REMOVED (not needed without real LLM):
#   writing_tests     — no test code to write in stub mode
#   verifying_red     — no tests to verify
#   testing_demo      — no implementation to demo
#   critiquing        — no implementation to critique
#   remediating_ci    — docs-only changes; CI won't fail
#   forensics         — replaced by simplified failure path (A3)
```

### Pipeline States

```
PLANNING:    preflight → worktree_setup → planning → committing_plan →
             researching → committing_research → judging
ENFORCEMENT: implementing → committing_implementation → changelog_gen →
             finalizing → pushing → creating_pr → waiting_ci →
             merging → cleaning_up
TERMINAL:    completed, failed, stopped
```

### Stub Pattern (replaces every yamlgraph_async action)

Each LLM step becomes:

```yaml
  planning:
    - type: bash
      command: |
        cd {wt_dir}
        echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — planning" >> docs/watcher-integration.md
        echo "" >> docs/watcher-integration.md
        git add docs/watcher-integration.md
        git commit -m "docs: integration — planning" --no-verify
      success: plan_done
      error: error
      timeout: 30
```

`--no-verify` on intermediate stub commits (CONF-XXX, see A2 below); `finalizing` runs `pre-commit run --all-files` on the full worktree.

### Real Actions

| State | Action Type | Tool | Notes |
|-------|-------------|------|-------|
| preflight | `bash_context` | `preflight.sh` | Unchanged from production |
| worktree_setup | `bash_context` | `worktree_setup.sh --topic {topic_file}` | Captures wt_dir/wt_branch/main_dir |
| committing_plan | `git_commit` | Built-in FSM action | Same action type as production (A1) |
| committing_research | `git_commit` | Built-in FSM action | Same action type as production (A1) |
| committing_implementation | `git_commit` | Built-in FSM action | Same action type as production (A1) |
| changelog_gen | `bash` | Inline script | Generates `type: docs` fragment |
| finalizing | `precommit` | Built-in FSM action | `max_attempts: 5`, same as production |
| pushing | `bash` | `git push origin {wt_branch} --force-with-lease` | Real push |
| creating_pr | `bash_context` | `create_pr.sh --branch {wt_branch} --dir {wt_dir}` | Captures pr_number/pr_url |
| waiting_ci | `bash_context` | `wait_ci.sh --pr {pr_number}` | Captures ci_result |
| merging | `bash` | `gh pr merge {pr_number} --squash --delete-branch` | Real merge |
| cleaning_up | `bash` | `worktree_teardown.sh --dir {wt_dir}` | Real teardown |

### Changelog Fragment (stub)

```yaml
  changelog_gen:
    - type: bash
      command: |
        cd {wt_dir}
        FRAG="changelog/unreleased/integration-test.md"
        mkdir -p changelog/unreleased
        printf -- '---\ntype: docs\nscope: integration\n---\n- Integration test run\n' > "$FRAG"
        git add "$FRAG"
        git commit -m "docs: changelog fragment" --no-verify
      success: changelog_done
      error: error
```

### Failure Path (A3)

Simplified failure handling — no forensics, just cleanup:

```yaml
  failed:
    - type: bash
      command: |
        # Tear down worktree if it exists
        if [ -n "{wt_dir}" ] && [ -d "{wt_dir}" ]; then
          bash .chaplain/lib/watcher/worktree_teardown.sh --dir {wt_dir}
        fi
        # Delete remote branch if it exists
        if [ -n "{wt_branch}" ]; then
          git push origin --delete {wt_branch} 2>/dev/null || true
        fi
        # Close PR if it exists
        if [ -n "{pr_number}" ]; then
          gh pr close {pr_number} 2>/dev/null || true
        fi
        # Move topic to failed/
        mkdir -p .chaplain/failed
        if [ -n "{topic_file}" ] && [ -f "{topic_file}" ]; then
          mv "{topic_file}" .chaplain/failed/
        fi
      description: "❌ Integration test failed — cleaning up"
```

Transitions to `failed` from all non-terminal states via timeout or error.

### Dispatcher Config

Same structure as `watcher-dispatcher.yaml` but:
- `machine_name: integration-dispatcher`
- `context.inbox_dir: .chaplain/inbox-integration`
- `processing_topic` launches `integration-pipeline.yaml`

### Confession Entry (A2)

Add to `docs/confessions.md`:

```
### CONF-XXX (next available ID)
- **File**: `.chaplain/config/integration-pipeline.yaml`
- **Code**: --no-verify
- **Sin**: Intermediate stub commits in integration test use `--no-verify` to skip pre-commit hooks.
- **Penance**: These commits exist only inside a worktree branch that will be squash-merged.
  The `finalizing` state runs `pre-commit run --all-files` on the complete worktree before push.
  The final squash-merged commit on main passes all CI gates. No unverified code reaches main.
```

### Test Script Wrapper (A4)

`scripts/run-integration-test.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

INBOX=".chaplain/inbox-integration"
LOG_FILE="docs/watcher-integration.md"

# Seed
mkdir -p "$INBOX"
echo "# Integration smoke test — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$INBOX/smoke-test.md"

# Ensure log file exists on main
if [ ! -f "$LOG_FILE" ]; then
  echo "# Watcher Integration Log" > "$LOG_FILE"
  git add "$LOG_FILE"
  git commit -m "docs: init integration log"
fi

# Run
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions \
  --initial-context "{\"inbox_dir\":\"$INBOX\"}" \
  --debug

# Report
echo ""
echo "=== Integration Test Complete ==="
echo "Check $LOG_FILE for timestamped entries."
echo "Check GitHub for merged PR."
```

## Acceptance Criteria

- [ ] Pipeline reaches `completed` state without manual intervention
- [ ] PR created on GitHub with `docs:` prefix title
- [ ] CI passes (docs-only changes, no Python modifications)
- [ ] PR merged via squash merge
- [ ] `docs/watcher-integration.md` on main contains timestamped entries for: planning, researching, judging, implementing
- [ ] Worktree cleaned up after completion
- [ ] Topic file removed from processing/
- [ ] No pre-commit hook failures
- [ ] Production configs (`watcher-dispatcher.yaml`, `watcher-pipeline.yaml`) unchanged
- [ ] `committing_plan`, `committing_research`, `committing_implementation` use real `git_commit` action (A1)
- [ ] `--no-verify` documented as CONF-XXX in `docs/confessions.md` (A2)
- [ ] Failure path tears down worktree, deletes remote branch, closes PR (A3)
- [ ] `scripts/run-integration-test.sh` runs full test with single command (A4)
- [ ] Integration pipeline has state mapping comment block at top (A5)

## Alternatives Considered

1. **Mock the FSM engine** — rejected: the point is testing real engine + real tools together.
2. **Use a test branch instead of main** — rejected: PR merge target must be main to test full CI flow.
3. **Keep all production states and skip LLM via env flag** — rejected: adds complexity to production config; separate configs are cleaner and don't risk production behavior changes.

## Related

- `feature-requests/FR-300-full-pipeline-run-logging-verification.md`
- `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`
- `feature-requests/FR-FSM-015-watcher2-pipeline-logging.md`

---

## Judgement

**Verdict: APPROVE with amendments**

### Assessment

The FR is well-structured, the problem is real, and the approach is correct. Stubbing LLM steps with bash commands to test the mechanical pipeline is the right pattern — it follows the `demo_vs_test` principle ("tests prove constraints; demos prove abstraction worth having").

### What's good

1. **Separate configs** — production untouched. No env flags, no conditional branches.
2. **Real tools for mechanical states** — preflight, worktree, PR, CI, merge, teardown all use the real bash scripts. This tests the exact code that broke.
3. **`docs:` commit type** — sidesteps diary-gate, demo-gate, changelog-req-gate without bypassing safety. The gates don't apply to docs-only changes by design.
4. **Acceptance criteria are concrete and verifiable** — each one maps to an observable outcome.

### Amendments required

**A1: Drop `committing_plan` and `committing_research` states.**
The production pipeline has `git_commit` actions for these. The integration pipeline should either use the same `git_commit` action type (if supported by the FSM engine) or collapse them into the preceding stub's bash command. Don't silently skip states that exist in production — either test them or explicitly document why they're excluded.

**A2: The `--no-verify` on stub commits needs a confession.**
Scripture forbids `--no-verify`. These are intermediate commits inside a worktree that will be squash-merged, and the final `finalizing` state runs `pre-commit run --all-files`. This is acceptable **only if** documented as a CONF-XXX exception in `docs/confessions.md`.

**A3: Add a cleanup-on-failure path.**
The FR shows the happy path but doesn't address what happens when the integration test fails mid-pipeline. Add a simplified failure path that at minimum tears down the worktree and removes the test branch from remote. Otherwise, repeated test runs accumulate stale worktrees and orphan branches.

**A4: Add a test script wrapper.**
The "How to Run" section shows manual steps. Create `scripts/run-integration-test.sh` that seeds the inbox, runs the dispatcher, waits for completion, and reports pass/fail. Makes the test repeatable and CI-able.

**A5: State mapping comment block.**
The integration pipeline config must have a comment block at the top listing exactly which production states are stubbed, which are real, and which are removed — so drift between production and integration configs is immediately visible.

### Scope freeze

After amendments, scope is:
- 2 new YAML configs (integration-dispatcher, integration-pipeline)
- 1 new directory (`.chaplain/inbox-integration/`)
- 1 wrapper script (`scripts/run-integration-test.sh`)
- 1 confession entry in `docs/confessions.md`
- 0 changes to production configs

Effort estimate: 0.5 days confirmed.

**Authority granted. Enforce.**
- `.chaplain/config/watcher-pipeline.yaml` (production reference)
- `.chaplain/config/watcher-dispatcher.yaml` (production reference)
- `.chaplain/lib/watcher/*.sh` (shared bash tools)
