---
type: feat
scope: ci
req: REQ-YG-148
---
- **FR-149 CI CHANGELOG Gate**: Add `changelog-gate` job to `.github/workflows/commitlint.yml` that blocks merge of `feat` and `fix` PRs unless `CHANGELOG.md` is modified in the PR diff. Uses job-level `if` condition to skip for other PR types. Closes the structural gap where server-side squash merges bypass local commit-msg hooks. (REQ-YG-148)
