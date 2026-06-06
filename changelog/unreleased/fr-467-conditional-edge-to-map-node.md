---
type: fix
scope: graph
req: REQ-YG-434
---
- **FR-467 Conditional Edge to Map Node**: A conditional (expression) edge whose target is a `map` node now compiles to a single router that fans out via `Send`, instead of registering a second unconditional map router alongside the expression router. Previously LangGraph ran both routers every superstep, so the condition never took effect and interrupt loops with a terminating branch (e.g. the dungeon-master turn loop) looped forever. Mixing an unconditional edge to a map node with conditional edges on the same source is now rejected at compile time. (REQ-YG-434)
