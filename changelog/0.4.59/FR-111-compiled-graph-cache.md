---
type: feat
scope: compiled
req: REQ-YG-107
---
- **FR-111 Compiled Graph Cache** (CAP-34, REQ-YG-107): Process-global `GRAPH_CACHE` in `yamlgraph/graph_cache.py` so `load_and_compile_async()` results survive action module reloads. Eliminates 1.5–4s recompilation on every LLM action invocation in engines that reload action modules per FSM transition. `cache=None` opt-out for test isolation. Migrates `yamlgraph_action.py` and `yamlgraph_preload_action.py` off local `_GRAPH_CACHE` workarounds. 10 unit tests.
