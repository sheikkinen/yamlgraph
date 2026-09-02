---
type: fix
scope: bridge
---
- **FR-954 Faithful no-fork import simulation**: the FR-950 no-fork import witness in `tests/unit/test_fr713_persistent_bridge.py` deleted only `os.register_at_fork` (a surface no real platform exhibits) and, since PR #555, pre-imported `asyncio`, `random` and `langgraph.checkpoint.base` so the cold dependency chain never ran under the simulated surface. The subprocess now imports only `os`, removes both `os.fork` and `os.register_at_fork`, asserts both are absent, and only then imports yamlgraph through its ordinary dependency chain — every fork-hook registrant (`uuid_utils`, stdlib `asyncio`/`random` on 3.14+) takes its genuine no-fork path exactly as on Windows. Test-only change; no production, capability or requirement change.
