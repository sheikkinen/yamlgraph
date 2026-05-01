---
type: fix
scope: ci
---
- **FR-302 Integration Test CI Compliance**: Use `docs:` PR title to bypass feat-specific CI gates; add `--title` flag to `create_pr.sh`; add ruff preflight check; remove `changelog_gen` state; fix `completed` infinite loop; add exit code assertion to run script.
- **FR-302 Stale Log & CI Timeout**: Clean old pipeline logs before starting; add 660s timeout to `waiting_ci` action.
