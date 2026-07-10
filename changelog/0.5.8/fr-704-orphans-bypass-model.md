---
type: feat
scope: demos
req: REQ-YG-536
---
- **FR-704 Recap Orphans Bypass the Model**: orphan assembly in the recap demo is now fully code-owned — `finalize_recap` copies unreferenced commit lines bit-exact into `orphans` (killing the reproducible one-character hash corruption `703b72d`→`703b72e` observed in two field runs) and appends deterministic window-rule convention entries (graph/prompt churn with no changelog fragment). The synthesis schema shrinks to two judgement fields (`workstreams`, `hotspots`); integration asserts orphan hashes by exact equality. Completes the FR-702/703/704 transport-eviction arc. (REQ-YG-536)
