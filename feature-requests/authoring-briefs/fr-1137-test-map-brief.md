# Authoring brief: FR-1137 test corpus map graph + prompt

**Governing FR:** feature-requests/FR-1137-test-corpus-map.md (judged; fold table in the FR; R-1 overruled by the operator)
**Prior art:** examples/demos/corpus_census/graph.yaml (map over items, llm sub-node, `sorted_add` collect, python reduce reading `findings_failures`); examples/demos/meta_map/graph.yaml (map `min_success: 0`, failures channel)
**Target directory:** examples/demos/test_map/
**Artifacts to author:** `graph.yaml`, `prompts/classify_tests.yaml`

## Task

Revision 2. Revision 1 authored `graph.yaml` and the prompt; its smoke
found (a) `freeze_corpus`/`publish_map` returned unkeyed dicts — now fixed
in Python, they return `{"corpus": …}` and `{"result": …}`; and (b) the map
sub-node variables used `{state.partition.value.*}`, which resolves to
nothing, so the model saw no nodeids and returned `records: []` for all 4
partitions (the publish step correctly rejected 167 `missing`). Fix (b) in
the existing `graph.yaml` (edit, do not rewrite) and re-run the smoke.

Author the graph and the single prompt for the FR-1137 test corpus map.
Python already exists — do NOT author or edit Python or JSON:
`examples/demos/test_map/tools.py` provides `freeze_corpus` and `publish_map`
(both take `state`); `examples/demos/test_map/extract.py` and
`examples/demos/test_map/reconcile.py` are its helpers. The contract below
is witnessed by `tests/unit/test_fr1137_test_map.py`
(`test_graph_map_uses_default_model_and_frozen_ceilings`,
`test_prompt_schema_enums_and_tie_break_match_tools`); both must pass.

## Graph contract — `graph.yaml`

- `version: "1.0"`, `name: test-map`, `prompts_relative: true`,
  `prompts_dir: prompts`. Header comment: FR-1137; the LLM only CLAIMS
  description/target/type — freeze, identity, reconciliation, canary and
  rendering are deterministic Python.
- NO `defaults.provider` and NO `defaults.model` anywhere; the model call
  must resolve to the environment default provider/model (FR-1137 Q4).
- `config: {max_map_items: 900, max_concurrency: 8, timeout: 3600}`.
- State: `scope: str`, `canary_path: str`, `json_path: str`, `md_path: str`,
  `run_id: str`, `corpus: dict`, `findings: {type: list, reducer: sorted_add}`,
  `findings_failures: list`, `result: dict`.
- Tools (`type: python`, `path: tools.py`): `freeze_corpus` → function
  `freeze_corpus`; `publish_map` → function `publish_map`.
- Nodes, edges exactly `START → freeze → classify → publish → END`:
  - `freeze`: python, tool `freeze_corpus`, state_key `corpus`, `on_error: fail`.
  - `classify`: `type: map`, `over: "{state.corpus.partitions}"`,
    `as: partition`, `max_items: 900`, `min_success: 0`,
    `collect: findings`. Sub-node: `type: llm`, `prompt: classify_tests`,
    `temperature: 0.0`, `timeout: 180`, `on_error: skip`,
    `state_key: records_out`, variables `path: "{state.partition.path}"`,
    `nodeids: "{state.partition.nodeids}"`,
    `text: "{state.partition.text}"`. The map injects the raw item under
    `as:` — there is NO `.value` wrapper (that wrapper exists only on
    collected map results of non-dict type). NO provider/model keys on the
    sub-node. The word "canary" must not appear in the sub-node.
  - `publish`: python, tool `publish_map`, state_key `result`, `on_error: fail`.

## Prompt contract — `prompts/classify_tests.yaml`

Inline output schema: `records`, a list of objects with required string
fields `nodeid`, `description`, `target` (enum `"core"`, `"linter"`,
`"examples"`, `"scripts"`, `"docs"`, `"other"`), `test_type` (enum `"unit"`,
`"integration"`, `"other"`). Use the `items: {type: object, properties: …}`
form for the list.

System guidance must state:

- Return exactly one record per listed nodeid, copying the nodeid verbatim;
  no other nodeids.
- `description`: exactly ONE sentence, single line, ending in one `.`, what
  the test verifies (not how).
- `target` = the primary artifact under test: `core` (the yamlgraph package),
  `linter` (the graph/prompt linter and lint commands), `examples`
  (examples/ graphs, demos, their tools), `scripts` (scripts/), `docs`
  (documentation, reference, FRs, diaries), `other` (CI workflows under
  .github/workflows, packaging, pyproject, ramp, hooks, anything else).
- When more than one target applies, pick by this order, verbatim:
  `linter > examples > scripts > docs > core > other`.
- `test_type`: `unit` = in-process, may read repo files, no subprocess, no
  network, no real LLM; `integration` = spawns a subprocess, uses the
  network, calls a real LLM, or runs a full graph; `other` = anything else
  (e.g. benchmarks).
- The word "canary" must not appear anywhere in the prompt file.

User template: the file path, the nodeid list, then the source text.

## Validation the authoring run must perform

- `yamlgraph graph lint examples/demos/test_map/graph.yaml`
- `.venv/bin/python -m pytest tests/unit/test_fr1137_test_map.py -q --no-cov`
- Smoke over a small committed scope with its own two-entry canary (4 map calls):

```bash
yamlgraph graph run examples/demos/test_map/graph.yaml --var scope=tests/unit/test_expression_language.py,tests/unit/test_commitlint_workflow.py --var canary_path=examples/demos/test_map/smoke-canary.json --var json_path=tmp/test-map-smoke/test-map.json --var md_path=tmp/test-map-smoke/test-map.md
```

`graph run` exits 0 even on node failure: verify by artifact. Accepted →
the run writes `tmp/test-map-smoke/test-map.json` and `tmp/test-map-smoke/test-map.md`,
and writes `tmp/test-map-smoke/raw-responses.jsonl` with 4 lines. Rejected →
the run writes only `tmp/test-map-smoke/test-map-rejected.json`; report its
defect kinds honestly. A rejection caused by the model (e.g. a two-sentence
description) is a valid honest outcome — do not edit Python to hide it;
you MAY tighten the prompt guidance once and re-run once.
