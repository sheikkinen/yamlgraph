# Authoring brief: corpus_census synthesize tail (FR-895)

**Prior art:** dispositioned in FR-895-census-synthesize-tail.md (canonical
guide reference/patterns/corpus-map-reduce.md; FR-892 corpus census; earlier
authoring briefs are process artifacts of unrelated FRs).

Extend `examples/demos/corpus_census/` with the human-readable brief tail
(FR-895, judged; scope frozen in FR-895-census-synthesize-tail.judgement.md).
Only `graph.yaml` and `prompts/` may change via this route; code helpers
already exist on this branch in `adapters/census_brief.py`.

## Required shape (append after reduce_ledger)

- New required state: `brief_path` (str), `brief_rubric` (str); plus
  `brief_input` (list), `claims` (dict), `brief` (dict).
- Node `prepare_brief_input` (python, tool in tools.py — you may add ONE
  function there): reads `{state.ledger}`'s jsonl_path, loads rows, calls
  `adapters/census_brief.build_synthesis_input(rows)` (import via
  examples.demos.corpus_census.adapters.census_brief), returns
  `{"brief_input": [...]}`. Requires brief_path and brief_rubric present —
  raise ValueError naming the missing variable BEFORE any synthesis call.
- Node `synthesize` (llm, **exactly one call**): prompt
  `prompts/synthesize_brief.yaml` — model pinned `claude-haiku-4-5`,
  temperature 0. Inline schema REQUIRING: `claims` = list of objects with
  claim_id (str), text (str), citations (list[str], each formatted
  `label:<label>` or `row:<item_ref>` drawn ONLY from the provided input),
  confidence (float 0-1). Variables: rubric `{state.brief_rubric}`,
  rows `{state.brief_input}`. The prompt must instruct: cite only
  provided identifiers; 3-8 claims; answer "what does this corpus say?".
- Node `render_brief` (python, ONE function in tools.py): calls
  `census_brief.emit_brief(claims, brief_input, brief_path,
  run_meta={model, prompt_version: synthesize_brief.v1, rows, source
  jsonl path})`; returns `{"brief": result}`. Do NOT fail the graph when
  the boundary rejects — the REJECTED artifact is the loud failure signal
  and `brief.accepted` carries the outcome.
- Edges: reduce_ledger → prepare_brief_input → synthesize → render_brief → END.

## Constraints

- The synthesis consumes ONLY `brief_input` (bounded, allowlisted by the
  existing helper) — never raw corpus items or the full contents list.
- Smoke: run the existing fixture flow
  (examples/demos/corpus_census/fixtures/discover.tool.yaml +
  examples/demos/corpus_census/fixtures/extract.tool.yaml,
  source=examples/demos/corpus_census/fixtures/corpus, rubric "classify
  each document's main topic in one word") ADDING --var brief_path=tmp/census-brief-smoke.md
  --var brief_rubric="What does this corpus cover overall?" and verify the
  brief file exists with a Findings section and zero validation errors.
- Also smoke the failure preflight: same command WITHOUT brief_path must
  fail loudly at prepare_brief_input, before the synthesize call.
- Lint clean; record lint + both smokes in the authoring report.

## Precedents

- examples/demos/corpus_census (this demo — FR-892 conventions),
  adapters/census_brief.py (the boundary contract), research-route
  (structured schema discipline), FR-895 judgement R-1..R-4.
