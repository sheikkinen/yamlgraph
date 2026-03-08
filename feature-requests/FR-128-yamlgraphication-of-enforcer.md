# Feature Request: FR-128 YAMLGraphication of Enforcer Worktree

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-03-07

## Summary

Replace inline `copilot -p` calls and hardcoded prompts in `scripts/enforce_worktree.sh` with a single `yamlgraph graph run examples/enforce/graph.yaml` invocation, completing the FR-106 vision of a declarative enforce pipeline.

## Value Statement

The enforce pipeline becomes a first-class YAMLGraph citizen — editable via YAML, observable via LangSmith, and consistent with the three-layer architecture — instead of an opaque shell script with hardcoded prompts.

## Problem

`scripts/enforce_worktree.sh` was implemented as a monolithic 200-line shell script (FR-106) that handles five phases inline:

| Phase | Current impl (shell) | Existing YAML equivalent |
|-------|---------------------|--------------------------|
| 1. Implement | `copilot -p "$IMPLEMENT_PROMPT" --allow-all` | `examples/enforce/prompts/enforce-implement.yaml` |
| 2. Test/demo | `copilot -p "$TEST_PROMPT" --allow-all --continue` | `examples/enforce/prompts/enforce-test-demo.yaml` |
| 3. Pre-commit | Shell loop: `pre-commit run` + `copilot -p "$FIX_PROMPT"` × 5 | `examples/enforce/prompts/enforce-precommit.yaml` |
| 4. Commit/push | `git add -A && git commit && git push` | `examples/enforce/prompts/enforce-submit-pr.yaml` |
| 5. Create PR | `gh pr create` | (included in submit_pr prompt) |

The YAML graph at `examples/enforce/graph.yaml` and its four prompts were created as part of FR-106 but **never wired into the shell script**. The script bypasses the graph entirely, violating:

- **Commandment 3** (config separate from code): prompts are hardcoded as bash variables, not YAML templates
- **Commandment 4** (honor existing patterns): `examples/copilot/graph.yaml` demonstrates the correct pattern — `.chaplain/watch.sh` delegates to `yamlgraph graph run`, not raw `copilot -p`
- **Three-layer architecture**: the shell script conflates Presentation (worktree setup), Logic (LLM phases), and Side Effects (git/pre-commit) into one file

**Evidence of drift**: `.chaplain/watch.sh` correctly delegates to `yamlgraph graph run examples/copilot/graph.yaml` (line 24). The enforce script should follow the same pattern but doesn't.

## Proposed Solution

Thin `scripts/enforce_worktree.sh` to a worktree lifecycle wrapper that delegates all Copilot phases to `yamlgraph graph run examples/enforce/graph.yaml`.

### Before (current — 200 lines)

```bash
# Phase 1: hardcoded prompt
IMPLEMENT_PROMPT="Read the feature request at $FR_PATH. Follow TDD..."
copilot -p "$IMPLEMENT_PROMPT" --allow-all

# Phase 2: hardcoded prompt
TEST_PROMPT="Run pytest for this feature..."
copilot -p "$TEST_PROMPT" --allow-all --continue

# Phase 3: shell loop with hardcoded prompt
for i in $(seq 1 5); do
    pre-commit run --all-files || copilot -p "$FIX_PROMPT" --allow-all --continue
done

# Phase 4-5: inline git and gh
git add -A && git commit -m "..." --no-verify
gh pr create --title "..." --body "..."
```

### After (proposed — ~80 lines)

```bash
# ... worktree setup (unchanged: validate, create worktree, symlink .venv) ...

cd "$WORKTREE_DIR"
log_info "Running enforce pipeline graph..."

yamlgraph graph run examples/enforce/graph.yaml \
    --var fr_path="$FR_PATH" \
    --var branch="$BRANCH" \
    --full

log_info "Enforce pipeline completed successfully!"

# ... NEXT STEPS output (unchanged) ...
```

### What the shell script retains (Presentation layer)

These operations are infrastructure lifecycle, not LLM orchestration — they belong in shell:

1. Argument validation and FR file existence check
2. Branch name derivation via `worktree_helpers`
3. Clean working tree validation
4. FR commit to main before worktree creation
5. Git worktree creation + `.venv` symlink
6. Trap-based worktree cleanup on exit
7. "NEXT STEPS" output banner

