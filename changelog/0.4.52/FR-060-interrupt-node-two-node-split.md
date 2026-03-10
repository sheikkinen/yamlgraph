---
type: fix
scope: interrupt
req: REQ-YG-021
---
- **FR-060 Interrupt node two-node split** (REQ-YG-021): `interrupt()` raises `GraphInterrupt` before the node returns, so `state_key` was never committed. Split `create_interrupt_node()` into `(prepare_fn, interrupt_fn)` tuple: prepare computes and commits payload to state, interrupt reads from state and pauses. `compile_node()` adds both with internal edge; `_process_edge()` redirects incoming edges to prepare node. Works with all checkpointers including `SimpleRedisCheckpointer`. Nine new tests, 17 existing updated.
