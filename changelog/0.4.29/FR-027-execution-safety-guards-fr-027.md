---
type: feat
scope: execution
req: REQ-YG-055
---
- **Execution Safety Guards (FR-027)** — P0 tier: protect against unbounded execution in graph pipelines.
  - **Map fan-out cap (`max_items`)**: Node-level `max_items` and graph-level `config.max_map_items` limit Send() fan-out; default 100. Truncates with warning. (REQ-YG-055)
  - **`recursion_limit` exposure**: `config.recursion_limit` parsed from YAML into `GraphConfig`; default 50. (REQ-YG-056)
  - **Loop limits in all node types**: `check_loop_limit` now enforced in tool, python, and passthrough nodes (was LLM-only). (REQ-YG-057)
  - **Linter W012**: Warns when cycle-participating nodes lack `loop_limits` entries. (REQ-YG-058)
