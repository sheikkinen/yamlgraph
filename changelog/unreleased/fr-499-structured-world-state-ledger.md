---
type: feat
scope: dungeon-master
---
- **FR-499 Phase A structured world_state ledger**: The DM v2 forward-carry
  `world_state` was a free-prose string — which let one chapter silently
  contradict an earlier chapter's facts (a phantom hand-axe, a seized staff
  wielded again, a wedged slab climbed over). Phase A replaces it with a typed,
  Pydantic-validated ledger (`characters[]{name, faction, status, location,
  inventory[]}`, `objects[]{name, holder, location}`, `facts[]`) emitted by
  `chapter_close`, persisted on the chapter card, and threaded through every
  carry-forward touch-point. A deterministic `format_world_state` renders it back
  to terse prompt text for the next chapter's play and close — never a raw dict
  repr, and never into the rendered manuscript. Detection-only: the ledger informs
  continuity but does not yet block (Phase B deferred).
