# Feature Request: Nested `fields:` in the inline schema form — a list of objects without switching dialects

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-28
**First consumer / first event:** the next author who writes a prompt in
the `schema:`/`fields:` form and needs a list of objects, at the moment
they type `list[dict]` and, on an Anthropic-bound node, receive E017
telling them to rewrite the whole schema in the JSON-Schema
`output_schema:` form. Today that is the only cure. Second consumer: the
eight committed `fields`-form prompts whose descriptions already say
"each with keys …" while their type says `list[dict]` or `list[str]`,
and the 132 `fields`-form prompts in the repository generally (47 use
`output_schema`), which keep the dialect they were written in.
**Research:** FR-890 route **not run** (the operator's rite for this FR
named judge, docs PR, outsider, merge). Substitute, per the TEMPLATE's
equivalent-record clause and the FR-1083 precedent: the live spike
[docs/spikes/constrained-object-2026-09-27/README.md](../docs/spikes/constrained-object-2026-09-27/README.md)
(why an object without declared properties cannot cross Anthropic's
decoder, and that the declared form fills), the FR-1125 migration record
(26 prompts moved dialect because the `fields` form could not say what
their descriptions said), the FR-1125 and FR-1126 diary seeds, and the
in-body [Alternatives Considered](#alternatives-considered) with an
`is_this_a_graph` answer.
**Prior art:** [FR-1054](FR-1054-nested-object-schemas-reach-the-provider.md)
made nested objects reach the provider in the `output_schema` form and,
in its alternative A6, **rejected** touching the `schema:`/`fields:`
dialect "as scope" because that dialect "fails loudly … and has no
silent-loss defect". That was true on 2026-09-0x; since FR-998 the
dialect's `list[dict]` is a silent-loss defect on Anthropic (the spike),
and since FR-1125 it is refused outright, so the dialect can no longer
express a list of objects at all. This FR re-enters A6's territory with
that changed premise and a narrower shape: it adds no JSON-Schema
features to the dialect, only nesting. [FR-1125](FR-1125-refuse-unconstrained-objects-anthropic.md)
made the refusal and pointed every message at `output_schema`; this FR
gives the message a second cure in the author's own dialect and does
not touch the refusal. [FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md)
owns the walker and lint codes; unchanged. [FR-1126](FR-1126-ramp-rtm-fr1125-showcase.md)
is the showcase whose README would gain the second cure. FR-644 (lint of
the `fields` dialect's types) is extended, not replaced. No REJECTED FR
in this territory beyond A6, dispositioned above.

## Summary

The inline `schema:`/`fields:` form can type scalars and lists of
scalars, but not a list of objects: `list[dict]` is the only spelling,
and on Anthropic it is refused (FR-1125) because the provider cannot
express an object with unknown keys. The cure today is to rewrite the
prompt in the `output_schema:` JSON-Schema form, which 26 prompts did on
2026-09-27. This FR lets a `fields` entry declare its own `fields:`,
so `type: list[object]` (or `type: object`) with a nested `fields:` block
builds a nested Pydantic model, exactly as FR-1054's `properties` does,
and the refusal message names both cures.

## Value Statement

An author keeps one dialect: a list of objects is declared in the same
`fields:` vocabulary as everything else, with `optional`, `default`,
`description` and constraints on the nested fields, and the schema
crosses Anthropic's decoder with every key intact.

## Problem

- `resolve_type` accepts `list[T]` for `T` in `{str,int,float,bool,dict,Any}`
  and `dict[K, V]` for scalar `K`, `V`; nothing nests
  (`yamlgraph/schema_loader.py`).
- Eight committed `fields`-form prompts describe object keys in prose
  ("each with keys: source_term, translation …") that the type could not
  carry; FR-1125 moved them to `output_schema`. Their authors did not
  choose JSON Schema; they had no other spelling.
- The reference's "When to use which format" table says the forms are
  equivalent ("Both formats produce identical Pydantic models"); they
  are not: only one can express nested objects.
- The E017 fix text offers exactly one cure, a dialect switch.

## Ideal Result

A `fields` entry may carry a nested `fields:` block. `type: object` with
`fields:` becomes a nested model; `type: list[object]` with `fields:`
becomes a list of that model; nesting works to any depth; nested fields
accept the same properties as top-level ones (`description`, `optional`,
`default`, `constraints`, `coding`). The built model's JSON schema is
identical in content to what the equivalent `output_schema` would
produce, so FR-1125's walker, lint and parity see declared properties
and stay silent. A bare `list[dict]` and `dict` keep their meaning
(open object) and their refusal on Anthropic. The reference tells the
truth about the two forms, and E017's fix names both cures.

## Proposed Solution

### S-1: Grammar

```yaml
schema:
  name: RankedStories
  fields:
    stories:
      type: list[object]
      description: "Top 5-8 stories"
      fields:
        title: {type: str, description: "Article title"}
        url: {type: str}
        relevance: {type: float, constraints: {ge: 0.0, le: 1.0}}
        reason: {type: str, optional: true}
    source:
      type: object
      fields:
        name: {type: str}
        feed: {type: str, optional: true}
```

Rules: `object` and `list[object]` are the only types that accept
`fields:`; a `fields:` block on any other type fails at load naming the
field; `object`/`list[object]` **without** `fields:` fails at load too
(an author who wants an open object writes `dict`/`list[dict]`, which
stay as they are). Nested model names are `<Parent>_<field>`, matching
FR-1054's naming so the two forms produce the same `$defs` keys.

### S-2: Loader

`build_pydantic_model` becomes recursive: `resolve_type` gains a branch
for `object`/`list[object]` that calls `build_pydantic_model` on the
nested block with the derived name; `optional`, `default`, `description`,
`constraints` and `coding` apply to nested fields through the same code
path as top-level ones. `load_schema_from_yaml` is unchanged.
`TYPE_MAP` is unchanged (`dict`, `Any` keep their meaning).

### S-3: Equivalence with `output_schema`

A test builds the same shape both ways (the FR-1126 showcase schema:
`entries` with five properties, one enum, one array of strings) and
asserts the two models' `model_json_schema()` are equal after `$defs`
name alignment, and that the public `anthropic.transform_schema` output
is equal too. FR-1125's walker returns no finding for either.

### S-4: Messages and reference

`schema_walk.refusal_message` for `open_object` names both cures:
"declare its properties with `fields:` on a `list[object]`/`object`
field, or with the `output_schema` form, or use a provider that accepts
open objects". The linter fix text likewise. `reference/prompt-yaml.md`
"Supported Types" gains `object` and `list[object]` with `fields:`;
"When to use which format" states what each form can and cannot express
(the `fields` form has constraints and nesting; `output_schema` has
`enum`; both nest). The FR-1126 showcase README shows the `fields:`
spelling as the second "after".

### S-5: Witnesses

`tests/unit/test_fr1127_nested_fields.py` (REQ: the schema-loading
requirement `build_pydantic_model` already carries, or a new one via the
FR-975/FR-980 route; the judge decides):

- RED: `list[object]` + `fields:` builds a model whose items have the
  declared properties (fails today with `Unknown type`).
- nested `optional`, `default`, `constraints`, `coding` behave as at top
  level; depth two works (`object` inside `list[object]`).
- `fields:` on a scalar type, and `object`/`list[object]` without
  `fields:`, fail at load naming the field.
- equivalence (S-3) both raw and transformed.
- `dict` and `list[dict]` are unchanged and still `open_object` for the
  walker.
- the refusal message and lint fix name both cures.

### Not in scope

- Migrating the 26 FR-1125 prompts back to the `fields` form: they work;
  a migration is a separate FR if anyone wants the dialect back.
- `enum` in the `fields` form, `$ref`, unions, recursive models.
- Any change to the refusal itself or to FR-998's policy.

## Acceptance Criteria

- [ ] AC-01: RED first: `build_pydantic_model` on a `list[object]` field
  with `fields:` fails today with `Unknown type` and passes after S-2;
  separate GREEN commit.
- [ ] AC-02: nested fields honour `description`, `optional`, `default`,
  `constraints` and `coding` exactly as top-level fields; two levels of
  nesting build.
- [ ] AC-03: `fields:` on a non-object type, and `object`/`list[object]`
  without `fields:`, raise at load naming the field and the rule.
- [ ] AC-04: the S-3 equivalence holds for raw and transformed schemas;
  FR-1125's walker returns no finding for either form.
- [ ] AC-05: `dict`, `dict[str, Any]`, `list[dict]` and `Any` are
  unchanged; FR-1123 and FR-1125 suites pass unchanged.
- [ ] AC-06: the open-object refusal message and the E017 fix text name
  the `fields:` cure and the `output_schema` cure; FR-1126's README
  equality test still passes (the quoted diagnostic updated with it).
- [ ] AC-07: reference "Supported Types" and "When to use which format"
  updated; the FR-1126 showcase shows both "after" spellings.
- [ ] AC-08: new tests carry the governing REQ ID; `python
  scripts/req_coverage.py --strict`, `lint-imports` and ruff pass;
  `schema_loader.py` stays under the module ceiling or is split.
- [ ] AC-09: changelog fragment (`feat`, scope `schema`), FR
  implementation record, Distill diary entry with a `**Seed:**`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Leave the `fields` form as is; `output_schema` is the nested form | Rejected. It makes 132 prompts second-class the day they need an object, and the reference's equivalence claim false. |
| `list[Model]` referencing a shared Pydantic model by name | Rejected. Moves the shape into Python, against "YAML prompts only"; and the digest showed shared models (`GenericReport`) carry open maps too. |
| Allow `properties:` (JSON-Schema spelling) inside the `fields` form | Rejected. Two vocabularies in one block; the `fields` form's own words (`fields`, `optional`, `constraints`) are enough. |
| Auto-convert a `fields`-form prompt to `output_schema` at load | Rejected. The author's file would not match what runs; FR-1054 already builds models from JSON Schema, so equivalence is the target, not conversion. |
| Add `enum` to the `fields` form in the same FR | Deferred. Different feature; `output_schema` has it today. |

`is_this_a_graph`: no; a loader grammar extension with a deterministic
equivalence witness.

## Related

- `yamlgraph/schema_loader.py` (`resolve_type`, `build_pydantic_model`,
  `_nested_type`), `yamlgraph/utils/schema_walk.py` (messages),
  `yamlgraph/linter/checks_schema.py` (fix text),
  `reference/prompt-yaml.md`, `examples/demos/ramp_rtm/README.md`.
- FR-1054 A6; FR-1125 migration ledger `docs/issues-2026-09-27-fr1125-census.md`.
