---
type: fix
scope: ci
---
- **Fix PR test status check**: `.github/workflows/workflow.yml` now triggers on `pull_request` so required branch protection check `test` runs for PRs, while release jobs remain tag-only.
