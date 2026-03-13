# FR-199: FSM Scripture CLAUDE.md — Diary

**Date:** 2026-03-13
**Feature:** FR-199 — Upgrade FSM CLAUDE.md to Full YAMLGraph Doctrine

## Cognitive Process

### The Task

Replace a four-line YAGNI/TDD/DRY/KISS block in `fsm/CLAUDE.md` with the full
YAMLGraph doctrine. Straightforward on paper; it surfaced a real infrastructure
trap mid-execution.

### Trap: Broken Symlink Ambush

The `fsm/` directory is a symlink to `../statemachine-engine`, which resolves
correctly in the main repo (`/Users/…/src/yamlgraph/fsm → /Users/…/src/statemachine-engine`)
but becomes a **broken symlink** in git worktrees because the relative target
`../statemachine-engine` lands outside the worktree directory tree.

Initial instinct: add a `pytest.skip()` when the symlink is broken. That is
exactly the `audit_as_ritual` trap — a guard that silences the test rather than
resolving the real constraint.

**Cure applied (`callsite_fix`):** Use `git worktree list --porcelain` to
discover the main worktree path at test collection time, then follow the symlink
from there. The test fails with a real failure message if the target is missing
anywhere, and passes correctly in both the main repo and in CI.

### Trap: Framework Costume Awareness

The `framework_costume` trap in the Knowledge Graph describes "FSM wearing DAG
costume". The inverse is equally real: this change is itself a meta-level
instance — making sure agents operating inside `fsm/` are not wearing a
"doctrine-lite" costume. The fix is to embed the full scaffold, not a summary.

### What Surprised Me

The broken-symlink problem was not anticipated in the FR ("documentation-only
change"). The FR's phrase "no tests required" collided with Commandment 7's
"no production branch without a witness test". Resolution: write the test, but
make it resilient to worktree topology using git's own worktree metadata.

This is exactly the `detection_without_enforcement` pattern applied in reverse:
the test MUST block on content absence, not just report it.

### Process Notes

- RED → GREEN required zero iteration: the doctrine text was exact, the test
  assertions were precise, and the file edit succeeded on the first attempt.
- The `_find_fsm_claude_md()` helper is the only non-trivial code in the test;
  it is a boundary normalizer (the_one_law: normalize at the entry boundary).

## Heuristic Extracted

**Symlink topology is a boundary.** When a file lives in a sibling repo
accessed via symlink, the symlink's validity is environment-dependent. Tests
that read through symlinks must normalize at that boundary using `git worktree
list`, not assume the symlink resolves identically in all contexts.

**Seed:** Should `.chaplain/watch.sh` verify that `fsm` symlink is valid before
processing `fsm/`-scoped proposals, and fail loudly if not?
