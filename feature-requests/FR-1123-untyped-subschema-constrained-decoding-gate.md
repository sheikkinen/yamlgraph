# Feature Request: Refuse untyped prompt-schema fields before constrained decoding

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-27
**First consumer / first event:** `yamlgraph graph lint
examples/daily_digest/graph.yaml`, at the moment the linter reads the
`rank_stories` prompt schema and finds `stories: list[Any]`; today it
says nothing, and the first Anthropic call raises after the map stage
has spent its tokens. Second consumer: `create_llm_node` at compile time
for any Anthropic-bound `llm` node whose output model carries an untyped
subschema, so `graph run` refuses before the first node runs. Third:
the nine committed prompt files in `examples/` that declare `Any` or
`list[Any]` fields and are latent call-time failures on the default
provider.
**Research:** [FR-1123.research.md](FR-1123.research.md)
**Prior art:** [FR-998](FR-998-anthropic-constrained-structured-output.md)
introduced the constrained binder and deliberately narrowed its second
attempt to the unsupported-`output_config` 400; this FR adds no
fallback and changes no policy in that module's invocation path; it
refuses earlier, with a better message, what the SDK already refuses at
call time. [FR-458](FR-458-openai-strict-schema-additional-properties.md)
and [FR-456](FR-456-structured-output-json-fallback.md) handle OpenAI
strict-schema rejections *after* the provider answers; this FR handles
an Anthropic rejection that is raised client-side before any request
and is therefore knowable at compile time. [FR-632](FR-632-pydantic-tojson-boundary.md)
is the boundary doctrine this FR applies to a schema entering a
provider. FR-025 created the linter's prompt checks (E013, E014, W023,
W026); none inspects field types, and this FR adds one that does.
[FR-1121](FR-1121-daily-digest-ranker-schema-loud-failure.md) fixes the
one consumer that failed in production and is independent of this FR.
[FR-1097](FR-1097-graph-run-completed-errors-exit-3.md) made recorded
errors change the exit status; this FR makes this error class never
reach the run.

## Summary

`build_pydantic_model` accepts `Any`, `list[Any]` and produces JSON
schemas with an empty subschema at that position. Since FR-998,
Anthropic-bound nodes send that schema through the SDK's strict
transform, which raises `Schema must have a 'type', 'anyOf', 'oneOf',
or 'allOf' field.` at invocation, naming neither prompt nor field. The
framework passes such prompts through `lint`, `validate` and compile.
This FR adds a linter check and a compile-time refusal that name the
prompt and the JSON path, retypes the committed examples that would
trip it, and adds a parity test so the framework's rule cannot drift
from the SDK's.

## Value Statement

A graph author who types a field `Any` on an Anthropic graph learns it
from `lint` in a second, with the field named, instead of from an
unattended run's log after the upstream nodes have paid for nothing.

## Problem

Verified offline on 2026-09-27 (anthropic SDK 1.3.0, yamlgraph main):

| Field type | JSON schema at the field | SDK transform |
|---|---|---|
| `Any` | `{"description": ..., "title": ...}` (no `type`) | raises |
| `list[Any]` | `items: {}` | raises |
| `dict` / `dict[str, Any]` | `{"type": "object", "additionalProperties": true}` | passes |
| `list[dict]` | `items: {"type": "object", "additionalProperties": true}` | passes |
| `list[str]` | `items: {"type": "string"}` | passes |

Committed prompt files that fail the transform today:

| File | Fields |
|---|---|
| `examples/daily_digest/prompts/rank_stories.yaml` | `stories: list[Any]` (FR-1121 retypes it) |
| `examples/book_translator/prompts/extract_terms.yaml` | `list[Any]` |
| `examples/book_translator/prompts/identify_chapters.yaml` | `list[Any]` |
| `examples/book_translator/prompts/translate_chunk.yaml` | `list[Any]` |
| `examples/yamlgraph_gen/prompts/generate_tools.yaml` | `list[Any]` |
| `examples/yamlgraph_gen/prompts/assemble_graph.yaml` | 1 × `Any` |
| `examples/yamlgraph_gen/prompts/generate_prompts.yaml` | 1 × `Any` |
| `examples/codegen/prompts/plan_discovery.yaml` | 1 × `Any` |
| `examples/codegen/prompts/synthesize.yaml` | 4 × `Any` |

