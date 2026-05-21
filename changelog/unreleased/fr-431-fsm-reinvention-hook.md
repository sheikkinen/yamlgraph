---
type: feat
scope: hooks
---
- **FR-431 FSM Reinvention Detection Hook**: `post-edit-checks` now inspects `feature-requests/*.md` edits and warns when a feature request shows FSM reinvention signals without references to existing FSM integration (`statemachine_engine`, `fsm-as-conductor`, `yamlgraph.utils.fsm`).
