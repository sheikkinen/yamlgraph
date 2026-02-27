# Feature Request: Parallel Development Pipeline via Git Worktrees

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 3 days
**Requested:** 2026-02-27
**FR:** FR-106

## Summary

Add a shell script (`scripts/enforce_worktree.sh`) and a YAMLGraph graph (`examples/enforce/graph.yaml`) that automate the Enforce phase in an isolated git worktree — from branch creation through Copilot-driven implementation, testing, pre-commit checks, and PR submission — enabling parallel feature development without blocking the main working tree.

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
- `examples/enforcer/` — Two-phase enforce→demo pipeline with session continuations
- FR-105 — Copilot session continuations (✅ Implemented)
- FR-081 — Copilot node type (✅ Implemented)
- Pre-commit hooks — Comprehensive quality gates

**What's missing:** An orchestration script that creates an isolated git worktree, runs a multi-stage Copilot pipeline (implement → test → pre-commit → PR), and cleans up — all without touching the developer's main worktree.

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

# Validate clean working tree (uncommitted changes would propagate to worktree)
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: Uncommitted changes in working tree" >&2
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

**Design notes:**
- Working tree validation uses `git diff --quiet && git diff --cached --quiet` (checks both staged and unstaged), not `git diff --quiet "$BASE_BRANCH"` which compares against the branch tip and fails when on a different branch.
- `tmp/worktrees/` is already covered by `tmp/` in `.gitignore`.

### 2. Enforce pipeline graph: `examples/enforce/graph.yaml`

Extends the existing `examples/enforcer/` pattern with two additional stages (pre-commit, PR submission) and worktree-aware variables:

