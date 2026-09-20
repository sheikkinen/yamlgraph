# Feature Request: FR-1054 Nested object schemas reach the provider

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
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

### Measured blast radius

Scan of the real tree (worktrees and `build/` excluded), building each
declared `output_schema` and comparing to what Pydantic emits:

```
files with nested output_schema: 11
nested sites:                    14
total declared keys discarded:   55
sites that survive:               0
```

Affected: `examples/api-discovery/prompts/synthesize.yaml`,
`.../browser-sniff/prompts/sniff.yaml`,
`.../endpoint-probe/prompts/probe.yaml`,
`.../schema-extract/prompts/{ckan,openapi,unsupported}.yaml`,
`examples/beautify/prompts/analyze.yaml` (two sites),
`examples/book_reviewer/prompts/chapter_review.yaml`,
`examples/demos/session-shapes/prompts/classify_session_shape.yaml`, and
two further sites including an OCR `manual_review` field. **Every single
nested site loses its keys. There are no survivors and no partial cases.**

### Field evidence

Observed in a downstream consumer (`yamlgraph-yt-summarizer`, FR-003)
across 11 transcript chunks, per-chunk output archived to disk:

| Declared shape | Items returned | Empty `{}` |
| --- | --- | --- |
| `array` of `string` (`concepts`, `questions`) | 155 | **0** |
| `array` of `object` (six fields) | 30 | **30** |

Flat fields populate perfectly; nested fields are empty at 100%. The
asymmetry is the signature. That project spent weeks attributing thin
output to a weak model tier before the per-chunk artifacts made the split
visible.

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
is to be ignored. Nesting works at any depth because the function that
builds the model is the same function that builds its parts.

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

- [ ] **AC-1** A condemning test asserts that an array-of-object schema
      with declared `items.properties` generates a JSON schema whose
      `items` carries those properties — and fails on `main` before the
      fix.
- [ ] **AC-2** A test covers a bare nested `object` field with
      `properties`, not only the array case.
- [ ] **AC-3** A test proves nested `required` is honoured: a missing
      required nested key raises `ValidationError`, and an optional one
      does not.
- [ ] **AC-4** A test proves `{"type": "object"}` with no `properties`
      still resolves to `dict`, and that `[{}]` still validates against
      it. The unconstrained-object declaration is not withdrawn.
- [ ] **AC-5** A test covers two levels of nesting (object in array in
      object), proving the recursion is general rather than one-deep.
- [ ] **AC-6** A test asserts generated nested model names are unique
      within one parent so two fields with identically-shaped items do
      not collide.
- [ ] **AC-7** The existing suite passes unchanged. Any test that
      asserted the `list[dict]` output is corrected in the same commit
      with its reasoning recorded here, not deleted.
- [ ] **AC-8** `python tmp/scan_nested.py` (or equivalent) reports zero
      sites losing keys across the real tree, down from 14.
- [ ] **AC-9** `reference/prompt-yaml.md:239`, which already advertises
      nested objects as supported, is verified accurate rather than
      changed — or corrected if the implemented behaviour differs from
      what it promises.
- [ ] **AC-10** FR-458's fallback is left in place and its test still
      passes. It now guards a case that should no longer arise.
- [ ] **AC-11** Gates: `ruff`, full `pytest`, `req_coverage --strict`,
      `lint-imports`. A capability file precedes the witnessing tests.
- [ ] **AC-12** A live run of one affected shipped example produces
      populated nested records, with the log committed as evidence.
      Supporting evidence, never a substitute for AC-1..AC-11.

## Alternatives Considered

| # | Alternative | Disposition |
| --- | --- | --- |
| A1 | Leave it; tell authors to use `parse_json: true` | **Rejected.** This is FR-466's workaround, and it is what the status quo already silently forces. It discards provider-side structured output, moves parsing failures to runtime, and leaves `output_schema:` as configuration whose only function is to mislead. |
| A2 | Lint-time error on nested schemas ("unsupported") | **Rejected.** Honest but strictly worse than the fix, which costs about the same. It would break 11 shipped prompts loudly instead of quietly, with no migration path. Worth reconsidering only if A4 proves the recursion unsafe. |
| A3 | Document the limitation in `prompt-yaml.md` | **Rejected.** The doc at `:239` currently claims nested objects *work*. Amending it to admit they do not is the cheapest possible response and leaves 55 discarded keys in place. |
| A4 | Recurse (proposed) | **Accepted.** Smallest change that makes the declaration true. The function already handles `properties` + `required` at one level; the fix is to call it on itself. Risk is behaviour change for existing consumers — see Risks. |
| A5 | Recurse, plus emit `additionalProperties: false` for OpenAI strict mode | **Deferred — not a schedule claim, a scope refusal.** Out of scope for this FR. If AC-12 or FR-458's fallback shows it is still needed after the recursion lands, it is a separate FR with its own witness. It is not required to make the declaration true, which is this FR's whole claim. |
| A6 | Also fix the `schema:`/`fields:` dialect (`resolve_type`) | **Rejected as scope.** That dialect raises `ValueError` on unknown types — it fails loudly, is already linted by FR-644, and has no silent-loss defect. Bundling it would widen the diff without sharing a root cause. |

## Risks

**This is a behaviour change, not only a bug fix.** Consumers currently
receiving `[{}]` may have adapted — dropping the field, defaulting it, or
parsing around it. After this, those fields populate. Code that assumed
empty could break on real content. That is the correct direction of
travel, but it is a real consequence and the reason this needs a
judgement rather than a drive-by patch. The 11 affected files are
enumerated above; the judge should decide whether each needs inspection
in this FR or in follow-ups, and say which.

**Deeply recursive or self-referential schemas.** The recursion has no
depth limit. A schema referencing itself would not terminate. No such
schema exists in the tree today (max observed depth: 2). The judge should
rule on whether a depth cap belongs in this FR or is over-engineering
against a case that cannot currently arise.

## Related

- `yamlgraph/schema_loader.py` — `build_pydantic_model_from_json_schema`
- `reference/prompt-yaml.md:239` — documents nested objects as supported
- Downstream witness: `yamlgraph-yt-summarizer` FR-002, FR-003
