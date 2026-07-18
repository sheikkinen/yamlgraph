---
type: feat
scope: scripts
---
- **FR-741 Orphan Intention Triage**: `todos.py` cross-checks orphaned
  todos against git artifacts (DELIVERED ELSEWHERE / NO ARTIFACT),
  supports content-keyed `--drop` dispositions (git-tracked sidecar),
  and feeds a now.py `intentions` section where live todos render as
  `claims:` with STALE CLAIM overruled by git. Backlog-zero triage:
  18 orphans → 3 preserved diary debts (FR-742 material).
