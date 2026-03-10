---
type: feat
scope: watchenforce
req: REQ-YG-116
---
- **FR-116 Watch→Enforce Spawn**: `watch.sh` snapshots `feature-requests/` before graph execution, diffs after via `comm -13`, skips rejected FRs (`Status.*Rejected`), and spawns `enforce_worktree.sh` via `nohup ... &` for approved FRs. Output redirected to `tmp/enforce-<slug>.log`. Pure shell, no state files, no Python helpers. 16 unit tests. (REQ-YG-116)
