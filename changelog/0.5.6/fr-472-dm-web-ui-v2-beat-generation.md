---
type: feat
scope: examples
req: REQ-YG-470
---
- **FR-472 DM Web UI v2 — On-Demand Beat Generation**: A chosen planned beat can now be woven on demand via a new stateless `weave-beat.yaml` graph (`plan_all` map over cast → `weave` → `normalize_beat`; no checkpointer, interrupt, or loop), returning editable prose with status `generated`; Accept persists the prose (verbatim or edited), appends it to the chapter file via the new `append_beat_to_chapter` helper, and flips status to `committed`. Generation is random-access — any chapter/beat in any order — completing the journey-first v2 redesign. (REQ-YG-470)
