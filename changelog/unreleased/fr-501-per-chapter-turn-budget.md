---
type: fix
scope: dungeon-master
---
- **FR-501 Per-Chapter Turn Budget**: Bound the DM v2 play loop with a per-chapter turn budget (`turn_ops.CHAPTER_TURN_CAP = 16`). A chapter's only natural exit is its director emitting `scene_complete`; a director that never resolves (observed live with a diffusion provider stuck in the "rising" phase for 91 turns) consumed the entire book `turn_cap` on one chapter. `chapter_should_close(doc, cid, n)` force-closes a chapter once it plays its full budget without resolving, so the book always terminates under any provider.
