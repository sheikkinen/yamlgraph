# Authoring brief: corpus_census pipeline graph (FR-892)

Create `examples/demos/corpus_census/` — the shared discover–extract–map–
reduce census pipeline with invocation-time tool slots (FR-892, judged;
scope frozen in FR-892-corpus-census-pipeline-injected-adapters.judgement.md).

## Required shape

- `tools:` declares TWO slots (the new FR-892 mechanism, already merged
  on this branch):
  - `discover: {slot: true, contract: {args: [source]}}` — enumerates
    corpus items; returns a list (JSON parse acceptable).
  - `extract: {slot: true, contract: {args: [item]}}` — fetches one
    item's content string.
  Slots are bound at run time via `--tool discover=... --tool extract=...`;
  the graph must NOT hardcode any corpus-specific tool.
- Pipeline nodes:
  1. `discover` (python/tool node via the discover slot) → `items` list.
  2. `extract_items`: `type: map` over `{state.items}` invoking the
     extract slot per item → `contents` (collect).
  3. `judge_items`: `type: map` over contents; sub-node `type: llm`,
     **model pinned `claude-haiku-4-5`, temperature 0, `on_error: skip`**;
     prompt `judge_item` with an inline schema REQUIRING these fields:
     judgement (str), confidence (float 0-1), evidence_span (str),
     abstained (bool), abstain_reason (str, empty when not abstained).
     The rubric text arrives as graph variable `{state.rubric}`.
  4. `reduce_ledger`: python tool (LLM-FREE, in the demo's tools.py):
     validates every finding and writes the frozen ledger artifact —
     markdown table + JSONL sibling to `{state.output_path}`; columns:
     item_ref, judgement, confidence, evidence_span, model,
     prompt_version, abstained+abstain_reason, disagreement flag.
     FAIL CLOSED (raise) on: empty required cell, judgement that is an
     error string ("Error:", "No results"), abstention rows dropped.
     Abstentions become ledger rows, never omissions.
  5. Optional `synthesize` tail: SKIPPED in v1 (out of scope creep).
- State: source (str), rubric (str), output_path (str), items (list),
  contents (list, sorted_add), findings (list, sorted_add), ledger (dict).
- `config: {max_map_items: 200}`.

## Constraints

- Cheap-map discipline: every LLM node pins model + temperature explicitly.
- The reducer is deterministic code — no LLM anywhere in reduce.
- Smoke test: bind fixture manifests (create under the demo, e.g.
  `fixtures/` with a discover manifest `ls {source}`-style over a tiny
  committed folder of 3 text files and a `cat {item}`-style extract
  manifest) and run the graph end-to-end with a trivial rubric
  ("classify each document's main topic in one word"); verify the ledger
  artifact exists with one row per item.
- Lint clean; record lint + smoke in the authoring report.

## Precedents to honor

- examples/demos/prompt_theme_analyzer (map fan-out + deterministic
  aggregation), examples/demos/research-route (fail-closed reducer,
  FR-890 R-3/R-4), FR-768 manifests, FR-892 slot binding
  (yamlgraph/tools/tool_slots.py — already on this branch).

**Prior art:** dispositioned in FR-892 (authoring brief per FR-767 route; sibling briefs fr-866/875/880 are unrelated corpora — noun matches only).
