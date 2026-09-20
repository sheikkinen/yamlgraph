# Feature Request: FR-1054 Nested object schemas reach the provider

**Priority:** HIGH
**Type:** Bug
**Status:** Judged APPROVED WITH REVISIONS (2026-09-20) — R-1..R-5 folded, authority active
**Effort:** 0.5 days
**Requested:** 2026-09-20
**First consumer / first event:** `examples/book_reviewer/prompts/chapter_review.yaml`
declares `criteria` as `[{name, score, justification}]` and currently
receives a list of empty objects. First event: the next `book_reviewer`
run after this lands emits scored criteria instead of `[{}, {}, {}, {}]`.
Ten other shipped prompts are in the same state (measured below).
**Research:** in-body dispositioned alternatives table (§Alternatives
Considered) plus the prior-art table below — FR-889 style, permitted by
the template in place of a separate research record.
**`is_this_a_graph`: no.** This is deterministic schema-to-Pydantic model
construction inside an existing loader function. It adds no LLM call, no
routing, no prompt artifact, and no graph artifact. There is nothing to
fan out over and no model judgement to make.
**Prior art:**
[FR-458](FR-458-openai-strict-schema-additional-properties.md) — saw this
exact `list[dict]` schema and concluded "the `list[dict]` type is valid
Python/Pydantic — the problem is OpenAI's strict mode requirement, not the
schema itself"; that conclusion is falsified here, but its provider
fallback stays as a safety net ·
[FR-466](FR-466-dungeon-master-example.md) — abandoned structured output
for an entire example (`parse_json: true`, `output_schema` demoted to
"documentation") because of this defect; this FR removes that reason ·
[FR-905](FR-905-ranked-story-boundary-validation.md) and
[FR-908](FR-908-daily-digest-slot-bound-refactor.md) — added deterministic
post-hoc validation of item shape because the schema could not carry it;
their validators remain correct and are untouched ·
[FR-904 judgement](FR-904-slot-bound-digest-collection.judgement.md) —
explicitly listed "framework-side nested schema support" as not
authorized, deferring precisely this work; this FR is that deferred work,
scoped and measured ·
[FR-795](FR-795-endpoint-probe-schema-dialect-repair.md) and
[FR-548](FR-548-dm-v2-world-codex-backstory-stage.md) — concern the
`schema:`/`fields:` dialect and `resolve_type`, which is explicitly out of
scope here (it fails loudly; this one fails silently) ·
[FR-644](FR-644-lint-inline-schema-types.md) — lints the `schema:` dialect
at lint time; complementary, no overlap.

## Summary

`build_pydantic_model_from_json_schema` reads only the first level of an
`output_schema:`. For an array of objects it reads `items.type`, maps
`"object" → dict`, and discards `items.properties` entirely. The model
sent to the provider describes an array of unconstrained objects, so the
provider returns `{}` per element — and `list[dict]` validates `[{}, {}]`
without complaint. Every nested object schema in the repository is
silently emptied.

## Value Statement

Graph authors who declare a nested output shape receive that shape,
instead of a list of empty objects and no indication that their
declaration was discarded.

## Problem

### The mechanism

