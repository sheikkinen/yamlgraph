---
type: feat
scope: examples
---
- **FR-479 DM Director/Narrator Split**: The Dungeon Master play loop now runs a
  structured `direct` node before the prose `recap` node. The director judges
  scene `phase`, emits an opening `establishing` description, signals
  `scene_complete` (stopping the plain next-turn advance), and raises
  informational `continuity` flags when a non-rostered character takes decisive
  action — surfaced to the DM, never auto-applied.
