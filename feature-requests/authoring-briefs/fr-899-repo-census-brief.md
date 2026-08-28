# Authoring brief: FR-899 repo_census graph (org repository census, pinned Azure)

**Governing FR:** feature-requests/FR-899-org-repo-census-azure.md (judged; scope frozen)
**Prior art:** fr-892-corpus-census-brief.md / fr-895-synthesize-tail-brief.md / fr-896-pattern-model-census-brief.md — briefs for the base pipeline, brief tail, and sibling census this graph deliberately mirrors (reuse, not overlap); fr-789-authoring-brief.md and deviant-daily-remove-guard-flags-brief.md — unrelated surfaces, noun-collision only.
**Target directory:** examples/demos/repo_census/
**Artifacts to author:** `graph.yaml`, `prompts/judge_repo_purpose.yaml`, `prompts/synthesize_repo_brief.yaml`, `README.md`

## Task

Author a sibling of `examples/demos/corpus_census/graph.yaml` for a GitHub
organization repository census. Structural precedent: corpus_census (FR-892
slots + FR-895 synthesize tail) and pattern_model_census (sibling-census
precedent). Python tools already exist — do NOT author Python:
`examples/demos/repo_census/tools.py` provides `preflight`,
`reduce_repo_ledger`, `prepare_brief_input`, `render_brief`; gh slot
adapters live in `examples/demos/corpus_census/adapters/`
(`gh-org-discover.tool.yaml`, `gh-repo-extract.tool.yaml`).

## Graph contract (frozen by FR-899 judgement)

- `defaults: {provider: azure, temperature: 0.0}`. EVERY LLM node carries
  explicit `provider: azure` and NO `model:` key (deployment comes from
  `AZURE_MODEL` env) and NO `fallback_provider`. This is a compliance
  boundary, not a preference.
- Nodes and edge order (exact):
  `START → preflight → discover → extract_items → judge_items →
  reduce_ledger → prepare_brief_input → synthesize → render_brief → END`
- `preflight`: type python, tool bound to `tools.py:preflight`,
  state_key `preflight_ok`, `on_error: fail`. MUST be the first node —
  it blocks gh discovery of corp data when Azure pinning is unconfigured.
- `discover` / `extract` are FR-892 tool SLOTS (`slot: true`, contracts
  `args: [source]` / `args: [item]`), bound at invocation time.
- `extract_items`: map over `{state.items}` as `item`, python slot sub-node,
  `on_error: fail`, collect `contents`, max_items 200.
- `judge_items`: map over `{state.contents}` as `judged_content`, LLM
  sub-node prompt `judge_repo_purpose`, `provider: azure`,
  `temperature: 0`, `on_error: skip`, state_key `finding`, collect
  `findings`, variables `rubric: "{state.rubric}"`,
  `content: "{state.judged_content.value}"`,
  `source_index: "{state.judged_content._map_index}"`.
- `reduce_ledger` / `prepare_brief_input` / `render_brief`: python nodes
  bound to the matching `tools.py` functions (state_keys `ledger`,
  `brief_input`, `brief`).
- `synthesize`: LLM node, prompt `synthesize_repo_brief`, `provider: azure`,
  state_key `claims`, variables `rubric: "{state.brief_rubric}"`,
  `rows: "{state.brief_input}"`.
- State keys: `source`, `rubric`, `output_path`, `brief_path`,
  `brief_rubric`, `activity_window_days: str`, `preflight_ok`, `items:
  list`, `contents: list (sorted_add)`, `findings: list (sorted_add)`,
  `ledger: dict`, `brief_input: list`, `claims: dict`, `brief: dict`.

## Prompt contracts (one judgement each)

- `judge_repo_purpose.yaml`: model receives rubric + one JSON evidence
  bundle (name, description, readme head). ONE judgement: `purpose` — a
  single sentence stating what the repository does and for whom. Schema
  fields: `source_index` (int, echo of supplied index), `purpose` (str),
  `evidence_span` (str, short exact span from the bundle). FORBIDDEN: the
  prompt must NOT mention or request repository activity, liveness,
  contributor/person analysis, counting, or percentages — those are
  code-owned (judgement C-4). Do not use those words in the prompt at all.
- `synthesize_repo_brief.yaml`: mirror `corpus_census/prompts/synthesize_brief.yaml`
  claims contract (claim_id, text, citations `row:<item_ref>` or
  `label:<label>`, confidence); the rubric asks what the organization's
  repository portfolio covers.

## README.md

Short: purpose, invocation (below), note that `AZURE_MODEL` governs the
deployment and the preflight blocks unconfigured runs. Demo org is pinned
to the public org `sheikkinen`; corp orgs are runtime `--var` input only
and their outputs are never committed.

## Validation (required)

- `yamlgraph graph lint examples/demos/repo_census/graph.yaml`
- Smoke (real run, public org, 2 repos — requires `.env` Azure keys + gh auth):

```bash
yamlgraph graph run examples/demos/repo_census/graph.yaml --tool discover=examples/demos/corpus_census/adapters/gh-org-discover.tool.yaml --tool extract=examples/demos/corpus_census/adapters/gh-repo-extract.tool.yaml --var source="sheikkinen:2" --var rubric="State this repository's purpose in one sentence: what it does and for whom." --var output_path=tmp/repo-census-smoke.md --var brief_path=tmp/repo-census-smoke-brief.md --var brief_rubric="Summarize this organization's repository portfolio." --full
```
