# FR-173: Bug-Fix Pipeline with Condemning Test Phase

Bug-fix pipeline via isolated git worktrees, enforcing Commandment 7: no bug shall be fixed unless first condemned by a failing test.

## Overview

This pipeline orchestrates the bug-fix workflow:

1. **Condemn** — Write condemning test; verify it FAILS on current code
2. **Fix** — Minimal change to make the condemning test pass
3. **Verify** — Run full test suite + pre-commit hooks
4. **Submit PR** — Commit with `fix(scope): FR-XXX` and create PR

All phases chain via session continuations (FR-105), giving each phase full context from prior phases.

## Architecture

The `scripts/bugfix_worktree.sh` shell script is a **thin Presentation-layer wrapper** that handles worktree lifecycle (create, symlink, cleanup), then delegates all LLM orchestration to this graph:

```
┌─────────────────────────────────────────┐
│  bugfix_worktree.sh (Presentation)      │
│  - Validate args, clean tree            │
│  - Create worktree, symlink .venv       │
│  - Cleanup on exit                      │
├─────────────────────────────────────────┤
│  graph.yaml (Logic)                     │
│  - condemn → fix                        │
│  - → verify → submit_pr                 │
├─────────────────────────────────────────┤
│  Copilot CLI (Side Effects)             │
│  - Test writing, code edits, git, gh    │
└─────────────────────────────────────────┘
```

## Key Difference from Enforce Pipeline

| Feature | Enforce | Bugfix |
|---------|---------|--------|
| First phase | Implement (write new code) | Condemn (prove bug exists) |
| TDD contract | RED = behavior doesn't exist yet | RED = bug exists in current code |
| Commit type | `feat(scope): FR-XXX` | `fix(scope): FR-XXX` |
| RED commit | Test + implementation together | Test ONLY — `SKIP=pytest` commit |
| Git history | Single implementation commit | Separate RED (condemn) and GREEN (fix) commits |

## Usage

### Via Orchestration Script (Recommended)

```bash
# Run bugfix pipeline for a bug report
scripts/bugfix_worktree.sh feature-requests/FR-XXX-bug-description.md

# Specify a different base branch
scripts/bugfix_worktree.sh feature-requests/FR-XXX-bug-description.md develop
```

The script:
- Validates clean working tree (no uncommitted changes)
- Creates isolated worktree at `tmp/worktrees/feat/fr-xxx-bug-description`
- Symlinks shared `.venv` to avoid redundant installs
- Runs this pipeline in the worktree
- Cleans up worktree on exit (success or failure)

### Direct Graph Execution

If you're already in a worktree or want manual control:

```bash
yamlgraph graph run examples/bugfix/graph.yaml \
    --var fr_path="feature-requests/FR-XXX-bug-description.md" \
    --var branch="feat/fr-xxx-bug-description" \
    --full
```

### Automatic Routing via watch.sh

When the Chaplain pipeline (`.chaplain/watch.sh`) detects a new FR with `Type: Bug`, it automatically spawns the bugfix pipeline instead of the enforce pipeline:

```bash
# No manual intervention needed — watch.sh routes automatically
echo "Fix the broken parser" > .chaplain/inbox/fix-parser-bug.md
```

## Condemning Test Protocol

The condemn phase enforces a strict contract:

1. **Read** the bug report (understand the failure)
2. **Write** test function(s) tagged `@pytest.mark.req("REQ-YG-XXX")`
3. **Run** `pytest tests/unit/<test_file>.py -v --no-cov` against unmodified code
4. **Assert failure** — if the test passes, the bug is not proven
5. **Commit RED** — `SKIP=pytest git commit -m "test(scope): FR-XXX condemning test"`

The RED commit (condemning test) and GREEN commit (fix) are separate in git history, providing a clear proof trail.

## Related

- [examples/enforce/](../enforce/) — Feature enforcement pipeline (four-phase TDD)
- [FR-105](../../feature-requests/FR-105-copilot-session-continuations.md) — Session continuations
- [FR-106](../../feature-requests/FR-106-parallel-worktree-pipeline.md) — Worktree pipeline
- [FR-128](../../feature-requests/FR-128-enforce-yamlgraphication.md) — Enforce graph delegation
