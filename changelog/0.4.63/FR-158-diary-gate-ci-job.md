---
type: feat
scope: diary
req: REQ-YG-152
---
- **FR-158 Diary Gate CI Job**: Add `diary-gate` job to `.github/workflows/commitlint.yml` that blocks merge of `feat`/`fix` PRs with `FR-XXX` reference unless a diary reflection file exists in the PR diff. Closes the enforcement gap where server-side squash merges bypass local pre-commit diary hooks. (REQ-YG-152)
