# Feature Request: Parallel Development Pipeline via Git Worktrees

**Priority:** MEDIUM
**Type:** Feature
**Status:** ✅ Approved
**Effort:** 3 days
**Requested:** 2026-02-27
**FR:** FR-106

## Summary

Add a shell script and YAMLGraph graph that automate the Enforce phase in an isolated git worktree — from branch creation through Copilot-driven implementation, testing, pre-commit checks, and PR submission — enabling parallel feature development without blocking the main working tree.

## Value Statement

Developers can run multiple feature implementations in parallel by offloading each to an isolated git worktree with its own Copilot session, eliminating the serial bottleneck of the current single-worktree workflow.

## Problem

The current development pipeline is inherently serial:

1. Developer works in the main worktree
2. Pre-commit hooks run a comprehensive suite (~15 hooks including ruff, pytest, vulture, jscpd, radon, req-coverage)
3. While hooks run or while Copilot implements a feature, the developer's worktree is locked
4. Multiple features cannot be enforced simultaneously

**What already exists:**
- `.chaplain/watch.sh` — Polls inbox for topics, runs the planner graph
- `.chaplain/inquisitor.sh` — Post-commit audit automation
- FR-105 — Copilot session continuations (✅ Implemented)
- FR-081 — Copilot node type (✅ Implemented)
- Pre-commit hooks — Comprehensive quality gates

**What's missing:** An end-to-end Enforce pipeline that operates in an isolated worktree, runs Copilot with full tool access, validates all quality gates, and submits a PR — all without touching the developer's main worktree.

## Proposed Solution

### 1. Orchestration script: `scripts/enforce_worktree.sh`

A thin shell script that creates an isolated worktree, runs the enforce graph, and cleans up:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/enforce_worktree.sh <feature-request-path> [base-branch]
FR_PATH="$1"
BASE_BRANCH="${2:-main}"

# Derive branch name from FR filename
BRANCH="feat/$(basename "$FR_PATH" .md | tr '[:upper:]' '[:lower:]')"
WORKTREE_DIR="tmp/worktrees/$BRANCH"

# Validate: no uncommitted changes on base branch
if ! git diff --quiet "$BASE_BRANCH"; then
  echo "ERROR: Uncommitted changes on $BASE_BRANCH" >&2
  exit 1
fi

# Create worktree with trap-based cleanup
cleanup() { git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true; }
trap cleanup EXIT

git worktree add "$WORKTREE_DIR" -b "$BRANCH" "$BASE_BRANCH"

# Symlink shared .venv to avoid redundant installs
ln -sf "$(pwd)/.venv" "$WORKTREE_DIR/.venv"

# Run the enforce graph inside the worktree
cd "$WORKTREE_DIR"
yamlgraph graph run examples/enforce/graph.yaml \
  --var fr_path="$FR_PATH" \
  --var branch="$BRANCH" \
  --full
```

### 2. Enforce pipeline graph: `examples/enforce/graph.yaml`

A YAMLGraph graph that orchestrates the full Enforce phase using copilot nodes (FR-081) with session continuations (FR-105):

```yaml
metadata:
  name: enforce-pipeline
  description: "End-to-end feature enforcement in isolated worktree"
  version: "1.0"
  variables:
    - fr_path   # Path to the approved feature request
    - branch    # Git branch name

nodes:
  implement:
    type: copilot
    prompt: prompts/enforce-implement.yaml
    variables:
      fr_path: "{fr_path}"
      branch: "{branch}"
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    state_key: implement_result
    timeout: 600

  test_and_demo:
    type: copilot
    prompt: prompts/enforce-test-demo.yaml
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    state_key: test_result
    timeout: 600

  precommit_check:
    type: copilot
    prompt: prompts/enforce-precommit.yaml
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    state_key: precommit_result
    timeout: 300

  submit_pr:
    type: copilot
    prompt: prompts/enforce-submit-pr.yaml
    variables:
      branch: "{branch}"
      fr_path: "{fr_path}"
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    state_key: pr_result
    timeout: 120

edges:
  - from: START
    to: implement
  - from: implement
    to: test_and_demo
  - from: test_and_demo
    to: precommit_check
  - from: precommit_check
    to: submit_pr
  - from: submit_pr
    to: END
