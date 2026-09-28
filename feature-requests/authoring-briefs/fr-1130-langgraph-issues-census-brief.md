# Authoring brief: FR-1130 LangGraph issues census graph

Governing FR: feature-requests/FR-1130-langgraph-issues-census.md (§3, judged
APPROVED WITH REVISIONS; judgement
feature-requests/FR-1130-langgraph-issues-census.judgement.md).

**Prior art:** dispositioned in FR-1130 §5; the graph precedent is
`examples/demos/person_profile_census/graph.yaml` (FR-1120 memo wiring).
Gate hits cap-journey-census, fr-984-census-max-concurrency,
fr-1124-novel-fandom-advisory-check and fr-1125 briefs are other census
graphs' briefs, not this graph.

## Task

Create **exactly one graph file**:
`examples/demos/langgraph_issues_census/graph.yaml`. No new prompt: the judge
is the existing `examples/demos/corpus_census/prompts/judge_item.yaml`
(vars `rubric`, `content`, `source_index`; schema `CorpusCensusFinding`). Do
not edit any existing graph, prompt, Python module or shared tool.

Already present in the target directory (do not edit): `rubric.md` (passed as
`--var rubric="$(cat …)"`) and `labels.json` (passed as `--var labels=`).

Python surfaces to wire (already committed, read them before wiring):

- `examples/demos/corpus_census/adapters/gh-issues-discover.tool.yaml`,
  `gh-issues-versions.tool.yaml`, `gh-issues-extract.tool.yaml` — bound as
  **slots** `discover`, `versions`, `extract` (runtime python; `discover`
  args `[source]`, `extract` args `[item]`), like
  `examples/demos/person_profile_census/graph.yaml`.
- `examples/demos/corpus_census/adapters/gh_issues_report.py` —
  `gh_issues_memo_prepare`, `gh_issues_pair`, `gh_issues_findings`,
  `gh_issues_crosstab` (each takes `state`, returns a dict of state updates:
  `memo_inputs`/`memo_query`/`executed_contents`, `paired`, `findings`,
  `crosstab`).
- `examples/demos/corpus_census/tools.py` `reduce_ledger` (unchanged; reads
  `items`, `findings`, `labels`, `model`, `output_path`; returns the ledger
  dict with `markdown_path`, `jsonl_path`, `rows`).
- Shared memo: `examples/shared/map_memo_split.tool.yaml`,
  `examples/shared/map_memo_merge.tool.yaml` via `manifest:`.

Python tool `path:` is confined to the graph root; reach the corpus_census
modules without violating that (e.g. `module:` import paths or manifests) and
record the choice in the report.

### Contract (FR-1130 §3)

- **vars / state:** `source`, `rubric`, `labels`, `provider`, `model`,
  `output_path`, `results_dir`, `fixture_path`, `memo_store` (required —
  `gh_issues_memo_prepare` raises without it), plus the internal keys
  `memo_inputs`, `memo_query`, `items`, `versions`, `memo`,
  `executed_contents` / `executed_findings` (list, `reducer: sorted_add`),
  `paired`, `merged`, `findings`, `ledger`, `crosstab`.
- **nodes, in order:** `memo_prepare` → `discover` → `versions` (`tool_call`,
  `args: state: "{state.memo_query}"`) → `memo_split` (`tool_call`
  `map_memo_split`, `items`, `versions: "{state.versions.result}"`, `store`,
  `inputs: "{state.memo_inputs}"`, `signature_files` EXACTLY, in this order:
  `examples/demos/langgraph_issues_census/graph.yaml`,
  `examples/demos/corpus_census/prompts/judge_item.yaml`,
  `examples/demos/corpus_census/tools.py`,
  `examples/demos/corpus_census/adapters/gh_issues_adapters.py`,
  `examples/demos/corpus_census/adapters/gh_issues_report.py`) →
  `extract_items` (map over `{state.memo.result.todo}`, slot `extract`,
  `on_error: fail`, collect `executed_contents`) → `judge_items` (map over
  `{state.executed_contents}`, llm `judge_item`, `provider:
  "{state.provider}"`, `model: "{state.model}"`, `temperature: 0`,
  `on_error: skip`, variables `rubric`, `content:
  "{state.judged_content.value}"`, `source_index:
  "{state.judged_content._map_index}"`, collect `executed_findings`) → `pair`
  → `memo_merge` (`tool_call` `map_memo_merge`, `plan:
  "{state.memo.result}"`, `results: "{state.paired}"`, `failures: []`,
  `map_name: judge_items`, `map_dispatch:
  "{state._map_verdict.judge_items.dispatch}"`, `min_success: 0` — judge
  failures travel inside `paired` as `error` records, the person_profile
  precedent) → `findings` → `reduce_ledger` → `crosstab`. All non-map nodes
  `on_error: fail`. No brief/synthesis tail.
- **ceilings:** `max_items: 10000` on both maps; `config: max_concurrency: 8`
  and a `max_map_items` that admits 10000.
- The judge prompt must resolve from the sibling directory (corpus_census
  `prompts/`).

## Validation

- `yamlgraph graph lint examples/demos/langgraph_issues_census/graph.yaml`
- Provider-free end-to-end witness, must pass unchanged:
  `pytest tests/unit/test_fr1130_census_graph.py -q --no-cov`
  (do not edit the test).
- Live smoke (small, paid, allowed once): with `set -a; . ./.env; set +a`,
  run the graph with `--tool discover=… --tool versions=… --tool extract=…`
  bound to the three gh-issues manifests,
  `--var source="langchain-ai/langgraph@6534,7400"`,
  `--var rubric="$(cat examples/demos/langgraph_issues_census/rubric.md)"`,
  `--var labels="$(cat examples/demos/langgraph_issues_census/labels.json)"`,
  `--var provider=azure --var model="$AZURE_MODEL"`,
  `--var output_path=tmp/fr1130/author-smoke/ledger.md`,
  `--var results_dir=tmp/fr1130/author-smoke`,
  `--var fixture_path=tests/fixtures/fr1130/raw_read.json`,
  `--var memo_store=tmp/fr1130/author-smoke/memo.sqlite`, `--token-usage`,
  teeing the full output to
  `examples/demos/langgraph_issues_census/demo-output.log`. Read the two
  ledger rows; #7400 is the canary and must be `spam-invalid`.
- Also write `examples/demos/langgraph_issues_census/README.md` with the run
  command (full census = `--var source=langchain-ai/langgraph`, results in
  `examples/demos/langgraph_issues_census/results`).