```yaml
version: "1.0"
name: enforce-pipeline
description: |
  End-to-end feature enforcement in isolated worktree.
  Four phases: implement → test/demo → pre-commit → submit PR.
  All phases chain via session continuations (FR-105).

prompts_relative: true
prompts_dir: prompts

state:
  fr_path: str        # Path to the approved feature request
  branch: str         # Git branch name
  implement_result: dict
  test_result: dict
  precommit_result: dict
  pr_result: dict

nodes:
  implement:
    type: copilot
    prompt: enforce-implement
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
    variables:
      fr_path: "{state.fr_path}"
      branch: "{state.branch}"
    state_key: implement_result
    timeout: 600

  test_and_demo:
    type: copilot
    prompt: enforce-test-demo
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    state_key: test_result
    timeout: 600

  precommit_check:
    type: copilot
    prompt: enforce-precommit
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    state_key: precommit_result
    timeout: 300

  submit_pr:
    type: copilot
    prompt: enforce-submit-pr
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.implement_result.session_id}"
    variables:
      branch: "{state.branch}"
      fr_path: "{state.fr_path}"
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

- **`prompts_relative: true` and `prompts_dir: prompts`** — Required for prompt resolution. Without these metadata flags, `prompt: enforce-implement` would not resolve to `examples/enforce/prompts/enforce-implement.yaml`. Follows the convention established in `examples/copilot/graph.yaml`.
- **No `read_fr` node** — The `implement` copilot node receives `fr_path` as a variable and reads it directly (Copilot has `--allow-all-paths` access). No `tool: read_file` node type exists.
- **Session continuations** — All downstream nodes chain via `resume: "{state.implement_result.session_id}"` (FR-105). This gives each phase full context from the implement phase.
- **Graph location** — Placed at `examples/enforce/` (separate from `examples/enforcer/` which is the simpler two-phase demo). The `enforce/` name matches the script name and represents the full end-to-end pipeline.

### 3. Prompts (in `examples/enforce/prompts/`)

Four prompts, each instructing Copilot for one pipeline phase:

| Prompt | Role |
|--------|------|
| `enforce-implement.yaml` | Read FR at `{fr_path}`, implement with TDD (red-green-refactor) |
| `enforce-test-demo.yaml` | Run tests, create/update example, run demo if applicable |
| `enforce-precommit.yaml` | Run `pre-commit run --all-files`, fix failures, iterate until clean |
| `enforce-submit-pr.yaml` | Stage, commit (conventional format + FR-XXX ref), push, create PR |

Prompt patterns follow the existing `examples/enforcer/prompts/` style (system + user blocks, variable substitution via `{var}`).

## Acceptance Criteria

- [x] `scripts/enforce_worktree.sh` creates an isolated git worktree for a given FR path
- [x] The worktree is cleaned up on both success and failure (trap handler)
- [x] Script validates clean working tree (both staged and unstaged) before creating worktree
- [x] Shared `.venv` is symlinked into the worktree (no redundant installs)
- [x] `examples/enforce/graph.yaml` passes `yamlgraph graph lint`
- [x] Graph uses `prompts_relative: true` and `prompts_dir: prompts` for prompt resolution
- [x] Each copilot node uses session continuations (`resume` flag chaining `implement_result.session_id`)
- [x] Pre-commit checks run inside the worktree, not the main tree
- [x] PR is created with conventional commit format and FR-XXX reference
- [x] Multiple worktree pipelines can run simultaneously without interference (two parallel invocations targeting different branches both succeed without cross-contamination)
- [x] Unit tests cover: branch name derivation, worktree path construction
- [x] Integration test: shell script creates and cleans up a real worktree (guarded by git availability)
- [x] Concurrency test: two parallel `enforce_worktree.sh` invocations targeting different FRs complete independently
- [ ] Documentation added to `reference/` describing the parallel pipeline workflow (deferred: README.md in examples/enforce/ serves this purpose)
- [x] Tests tagged with `@pytest.mark.req` for new requirement IDs (REQ-YG-106+)
- [x] `tmp/worktrees/` already in `.gitignore` via `tmp/` — verified, no change needed

## Constraints

- **Depends on FR-105** (copilot session continuations) — ✅ Implemented
- **Depends on FR-081** (copilot node type) — ✅ Implemented
- **Git worktree requires clean working tree** — script validates no staged or unstaged changes
- **Shared `.venv`** — worktrees symlink to the main tree's `.venv` to avoid redundant installs
- **Disk space** — worktrees are full checkouts; `tmp/worktrees/` is covered by `.gitignore`
- **macOS-only** — script uses Darwin-compatible syntax; Linux portability is a documented limitation for future work
- **Watch.sh integration deferred** — extending `watch.sh` to auto-detect approved FRs is out of scope; this FR delivers the standalone script and graph only

## Alternatives Considered

1. **Docker-based isolation** — Heavier, requires Docker daemon, doesn't leverage git worktree's native branch isolation. Overkill for the stated goal.

2. **Sequential pipeline in main worktree** — This is the status quo. Works but blocks the developer during Copilot execution and pre-commit checks.

3. **GitHub Actions / remote CI** — Complements but doesn't replace local enforcement. The Scripture's pre-commit hooks are local-first by design.

4. **Pass FR content as `--var` instead of path** — `--var fr_content="$(cat $FR_PATH)"` would avoid Copilot needing file access, but FR files can be large and shell quoting becomes fragile. Passing the path is simpler.

5. **Extend existing `examples/enforcer/`** — The enforcer is a clean two-phase demo (enforce→demo). Adding worktree orchestration and two more phases would bloat its scope. A separate `examples/enforce/` keeps single responsibility.

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Reviewed:** 2026-02-27

### Evaluation

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Scope clarity | ✅ Strong | Three deliverables (script, graph, prompts) clearly defined. Explicit deferrals (watch.sh, Linux) prevent scope creep. |
| Minimality | ✅ Strong | Thin orchestration over existing capabilities (FR-081, FR-105). No new framework code required. |
| Internal consistency | ✅ Strong | No contradictions. Graph YAML uses valid copilot node fields per current schema. |
| Acceptance criteria | ✅ Measurable | All 16 criteria are testable or inspectable. |
| Feasibility | ✅ Sound | 3-day estimate reasonable. All dependencies implemented. |
| Architecture alignment | ✅ Strong | Follows three-layer pattern. Extends existing `examples/enforcer/` pattern. |

### Notes for Implementation

1. **Shell test strategy (AC11):** "Unit tests cover branch name derivation, worktree path construction" — since the implementation is a shell script, the implementer should choose one of: (a) extract logic into a thin Python helper testable by pytest, (b) use subprocess-based tests that invoke the script with `--dry-run`, or (c) test the derivation logic as a standalone bash function. Option (a) is recommended for consistency with the test suite.

2. **Session thread topology:** All downstream nodes resume from `implement_result.session_id`, creating a single conversation thread. This is correct — each phase contributes to the same Copilot session, giving subsequent phases full context. The implementer should document this as a design note in the graph's description.

3. **No `on_error` between phases:** The linear pipeline has no error routing. If `implement` produces poor results, subsequent phases still execute. This is acceptable — the pre-commit phase acts as the quality gate, and Copilot nodes surface errors in their output. Adding `on_error: fail` is optional but would be a defensive improvement.

4. **`.venv` symlink risk:** Symlinked virtualenvs work for most packages but may fail for packages with absolute path references in `.pth` files. This is a known minor risk, acceptable for the stated use case.

## Related

- `feature-requests/105-copilot-session-continuations.md` — Session chaining (✅ Implemented)
- `feature-requests/FR-081-copilot-node.md` — Copilot node type (✅ Implemented)
- `examples/enforcer/graph.yaml` — Existing two-phase enforce→demo pipeline
- `examples/copilot/graph.yaml` — Reference for `prompts_relative`/`prompts_dir` metadata pattern
- `.chaplain/watch.sh` — Existing watch loop (integration deferred to follow-up FR)
- `.pre-commit-config.yaml` — Quality gates that run inside the worktree