```

**Key design decisions:**

- **No `read_fr` node** — The original proposal used a `tool: read_file` node that doesn't exist. Instead, the `implement` copilot node receives `fr_path` as a variable and reads it directly (Copilot has `--allow-all-paths` access). This eliminates a non-existent dependency.
- **Graph location** — Placed at `examples/enforce/graph.yaml` following existing convention (no `graphs/` directory exists at project root).
- **Session continuations** — All downstream nodes chain via `resume: "{state.implement_result.session_id}"` (FR-105, implemented).

### 3. Prompts (in `examples/enforce/prompts/`)

Each prompt receives the feature request path and instructs Copilot:

- **`enforce-implement.yaml`**: Read the FR at `{fr_path}`, implement the minimum changes, follow TDD (red-green-refactor)
- **`enforce-test-demo.yaml`**: Run tests, create/update example, run demo if applicable
- **`enforce-precommit.yaml`**: Run `pre-commit run --all-files`, fix any failures, iterate until clean
- **`enforce-submit-pr.yaml`**: Stage, commit (conventional format with FR-XXX), push, create PR with auto-merge label

## Acceptance Criteria

- [ ] `scripts/enforce_worktree.sh` creates an isolated git worktree for a given FR path
- [ ] The worktree is cleaned up on both success and failure (trap handler)
- [ ] Script validates no uncommitted changes on base branch before creating worktree
- [ ] Shared `.venv` is symlinked into the worktree (no redundant installs)
- [ ] `examples/enforce/graph.yaml` passes `yamlgraph graph lint`
- [ ] Each copilot node uses session continuations (`resume` flag)
- [ ] Pre-commit checks run inside the worktree, not the main tree
- [ ] PR is created with conventional commit format and FR-XXX reference
- [ ] Multiple worktree pipelines can run simultaneously without interference (tested: two parallel invocations targeting different branches both succeed without cross-contamination of files or state)
- [ ] `tmp/worktrees/` is already in `.gitignore` (verified, no change needed)
- [ ] Unit tests cover: branch name derivation, worktree path construction
- [ ] Integration test: shell script creates and cleans up a real worktree (guarded by git availability)
- [ ] Concurrency test: two parallel `enforce_worktree.sh` invocations targeting different FRs complete independently
- [ ] Documentation added to `reference/` describing the parallel pipeline workflow
- [ ] Tests tagged with `@pytest.mark.req` for new requirement IDs

## Constraints

- **Depends on FR-105** (copilot session continuations) — ✅ Implemented
- **Depends on FR-081** (copilot node type) — ✅ Implemented
- **Git worktree requires clean state** — the script validates no uncommitted changes on the base branch
- **Shared `.venv`** — worktrees symlink to the main tree's `.venv` to avoid redundant installs
- **Disk space** — worktrees are full checkouts; `tmp/worktrees/` is already in `.gitignore`
- **macOS-only** — script uses Darwin-compatible syntax; portability to Linux is a future concern (document limitation)
- **Watch.sh integration deferred** — extending `watch.sh` to auto-detect approved FRs is out of scope; this FR delivers the standalone script and graph only. Watch.sh integration is a follow-up FR.

## Alternatives Considered

1. **Docker-based isolation** — Heavier, requires Docker daemon, doesn't leverage git worktree's native branch isolation. Overkill for the stated goal.

2. **Sequential pipeline in main worktree** — This is the status quo. It works but blocks the developer.

3. **GitHub Actions / remote CI** — Complements but doesn't replace local enforcement. The Scripture's pre-commit hooks are local-first by design. Remote CI is a future enhancement, not a substitute.

4. **Pass FR content as `--var` instead of path** — `--var fr_content="$(cat $FR_PATH)"` would avoid Copilot needing file access, but FR files can be large and shell quoting becomes fragile. Passing the path and letting Copilot read it is simpler and more robust.

## Judgement Amendment Resolution

The original inbox topic received a Judgement of AMEND with 6 issues. Resolutions:

| # | Issue | Resolution |
|---|-------|------------|
| ISSUE-1 | `read_file` tool does not exist | ✅ Removed `read_fr` node. Copilot reads FR directly via `--allow-all-paths`. |
| ISSUE-2 | `graphs/` directory does not exist | ✅ Placed at `examples/enforce/graph.yaml` following existing convention. |
| ISSUE-3 | FR-105 dependency status unclear | ✅ FR-105 is fully implemented (2026-02-27). Dependency satisfied. |
| ISSUE-4 | Concurrent testing strategy missing | ✅ Added concrete AC: two parallel invocations targeting different branches both succeed without cross-contamination. |
| ISSUE-5 | macOS-specific shell syntax | ✅ Deferred watch.sh integration (the source of `sed -i ''`). Script uses only portable shell constructs. macOS limitation documented in Constraints. |
| ISSUE-6 | Effort estimate optimistic | ✅ Reduced scope: deferred watch.sh integration to follow-up FR. Core scope is script + graph + prompts + tests + docs = 3 days. |

## Judgement Verdict: APPROVE

**Date:** 2026-02-27
**Verdict:** APPROVE — Scope frozen. Authority granted to implement.

### Findings

The FR is well-structured, dependencies are verified as implemented, scope is clear and minimal, and the design aligns with existing architecture (three-layer pattern, copilot node conventions, `examples/` placement).

### Implementation Notes (non-blocking)

Two minor issues to correct during implementation:

1. **Prompt resolution requires metadata flags.** The graph YAML example is missing `prompts_relative: true` and `prompts_dir: prompts` in the `metadata:` block. Without these, `prompt: prompts/enforce-implement.yaml` will not resolve to `examples/enforce/prompts/enforce-implement.yaml`. Follow the convention in `examples/copilot/graph.yaml`: add the metadata flags and use bare prompt names (e.g., `prompt: enforce-implement`).

2. **Shell validation logic is imprecise.** `git diff --quiet "$BASE_BRANCH"` compares the working tree to the base branch tip — it does not check "uncommitted changes on base branch" as the comment states. If the developer is on a different branch, this always fails. Replace with `git diff --quiet && git diff --cached --quiet` to check for a clean working tree, or remove the check entirely (git worktree creation works with a dirty working tree).

### Strengths

- Dependencies (FR-081, FR-105) verified as fully implemented
- Amendment resolution table demonstrates iterative improvement on all 6 prior issues
- Watch.sh integration properly deferred to a follow-up FR
- Concurrency AC is concrete and testable
- Alternatives considered are thorough and well-reasoned
- Copilot node schema (cli_flags, resume, session_id) validated against actual codebase

## Related

- `feature-requests/105-copilot-session-continuations.md` — Prerequisite: session chaining (✅ Implemented)
- `feature-requests/FR-081-copilot-node.md` — Copilot node type (✅ Implemented)
- `feature-requests/068-chaplain-watch.md` — Watch loop automation
- `feature-requests/FR-098-consolidate-watch-graph.md` — Watch graph consolidation
- `.chaplain/watch.sh` — Existing watch loop (integration deferred to follow-up FR)
- `.pre-commit-config.yaml` — Quality gates that run inside the worktree
