# Feature Request: Refuse untyped prompt-schema fields before constrained decoding

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS; R-1..R-6 folded 2026-09-27 ([judgement](FR-1123-untyped-subschema-constrained-decoding-gate.judgement.md)); implemented 2026-09-27 (see Implementation Record)
**REQ:** REQ-YG-712 (new, CAP-164)
**Effort:** 1.5 days
**Requested:** 2026-09-27
**First consumer / first event:** `yamlgraph graph lint
examples/daily_digest/graph.yaml`, at the moment the linter reads the
`rank_stories` prompt schema and finds `stories: list[Any]`; today it
says nothing, and the first Anthropic call raises after the map stage
has spent its tokens. Second consumer: `create_node_function` (reached
from `_compile_llm_node`) at compile time for any statically
Anthropic-bound `llm` node whose output model carries an untyped
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
[FR-1086](FR-1086-lint-compile-check.md) and its judgement (R-3) hold
active authority over lint code `E015`; this FR therefore uses `E016`
(error) and `W028` (warning) and claims no code FR-1086 owns.
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
(`get_output_model_for_node` in `resolve_llm_node_config`), bound with
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

### S-0: One pure provider resolver (judgement R-1)

`resolve_static_provider(node_provider, default_provider)` in
`yamlgraph/utils/llm_factory.py`: precedence node provider, graph
`defaults.provider`, `PROVIDER`, built-in `"anthropic"`. A
`{state.x}` reference returns `None` (unresolved until execution).
`create_llm` uses the same helper for its own selection, so compile,
lint and runtime cannot disagree.

### S-2: Compile-time and runtime refusal for Anthropic-bound nodes (judgement R-2)

Runtime: `bind_structured_output` validates only when the actual model
is Anthropic (`is_anthropic_chat_model`) **and** the effective method is
`json_schema`. It calls the walker on `output_model.model_json_schema()`
and raises `UnconstrainableSchemaError` naming the model and every path
before touching `with_structured_output`. Non-Anthropic models and an
explicit `function_calling` override never call the walker.

Compile: `_compile_llm_node` → `create_node_function` →
`resolve_llm_node_config` builds the output model. When
`resolve_static_provider` returns `"anthropic"`, the walker runs there
and the error names node, prompt, model and every path, so `graph run`
and `compile_graph` fail before the first node executes. A
state-derived provider cannot be refused at compile time; it is caught
by the binder on the actual model. The message:

```
Prompt 'rank_stories' (RankedStories): field 'stories.items' has no
type; Anthropic constrained decoding rejects untyped subschemas.
Declare a concrete type (e.g. list[dict], list[str]) or a nested schema.
```

Providers other than Anthropic are untouched: the binder's non-Anthropic
branch does not call the walker. No method downgrade, no second attempt.

### S-3: Linter checks E016 / W028 (judgement R-1)

`yamlgraph/linter/checks_prompts.py` gains one check wired through
`lint_graph`. For every `llm`/`router` node with a prompt output schema,
the provider is classified by `resolve_static_provider`:

- static `anthropic` → error `E016`, one per offending path;
- statically known non-Anthropic (Mistral, OpenAI, …) → no issue;
- unresolved (`{state.x}`) → warning `W028` per path, stating that an
  Anthropic runtime selection would reject it.

### S-4: Witnesses

- RED: `tests/unit/test_fr1123_untyped_subschema.py` builds each of the
  five type rows above through `build_pydantic_model`, asserts
  `find_untyped_subschemas` returns exactly the failing paths, and
  asserts `bind_structured_output` on a stub Anthropic model raises
  `UnconstrainableSchemaError` naming `stories.items`.
- Parity (judgement R-3): the oracle result is "`transform_schema`
  raises the missing `type`/`anyOf`/`oneOf`/`allOf` error"; it is
  compared with `bool(find_untyped_subschemas(schema))` over the
  fixtures and every committed prompt schema under `examples/`,
  `graphs/` and `.github/`. Any other SDK rejection propagates from the
  harness. The private SDK module is imported in exactly one `slow` test
  module, never in production.
- Linter: a fixture graph on Anthropic with a `list[Any]` prompt gets
  E016 at the right path; `provider: mistral` gets nothing; a
  `{state.provider}` graph gets W028; a `list[dict]` prompt gets nothing.
