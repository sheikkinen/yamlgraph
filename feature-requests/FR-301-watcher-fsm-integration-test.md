# Feature Request: FR-301 Watcher FSM Integration Test (No-LLM End-to-End)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
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

### Pipeline States (Simplified)

```
PLANNING:    preflight → worktree_setup → planning → researching → judging
ENFORCEMENT: implementing → changelog_gen → finalizing → pushing →
             creating_pr → waiting_ci → merging → cleaning_up
TERMINAL:    completed, failed, stopped
```

Removed from production pipeline: `committing_plan`, `committing_research`, `writing_tests`, `verifying_red`, `committing_implementation`, `testing_demo`, `critiquing`, `remediating_ci`, `forensics`.

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

`--no-verify` on intermediate stub commits; pre-commit runs once in `finalizing`.

### Real Actions (unchanged)

| State | Tool | Notes |
|-------|------|-------|
| preflight | `preflight.sh` | Real bash_context |
| worktree_setup | `worktree_setup.sh --topic {topic_file}` | Real bash_context, captures wt_dir/wt_branch/main_dir |
| finalizing | `cd {wt_dir} && pre-commit run --all-files` | Docs-only changes pass all hooks |
| pushing | `git push origin {wt_branch} --force-with-lease` | Real push |
| creating_pr | `create_pr.sh --branch {wt_branch} --dir {wt_dir}` | Real bash_context, captures pr_number/pr_url |
| waiting_ci | `wait_ci.sh --pr {pr_number}` | Real bash_context, captures ci_result |
| merging | `gh pr merge {pr_number} --squash` | Real merge |
| cleaning_up | `worktree_teardown.sh --dir {wt_dir}` | Real teardown |

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

### Dispatcher Config

Same structure as `watcher-dispatcher.yaml` but:
- `machine_name: integration-dispatcher`
- `context.inbox_dir: .chaplain/inbox-integration`
- `processing_topic` launches `integration-pipeline.yaml`

### How to Run

```bash
# Seed the topic
mkdir -p .chaplain/inbox-integration
echo "# Integration smoke test" > .chaplain/inbox-integration/smoke-test.md

# Ensure docs/watcher-integration.md exists on main
test -f docs/watcher-integration.md || {
  echo "# Watcher Integration Log" > docs/watcher-integration.md
  git add docs/watcher-integration.md
  git commit -m "docs: init integration log"
}

# Run
source .venv/bin/activate
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions \
  --initial-context '{"inbox_dir":".chaplain/inbox-integration"}' \
  --debug
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

## Alternatives Considered

1. **Mock the FSM engine** — rejected: the point is testing real engine + real tools together.
2. **Use a test branch instead of main** — rejected: PR merge target must be main to test full CI flow.
3. **Keep all production states and skip LLM via env flag** — rejected: adds complexity to production config; separate configs are cleaner and don't risk production behavior changes.

## Related

- `feature-requests/FR-300-full-pipeline-run-logging-verification.md`
- `feature-requests/FR-295-watcher-fsm-phase2-single-worker-validation.md`
- `feature-requests/FR-FSM-015-watcher2-pipeline-logging.md`
- `.chaplain/config/watcher-pipeline.yaml` (production reference)
- `.chaplain/config/watcher-dispatcher.yaml` (production reference)
- `.chaplain/lib/watcher/*.sh` (shared bash tools)
