---
type: feat
scope: schema
---
- **FR-673 Node config boundary validation**: `NodeConfig` now uses `extra="forbid"` — unknown YAML keys on nodes are rejected at load time with a named error. Added 20+ missing fields to the schema covering all node types. (REQ-YG-002)
- **FR-674 Guard schema split**: Extracted guard/verification/cache config classes to `models/guard_schema.py`, bringing `graph_schema.py` from 531 → 437 lines (below 450 ceiling). (REQ-YG-002)