- After S-5, a test asserts no committed prompt schema trips the walker.

### S-5: Retype the committed prompts

Every directory FR-1123 modifies is authored through `scripts/author.sh`
with one committed brief under `feature-requests/authoring-briefs/`;
each `tmp/draft-authoring-report.md` is verified before the next run and
summarized in the implementation record, never committed (judgement
R-5). Frozen types (judgement R-4); descriptions updated to match:

| Prompt field | Required type |
|---|---|
| `daily_digest/rank_stories.stories` | `list[dict]` |
| `book_translator/extract_terms.terms` | `list[dict]` |
| `book_translator/identify_chapters.markers` | `list[dict]` |
| `book_translator/translate_chunk.difficult_passages` | `list[dict]` |
| `yamlgraph_gen/generate_tools.tools` | `list[dict]` |
| `yamlgraph_gen/assemble_graph.node_list` | `list[dict]` |
| `yamlgraph_gen/generate_prompts.prompts` | `list[dict]` |
| `codegen/plan_discovery.tasks` | `list[dict]` |
| `codegen/synthesize.target_files` | `list[dict]` |
| `codegen/synthesize.dependencies` | `list[str]` |
| `codegen/synthesize.test_coverage` | `dict` |
| `codegen/synthesize.patterns_to_follow` | `list[str]` |

If FR-1121 lands first, FR-1123 verifies the digest field and does not
rewrite it. No exception may leave an empty subschema in the census.

### Not in scope

- A nested `fields:` grammar in `schema_loader` (`list[Model]`): its
  own FR; this FR only closes the empty-subschema hole.
- Changing FR-998's second-attempt policy or adding any fallback.
- OpenAI strict-mode rules (FR-458 owns them).
- The framework default `on_error` for `llm` nodes: filed as
  [FR-1124](FR-1124-llm-node-default-on-error.md).

## Acceptance Criteria

Replaced by the judgement's revised criteria (R-6); scope frozen per the
judgement's D-1..D-8 and "Not authorized" list.

- [x] AC-01 (RED): before production implementation, the five frozen type fixtures prove exact walker results: `Any` and `list[Any]` expose their precise paths; `dict`, `list[dict]`, and `list[str]` expose none. The RED commit precedes GREEN.
- [x] AC-02: nested fixtures cover `properties`, `items`, `prefixItems`, `anyOf`, `oneOf`, `allOf`, `$defs`, dict-valued `additionalProperties`, and accepted `$ref`; assertions compare exact, deterministically ordered JSON paths.
- [x] AC-03: `bind_structured_output` raises `UnconstrainableSchemaError` before `with_structured_output` for an actual Anthropic model using effective `json_schema`; the error names model and every path. Spies prove no walker call for a non-Anthropic model or explicit `function_calling`.
- [x] AC-04: provider-resolution tests cover node override, graph default, `PROVIDER`, built-in Anthropic default, explicit known non-Anthropic, and state-derived unresolved provider; `create_llm` and compile/lint classification use the same pure resolver.
- [x] AC-05: compiling a static-Anthropic fixture fails before any node executes and names node, prompt, model, and path. A state-derived-provider fixture compiles, then the binder refuses before `with_structured_output` when the runtime model is Anthropic.
- [x] AC-06: lint emits `E016` per offending path for static Anthropic, `W028` per offending path for unresolved provider, and no issue for explicit Mistral or another known non-Anthropic provider; both checks are wired through `lint_graph`, serialized through the existing issue shape, and documented.
- [x] AC-07: the private-SDK test imports `transform_schema` in exactly one test module and proves parity only for the cited missing-keyword rejection over the frozen fixtures and every committed prompt schema under `examples/`, `graphs/`, and `.github/`; production contains no private SDK import.
- [x] AC-08: the committed prompt census contains none of the forbidden untyped paths, and all twelve fields have exactly the R-4 types and matching descriptions. If FR-1121 supplied the digest migration first, the census records that ownership without rewriting it.
- [x] AC-09: every example directory modified by FR-1123 has a cited committed authoring brief and a separately verified `tmp/draft-authoring-report.md`; the implementation record lists each adapter command, authored paths, lint result, smoke result or exact blocked reason, and repairs. Temporary reports are not committed.
- [x] AC-10: `graph run` on the static-Anthropic fixture exits nonzero with the compile error on stderr and a witness proves no graph node executed.
- [x] AC-11: `structured_output.py` remains below 400 lines or the walker is split into `schema_walk.py`; `lint-imports` passes and no production `.with_structured_output(` call is added outside the FR-998 policy module.
- [x] AC-12: tests carry the approved REQ marker; the capability/architecture record, canonical documentation, changelog fragment, FR implementation record, and Distill entry exist; targeted tests, `python scripts/req_coverage.py --strict`, and the full unit suite pass without weakened assertions.

