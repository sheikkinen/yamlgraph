# Feature Request: Documented `graph run` invocations that cannot run as written

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed (2026-09-26) — filed by the FR-1084 census (AC-09);
awaiting judgement.
**Effort:** 1 day
**Requested:** 2026-09-26
**First consumer / first event:** a reader who copies one of the invocations
below from its README and runs it from the repository root; today each one
fails before any LLM call, or (python-map) runs without the documented input.
**Research:** not run; each finding is a mechanical census row in
`tests/fixtures/fr1084/invocations.tsv` (FR-1084).
**Prior art:**
- [FR-1084](FR-1084-reject-undeclared-cli-vars.md): the census that found
  these; it may repair only an unambiguous documentation key typo, so these
  are excluded there with this FR number.
- [FR-1087](FR-1087-safety-guards-demo-repair.md), [FR-1088](FR-1088-innovation-matrix-repair.md):
  own the safety-guards and innovation-matrix census rows; not repeated here.
- [FR-768](FR-768-tool-manifest-declaration-reuse.md): `--tool` manifests resolve from the current
  directory (`graph_loader.py` passes `Path.cwd()`).

## Summary

Five documented invocations fail when run from the repository root:

| Source | Graph | Failure |
|---|---|---|
| `examples/demos/corpus_census/README.md` L8 | `examples/demos/corpus_census/graph.yaml` | `--tool discover=fixtures/discover.tool.yaml` resolves from the cwd, not the graph directory: manifest not found |
| `reference/graph-yaml.md` L1648 | `examples/demos/corpus_census/graph.yaml` | `adapters/pdf-discover.tool.yaml` does not exist |
| `examples/demos/forensic-failure-diary/README.md` L24 | `examples/demos/forensic-failure-diary/graph.yaml` | `GraphConfigSchema`: `nodes.forensic_analysis.schema` is a dict where a string is required |
| `examples/demos/hook_classifier/README.md` L16 | `examples/demos/hook_classifier/graph.yaml` | `GraphConfigSchema`: `nodes.classify.variables.session_history` is `[]` where a string is required |
| `examples/demos/python-map/README.md` L14 | `examples/demos/python-map/graph.yaml` | `--var texts=…` is not a state key; the map reads `{state.sample.texts}` from `data_files` |

`yamlgraph graph validate` reports both `GraphConfigSchema` graphs as valid
while `load_graph_config` rejects them.

## Proposed Solution

Decided at judgement. Candidates: fix each README invocation or graph; for the
two schema failures, make `graph validate` use the same load path as
`graph run`.

## Acceptance Criteria

- [ ] Each row above is `PASS` in the FR-1084 census and its exclusion row is
  removed from `tests/fixtures/fr1084/exclusions.tsv`.

## Related

- [FR-1084](FR-1084-reject-undeclared-cli-vars.md)
