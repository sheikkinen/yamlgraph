# Task: FR-809 repair — restore in-boundary sniff_url selection (graph.yaml only)

A previous timed-out validation run left `examples/api-discovery/graph.yaml`
depending on `probe_findings.has_html_pages`, a field the committed
endpoint-probe step schema does not emit (its addition was reverted: step
graphs are frozen under FR-809 — no step-graph or leaf-tool changes).

Repair `examples/api-discovery/graph.yaml` ONLY. Do not touch any file
under `examples/api-discovery/steps/` or `examples/api-discovery/tools/`,
nor the prompts.

1. Remove the three conditional edges out of `endpoint_probe` that test
   `probe_findings.has_html_pages`; restore the single unconditional edge
   `endpoint_probe` → `select_sniff_url` (followed by the existing
   `select_sniff_url` → `page_analysis`).
2. Change the `select_sniff_url` node's variables back to
   `html_pages: "{state.candidate_urls.candidate_urls}"` — the list
   page-analysis receives, non-empty on this path because it is gated by
   `candidate_urls.has_candidates == true`. This matches the frozen
   handoff table ("deterministic selection from the HTML page list
   page-analysis received").
3. Leave every other node, edge, prompt, and state key exactly as-is.

## Validation

```bash
yamlgraph graph lint examples/api-discovery/graph.yaml
pytest tests/unit/test_fr809_orchestrator_v2.py tests/unit/test_fr791_api_discovery_orchestrator.py -q --no-cov
```

Both must be fully green. Record the repair in tmp/draft-authoring-report.md.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
