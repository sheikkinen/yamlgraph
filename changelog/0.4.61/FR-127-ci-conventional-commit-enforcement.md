---
type: feat
scope: ci
---
- **FR-127 CI Conventional Commit Enforcement**: `.github/workflows/commitlint.yml` validates PR titles against Conventional Commits via `action-semantic-pull-request@v5`; enforces `FR-XXX` reference on `feat` PRs via inline script with env-based variable passing (no script injection). `revert` type added to both CI and local `conventional-pre-commit` hook for parity.
