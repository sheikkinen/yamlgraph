---
type: feat
scope: testing
---
- **FR-755 + FR-756 Core/Process Separation**: documented FSM bridge as contrib-tier ownership, added import-linter guard preventing core modules from importing `yamlgraph.utils.fsm`, introduced `process` test marker and collection-time boundary lint, and added CI `core-test` job for `pytest tests/unit -m "not process" -q --no-cov`.
