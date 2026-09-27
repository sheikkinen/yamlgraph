# Problem brief: prompt schemas the framework accepts at load time and the provider refuses at call time

**Prior art:** FR-998
(`feature-requests/FR-998-anthropic-constrained-structured-output.md`,
Enforced 2026-09-18, yamlgraph 0.5.25) routes every Anthropic `llm` node
with an inline `schema:` through `json_schema` constrained decoding and
makes exactly one forced-tool-call second attempt when, and only when,
Anthropic answers a typed 400 saying the model does not support
`output_config`; every other error propagates. Its fixtures cover
`list[str]`; none covers `Any`. FR-458 and FR-456 added the OpenAI
strict-schema and JSON fallbacks, keyed on OpenAI error strings
(`invalid_json_schema`, `additionalProperties`). FR-632 is the Pydantic
boundary doctrine: normalise where external data enters. FR-025 created
the linter's prompt checks (E013, E014, W023, W026 in
`yamlgraph/linter/checks_prompts.py`); none inspects field types against
a provider's structured-output rules. FR-1097/FR-1098 made `graph run`
exit status truthful about recorded errors. No REJECTED FR was found in
this territory.

## Problem statement

`yamlgraph.schema_loader.build_pydantic_model` accepts a field typed
`Any`, `list[Any]` or `dict[str, Any]` and builds a Pydantic model whose
JSON schema carries an empty subschema (`{}`) at that position. Before
FR-998 the empty subschema reached Anthropic through forced tool calling
and was accepted. Since FR-998 the same model is bound with
`method="json_schema"`, and the Anthropic SDK's strict transform
(`anthropic/lib/_parse/_transform.py`) raises `ValueError("Schema must
have a 'type', 'anyOf', 'oneOf', or 'allOf' field.")` for any subschema
without a type. The raise happens client-side, at invocation, after
every upstream node has run and spent its tokens, and the message names
neither the prompt nor the field.

The framework therefore has a class of prompt schema that passes
`yamlgraph graph lint`, passes `graph validate`, compiles, and fails on
the first Anthropic call. Five committed prompt files in this repository
declare `list[Any]` (`examples/book_translator/prompts/extract_terms.yaml`,
`identify_chapters.yaml`, `translate_chunk.yaml`,
`examples/daily_digest/prompts/rank_stories.yaml`,
`examples/yamlgraph_gen/prompts/generate_tools.yaml`), and twenty-eight
fields across the repository's prompt YAMLs are typed bare `Any`. Each
is a latent call-time failure on the default provider. The standalone
digest repository built from the daily_digest example failed this way
for nine consecutive unattended runs.

FR-998's error policy is deliberately narrow: only the
unsupported-`output_config` 400 earns a second attempt, so this
`ValueError` propagates as designed. The question is not whether to add
a fallback; a silent downgrade to forced tool calling would hide exactly
the field the author left untyped. The question is at which boundary the
framework should refuse an untyped subschema for a provider that
constrains on it, what the refusal should say, and whether the existing
prompt files should be retyped, annotated, or left as witnesses.

## Classification

enforcement/latency-critical

## Constraints

- Normalise at the boundary where the schema enters, not where the
  provider rejects it (Scripture, `the_one_law`). The provider's
  transform is the oracle; the framework's check must agree with it, not
  approximate it with a second rule set that drifts.
- No silent fallback and no method downgrade: a schema the constrained
  decoder cannot express fails loudly with the prompt name and field
  path, before any node runs when the information exists at load time.
- The schema loader is provider-agnostic; any refusal that is specific
  to Anthropic's constrained decoding must be placed where the provider
  is known, or be phrased as a general "untyped subschema" rule that
  every provider's structured output tolerates.
- Existing behaviour for providers that accept empty subschemas must
  stay: a `list[Any]` prompt on Mistral or OpenAI's non-strict path
  still runs today, and a repo-wide retype is a judged migration, not a
  side effect.
- Every committed prompt file that a new gate would reject must be
  dispositioned in the same FR: retyped through `scripts/author.sh` with
  a committed brief, or listed with the reason it stays.
- `list[dict]` is the nearest typed shape the loader accepts today
  (`items: {type: object, additionalProperties: true}` passes the
  transform); nested generics such as `list[dict[str, Any]]` are not
  parsed by `resolve_type`. Widening the type grammar is a separate
  scope unless the research shows it is the minimal cure.
- A witness must run offline: build the model, pass its JSON schema
  through the SDK transform, assert the raise; no provider key.
- `is_this_a_graph`: no; this is a load-time or bind-time check on a
  Pydantic model, and the research should confirm there is no reason to
  route it through a graph.

## Witnessed incidents

- 2026-09-19 through 2026-09-27, `sheikkinen/yamlgraph-daily-digest`
  GitHub Actions runs: `Node rank_stories failed: Schema must have a
  'type', 'anyOf', 'oneOf', or 'allOf' field.` on every run after the
  workflow's floating `yamlgraph>=0.5.23` resolved to 0.5.25; the
  preceding map stage completed every per-article call first.
- 2026-09-27, offline reproduction on this host (anthropic SDK 1.3.0,
  yamlgraph main): `build_pydantic_model` on the digest ranker schema
  yields `properties.stories.items == {}`; `transform_schema` raises the
  quoted message. Substituting `list[dict]` yields
  `{"type": "object", "additionalProperties": true}` and passes.
  `list[dict[str, Any]]` raises `Unknown type` from `resolve_type`
  before any schema is built.
- `anthropic/lib/_parse/_transform.py` line 112 (SDK 1.3.0): the raise
  fires in the `else` branch after popping `type`, `anyOf`, `oneOf`,
  `allOf`; it is reached for `{}` and also for a bare `$ref`-less
  `{"description": ...}`.
- `yamlgraph/schema_loader.py` on main: `TYPE_MAP` includes `"Any":
  Any`; `resolve_type` accepts `list[T]` for any `T` in the map and
  `dict[K, V]` for scalar `K`, `V`; no check inspects the resulting
  JSON schema.
- `yamlgraph/utils/structured_output.py` on main (FR-998):
  `bind_structured_output` forces `method="json_schema"` for
  `is_anthropic_chat_model(llm)`; `invoke_structured` re-raises every
  error except the typed unsupported-`output_config` 400.
- 2026-09-27, `grep -rl "list\[Any\]" --include=*.yaml examples/`: five
  files; `grep -rn "type: *Any\b" --include=*.yaml .`: twenty-eight
  fields. `tests/unit/test_fr998_structured_output.py` imports `Any`
  only for type hints; no fixture declares an `Any` field.
- `yamlgraph graph lint` on the digest graph, 2026-09-27: no diagnostic
  concerns the ranker schema. Linter prompt checks E013, E014, W023 and
  W026 concern variables, templates and schema presence, not field
  types.
