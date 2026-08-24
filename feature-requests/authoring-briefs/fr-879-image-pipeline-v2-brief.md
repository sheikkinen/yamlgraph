# Authoring brief: FR-879 examples/image_pipeline_v2 — critic-filtered z-image pipeline

Governing FR: `feature-requests/FR-879-image-pipeline-v2-critic-filter.md`
(judged APPROVED WITH REVISIONS; R-1..R-5 folded). This brief authors
ONLY the graph and prompt artifacts; the Python nodes already exist and
are tested (`tests/unit/test_image_pipeline_v2.py`).

**Prior art:** fr-826-deviant-daily-brief (authored the deviant-daily
publish pipeline — different repo, different graph; supplies the critic
this brief consumes), fr-781-authoring-brief (file-hook demo, unrelated
shape), deviant-daily-remove-guard-flags-brief (dispatch flag removal,
unrelated), fr-787/fr-789-authoring-briefs (other pipelines; structural
precedent only). None authors a critic-filtered example; noun overlap.

## Artifacts to author

1. `examples/image_pipeline_v2/graph.yaml`
2. `examples/image_pipeline_v2/prompts/generate_candidates.yaml`

## Graph contract

Name `image-pipeline-v2`, description: critic-filtered single-provider
image pipeline (generate → score → filter → render).

Pipeline (linear):

```
START → generate_candidates (llm) → score_filter (python) →
save_report (python) → generate_images (python) → END
```

State keys:

- `style: str` (input var; default demo value "dark fantasy")
- `candidates: any` (LLM output: dict with prompts list)
- `top_k: str` (input var, default "3")
- `n_candidates: str` (input var, default "10")
- `scored: list`, `prompts: list`, `report_file: str`,
  `local_report_file: str`, `output_dir: str`, `images: list`

Tools (all `type: python`):

- `score_filter`: module `examples.image_pipeline_v2.nodes.score_filter`,
  function `score_filter_node` — scores candidates via the deviant-daily
  critic subprocess (env `DEVIANT_DAILY_DIR`), selects top-k survivors
  into `prompts`, full rows into `scored`.
- `save_report`: module `examples.image_pipeline_v2.nodes.save_report`,
  function `save_report_node` — writes sanitized + local rejection
  tables, sets `output_dir`.
- `generate_images`: module `examples.image_pipeline.nodes.generate_images`
  (v1 module reused UNMODIFIED), function `generate_images_node` —
  renders `prompts` via Replicate z-image into `output_dir`.

Node wiring: `generate_candidates` → state_key `candidates`;
`score_filter` requires `candidates`, `save_report` requires `scored`,
`generate_images` requires `prompts` and runs after `save_report` (it
needs `output_dir`).

## Hard constraints (judgement gates)

- NO `provider:` or `model:` key anywhere: not in nodes, not in
  `defaults:`, not in the prompt YAML. Provider resolves from the
  runtime environment (`.env` `PROVIDER`) — AC-06.
- The prompt `generate_candidates.yaml` MUST declare an inline schema
  named `CandidatePrompts` with field
  `prompts: {type: list[str], description: exactly n_candidates
  standalone image-generation prompts}` — AC-07.
- Prompt content: system = expert image-prompt writer; user template
  takes `{style}` and `{n_candidates}`; each prompt must be a complete
  standalone image prompt of 100–800 characters (the critic boundary
  window), varied subjects, no numbering or commentary — return only
  the structured output.
- Do not touch anything under `examples/image_pipeline/` (v1) — AC-15.

## Validation

- `yamlgraph graph lint examples/image_pipeline_v2/graph.yaml` must pass.
- Smoke: `yamlgraph graph run examples/image_pipeline_v2/graph.yaml
  --var style="dark fantasy" --var n_candidates="3" --var top_k="1"`
  is expected to FAIL at `score_filter` unless `DEVIANT_DAILY_DIR` is
  set — a run reaching score_filter's fail-fast message counts as a
  passing smoke for graph wiring (record it honestly as such). If
  `DEVIANT_DAILY_DIR` is set in the environment, the full path may
  execute; do NOT set `REPLICATE_API_TOKEN` handling yourself.

## Precedent

- `examples/image_pipeline/graph.yaml` (v1: llm→map→python chain,
  tools block, prompts_relative) — closest structural precedent.
- `examples/style_convert/` (python-tool reuse across example dirs).
