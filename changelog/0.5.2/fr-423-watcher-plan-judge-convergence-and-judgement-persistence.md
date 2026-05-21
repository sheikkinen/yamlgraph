---
type: fix
scope: watcher
---
- **FR-423 Watcher Plan/Judge Convergence**: Stabilize `fr_path` across AMEND loops, require in-place plan edits when `fr_path` exists, and add judge writeback persistence guard to fail fast when AMEND/REJECT rationale is not persisted to the FR artifact.