### What moves to the YAML graph (Logic layer)

All four Copilot phases, already defined in `examples/enforce/graph.yaml`:

1. `implement` — TDD implementation (copilot node)
2. `test_and_demo` — Run tests, create demos (copilot node, session continuation)
3. `precommit_check` — Run pre-commit, fix failures (copilot node, session continuation)
4. `submit_pr` — Commit, push, create PR (copilot node, session continuation)

### What changes in the existing graph

The existing `examples/enforce/graph.yaml` is already well-structured. No changes needed to the graph or its prompts — they already implement the same phases with richer, better-structured prompts than the shell script's inline strings.

### What does NOT change

| File | Reason |
|------|--------|
| `examples/enforce/graph.yaml` | Already correct — the graph was built for this purpose |
| `examples/enforce/prompts/*.yaml` | Already implement all four phases with proper templates |
| `.chaplain/watch.sh` | Already delegates to yamlgraph correctly |
| `examples/copilot/graph.yaml` | Separate workflow (Plan→Judge→Summarize→WriteDiary) |
| `yamlgraph/utils/worktree_helpers.py` | Still used by the shell wrapper for branch/path derivation |

## Acceptance Criteria

- [x] `scripts/enforce_worktree.sh` calls `yamlgraph graph run examples/enforce/graph.yaml` instead of raw `copilot -p`
- [x] All inline prompt strings (`IMPLEMENT_PROMPT`, `TEST_PROMPT`, `FIX_PROMPT`) are removed from the shell script
- [x] The hardcoded Phase 3 pre-commit retry loop (lines 132-157) is removed — the `precommit_check` copilot node handles iteration via its prompt
- [x] The hardcoded Phase 4-5 git/PR commands (lines 159-178) are removed — the `submit_pr` copilot node handles commit and PR creation via its prompt
- [x] Worktree lifecycle (create, symlink, cleanup trap) remains in the shell script
- [x] `--var fr_path` and `--var branch` are passed to the graph run
- [x] `examples/enforce/graph.yaml` passes `yamlgraph graph lint`
- [x] Shell script shrinks from ~200 lines to ~80 lines
- [x] End-to-end flow: `scripts/enforce_worktree.sh <FR-path>` creates worktree, runs graph, graph executes all four phases, worktree is cleaned up
- [x] `.chaplain/watch.sh` integration unchanged (it spawns `enforce_worktree.sh` which now internally uses the graph)
- [x] Tests: existing worktree helper unit tests remain green
- [x] Documentation: `examples/enforce/README.md` updated to note that the shell script delegates to the graph

## Alternatives Considered

1. **Move the enforce graph into `examples/copilot/`** — The enforce pipeline is a separate workflow from Plan→Judge. Keeping them in separate directories maintains single responsibility. `examples/enforce/` already exists and is well-structured. Rejected.

2. **Replace the shell script entirely with a Python CLI** — The worktree lifecycle (create, symlink, trap cleanup) is naturally expressed in shell. A Python wrapper would add complexity for no benefit — the shell script's remaining job is infrastructure, not logic. Rejected.

3. **Add shell tool nodes to the graph for git operations** — The `submit_pr` copilot node already handles git commit/push/PR creation via its prompt. Adding deterministic shell nodes would split the Copilot session context, losing the benefit of session continuations. Rejected.

4. **Rewrite the graph from scratch in `examples/copilot/`** — The graph at `examples/enforce/graph.yaml` is already correct and tested. Rewriting would duplicate effort and create drift risk. The fix is to wire the existing graph, not replace it. Rejected.

## Related

- `scripts/enforce_worktree.sh` — Shell script to be thinned (the target)
- `examples/enforce/graph.yaml` — Existing YAML graph that defines the pipeline (FR-106)
- `examples/enforce/prompts/*.yaml` — Four phase prompts (already exist)
- `.chaplain/watch.sh` — Reference pattern for shell-to-yamlgraph delegation (line 24)
- `examples/copilot/graph.yaml` — Reference pattern for copilot node graphs
- `feature-requests/FR-106-parallel-worktree-pipeline.md` — Original FR that created both script and graph
- `feature-requests/FR-125-enforce-pipeline-finalize.md` — Post-merge finalization (unaffected)
