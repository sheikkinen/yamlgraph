---
type: fix
scope: concurrency
req: REQ-YG-698
---
- **FR-1085 One resolved max_concurrency for managed runs**: CLI `graph run` (sync, `--async`, `--stream`), `invoke_graph`, `run_graph_async` and `run_graph_streaming_native` now always pass LangGraph a `max_concurrency`, resolved as caller run value (or `--max-concurrency`) → graph `config.max_concurrency` → `YAMLGRAPH_MAX_CONCURRENCY` → `8`. Before, an unset width fell back to LangGraph's thread-pool default, so a 40-item map ran 32 branches at once on a 64-CPU host and only 6 on a 2-CPU host. A bad caller or environment value raises `ValueError` naming its source and value before any node runs; the caller's run config is copied, never mutated. A raw compiled `app.invoke`/`ainvoke` stays caller-owned. (REQ-YG-698)
