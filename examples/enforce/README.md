# FR-106: Parallel Development Pipeline via Git Worktrees

End-to-end feature enforcement in isolated git worktrees, enabling parallel feature development.

## Overview

This pipeline orchestrates the full Enforce phase:

1. **Implement** - Read FR, implement with TDD (red-green-refactor)
2. **Test & Demo** - Run tests, create examples if applicable
3. **Critique** - Evaluate implementation against FR acceptance criteria (FR-169)
4. **Refine** - Address critique feedback (loops with Critique, max 2 iterations)
5. **Distill Reflection** - Generate diary reflection from critique findings
6. **Pre-commit** - Run all pre-commit hooks, fix failures
7. **Submit PR** - Commit, push, create PR

All phases chain via session continuations (FR-105), giving each phase full context from prior phases.

### Reflexion Loop (FR-169)

Between Test & Demo and Pre-commit, a reflexion loop evaluates the implementation against the FR's acceptance criteria:

```
test_and_demo → critique ──(score ≥ 0.85)──→ distill_reflection → precommit_check
                   ↑          │
                   │    (score < 0.85)
                   │          ↓
                   └──── refine
```

- **Critique** scores the implementation 0.0–1.0 against FR acceptance criteria
- **Refine** addresses specific feedback items, then loops back to Critique
- Loop is bounded: max 3 critique iterations, 2 refine iterations
- `loop_exits: { critique: distill_reflection }` ensures post-loop pipeline continues (FR-172)
- **Distill Reflection** generates a meaningful diary entry from the critique context

Worst-case timeout: 3×300s + 2×300s + 300s = **30 minutes**.

## Architecture (FR-128)

The `scripts/enforce_worktree.sh` shell script is a **thin Presentation-layer wrapper** that handles worktree lifecycle (create, symlink, cleanup), then delegates all LLM orchestration to this graph:

```
┌─────────────────────────────────────────┐
│  enforce_worktree.sh (Presentation)     │
│  - Validate args, clean tree            │
│  - Create worktree, symlink .venv       │
│  - Cleanup on exit                      │
├─────────────────────────────────────────┤
│  graph.yaml (Logic)                     │
│  - implement → test_and_demo            │
│  - → critique ↔ refine → distill        │
│  - → precommit_check → submit_pr        │
├─────────────────────────────────────────┤
│  Copilot CLI (Side Effects)             │
│  - Code edits, test runs, git, gh       │
└─────────────────────────────────────────┘
```

This follows the same delegation pattern as `.chaplain/watch.sh` → `examples/copilot/graph.yaml`.

## Usage

### Via Orchestration Script (Recommended)

The `scripts/enforce_worktree.sh` script handles worktree creation, cleanup, and pipeline execution:

```bash
# Run enforce pipeline for a feature request
scripts/enforce_worktree.sh feature-requests/FR-XXX-feature-name.md

# Specify a different base branch
scripts/enforce_worktree.sh feature-requests/FR-XXX-feature-name.md develop
```

The script:
- Validates clean working tree (no uncommitted changes)
- Creates isolated worktree at `tmp/worktrees/feat/fr-xxx-feature-name`
- Symlinks shared `.venv` to avoid redundant installs
- Runs this pipeline in the worktree
- Cleans up worktree on exit (success or failure)

### Direct Graph Execution

If you're already in a worktree or want manual control:

```bash
yamlgraph graph run examples/enforce/graph.yaml \
    --var fr_path="feature-requests/FR-XXX-feature-name.md" \
    --var branch="feat/fr-xxx-feature-name" \
    --full
```

## Parallel Development

Multiple features can be enforced simultaneously:

```bash
# Terminal 1
scripts/enforce_worktree.sh feature-requests/FR-107-feature-a.md &

# Terminal 2
scripts/enforce_worktree.sh feature-requests/FR-108-feature-b.md &

# Both run independently in separate worktrees
```

## Requirements

- Git (for worktree management)
- Clean working tree (script validates no uncommitted changes)
- Approved feature request with "Status: Approved" or "Verdict: APPROVE"
- GitHub Copilot CLI (`copilot` command available)

## Related

- [examples/enforcer/](../enforcer/) - Simpler two-phase enforce→demo pipeline
- [FR-105](../../feature-requests/FR-105-copilot-session-continuations.md) - Session continuations (✅ Implemented)
- [FR-081](../../feature-requests/FR-081-copilot-node.md) - Copilot node type (✅ Implemented)
- [FR-169](../../feature-requests/FR-169-enforce-reflexion-loop.md) - Reflexion loop (critique → refine → distill)
- [FR-172](../../feature-requests/FR-172-configurable-loop-exit-target.md) - Configurable loop exit target
