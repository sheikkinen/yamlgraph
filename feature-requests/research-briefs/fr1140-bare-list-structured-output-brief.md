# Problem brief: structured output fails when the model returns the only list field bare

**Prior art:** FR-059 (the provider's type lie: normalize LLM output at the
schema boundary); FR-464 (structured-output fallback: JSON extraction after
a `response_format` rejection, `executor_base.attempt_structured_invoke`);
FR-998 (structured-output provider policy, `yamlgraph/utils/structured_output.py`;
constrained decoding only for Anthropic, library default for every other
provider); FR-933 (retry carries validation feedback into the next
attempt); FR-1073 (map failures are typed `MapFailure` records, `min_success`);
FR-1137 (test corpus map, the witnessing consumer).

## Problem statement

A prompt whose inline `output_schema` is an object with exactly one
required property of array type (for example `{records: [...]}`) is
bound through `with_structured_output`. Some providers answer with the
array alone — `[{...}, {...}]` — instead of `{"records": [{...}]}`. The
array content is otherwise well formed, but Pydantic validation of the
generated output model raises `Input should be an object
[type=model_type, input_type=list]`, and the node fails. Under
`on_error: skip` the branch is lost; under `on_error: retry` the call is
repeated at full token cost; the repeated call may answer the same way.

The shape mismatch is mechanical and unambiguous only in this narrow
case: the model has one field, that field is a list, and the answer is a
list. In every other shape (several fields, a non-list field, a list
answer to a multi-field model) there is no unique repair.

The question: where, if anywhere, should yamlgraph reconcile this
answer shape with the declared output model, and what must be recorded
when it does — or is prompt guidance plus retry the whole answer?

## Classification

judgement/analysis/generation

## Constraints

- Normalize at the boundary where provider output enters
  (`the_one_law`); a downstream guard in each consumer is the
  `downstream_fix` trap.
- No silent fallback (Commandment 6): any reconciliation must be visible
  in logs or metadata, and must never apply to shapes without a unique
  repair.
- One structured-output policy module exists (FR-998); every production
  structured call routes through `invoke_structured` / `ainvoke_structured`
  or the FR-464 fallback. A second policy surface is duplication.
- Provider factory only (`create_llm`); no provider-specific imports in
  node code.
- Sync and native-async paths must behave identically (FR-679, FR-998).
- Anthropic constrained decoding (`json_schema`) already prevents the
  shape; the defect is observed on providers left on the library
  default.
- TDD: the failing test reproduces the provider answer without network.

## Witnessed incidents

- 2026-09-28 FR-1137 full run: 545 map branches at the default
  provider/model (inception / mercury-2.5, `ChatOpenAI` against
  `https://api.inceptionlabs.ai/v1`, langchain-openai 1.6.2), temperature
  0. Three branches (17:46:49, 17:47:09, 17:47:33) failed with
  `1 validation error for ClassifyTestsOutput — Input should be an object
  [type=model_type, input_value=[{'nodeid': 'tests/integr...t_type':
  'integration'}], input_type=list]`. The truncated input values show
  records with the expected keys. All other 542 branches answered the
  object shape.
- The consumer's schema: `output_schema: {type: object, properties:
  {records: {type: array, items: {...}}}, required: [records]}` in
  `examples/demos/test_map/prompts/classify_tests.yaml`.
- The FR-1137 consumer now retries twice with validation feedback and
  tolerates up to 5% failed partitions; the core question is independent
  of that consumer-side tolerance.
