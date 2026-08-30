---
type: removal
scope: hooks
req: REQ-YG-629
---
- **FR-927 Retire the FR-902 Lane-Guard Hook Machinery**: Deleted the session-lane hook system — `pre-command-guard.sh` Check 8 (lane-ownership denial, write-verb grep alternation, `FR902_ALLOW_OUTSIDE` escape), `checks/lane_guard.py`, `session-worktree.sh`, `session-checkpoint.sh`, their `session-probe.json` registrations, the `fr902.live` gate, and the FR-902 hook tests. FR-889's OS write lock is now the only write barrier on the main checkout; `scripts/worktree.sh session`/`gc`, `now.py` lane listing and `session_join.py` remain as manual tooling. Absence pinned permanently by `.github/hooks/tests/test_fr902_retired.py`. (REQ-YG-629)
