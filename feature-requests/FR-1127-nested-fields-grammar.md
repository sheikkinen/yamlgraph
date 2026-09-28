# Feature Request: Nested `fields:` in the inline schema form — a list of objects without switching dialects

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved with revisions ([judgement](FR-1127-nested-fields-grammar.judgement.md), 2026-09-28); R-1..R-4 folded 2026-09-28 (see [Judgement fold](#judgement-fold-2026-09-28)); authority active, not yet enforced
**Effort:** 1.5 days
**Requested:** 2026-09-28
**First consumer / first event:** the next author who writes a prompt in
the `schema:`/`fields:` form and needs a list of objects, at the moment
they type `list[dict]` and, on an Anthropic-bound node, receive E017
telling them to rewrite the whole schema in the JSON-Schema
`output_schema:` form. Today that is the only cure. Second consumer: the
authors of the prompts FR-1125 had to move out of the dialect because it
could not say what their descriptions said (historical demand, not a
current `fields`-form population; the FR-1125 ledger records them), for
example `examples/book_translator/prompts/extract_terms.yaml`,
`examples/book_translator/prompts/identify_chapters.yaml` and
`examples/demos/ramp_rtm/prompts/derive_reqs.yaml`. Third consumer: the
`fields`-form prompts in the repository generally, which keep the
dialect they were written in: at `bff255e6`,
`git grep -l "^schema:" -- 'examples/**/prompts/*.yaml' 'graphs/**/prompts/*.yaml' '.github/**/prompts/*.yaml' | wc -l`
gives 132, and the same for `^output_schema:` gives 47.
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
is the showcase whose README would gain the second cure. FR-644 (a still-Proposed lint of the `fields` dialect's types) is prior
proposal only; no inline-schema type checker from it exists and none is
added here. No REJECTED FR
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
- On 2026-09-27 FR-1125 moved prompts out of the `fields` form because
  their descriptions named object keys the type could not carry
  (`examples/book_translator/prompts/extract_terms.yaml` "each with keys:
  source_term, translation, context, importance";
  `identify_chapters.yaml`; `examples/demos/ramp_rtm/prompts/derive_reqs.yaml`
  "exactly these keys: req_id, statement …"). Their authors did not
  choose JSON Schema; they had no other spelling. The FR-1125 ledger is
  the historical record of that demand.
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

### S-2: Loader (R-1: field-aware recursion, not a `resolve_type` branch)

`resolve_type(type_str, field_name)` and `TYPE_MAP` are unchanged for
every existing spelling; the public resolver sees only a type string and
cannot recurse. `build_pydantic_model` gains a private field-aware helper
that receives the complete field definition, the parent model name and
the dotted field path:

- for `object` and `list[object]`, `fields` must be a non-empty mapping;
  the helper calls `build_pydantic_model` recursively with the
  path-derived name `<Parent>_<field>` and wraps the result in
  `list[...]` only for `list[object]`;
- a present `fields` key on any other type is rejected;
- missing, null, empty, or non-mapping `fields` on `object`/`list[object]`
  is rejected (an empty nested block would recreate FR-1125's open
  object);
- every rejection is a `ValueError` naming the full dotted field path,
  the declared type and the violated rule, at any depth.

`optional`, `default`, `description`, `constraints` and `coding` apply to
nested fields through the same code path as top-level ones (coding keys
normalised as today). `load_schema_from_yaml` and
`build_pydantic_model_from_json_schema` are unchanged.

### S-3: Two witnesses, not one equality (R-2)

The JSON-Schema builder drops `enum` to `str` and does not preserve
source defaults, so an equality on the ramp showcase schema would
certify shared loss, not fidelity. Two witnesses instead:

1. **Dialect equivalence on the shared implemented subset.** A fixture
   with nested objects, primitive fields, arrays of primitives,
   descriptions and matched required/optional semantics, and nothing
   else (no enum, source default, dialect-only constraint, `$ref`, union,
   array of arrays, recursive model). Both builders' complete
   `model_json_schema()` outputs are equal after a named normalisation
   that may rewrite only root and nested model titles, `$defs` keys and
   the matching `$ref` targets; complete public
   `anthropic.transform_schema` outputs are equal under the same
   normalisation. The normaliser never drops a semantic key.
2. **Ramp-shaped content witness.** The FR-1126 showcase shape written
   in the `fields:` grammar preserves exactly `req_id`, `statement`,
   `witness_tests`, `confidence`, `status`, their required set, survives
   `anthropic.transform_schema`, and yields no `open_object` finding in
   either dialect. It claims no enum or default equivalence.

### S-4: Messages and reference (R-4: both diagnostic surfaces)

Two user-visible strings change, wording only: `schema_walk.refusal_message`
for `open_object` (shared by compile, bind and lint messages) and
`checks_schema._FIXES["open_object"]` (the linter's fix string). Each
names all three remedies: nested native `fields:` on an `object` or
`list[object]` field, declared `output_schema` properties, and a provider
that accepts open objects. FR-1126's README diagnostic and its equality
witness are updated to the new complete message, never weakened.
`reference/prompt-yaml.md` "Supported Types" gains `object` and
`list[object]` with the mandatory non-empty nested `fields:` mapping,
recursive finite nesting and the error cases; "When to use which format"
states the exact supported differences (the `fields` form has
constraints and nesting; `output_schema` has `enum`; both nest) and drops
the unqualified identical-model claim. The FR-1126 showcase README shows
the `fields:` spelling as a second "after" without touching the demo's
graph or prompt.

### S-5: Witnesses (R-4: requirement ownership frozen)

`tests/unit/test_fr1127_nested_fields.py` on **CAP-12 / REQ-YG-044**
(schema loading and model building; FR-1054's precedent); the
coding-key assertion additionally on **REQ-YG-039**. No new capability or
requirement.

- RED: `list[object]` + `fields:` builds a model whose items carry the
  declared properties; fails today with `Unknown type`, not on setup.
- nested `description`, requiredness, `optional`, `default`, applicable
  `constraints` and `coding` behave as at top level; depth two works
  (`object` inside `list[object]`); sibling paths produce distinct
  classes and names.
- the five invalid forms of S-2 raise `ValueError` naming the dotted
  path, type and rule; one at depth two.
- the two S-3 witnesses, raw and transformed.
- `dict`, `dict[str, Any]`, `list[dict]`, `Any`, primitives, lists of
  primitives, optional/default, constraints, coding normalisation and the
  JSON-Schema builder are unchanged; open forms still yield
  `open_object`.
- both diagnostic surfaces name the three remedies; the FR-1126 README
  equality holds against the new message.

### Not in scope

- Migrating the 26 FR-1125 prompts back to the `fields` form: they work;
  a migration is a separate FR if anyone wants the dialect back.
- `enum` in the `fields` form, `$ref`, unions, recursive models.
- Any change to the refusal itself or to FR-998's policy.

## Acceptance Criteria

The judgement's revised list is binding; it replaces the original
AC-01..AC-09.

- [ ] AC-01: Before production implementation, this committed FR folds R-1 through R-4 and records that CAP-12 / REQ-YG-044 governs the grammar; coding normalization remains REQ-YG-039.
- [ ] AC-02 (RED): a commit preceding production implementation adds `tests/unit/test_fr1127_nested_fields.py`, tagged with the frozen requirement IDs, and fails because `list[object]`/`object` nested construction is absent rather than because of imports or fixtures. GREEN lands in a separate later commit.
- [ ] AC-03: `object` and `list[object]` with non-empty mapping-valued `fields` build path-named nested models; a depth-two `object` inside `list[object]` validates populated values, and sibling paths produce distinct model classes and names.
- [ ] AC-04: nested `description`, requiredness, `optional`, `default`, and applicable Pydantic `constraints` match top-level native-field behavior. Nested coding keys are normalized exactly as top-level keys, with the coding-specific assertion marked REQ-YG-039.
- [ ] AC-05: `fields` on a scalar/list-of-scalar/dict type, and missing, null, empty, or non-mapping `fields` on `object`/`list[object]`, each raise `ValueError` naming the complete dotted field path, declared type, and rule; a depth-two invalid declaration proves recursive error context.
- [ ] AC-06: a shared-subset fixture produces complete equal raw schemas after normalization limited to root/nested titles, `$defs` names, and matching `$ref` targets; complete public `anthropic.transform_schema` outputs are equal under the same normalization. The fixture contains no enum, source default, dialect-only constraint, `$ref`, union, array-of-array, or recursive declaration.
- [ ] AC-07: a separate ramp-shaped fixture preserves exactly `req_id`, `statement`, `witness_tests`, `confidence`, and `status`, preserves their required-name set, survives public `anthropic.transform_schema`, and yields no `open_object` finding in either dialect. It makes no enum/default equivalence claim.
- [ ] AC-08: existing `dict`, `dict[str, Any]`, `list[dict]`, `Any`, primitive, primitive-list, optional/default, constraint, coding-normalization, and JSON-Schema builder behavior passes unchanged. The existing open forms still produce `open_object` findings.
- [ ] AC-09: compile/bind `refusal_message` and the E017 `LintIssue.fix` each name all three remedies: nested native `fields:`, declared `output_schema` properties, and a provider accepting open objects. The updated FR-1126 README diagnostic equals the emitted complete E017 diagnostic after its existing whitespace normalization.
- [ ] AC-10: `reference/prompt-yaml.md` documents `object` and `list[object]`, the mandatory non-empty nested `fields:` mapping, recursive finite nesting, error cases, and the exact supported differences between the two dialects; it no longer makes an unqualified identical-model claim.
- [ ] AC-11: `examples/demos/ramp_rtm/README.md` shows the existing `output_schema` after-form and the equivalent nested `fields:` after-form without modifying the demo graph or prompt.
- [ ] AC-12: the focused command `pytest tests/unit/test_fr1127_nested_fields.py tests/unit/test_schema_loader.py tests/unit/test_coding_key_normalization.py tests/unit/test_fr1054_nested_object_schemas.py tests/unit/test_fr1123_untyped_subschema.py tests/unit/test_fr1125_open_objects.py tests/unit/test_fr1126_ramp_rtm_showcase.py -q --no-cov` passes.
- [ ] AC-13: `ruff check yamlgraph/schema_loader.py yamlgraph/utils/schema_walk.py yamlgraph/linter/checks_schema.py tests/unit/test_fr1127_nested_fields.py`, `python scripts/req_coverage.py --strict`, and `lint-imports` pass; `schema_loader.py` remains within the repository module ceiling or is split without expanding public API.
- [ ] AC-14: a `feat` changelog fragment with scope `schema`, the FR implementation record with RED/GREEN SHAs and exact validation results, and a Distill diary entry containing `**Seed:**` are committed.

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

## Judgement fold (2026-09-28)

[Judgement](FR-1127-nested-fields-grammar.judgement.md): APPROVED WITH
REVISIONS. Folded the same day:

- **R-1** → S-2: recursion lives in a private field-aware helper called by
  `build_pydantic_model`; `resolve_type` and `TYPE_MAP` untouched; the
  five invalid forms and their `ValueError` wording frozen; AC-05.
- **R-2** → S-3: a shared-subset dialect-equivalence witness with a
  names-only normaliser, and a separate ramp-shaped content witness that
  claims no enum or default equivalence; AC-06, AC-07.
- **R-3** → first-consumer line and Problem: the eight prompts are
  historical demand (three named), the 132/47 counts carry their command
  and commit, FR-644 is prior proposal only.
- **R-4** → S-4, S-5: CAP-12 / REQ-YG-044 governs; REQ-YG-039 for the
  coding assertion; both diagnostic surfaces (`refusal_message` and the
  linter fix string) name the three remedies; FR-1126's witness updated,
  never weakened.

Scope frozen to the judgement's D-1..D-6; conditions C-1..C-7 are gates.
Judge rendered from the author's session via the sole route, as recorded
for FR-1121..FR-1126.

## Related

- `yamlgraph/schema_loader.py` (`resolve_type`, `build_pydantic_model`,
  `_nested_type`), `yamlgraph/utils/schema_walk.py` (messages),
  `yamlgraph/linter/checks_schema.py` (fix text),
  `reference/prompt-yaml.md`, `examples/demos/ramp_rtm/README.md`.
- FR-1054 A6; FR-1125 migration ledger `docs/issues-2026-09-27-fr1125-census.md`.
