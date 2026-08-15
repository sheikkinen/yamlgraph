---
type: feat
scope: examples
req: REQ-YG-595
---
- **FR-791 API Discovery Orchestrator**: `examples/api-discovery/graph.yaml` composes the four enforced step manifests (endpoint-probe, page-analysis, platform-confirm, schema-extract) via `tool_call` nodes with conditional skip routing, llm candidate generation, and a single synthesize terminal emitting `found`/`not_found`/`needs_manual` with honest `steps_tried`. One command replaces the 10–30 min manual probe: live smokes returned `found` with real StatFin PxWeb data (fi/en/sv endpoints) and `not_found` for `example.invalid` reporting only executed steps. Recon/browser-sniff excluded from v1 per judgement. (REQ-YG-595)
