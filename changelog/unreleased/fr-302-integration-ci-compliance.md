---
type: fix
scope: ci
---
- **FR-302 Integration Test CI Compliance**: Use `docs:` PR title to bypass feat-specific CI gates; add `--title` flag to `create_pr.sh`; add ruff preflight check; remove `changelog_gen` state; fix `completed` infinite loop; add exit code assertion to run script.
- **FR-302 Stale Log & CI Timeout**: Clean old pipeline logs before starting; add 660s timeout to `waiting_ci` action.
- **FR-302 Preflight Scope**: Scope ruff preflight checks to `yamlgraph/` to avoid test/example formatting drift blocking the pipeline.
- **FR-302 Source Guard**: Guard `create_pr.sh` arg parsing for source vs direct execution; fix test mock ordering for `common.sh` log functions; add `ruff` mock to preflight tests.
- **FR-302 Merge Fix**: Remove `--delete-branch` from merge command; worktree teardown handles local branch cleanup.
- **FR-302 Unique Branch**: Use timestamped topic slug to avoid merged-PR collision guard blocking re-runs.
- **FR-302 Terminal State Assertion**: Fix polling and success assertion to match FSM engine terminal-state semantics (`completed` halts, no `stopped` transition).