Twelve fields in nine files. Each is accepted by `resolve_type`
(`TYPE_MAP["Any"]`), built into a model at node-factory time
(`get_output_model_for_node` in `create_llm_node`), bound with
`method="json_schema"` when the provider is Anthropic, and rejected by
`transform_schema` on the first invoke. The rejection message is the
SDK's, with no prompt name and no field path. The only committed
witness of the class is the digest outage.

## Ideal Result

The rule "a subschema must carry `type`, `anyOf`, `oneOf`, `allOf` or
`$ref`" lives in one place in the framework, is checked at the two
boundaries where the schema enters (lint, and compile for an
Anthropic-bound node), names the prompt and JSON path when it fires,
and is proven equal to the SDK's transform by a parity test over a
fixture set. No committed prompt in this repository trips it. Providers
that accept empty subschemas keep accepting them; the compile-time
refusal fires only where constrained decoding will.

## Proposed Solution

### S-1: One rule, one function

`yamlgraph/utils/structured_output.py` gains

```python
class UnconstrainableSchemaError(ValueError):
    """A prompt schema carries a subschema constrained decoding cannot express."""

def find_untyped_subschemas(schema: dict) -> list[str]:
    """JSON paths of subschemas lacking type/anyOf/oneOf/allOf/$ref."""
```

The walker follows `properties`, `items`, `prefixItems`, `anyOf`,
`oneOf`, `allOf`, `$defs` and `additionalProperties` when it is a dict.
It mirrors the SDK's `transform_schema` branch verbatim and nothing
else; the parity test (S-4) is what keeps it honest. The module stays
under its size ceiling; if it does not, the walker moves to
`yamlgraph/utils/schema_walk.py`.

### S-2: Compile-time refusal for Anthropic-bound nodes

In `bind_structured_output`, when the resolved method is
`CONSTRAINED_METHOD`, call the walker on `output_model.model_json_schema()`
and raise `UnconstrainableSchemaError` naming the model and every
path before touching `with_structured_output`. Because
`create_llm_node` builds the output model at factory time and the
provider is known there, `create_llm_node` performs the same check when
`is_anthropic_chat_model` would be true for its provider, so
`graph run` and `compile_graph` fail before the first node executes.
The message:

```
Prompt 'rank_stories' (RankedStories): field 'stories.items' has no
type; Anthropic constrained decoding rejects untyped subschemas.
Declare a concrete type (e.g. list[dict], list[str]) or a nested schema.
```

Providers other than Anthropic are untouched: the binder's non-Anthropic
branch does not call the walker. No method downgrade, no second attempt.

### S-3: Linter check E015

`yamlgraph/linter/checks_prompts.py` gains E015: for every `llm` node
whose resolved provider is Anthropic (node, then `defaults.provider`,
then the environment default the linter already resolves for W-series
provider checks), build the prompt's output model and run the walker;
one diagnostic per untyped path, with the fix text above. When the
provider cannot be resolved statically, the check is a W-series warning
with the same text, so an author on any provider still sees it.

### S-4: Witnesses

- RED: `tests/unit/test_fr1123_untyped_subschema.py` builds each of the
  five type rows above through `build_pydantic_model`, asserts
  `find_untyped_subschemas` returns exactly the failing paths, and
  asserts `bind_structured_output` on a stub Anthropic model raises
  `UnconstrainableSchemaError` naming `stories.items`.
- Parity: the same fixtures, plus every committed prompt schema under
  `examples/`, `graphs/` and `.github/`, are run through both the walker
  and `anthropic.lib._parse._transform.transform_schema`; the sets of
  raising schemas must be equal. This is the only place the private SDK
  module is imported, marked `slow` and skipped when the SDK is absent.
- Linter: a fixture graph on Anthropic with a `list[Any]` prompt gets
  E015 at the right path; the same graph on `provider: mistral` gets the
  W-series form; a `list[dict]` prompt gets nothing.
