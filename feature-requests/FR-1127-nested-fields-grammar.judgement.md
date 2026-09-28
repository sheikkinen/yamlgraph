# Judgement: FR-1127 Nested `fields:` in the inline schema form — a list of objects without switching dialects

**Verdict:** APPROVED WITH REVISIONS — the nested grammar is a coherent framework primitive, but authority activates only after R-1 through R-4 are folded into the committed FR.

**Reviewed against:** `feature-requests/FR-1127-nested-fields-grammar.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `docs/spikes/constrained-object-2026-09-27/README.md`; `docs/issues-2026-09-27-fr1125-census.md`; `docs/diary/diary-2026-09-27-reflection-fr-1125-the-schema-that-passed-and-said-nothing.md`; `docs/diary/diary-2026-09-27-reflection-fr-1126-show-the-refusal.md`; `docs/diary/2026-09-27-reflection-release-0.6.2.md`; `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md`; `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`; `feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md`; `feature-requests/FR-1126-ramp-rtm-fr1125-showcase.md`; `feature-requests/FR-644-lint-inline-schema-types.md`; `feature-requests/FR-1083-exit-code-reflects-errors.md`; `yamlgraph/schema_loader.py`; `yamlgraph/utils/schema_walk.py`; `yamlgraph/linter/checks_schema.py`; `reference/prompt-yaml.md`; `examples/demos/ramp_rtm/README.md`; `examples/demos/ramp_rtm/prompts/derive_reqs.yaml`; `tests/unit/test_schema_loader.py`; `tests/unit/test_coding_key_normalization.py`; `tests/unit/test_fr1054_nested_object_schemas.py`; `ARCHITECTURE.md`.

## What is sound

The problem is real and evidenced at the provider boundary. The spike proves that Anthropic cannot carry an open object, while a declared nested object survives and fills; FR-1125 deliberately deferred this nested `fields:` grammar (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:264-270`). FR-1127 also directly dispositions FR-1054's rejected alternative A6 rather than silently reopening it (`feature-requests/FR-1127-nested-fields-grammar.md:27-38`; `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:292-302`).

The scope is cohesive: one native-schema grammar extension, its boundary diagnostics, witnesses, and directly affected documentation. It does not bundle provider fallback, migration, enum support, references, unions, or recursive models (`feature-requests/FR-1127-nested-fields-grammar.md:167-172`). Those exclusions keep the work at the existing schema-loading boundary and preserve FR-1123/FR-1125 policy.

The proposal is a **framework primitive**. It serves more than three demonstrated schema declarations, extends a core authoring dialect, and closes a capability gap that the existing `output_schema` abstraction solves only by forcing a dialect switch. Recursion follows established FR-1054 architecture: path-derived nested Pydantic models already work in the JSON-Schema builder (`yamlgraph/schema_loader.py:177-187`; `tests/unit/test_fr1054_nested_object_schemas.py:95-139`). The work is feasible within the current module and dependencies.

The principal behavior is directly testable: generated JSON Schema, Pydantic validation, walker findings, transformed schema, exceptions, diagnostics, and documentation are all deterministic. The research substitute is substantive: it supplies a live mechanism probe, five dispositioned solution classes, precedent, and an explicit `is_this_a_graph` answer (`feature-requests/FR-1127-nested-fields-grammar.md:17-26,198-211`), satisfying the repository's equivalent-record rule.

## Required revisions

### R-1: Specify field-aware recursion instead of assigning nested construction to `resolve_type`

Replace S-2's statement that "`resolve_type` gains a branch ... that calls `build_pydantic_model`" (`feature-requests/FR-1127-nested-fields-grammar.md:121-128`). The current public resolver receives only a type string and optional field name, so it has neither the nested `fields:` mapping nor the parent model name needed to perform the proposed recursion (`yamlgraph/schema_loader.py:62-101`). Fold an explicit field-aware design into S-2:

- keep `resolve_type(type_str, field_name)` and `TYPE_MAP` behavior unchanged for every existing spelling;
- add a private field-type helper called by `build_pydantic_model`, receiving the complete field definition, parent model name, and dotted field path;
- for `object` and `list[object]`, require `fields` to be a non-empty mapping, recursively call `build_pydantic_model` with the path-derived `<Parent>_<field>` name, and wrap the result in `list[...]` only for `list[object]`;
- reject a present `fields` key on every other type, and reject missing, null, empty, or non-mapping `fields` on `object`/`list[object]`;
- every rejection must be `ValueError` and name the full dotted field path, declared type, and violated rule.

Revise AC-03 to cover all five invalid forms above and a depth-two dotted error path. This makes the grammar total, prevents an empty nested block from recreating FR-1125's open-object defect, and preserves callers and tests of the existing public resolver.

### R-2: Define equivalence over the dialects' shared implemented subset

Replace S-3's ramp-showcase equality fixture. That source schema declares `default: []` and an enum (`examples/demos/ramp_rtm/prompts/derive_reqs.yaml`), while the current JSON-Schema builder turns enum into plain `str` and assigns `None` to non-required fields rather than preserving source defaults (`yamlgraph/schema_loader.py:217-231`; `tests/unit/test_schema_loader.py`, `test_enum_type_becomes_string`). Exact equality on that fixture would therefore certify equal information loss, not dialect fidelity, and conflicts with enum being explicitly out of scope (`feature-requests/FR-1127-nested-fields-grammar.md:167-172`).

