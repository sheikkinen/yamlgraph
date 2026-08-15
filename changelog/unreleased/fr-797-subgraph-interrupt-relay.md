---
type: fix
scope: subgraph
req: REQ-YG-042
---
- **FR-797 Subgraph Interrupt Relay**: Repair subgraph interrupt propagation under LangGraph 1.x via a compile-time two-node split (`{name}__run` commits mapped child state and relay internals; `{name}__pause` performs a parent-native `interrupt`). Child interrupts now surface to the parent with pause-state committed before the pause, resume replays into the paused child, and unrelayed child interrupts fail loud with `ValueError`. Conditional outgoing edges from relay nodes are rejected at compile time (phase 1). (REQ-YG-042)