- After S-5, a test asserts no committed prompt schema trips the walker.

### S-5: Retype the committed prompts

Every file in the Problem table is authored through `scripts/author.sh`
with a committed brief per example directory. The default retype is
`list[Any]` → `list[dict]` and `Any` → `dict` or `str` as the prompt's
own description states; where a description gives no shape, the brief
says so and the judge decides between a typed default and a documented
exception. The digest example is retyped by FR-1121 first; if FR-1123
lands first it retypes it and FR-1121 records that.

### Not in scope

- A nested `fields:` grammar in `schema_loader` (`list[Model]`): its
  own FR; this FR only closes the empty-subschema hole.
- Changing FR-998's second-attempt policy or adding any fallback.
- OpenAI strict-mode rules (FR-458 owns them).
- The framework default `on_error` for `llm` nodes: filed as
  [FR-1124](FR-1124-llm-node-default-on-error.md).

## Acceptance Criteria

- [ ] AC-1: `find_untyped_subschemas` returns `["stories.items"]` for
  the digest schema and `[]` for `list[dict]`, `dict`, `list[str]`; RED
  commit precedes GREEN.
- [ ] AC-2: `bind_structured_output` on an Anthropic chat model with an
  untyped subschema raises `UnconstrainableSchemaError` before calling
  `with_structured_output`; on a non-Anthropic model it does not call
  the walker (spy assertion).
- [ ] AC-3: `compile_graph` on a fixture Anthropic graph with a
  `list[Any]` prompt raises the same error naming node, prompt and path;
  `graph run` exits non-zero with the message on stderr and no node
  executes.
- [ ] AC-4: parity test passes over the fixtures and every committed
  prompt schema; it imports the SDK's transform in exactly one place.
- [ ] AC-5: E015 fires for the Anthropic fixture, the W form fires for
  an unresolved or non-Anthropic provider, nothing fires for typed
  schemas; `reference/graph-yaml.md` or the linter reference documents
  the code.
- [ ] AC-6: all nine files in the Problem table are retyped or
  dispositioned with a committed brief and adapter report each;
  `yamlgraph graph lint` is E015-clean repo-wide.
- [ ] AC-7: `structured_output.py` stays under 400 lines or the walker
  is split out; `lint-imports` passes.
- [ ] AC-8: new tests carry a REQ ID (FR-998's REQ, or a new one via the
  FR-975/FR-980 reservation route); `python scripts/req_coverage.py
  --strict` passes; changelog fragment; FR implementation record;
  Distill diary entry with a `**Seed:**`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Fall back to `function_calling` when the transform raises | Rejected. Silent downgrade hides the untyped field; FR-998 chose the narrow second attempt on purpose. |
| Refuse `Any` in `resolve_type` / `TYPE_MAP` outright | Rejected. Provider-agnostic loader; Mistral and non-strict OpenAI accept empty subschemas today, and `Any` in non-LLM contexts (tool arg schemas) is legitimate. |
| Import the SDK's `transform_schema` as the production check | Rejected. Private module (`anthropic.lib._parse._transform`); acceptable as a test oracle, not as a runtime dependency. |
| Auto-rewrite `Any` to `dict` at bind time | Rejected. Changes the meaning the author wrote; the author should choose the type. |
| Lint only, no compile-time refusal | Rejected. Lint is advisory unless gated in CI; the digest repository does not lint in its workflow. Compile-time refusal is the floor. |
| Compile-time refusal only, no lint | Rejected. The author's first feedback loop is `lint`; the path should be named there first. |

`is_this_a_graph`: no. This is a deterministic walk of a JSON schema at
load and compile time; no model is consulted and nothing fans out.

## Related

- `yamlgraph/utils/structured_output.py` (FR-998),
  `yamlgraph/schema_loader.py` (`TYPE_MAP`, `resolve_type`),
  `yamlgraph/node_factory/llm_nodes.py` (`get_output_model_for_node`),
  `yamlgraph/linter/checks_prompts.py`.
- `anthropic/lib/_parse/_transform.py` line 112 (SDK 1.3.0), the
  oracle.
- FR-1121 (the production incident), FR-1122 (digest map migration).
