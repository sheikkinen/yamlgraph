# Task brief: FR-1034 independent model selection for the census brief

**Governing FR:** `feature-requests/FR-1034-census-brief-model-selection.md`
(Approved with revisions; all three folded. Judgement:
`feature-requests/FR-1034-census-brief-model-selection.judgement.md`.)

**Target directory:** `examples/demos/corpus_census/`
**Artifact to modify:** `graph.yaml` (state block, tools block, one node's
provider/model fields, one new node, one edge rewire).

## Why

`judge_items` and `synthesize` both read `{state.provider}` / `{state.model}`
(`graph.yaml:95-96` and `:119-120`), so a cheap model chosen for the many
small per-item calls is forced onto the single long synthesis call. Measured
2026-09-09: 150 files classified on `mercury-2.5` for ~$0.04, then the
synthesis returned `429 output token limit exceeded` and the brief was lost.

## Required changes to graph.yaml

1. **State block** — add two optional input fields and one output field:
   - `brief_provider: str`
   - `brief_model: str`
   - `brief_llm: dict`

   Omitted inputs are valid because the generated state TypedDict is
   `total=False` (`yamlgraph/models/state_builder.py:174-213`).

2. **Tools block** — add a python tool declaration:

   ```yaml
   resolve_brief_llm:
     type: python
     path: brief_model_selection.py
     function: resolve_brief_llm
     description: "Resolve the effective provider/model for the synthesis call."
   ```

   The module is new and lives beside the graph. It must NOT go in `tools.py`,
   which is already exactly 450 lines — the repository's hard module maximum.

3. **New node**, placed between `prepare_brief_input` and `synthesize`:

   ```yaml
   resolve_brief_llm:
     type: python
     tool: resolve_brief_llm
     state_key: brief_llm
   ```

4. **`synthesize` node** — change only its two selection fields:
   - `provider: "{state.brief_llm.provider}"`
   - `model: "{state.brief_llm.model}"`

   Dotted access into a dict-valued state key is existing behaviour:
   `judge_items` already reads `{state.judged_content.value}` and
   `{state.judged_content._map_index}` (`graph.yaml:100-101`).

5. **Edges** — rewire `prepare_brief_input -> resolve_brief_llm -> synthesize`,
   replacing the direct `prepare_brief_input -> synthesize` edge.

## Explicitly out of scope

`judge_items` and every other node's provider/model; the reducer; the ledger
schema; the citation boundary; `census_brief.py`; prompts; new CLI flags; retry
or fallback logic on provider errors; the corpus adapters. Non-graph
deliverables (the new module, `render_brief` provenance, tests, documentation
corrections, registry wiring) are implemented outside this authoring run.

## Acceptance for this authoring run

`yamlgraph graph lint examples/demos/corpus_census/graph.yaml` passes, and the
graph still compiles with the existing eight nodes plus the new one.
