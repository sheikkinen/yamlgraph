---
type: fix
scope: linter
---
- **FR-621 Linter descends into map sub-nodes**: `check_tool_references()` now
  collects tool references from a node *and* its `type: map` sub-node (nested
  under `node:`). This removes a W001 false positive (a tool used only inside a
  map sub-node was reported "defined but never used") and closes an E003 false
  negative (an undefined tool referenced inside a map sub-node passed lint and
  failed only at runtime). (REQ-YG-003)
