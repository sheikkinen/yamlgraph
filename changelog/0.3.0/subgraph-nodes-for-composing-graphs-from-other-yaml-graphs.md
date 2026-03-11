---
type: feat
scope: subgraph
---
- **Subgraph Nodes** for composing graphs from other YAML graphs
  - New `type: subgraph` node embeds child graphs
  - Two modes: `mode: invoke` (explicit state mapping) or `mode: direct` (shared schema)
  - Input/output mapping: `{parent_key: child_key}`, `"auto"`, or `"*"`
  - Thread ID propagation for checkpointer continuity
  - Circular reference detection with clear error messages
  - Nested subgraphs supported (graphs within graphs)
  - See demo: `graphs/subgraph-demo.yaml`
