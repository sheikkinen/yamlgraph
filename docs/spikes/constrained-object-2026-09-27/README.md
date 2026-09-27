# Spike: unconstrained objects under Anthropic constrained decoding

**Date:** 2026-09-27
**Trigger:** `sheikkinen/yamlgraph-daily-digest` run 36335550129, the first
production run on yamlgraph 0.6.1 after FR-1121 and FR-1122: thirteen
articles analysed, `rank_stories` completed successfully, and the ranker
returned zero stories (`InvalidRankedStoriesError: ranker returned 0 item(s)`).
FR-1121 had retyped the ranker's result from `list[Any]` to `list[dict]` on
the evidence that the Anthropic SDK's schema transform no longer raised.
**Status:** research record. No FR is drafted from it yet; the findings below
are the constraints any FR must satisfy.

## Question

What does Anthropic constrained decoding (`with_structured_output(method="json_schema")`,
the method FR-998 forces for every Anthropic `llm` node) do with a field the
prompt schema types as an unconstrained object (`dict`, `list[dict]`,
`dict[str, Any]`)? Is that why the ranker answered `[]`? Which declared form
carries a story through, and is the hollowing a client-library choice or an
API constraint?

## Method

`probe_constrained_object.py`, run once on 2026-09-27 (`probe-output.txt`, `results.json`):

- The digest's real ranker prompt (`prompts/rank_stories.yaml` as merged in
  digest #5), rendered with three analysed articles.
- Four schema forms: **A** `fields` form `stories: list[dict]` (production
  today); **B** `stories: list[Any]` (production before FR-1121); **C** the
  FR-1054 `output_schema` form with declared item properties; **D** a bare
  `dict` field.
- Two binding methods through the same libraries the digest uses:
  `json_schema` (langchain-anthropic → `anthropic.transform_schema` →
  `output_config.format`) and `function_calling` (forced tool call, the
  pre-FR-998 path).
- Model: `claude-haiku-4-5`, the default `create_llm` resolves for
  `provider: anthropic` with no model named, exactly as the digest workflow.
- Recorded per run: the wire schema for the `stories` field, the raw
  content or tool call, the parsed value, the parsing error.
- One extra call to the raw Anthropic API with the SDK transform bypassed.

## Results

| Form | `json_schema` wire schema for `stories.items` / `stories` | `json_schema` result | `function_calling` result |
|---|---|---|---|
| A `list[dict]` | `{type: object, properties: {}, additionalProperties: false}` | `{"stories": []}` — twice out of two | 3 stories, all fields |
| B `list[Any]` | transform raises `Schema must have a 'type'…` | call never made (the FR-1121 incident) | 3 stories, all fields |
| C `output_schema` nested | `$ref` to a `$defs` entry with `title, url, summary, relevance, reason`, `required` all five, `additionalProperties: false` | 3 stories, all fields | 3 stories, all fields |
| D `dict` | `{type: object, properties: {}, additionalProperties: false}` | `{"stories": {}}` | populated map |

Raw API, SDK transform bypassed, `items: {type: object, additionalProperties: true}`:

```
400 invalid_request_error: output_config.format.schema: For 'object' type,
'additionalProperties: true' is not supported. Please set 'additionalProperties' to false
```

## Findings

- **F1. The hollowing is the API's rule, not a library bug.** Anthropic
  constrained decoding refuses `additionalProperties: true`. The SDK's
  `transform_schema` is what makes an unconstrained object sendable at all,
  and the only way it can is `properties: {}` plus `additionalProperties:
  false`: a grammar in which the only object is `{}`. The model then does
  the only sane thing, returns an empty list or an empty object, and the
  call succeeds. No client-side change can keep `dict` semantics under
  `json_schema`.
- **F2. This is why the digest ranked nothing.** Form A reproduces run
  36335550129 exactly, twice out of two, on the digest's own prompt and
  model. It is deterministic in the schema, not a model mood.
- **F3. It is the same defect class as the FR-1121 incident, one step
  later.** `list[Any]` failed loudly at bind time (FR-998's transform
  raises). `list[dict]` fails silently at answer time. FR-1123's gate and
  parity test, and FR-1121's own witness, checked "does the transform
  raise?" and so approved the second form. `plausible_wrong_answer`: the
  output passes the shape check and is semantically empty.
- **F4. `function_calling` never had this problem.** Under a forced tool
  call the wire schema keeps `additionalProperties: true` and the model
  fills every form, A, B and D included. FR-998 traded that for
  constrained decoding to fix the `list[str]`-as-string lie; the trade
  silently hollowed every unconstrained-object field on Anthropic from
  0.5.25 on.
- **F5. The typed form exists and works.** FR-1054's `output_schema` with
  declared item `properties` survives the transform intact (`$defs`,
  properties, `required`) and fills under both methods. The `fields` form
  has no way to express it (`resolve_type` accepts only `list[T]` with
  scalar or `dict` `T`).
- **F6. The affected surface on `main` today is 32 field declarations in
  26 prompt files** typed `dict` or `list[dict]` (`git grep` on
  2026-09-27 after #728). Nine of them were retyped to `list[dict]` by
  FR-1123 this afternoon; the rest have been unconstrained objects since
  before FR-998 and are hollow on Anthropic since 0.5.25 wherever the
  graph runs on that provider. Which of them actually run on Anthropic
  (versus inception, deepseek, mistral defaults) is not established here.

## Implications for any fix (constraints, not a proposal)

1. Under `json_schema`, an object with no declared `properties` is not a
   representable shape. The framework must treat `dict`, `list[dict]` and
   `dict[str, Any]` on an Anthropic-bound node as either (a) a refusal at
   lint and bind time, like FR-1123 does for `Any`, with a message naming
   the field and pointing at `output_schema` properties, or (b) an explicit
   per-field fallback to `function_calling` for that node, which is a policy
   decision FR-998 currently forbids. (a) is loud and consistent; (b)
   preserves the "keys genuinely unknown" use the reference documents.
2. Any gate or parity test must compare the **transformed** schema's
   information content against the declared one (properties preserved,
   `additionalProperties` semantics), not merely whether the transform
   raises. A schema that survives with `properties: {}` where the author
   declared an object with unknown keys has lost information and must be
   reported.
3. The digest's ranker prompt, and the nine FR-1123 retypes, need declared
   item properties (`output_schema` form) or a documented reason to stay
   unconstrained under a different method. For the digest the five story
   fields are already named in the prompt text; declaring them is the
   whole change.
4. FR-1121's C-7 ("`list[dict]` is the full schema change authorized")
   and FR-1123's migration target were decided on the "does not raise"
   witness. Both need a deviation record citing this spike; neither is
   re-opened here.

## Files

- `probe_constrained_object.py` — the runs above, reproducible with an `ANTHROPIC_API_KEY`.
- `probe-output.txt` — the console record of the run.
- `results.json` — wire schemas, raw content, parsed values, usage, per run.
