---
type: fix
scope: map
req: REQ-YG-645
---
- **FR-984 Expose `max_concurrency` for map fan-out**: `config.max_concurrency` in `graph.yaml` and `--max-concurrency` on the CLI now reach LangGraph's `RunnableConfig["max_concurrency"]`, capping how many parallel map branches run at once for the whole invocation. Absent everywhere, no key is passed and behaviour is unchanged; booleans, strings, fractions, zero and negatives are rejected at load and at the parser. Throttling is delegated entirely to LangGraph — no yamlgraph scheduler. First consumer: the person-profile census graph now sets `config.max_concurrency: 4` after losing 100 of 259 rows to Azure 429s at the default pool width; its README shows the `--max-concurrency 2` override. (REQ-YG-645)
