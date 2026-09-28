---
type: feat
scope: test-map
req: REQ-YG-723
---
- **FR-1137 Test corpus map**: new demo `examples/demos/test_map/` maps every test function in `tests/unit` and `tests/integration` to a one-sentence description, a primary target (`core`/`linter`/`examples`/`scripts`/`docs`/`other`) and a test type (`unit`/`integration`/`other`) with one structured call per payload at the default provider/model and temperature 0. Freeze, AST identity, ceilings, reconciliation, a withheld canary and hashing are deterministic Python; a run with any defect writes only `tmp/test-map/test-map-rejected.json`, otherwise canonical JSON with provenance plus a Markdown rendering of that JSON. Tolerated map-branch failures (runtime `MapFailure` models) are normalised to dicts at the publish boundary so they land in the rejection report. Up to 5% of partitions may fail (retry twice, map `min_success: 0.95`); failed partitions are listed with their tests, above 5% the map is rejected. (REQ-YG-723)
