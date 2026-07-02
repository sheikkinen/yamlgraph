---
type: feat
scope: novel_fandom
req: REQ-YG-497
---
- **FR-647 Event propagation pre-pass**: `anchor_events` Python node runs once before the worldgen loop, computing per-character event context with spatial scoping (world/regional/local) and age arithmetic from absolute dates. Schema: `Character.birth_year`, `Event.year`/`scope`/`affected_locations`, `Premise.calendar_note`. Deepen prompt enriched with event timeline. (REQ-YG-497)
