---
type: feat
scope: ci
req: REQ-YG-151
---
- **FR-157 CI Conflict Marker Gate**: Add `conflict-check` job to `.github/workflows/commitlint.yml` that greps tracked files for unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), excluding `.github/` and `*.md.bak`. Complements the local `check-merge-conflict` pre-commit hook which is bypassed by server-side squash merges. Document `conflict-check` status check and "require branches to be up to date" setting in `CLAUDE.md` branch protection table. (REQ-YG-151)
