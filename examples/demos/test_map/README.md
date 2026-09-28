# test_map — test corpus map (FR-1137)

Maps every test function under `tests/unit` and `tests/integration` to:

- `description` — exactly one sentence saying what the test verifies;
- `target` — `core`, `linter`, `examples`, `scripts`, `docs` or `other`
  (tie-break `linter > examples > scripts > docs > core > other`);
- `test_type` — `unit`, `integration` or `other`.

The model only claims those three fields. Everything else is deterministic:

| Stage | Code | Does |
|---|---|---|
| freeze | `tools.freeze_corpus` | refuses a dirty scope; checks file, byte, payload-token and partition ceilings before any LLM call; records commit SHA, per-file SHA-256, corpus hash, provider/model |
| extract | `extract.py` | AST nodeids, lines, inherited markers, `reqs` from `scripts/req_coverage.py`; packs whole tests into ≤ 8,000-token payloads carrying the import block |
| classify | `graph.yaml` map → `prompts/classify_tests.yaml` | one structured call per payload, default provider/model, temperature 0; a failed call is retried twice with validation feedback; the map needs `min_success: 0.95` |
| publish | `tools.publish_map` + `reconcile.py` | a partition fails on any missing, unknown, duplicate, wrong-partition, out-of-enum, malformed-description or map-error record; failed partitions are listed with their nodeids and defects (`failed_partitions`) and their tests left unmapped. Rejects when more than 5% of partitions fail, on a defect tied to no partition, or on a withheld-canary mismatch (canary tests in failed partitions count as skipped); otherwise writes JSON, then Markdown rendered only from the JSON |

## Run

```bash
yamlgraph graph run examples/demos/test_map/graph.yaml --token-usage > tmp/test-map-run.log 2>&1
```

The test scope must be committed and clean. Outputs:

- accepted: `tmp/test-map/test-map.json`, `tmp/test-map/test-map.md`,
  `tmp/test-map/raw-responses.jsonl`;
- rejected: only `tmp/test-map/test-map-rejected.json` (defects, raw
  findings, failures); the canonical files are deleted.

`graph run` exits 0 on some node failures and 3 when a call failed after
its retries — check the artifacts, not the exit code.

Small smoke (4 calls; `demo-output.log` is this run):

```bash
yamlgraph graph run examples/demos/test_map/graph.yaml --var scope=tests/unit/test_expression_language.py,tests/unit/test_commitlint_workflow.py --var canary_path=examples/demos/test_map/smoke-canary.json --var json_path=tmp/test-map-smoke/test-map.json --var md_path=tmp/test-map-smoke/test-map.md --full
```

`canary.json` holds seven hand-classified tests, one per target plus a
tie-break case. It is never shown to the model.
