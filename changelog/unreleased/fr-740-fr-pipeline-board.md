---
type: feat
scope: scripts
---
- **FR-740 FR Pipeline Board**: `scripts/fr_board.py` generates a
  priority table + Mermaid DAG from FR status headers, Parent links,
  and `gates.yaml` (owned gates with pre-drafted questions); two-way
  drift lint wired at pre-commit; TEMPLATE.md gains the judgement
  skeleton with the questions-or-none terminal section. First render
  surfaced 13 duplicate FR/NC IDs and the status-header lag it exists
  to expose.
