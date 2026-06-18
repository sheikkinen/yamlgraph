---
type: feat
scope: examples
---
- **FR-513 Emotional State in World Ledger**: The DM v2 `world_state` ledger now
  carries a typed `relationships` array (romantic_bond, alliance, enmity,
  hierarchy, rivalry) so emotional and alliance facts persist across chapter
  boundaries instead of resetting from context-window proximity. Relationships are
  grounded at the boundary — `parse_world_state` drops any bond lacking
  `recap_citations` or fewer than two named parties (no hallucinated lovers).
  `format_world_state` renders them compactly with a `relationships` selector:
  `active` (turn context, dormant/archived excluded) vs `all` (close
  carry-forward, status-labelled). `running_scene` threads active relationships
  into turn-1 play context; `chapter_close.yaml` extracts them from the recaps.
