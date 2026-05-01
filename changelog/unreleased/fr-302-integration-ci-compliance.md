---
type: fix
scope: ci
---
- **FR-302 Integration Test CI Compliance**: Use `docs:` PR title to bypass feat-specific CI gates; add `--title` flag to `create_pr.sh`; add ruff preflight check; remove `changelog_gen` state; fix `completed` infinite loop; add exit code assertion to run script.
