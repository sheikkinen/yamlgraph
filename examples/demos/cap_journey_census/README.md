# CAP Journey Census demo

Capability-registry census for `docs/2026-09-05-research-plan-cap-journey-census.md`: the graph reads `capabilities/CAP-*.yaml`, asks one cheap per-CAP classification for the four columns the traceability chain cannot carry — customer journey, blast kind, keep/retire/extend disposition, and value proposition — then stops at an LLM-free reduced ledger.

```bash
PYTHONPATH=$PWD yamlgraph graph run examples/demos/cap_journey_census/graph.yaml \
  --var source="capabilities:ids=CAP-131,CAP-81,CAP-126" \
  --var provider=anthropic \
  --var model=claude-haiku-4-5 \
  --var journey_ids="author_graph,run_operate,debug_observe,integrate,serve_embed,census_classify,govern_process,audit_comply,conversational_app,none_internal" \
  --var journeys_path=examples/demos/cap_journey_census/journeys.yaml \
  --var canaries_path="" \
  --var output_path=tmp/cap-census/smoke.md \
  --json > tmp/cap-census/smoke.json
```

The reducer applies fail-closed anchors after the model call: journey ids must reconcile with the catalog, `keep` must cite a mechanical consumer path, `evidence_span` must be an exact substring from the CAP yaml or FR head, and the hidden gate runs after markdown and JSONL artifacts are written so rows remain inspectable. `retire` rows are claims, not removals; they still go through the FR-466 lifecycle.
