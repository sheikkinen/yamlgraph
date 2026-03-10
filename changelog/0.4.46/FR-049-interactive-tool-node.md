---
type: feat
scope: interactive
req: REQ-YG-075
---
- **FR-049 Interactive Tool Node** (CAP-24, REQ-YG-075): New `type: interactive_tool` node that expands a single YAML node into a full multi-turn conversation loop (`__start` → `__ask` → `__step` ↺ → `__end`) at compile time
  - Config-level expansion via `expand_interactive_tools()` — no new factory needed
  - `loop_until` condition with automatic `negate_condition()` for loop-back routing
  - `max_iterations` safety guard, optional `end` tool, `on_error` propagation
  - 31 unit tests + 10 integration tests (stub chatbot, sync/async, SQLite, streaming)