## Implementation Record

Status: implemented (RED commit, then GREEN + migrations in one commit
because the census test interlocks with the prompt edits). All twelve
ACs pass; `tests/unit/test_fr1123_*.py` 53 passed (parity module
included, `-m slow`), full unit suite green, `req_coverage --strict`
green, `lint-imports` 3 contracts kept.

**Deviations from the judgement**

- D-2 said the shared resolver lives in `llm_factory`. The
  `linter-llm-free` import contract forbids the linter from importing
  `llm_factory`, so `resolve_static_provider` and the walker live in the
  new pure module `yamlgraph/utils/schema_walk.py`; `create_llm`,
  compile and lint all call it (AC-04 still holds: one resolver).
- Traversal mirrors SDK 1.5.0 `transform_schema` exactly (S-1, C-5):
  `prefixItems` and dict-valued `additionalProperties` are never
  validated by the SDK, so their AC-02 fixtures assert `[]`. Adding a
  rule there would break AC-07 parity.
- Lint (E016/W028) covers top-level `llm`/`router` nodes; map
  sub-nodes are covered by the compile-time refusal, which runs in
  `create_node_function` for every LLM node.
- AC-10: `graph run` prints CLI errors to stdout in text mode and to
  stderr only with `--json` (existing `graph_commands.py` convention).
  The test runs with `--json`; the CLI stream policy was not changed.
- `test_fr335` module-map budget 293 → 294 for `schema_walk.py`,
  following the per-new-module precedent recorded in that test
  (FR-892, FR-810, ...).

**Migrations (C-6, AC-09)** — each via `scripts/author.sh <brief>`,
report verified by the wrapper (headings + authored path exists), not
committed:

| Brief | Authored paths | Lint | Smoke |
|---|---|---|---|
| `authoring-briefs/fr-1123-daily-digest-typed-stories-brief.md` | `examples/daily_digest/prompts/rank_stories.yaml` | exit 0, no E016/W028 (unrelated W013/W021 left, graph out of scope) | walker `[]` |
| `authoring-briefs/fr-1123-book-translator-typed-lists-brief.md` | `extract_terms.yaml`, `identify_chapters.yaml`, `translate_chunk.yaml` | exit 0, no E016/W028 | walker all `[]` |
| `authoring-briefs/fr-1123-yamlgraph-gen-typed-fields-brief.md` | `generate_tools.yaml`, `assemble_graph.yaml`, `generate_prompts.yaml` | exit 0, no E016/W028 (unrelated warnings left) | walker all `[]` |
| `authoring-briefs/fr-1123-codegen-typed-fields-brief.md` | `plan_discovery.yaml`, `synthesize.yaml` | exit 0, no E016/W028 | walker all `[]` |

Repairs: none. Blocked validation: no live LLM smoke (not required by
the briefs; the walker is the property under test). FR-1121 had not
migrated the digest field, so FR-1123 did.

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

### Deviation recorded 2026-09-27 (FR-1125)

`list[dict]` was chosen under judgement C-7 on the witness "the Anthropic
SDK transform does not raise". The spike `docs/spikes/constrained-object-2026-09-27/`
shows that transform rewrites an object with no declared properties into
`properties: {}` + `additionalProperties: false`, so the ranker answered
`{"stories": []}` on its first run on 0.6.1 (digest run 36335550129) and
the FR-905 boundary refused it. The schema is retyped to the FR-1054
`output_schema` form with declared item properties under FR-1125; the
FR-1121 witnesses become content witnesses there. Nothing in FR-1121's
loud-failure work is reverted: the loudness is what exposed the hollow form.