Fold two separate witnesses:

1. A dialect-equivalence fixture limited to the intersection both builders actually support: nested objects, primitive fields, arrays of primitives, descriptions, and matched required/optional semantics; no enum, source default, dialect-only constraint, `$ref`, union, or recursive model. Compare complete `model_json_schema()` outputs after a named normalization that may rewrite only root/nested model titles, `$defs` keys, and corresponding `$ref` targets. Apply the same narrow normalization before comparing complete public `anthropic.transform_schema` outputs.
2. A ramp-shaped content witness that asserts the five nested property names, required-name set, no `open_object` finding, and preservation through `anthropic.transform_schema`; it must not claim full dialect equality or enum/default preservation.

State explicitly that arbitrary key dropping is forbidden in the normalizer. Update AC-04 to name both witnesses and their exact assertions.

### R-3: Correct the consumer evidence and prior-art status

Rewrite the present-tense claim that eight committed prompts are still `fields`-form consumers (`feature-requests/FR-1127-nested-fields-grammar.md:9-16,65-68`). FR-1125 migrated the named known-key cases to `output_schema`; its committed ledger is historical evidence of demand, not a current `fields`-form population (`docs/issues-2026-09-27-fr1125-census.md`, Dispositions and Result after enforcement). Name at least three concrete migrated prompt paths as demonstrated historical use cases.

For the separate "132 `fields`-form prompts" claim, either add to the FR a reproducible repository command, counted scope, commit SHA, and result, or remove the number. Also correct the statement that FR-644 "is extended": FR-644 remains Proposed and no inline-schema type checker from it exists; describe it as prior proposal only (`feature-requests/FR-644-lint-inline-schema-types.md:1-7`; current linter code uses E008 for other concerns). These corrections preserve the framework-primitive classification without relying on a stale population or nonexistent implementation.

### R-4: Freeze requirement ownership and both diagnostic surfaces

Replace the open-ended REQ decision in S-5 (`feature-requests/FR-1127-nested-fields-grammar.md:147-149`). Reuse **CAP-12 / REQ-YG-044** for nested grammar and model-building witnesses, matching `ARCHITECTURE.md:756` and FR-1054's precedent (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:224-233`). A focused assertion about coding-key normalization must additionally use the existing **REQ-YG-039**, matching `tests/unit/test_coding_key_normalization.py`; no new capability or requirement is authorized.

Freeze separate exact assertions for the two user-visible E017 surfaces. `schema_walk.refusal_message` is shared by compile, bind, and lint messages, while `checks_schema._FIXES["open_object"]` is a distinct linter fix string (`yamlgraph/utils/schema_walk.py:107-134`; `yamlgraph/linter/checks_schema.py:28-40,92-103`). Both must name the native cure (`fields:` on `object`/`list[object]`), the `output_schema` cure, and the non-Anthropic-provider alternative. The existing FR-1126 README equality witness must be updated to the new complete diagnostic, not weakened.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/schema_loader.py`: field-aware native-schema recursion and validation for `object` / `list[object]` only |
| D-2 | `tests/unit/test_fr1127_nested_fields.py`: RED/GREEN grammar, validation, nesting, preservation, equivalence, transform, and walker witnesses |
| D-3 | `yamlgraph/utils/schema_walk.py` and `yamlgraph/linter/checks_schema.py`: wording-only update to the existing open-object cure |
| D-4 | Existing FR-1126 diagnostic witness and `examples/demos/ramp_rtm/README.md`: exact-message update and second valid "after" spelling |
| D-5 | `reference/prompt-yaml.md`: supported native nested types and an accurate dialect comparison |
| D-6 | `changelog/unreleased/`, FR-1127 implementation record, and one `docs/diary/` Distill entry |

Not authorized: edits to `graph.yaml` or `prompts/*.yaml`; migration of FR-1125 prompts; changes to `build_pydantic_model_from_json_schema`; enum, `$ref`, unions, arrays of arrays, recursive/cyclic models, or open-object semantics; provider fallback or FR-998 policy changes; new lint codes or implementation of FR-644; changes to walker classification, provider resolution, compile/bind refusal timing, CI, hooks, or doctrine.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 are folded into the committed FR before RED or production implementation begins. | GATE |
| C-2 | RED and GREEN are separate commits; RED fails on absent nested behavior, not setup. | GATE |
| C-3 | Existing open-object spellings and FR-1123/FR-1125 refusal policy remain unchanged. | GATE |
| C-4 | Equivalence normalization rewrites names/references only and cannot discard semantic schema keys. | GATE |
| C-5 | No governed graph or prompt artifact is edited; encountering a need for one stops enforcement for separate authority. | GATE |
| C-6 | No enum/default enhancement to the JSON-Schema builder, new lint code, provider fallback, or migration enters this change. | GATE |
| C-7 | All tests carry the frozen requirement markers and all AC-12/AC-13 commands pass before implementation is recorded complete. | GATE |

Authority granted: after the four revisions are committed, implement the frozen native `object` / `list[object]` nested-fields grammar, its exact diagnostics, witnesses, and directly related documentation only.
