---
type: fix
scope: race
req: REQ-YG-724
---
- **FR-1144 Race nodes honour `thinking_budget`**: `type: race` nodes and router nodes with race `candidates:` now resolve `thinking_budget` from the node, then graph `defaults`, then `None` (the `llm`-node order), and pass it to every candidate's `create_llm` call. Previously the value was accepted and silently dropped, so thinking models such as `vertex/gemini-2.5-flash` thought on every race call (measured 5.46 s / 600 reasoning tokens vs 1.13 s / 0 at `thinking_budget: 0`). Provider dispatch is unchanged: non-thinking providers never receive the value. (REQ-YG-724)
