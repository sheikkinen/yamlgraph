---
type: feat
scope: examples
---
- **FR-480 DM Roster/Scene Name Binding**: The Dungeon Master key-scene generator
  is now bound to the rostered character names. The roster's display names are
  threaded into `key_scene.yaml` as an authoritative cast, so the scene cannot
  mint a character name the roster never sanctioned (e.g. `Brog` vs `Broga`) —
  removing the continuity drift at the generation boundary rather than flagging it
  every turn downstream.
