---
type: feat
scope: examples
req: REQ-YG-468
---
- **FR-470 DM Web UI v2 — Synopsis Review**: The dungeon-master web board is now
  journey-first. Preplan stops at the story skeleton (no eager weave) and renders
  an editable **synopsis card**; the DM can **regenerate**, **edit**, or **accept**
  the synopsis (logline, conflict, themes, tone, arc) before browsing the outline.
  A per-session story document (`story_doc` over `story.json`) is the source of
  truth; the v1 turn-loop checkpointer is retired from the web path (CAP-169
  retired, superseded by CAP-170). (REQ-YG-468)
