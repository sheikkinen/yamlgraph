---
type: feat
scope: p1
req: REQ-YG-059
---
- **FR-027 P1 complete**: Execution safety guards — all P1 items implemented under TDD.
  - **`max_iterations` default fix**: Corrected agent node default from 5→10 to match Pydantic schema; eliminates silent shadowing across 6 sources. (REQ-YG-059)
  - **`max_tokens` end-to-end wiring**: Wired from graph YAML `config.max_tokens` and node-level `max_tokens` through `graph_loader` → `llm_factory` → `executor` → `llm_nodes` → all providers. Uses `optional_kwargs` pattern (only sent when explicitly set). LLM cache key expanded to 4-tuple. (REQ-YG-060)
  - **Global execution timeout**: `config.timeout` in YAML and `--timeout` CLI flag; uses `signal.alarm` on Unix. Raises `SystemExit(1)` on expiry. CLI overrides YAML. (REQ-YG-061)
