---
type: fix
scope: cli
req: REQ-YG-697
---
- **FR-1084 graph run refuses undeclared --var keys**: `yamlgraph graph run` now checks every `--var` and `--var-file` key against the compiled graph's input schema before any LLM call. An unknown key exits 1 with one message naming every unknown key and the keys the graph accepts; previously LangGraph dropped it silently and the run finished on `None` (the 2026-09-24 innovation-matrix `domain` incident). `--import-state` and graph `variables:` are not checked. The census test pins every documented `graph run` invocation as PASS or a reasoned exclusion. The graph state class is now built with `typing_extensions.TypedDict` (new core dependency), so the input schema also builds on Python 3.11. (REQ-YG-697)
