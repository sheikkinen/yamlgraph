---
type: feat
scope: interruptoutputmapping
---
- **interrupt_output_mapping for subgraphs** (FR-006) - Expose child state during interrupts
  - New `interrupt_output_mapping` field in subgraph node config
  - Maps child state → parent when subgraph hits an interrupt node
  - Uses LangGraph's internal `__pregel_send` to update parent state before interrupt propagates
  - `output_mapping` still used for normal completion (reaches END)
  - 3 integration tests for interrupt output mapping
  - See [reference/subgraph-nodes.md](reference/subgraph-nodes.md#interrupt-output-mapping-fr-006)
