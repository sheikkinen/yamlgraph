# FR-106: Parallel Development Pipeline via Git Worktrees

End-to-end feature enforcement in isolated git worktrees, enabling parallel feature development.

## Overview

This pipeline orchestrates the full Enforce phase:

1. **Implement** - Read FR, implement with TDD (red-green-refactor)
2. **Test & Demo** - Run tests, create examples if applicable
3. **Pre-commit** - Run all pre-commit hooks, fix failures
4. **Submit PR** - Commit, push, create PR

All phases chain via session continuations (FR-105), giving each phase full context from prior phases.

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
