---
type: feat
scope: ci
---
- **FR-919 Doc-Only PR CI Skip**: PRs whose diff contains only Markdown files skip `core-test`, the `test` matrix, and `security` via per-workflow `changes` gate jobs (dorny/paths-filter, single `!**/*.md` glob); skipped required checks satisfy branch protection, and tag pushes short-circuit to a full run so the release chain can never skip.