[`yamlgraph/schema_loader.py:206-208`](../yamlgraph/schema_loader.py#L206-L208):

```python
items = field_def.get("items", {})
item_type = JSON_SCHEMA_TYPE_MAP.get(items.get("type", "string"), str)
field_type = list[item_type]
```

`items["type"]` is read; `items["properties"]` is never opened. With
`"object": dict` at [L173](../yamlgraph/schema_loader.py#L173), a fully
specified item schema becomes `list[dict]`, which Pydantic renders back
out as:

```json
{"type": "array", "items": {"type": "object", "additionalProperties": true}}
```

The function is not recursive. Bare nested `object` fields lose their
properties the same way.

### Why it is silent

Three layers each behave correctly in isolation:

1. The generated schema says *an array of objects, contents unspecified,
   nothing required*.
2. `{}` satisfies that schema completely. The provider, asked for an
   unspecified object, returns the cheapest conforming value.
3. `list[dict]` validates `[{}, {}]`. `{}` is a dict.

No exception, no warning, no lint error. This is
`plausible_wrong_answer`: a shape check passing on semantically empty
content. Commandment 6 — *a plausible wrong answer is harder to catch
than a crash*.

### Measured blast radius — complete inventory

Every `output_schema` in `examples/**/prompts/*.yaml` is built and its
declared nested keys compared against `model_json_schema()`. All 14 sites
in the tree, with the keys each one declares and loses:

| File | Field | Keys | Declared nested keys (all discarded) |
| --- | --- | --- | --- |
| `examples/api-discovery/prompts/synthesize.yaml` | `profile` | 11 | `auth_model`, `confidence`, `data_freshness`, `endpoints`, `languages`, `limitations`, `platform_family`, `probe_suggestion`, `sample_response`, `total_records`, `url` |
| `examples/api-discovery/steps/browser-sniff/prompts/sniff.yaml` | `api_calls` | 5 | `body_preview`, `content_type`, `method`, `status`, `url` |
| `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml` | `live_endpoints` | 4 | `body_preview`, `content_type`, `status`, `url` |
| `examples/api-discovery/steps/schema-extract/prompts/ckan.yaml` | `endpoints` | 4 | `description`, `method`, `parameters`, `path` |
| `examples/api-discovery/steps/schema-extract/prompts/openapi.yaml` | `endpoints` | 4 | `description`, `method`, `parameters`, `path` |
| `examples/api-discovery/steps/schema-extract/prompts/unsupported.yaml` | `endpoints` | 4 | `description`, `method`, `parameters`, `path` |
| `examples/beautify/prompts/analyze.yaml` | `features` | 3 | `description`, `emoji`, `title` |
| `examples/beautify/prompts/analyze.yaml` | `nodes` | 4 | `description`, `emoji`, `name`, `type` |
| `examples/book_reviewer/prompts/chapter_review.yaml` | `criteria` | 3 | `justification`, `name`, `score` |
| `examples/demos/session-shapes/prompts/classify_session_shape.yaml` | `shape_mix` | 2 | `fraction`, `shape` |
| `examples/npc/prompts/npc_behavior.yaml` | `triggers` | 2 | `condition`, `reaction` |
| `examples/ocr_cleanup/prompts/cleanup_page.yaml` | `paragraphs` | 3 | `ends_mid_sentence`, `starts_mid_sentence`, `text` |
| `examples/ocr_cleanup/prompts/cleanup_page.yaml` | `corrections` | 3 | `corrected`, `original`, `type` |
| `examples/ocr_cleanup/prompts/cleanup_page.yaml` | `manual_review` | 3 | `location`, `reason`, `text` |

**14 sites, 11 files, 55 declared keys, zero survivors.** One site
(`profile`) is a bare nested object; the other 13 are arrays of objects.
Maximum declared depth is two. No site partially survives — the loss is
total and uniform, which is what a discarded branch looks like rather
than a provider or model effect.

This inventory becomes a committed test under AC-07, so the table cannot
drift from the tree. Reproduce with
`pytest tests/unit/test_fr1054_nested_object_schemas.py -q --no-cov`.

### Supporting context (not an enforcement gate)

A downstream consumer outside this repository
(`yamlgraph-yt-summarizer`) archived per-chunk map output across 11
transcript chunks and observed 155 items returned for `array`-of-`string`
fields with zero empties, against 30 items for `array`-of-`object` fields
with 30 empties. No artifact from that repository is cited as evidence
here and none is required: the in-tree inventory above is the closed
evidence for this FR. The observation is recorded only because it is how
the defect was first noticed.

### Why it was not caught

FR-458 hit this schema from the OpenAI side, where strict mode *rejects*
`additionalProperties: true` with a 400. It diagnosed the rejection as a
provider quirk and added a `method="function_calling"` fallback. That fix
is correct for what it addressed, and it also removed the only loud
symptom the defect ever produced — after it, Anthropic's silent `{}`
became the universal behaviour. FR-466 then abandoned structured output
for a whole example rather than fight it. The defect has been routed
around at least four times and never named.

## Ideal Result

A graph author writes the item shape once in the prompt YAML, and that
shape is what the provider is asked for and what the state receives. No
dialect to learn, no post-hoc validator to hand-write, no
`parse_json: true` escape hatch, and no configuration whose only effect
is to be ignored. Finite nested declarations resolve because the function
that builds the model is the same function that builds its parts.

## Proposed Solution

Make `build_pydantic_model_from_json_schema` recurse. When a field is an
object with `properties`, or an array whose `items` is an object with
`properties`, build a nested model with that same function and use it as
the field or element type.

```python
def _item_type(spec: dict, model_name: str, field_name: str) -> type:
    """Element/field type for a spec, recursing into declared properties."""
    if spec.get("type") == "object" and spec.get("properties"):
        return build_pydantic_model_from_json_schema(
            spec, f"{model_name}_{field_name}"
        )
    return JSON_SCHEMA_TYPE_MAP.get(spec.get("type", "string"), str)
```

Called from both the array branch and the scalar branch. An object with
no `properties` keeps mapping to `dict` — that is a genuine
"unconstrained object" declaration and stays supported.

### Supported subset (exhaustive)

In scope: finite inline `output_schema` specifications recursing through
`properties`, for both object-typed fields and array `items` of type
`object`; nested `required` lists applying at their own object level; and
`{"type": "object"}` without `properties` continuing to resolve to `dict`.

Not authorized here: arrays of arrays, `$ref`, recursive or cyclic
references including YAML aliases, the `oneOf`/`anyOf`/`allOf`
combinators, and any schema-depth policy. Encountering one of these
during enforcement stops the work for a separate FR rather than widening
this one.

**No depth cap is added.** The measured tree has maximum depth two. A cap
would be a new rejection policy with no witness to justify it, and
cycles — the only case a cap would catch — are already outside the
supported subset above.

A prompt already in the tree then works as written:

```yaml
output_schema:
  type: object
  properties:
    criteria:
      type: array
      items:
        type: object
        properties:
          name: {type: string}
          score: {type: integer}
          justification: {type: string}
        required: [name, score]
```

Nested `required` is honoured by the recursion, because the same function
already reads `required` at its top level.

## Acceptance Criteria

Witnesses use the existing **CAP-12 / REQ-YG-044** contract for schema
loading and model building. No new capability or requirement ID is
created for a repair to an existing responsibility.

- [ ] **AC-01** R-1..R-5 are folded into this committed FR before
      enforcement begins, including the `is_this_a_graph: no` answer and
      the exact 14-site inventory.
- [ ] **AC-02** A RED commit adds
      `tests/unit/test_fr1054_nested_object_schemas.py`, tagged only
      `@pytest.mark.req("REQ-YG-044")`, failing because an
      array-of-object schema's generated `items` omits its declared
      properties. The GREEN implementation lands in a separate later
      commit.
- [ ] **AC-03** The witness proves both array-item objects and bare
      object fields preserve declared nested properties in
      `model_json_schema()`.
- [ ] **AC-04** The witness proves nested `required` semantics: an
      omitted optional nested key is accepted; an omitted required
      nested key raises `pydantic.ValidationError`.
- [ ] **AC-05** The witness proves `{"type": "object"}` without
      `properties` still maps to `dict` and accepts `{}`, including
      `[{}]` as array items.
- [ ] **AC-06** The witness proves finite two-level recursion (object in
      array in object), validates the nested values, and asserts
      path-derived nested model names are distinct for two sibling
      fields.
- [ ] **AC-07** The witness scans committed
      `examples/**/prompts/*.yaml` `output_schema` blocks, compares every
      declared nested key set against the generated JSON schema, reports
      each mismatch by file and field path, and passes with zero losses.
      Exact command:
      `pytest tests/unit/test_fr1054_nested_object_schemas.py -q --no-cov`
- [ ] **AC-08** Existing primitive-field, primitive-array, enum,
      description, coding-key-normalization, and output-schema-loading
      behaviour stays green:
      `pytest tests/unit/test_schema_loader.py tests/unit/test_coding_key_normalization.py -q --no-cov`
- [ ] **AC-09** `reference/prompt-yaml.md` documents recursive finite
      inline nested object properties, nested `required`, and the
      distinction between a declared object shape and an unconstrained
      `type: object` with no `properties`.
- [ ] **AC-10** The FR-458 fallback is preserved exactly and passes
      unchanged:
      `pytest tests/unit/test_fr449_agent_structured_anthropic.py::TestOpenAIStrictSchemaFallback::test_fallback_to_function_calling_on_invalid_json_schema -q --no-cov`
      The recursion preserves nested properties but does **not** emit
      `additionalProperties: false`, so OpenAI strict-mode rejection can
      still occur. That fallback remains an active provider-boundary
      behaviour, not a dormant safety net.
- [ ] **AC-11** A live run uses a temporary copy of
      `examples/book_reviewer/sample_book.md` with
      `examples/book_reviewer/graph.yaml`.
      `examples/book_reviewer/demo-output-fr-1054.log` records the
      command, provider/model, git SHA, successful exit, and at least one
      `criteria` item with non-empty `name` and `justification` plus an
      integer `score`, and contains no empty `criteria` object.
      Supporting evidence, never a substitute for AC-02..AC-10.
- [ ] **AC-12** Gates exit 0:
      `ruff check yamlgraph/schema_loader.py tests/unit/test_fr1054_nested_object_schemas.py`,
      `pytest tests/ -q`, `python scripts/req_coverage.py --strict`,
      `lint-imports`.
- [ ] **AC-13** The implementation-status section records the RED and
      GREEN commit SHAs, the 14-site scan result, the live-run evidence
      path, and any deviation from frozen scope. A changelog fragment and
      a `docs/diary/` Distill entry with a `Seed:` are present.

No individual edit to the 11 affected prompt files is required or
authorized. The committed inventory test covers every declared site, and
the `book_reviewer` run is the one semantic integration witness.

## Alternatives Considered

| # | Alternative | Disposition |
| --- | --- | --- |
| A1 | Leave it; tell authors to use `parse_json: true` | **Rejected.** This is FR-466's workaround, and it is what the status quo already silently forces. It discards provider-side structured output, moves parsing failures to runtime, and leaves `output_schema:` as configuration whose only function is to mislead. |
| A2 | Lint-time error on nested schemas ("unsupported") | **Rejected.** Honest but strictly worse than the fix, which costs about the same. It would break 11 shipped prompts loudly instead of quietly, with no migration path. Worth reconsidering only if A4 proves the recursion unsafe. |
| A3 | Document the limitation in `prompt-yaml.md` | **Rejected.** The doc at `:239` currently claims nested objects *work*. Amending it to admit they do not is the cheapest possible response and leaves 55 discarded keys in place. |
| A4 | Recurse (proposed) | **Accepted.** Smallest change that makes the declaration true. The function already handles `properties` + `required` at one level; the fix is to call it on itself. Risk is behaviour change for existing consumers — see Risks. |
| A5 | Recurse, plus emit `additionalProperties: false` for OpenAI strict mode | **Refused for this FR, not scheduled.** The recursion does not close strict mode, and FR-458's fallback stays active because of that. Closing it is separate work with its own witness. It is not required to make the declaration true, which is this FR's whole claim. |
| A6 | Also fix the `schema:`/`fields:` dialect (`resolve_type`) | **Rejected as scope.** That dialect raises `ValueError` on unknown types — it fails loudly, is already linted by FR-644, and has no silent-loss defect. Bundling it would widen the diff without sharing a root cause. |

## Risks

**This is a behaviour change, not only a bug fix.** Consumers currently
receiving `[{}]` may have adapted — dropping the field, defaulting it, or
parsing around it. After this, those fields populate. Code that assumed
empty could break on real content. That is the correct direction of
travel, but it is a real consequence and the reason this needs a
judgement rather than a drive-by patch. Judged resolution: no shipped
prompt or graph artifact is edited under this FR; the 14 declared sites
are validated by the committed inventory test, and `book_reviewer` is the
single semantic witness.

**Recursion termination.** No depth cap is added. Cycles are the only
case a cap would catch, and cyclic/`$ref` schemas are outside the
supported subset declared above. The measured tree has maximum depth two.

## Related

- `yamlgraph/schema_loader.py` — `build_pydantic_model_from_json_schema`
- `reference/prompt-yaml.md:239` — documents nested objects as supported
- Downstream witness: `yamlgraph-yt-summarizer` FR-002, FR-003
