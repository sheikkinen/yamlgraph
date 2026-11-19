---
type: fix
scope: release
req: REQ-YG-190
---
- **FR-1167 Release flow: branch → PR → tag the squash commit**: `scripts/release.sh` refuses to run on main and no longer tags the branch commit, which squash merge never puts on main. Its output, `reference/release-checklist.md` and the `release-version` skill document the actual route: freeze on `release/vX.Y.Z`, PR, human squash merge, tag the verified squash commit, push that one tag, and verify the tag CI run, the GitHub release and the exact PyPI version. Includes recovery for a merged but untagged freeze, the cause of the unpublished v0.6.6. (REQ-YG-190)
