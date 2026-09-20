# Judgement: FR-1054 Nested object schemas reach the provider

**Prior art:** retrieval on this judgement's filename nouns returned
`FR-766-runpod-provider.judgement.md`,
`FR-945-lan-recon-skill.judgement.md`, and
`FR-823-hosted-declarative-graph-runner.judgement.md`. All three are
filename-noun collisions on "provider.judgement" and "nested", with no
shared problem: FR-766 is RunPod LLM provider integration, FR-945 is
WinRM LAN host recon, FR-823 is a hosted graph runner. None touches
`schema_loader`, JSON-Schema-to-Pydantic construction, or structured
output shape. Dismissed. The substantive prior art for this defect is
dispositioned in the FR itself (FR-458, FR-466, FR-905, FR-908, FR-904,
FR-795, FR-548, FR-644).

**Verdict:** APPROVED WITH REVISIONS — recursive nested-model construction is the smallest architecture-aligned fix for a confirmed framework defect, but authority activates only after the FR completes the research gate, binds the work to existing REQ-YG-044, defines the supported recursion domain, corrects the OpenAI fallback claim, and replaces ambiguous verification criteria with exact witnesses.

**Reviewed against:** `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md`; `yamlgraph/schema_loader.py`; `reference/prompt-yaml.md`; `examples/book_reviewer/prompts/chapter_review.yaml`; `examples/book_reviewer/graph.yaml`; `examples/book_reviewer/README.md`; `examples/beautify/prompts/analyze.yaml`; `examples/ocr_cleanup/prompts/cleanup_page.yaml`; committed path/count inventory of `examples/**/prompts/*.yaml`; `tests/unit/test_schema_loader.py`; `tests/unit/test_coding_key_normalization.py`; `tests/unit/test_fr449_agent_structured_anthropic.py`; `tests/unit/test_fr678_narrow_structured_catch.py`; `tests/unit/test_fr998_structured_output.py`; `capabilities/CAP-12-utilities.yaml`; `ARCHITECTURE.md`; `feature-requests/FR-458-openai-strict-schema-additional-properties.md`; `feature-requests/FR-466-dungeon-master-example.md`; `feature-requests/FR-548-dm-v2-world-codex-backstory-stage.md`; `feature-requests/FR-644-lint-inline-schema-types.md`; `feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md`; `feature-requests/FR-904-slot-bound-digest-collection.judgement.md`; `feature-requests/FR-905-ranked-story-boundary-validation.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; repo doctrine in project instructions.

**Draft status:** Advisory until human-reviewed.

## What is sound

The defect is concrete and located at the correct boundary. The JSON-Schema builder maps an array item's `"object"` type directly to `dict` and never reads the item's `properties` (`yamlgraph/schema_loader.py:167-174`, `yamlgraph/schema_loader.py:177-213`), exactly matching the FR's causal account (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:42-48`). The first-consumer prompt declares `criteria.items.properties` and nested `required` keys (`examples/book_reviewer/prompts/chapter_review.yaml:31-50`), while the public reference labels `object` as the nested-object type (`reference/prompt-yaml.md:232-239`). This is a real silent-contract defect, not a speculative extension.

The proposed implementation is minimal and architecture-aligned. Reusing `build_pydantic_model_from_json_schema` for nested object specifications preserves one parser for `properties` and `required` rather than adding a parallel dialect or post-hoc consumer validator (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:152-191`). Existing tests already locate this function under schema-loading requirement REQ-YG-044 (`tests/unit/test_schema_loader.py:319-466`), and CAP-12 explicitly owns `schema_loader` and "Schema loading and model building" (`capabilities/CAP-12-utilities.yaml:1-22`; `ARCHITECTURE.md:735-740`).

The prior-art disposition is unusually strong. FR-458's provider fallback, FR-466 and FR-548's `parse_json` workarounds, FR-905's consumer-side validation, FR-904's explicit framework deferral, and FR-795/FR-644's separate native-`schema:` dialect concern are distinguished rather than silently superseded (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:16-38`). The alternatives table preserves six genuine choices and rejects both documentation-only and cross-dialect scope expansion (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:229-238`).

The acceptance-test core is derivable: array-contained objects, bare nested objects, nested required/optional behavior, unconstrained objects, and two-level recursion each have direct failing assertions (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:193-211`). The change has one responsibility and is strategically classified as a **framework primitive**: the FR reports 11 shipped prompt consumers and 14 nested sites, while the existing schema-building abstraction is the defective shared boundary (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:99-115`).

## Required revisions

### R-1: Complete the research gate and make the blast-radius evidence reproducible

Add the required explicit answer: **`is_this_a_graph`: no.** This is deterministic schema-to-Pydantic model construction in the existing loader; it adds no LLM orchestration, routing, prompt artifact, or graph artifact. The current alternatives table is substantive, but the local doctrine requires this answer (`.github/skills/judge-fr/doctrine.md:118-128`).

Replace "two further sites" and the unreferenced scan totals with an exact committed inventory of all 14 nested sites, including file path, field path, declared nested keys, and generated keys before the fix. State the exact reproducible command that produces the inventory. The downstream `yamlgraph-yt-summarizer` observation may remain supporting context, but because no committed artifact or repository path is cited for its 11 chunks, it cannot be an enforcement gate under input closure.

### R-2: Bind the witnesses to existing REQ-YG-044; do not create a new capability

Replace AC-11's "A capability file precedes the witnessing tests" requirement with: all new test functions carry `@pytest.mark.req("REQ-YG-044")`, and `python scripts/req_coverage.py --strict` passes. Schema loading and model building already belong to CAP-12 / REQ-YG-044 (`capabilities/CAP-12-utilities.yaml:13-22`; `ARCHITECTURE.md:737-740`), and the existing JSON-Schema builder tests already use that requirement (`tests/unit/test_schema_loader.py:319-466`). A second capability would duplicate an established responsibility.

### R-3: Correct the FR-458 fallback claim and freeze strict-mode work out of scope

Delete AC-10's statement that the FR-458 case "should no longer arise." The proposed recursion preserves nested properties but does not add `additionalProperties: false`; therefore OpenAI strict schema rejection can still occur, and the function-calling fallback remains an active provider-boundary behavior, not merely a dormant safety net. Require the existing fallback witness `tests/unit/test_fr449_agent_structured_anthropic.py::TestOpenAIStrictSchemaFallback::test_fallback_to_function_calling_on_invalid_json_schema` to pass (`tests/unit/test_fr449_agent_structured_anthropic.py:431-476`).

Keep adding `additionalProperties: false`, changing structured-output retry policy, and modifying `yamlgraph/tools/agent.py` or `yamlgraph/utils/structured_output.py` outside this FR. If the live run exposes a strict-mode issue not handled by the existing fallback, stop and file a separate FR rather than widening this one.

### R-4: Define the supported recursive schema subset and rule out a depth cap

Replace the unqualified "nesting works at any depth" claim with a precise contract: finite inline `output_schema` object specifications recurse through `properties`, including object fields and array items whose type is `object`; nested `required` lists apply at their own object level; an object without `properties` remains `dict`. Arrays of arrays, `$ref`, recursive references/cyclic YAML aliases, combinators such as `oneOf`/`anyOf`/`allOf`, and a new schema-depth policy are not authorized.

Do not add a depth cap in this FR. The measured tree has maximum depth two (`feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md:251-255`), and a cap would introduce a new rejection policy without a current witness. Prove finite recursion at two levels as already required; self-reference and unsupported JSON-Schema constructs require separate evidence and authority.

### R-5: Replace ambiguous verification choices with exact artifacts and commands

Fold the revised acceptance criteria below into the FR. In particular:

- replace `python tmp/scan_nested.py (or equivalent)` with one committed test module and one exact command;
- replace "verified accurate rather than changed — or corrected" with an explicit documentation update describing the supported subset;
- name the exact live example, command, evidence path, and semantic evidence required;
- resolve AC-7's "same commit" ambiguity so the RED witness commit and GREEN implementation commit remain separate as required by repo doctrine; and
- spell out every gate command instead of naming tools only.

No individual edit to the 11 affected prompt files is required. The committed inventory witness covers every declared site, and the `book_reviewer` live run is the one semantic integration witness.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md`: fold R-1 through R-5, exact 14-site inventory, revised acceptance criteria, and later implementation status/decisions |
| D-2 | `yamlgraph/schema_loader.py`: recursive construction only for finite inline `output_schema` object properties and array-item objects |
| D-3 | `tests/unit/test_fr1054_nested_object_schemas.py`: RED/GREEN unit witnesses and the committed real-tree nested-site inventory assertion, all tagged REQ-YG-044 |
| D-4 | `reference/prompt-yaml.md`: explicit nested-object support contract and example, including unconstrained-object behavior |
| D-5 | `examples/book_reviewer/demo-output-fr-1054.log`: one live post-fix run showing populated `criteria` records |
| D-6 | The existing FR-458 fallback test, run unchanged as a regression witness |
| D-7 | One FR-1054 changelog fragment and one `docs/diary/` Distill entry with a `Seed:` |

Not authorized: changes to any existing prompt YAML or graph YAML; the native `schema:`/`fields:` dialect or `resolve_type`; `additionalProperties` policy; provider selection or structured-output retry policy; `yamlgraph/tools/agent.py`; `yamlgraph/utils/structured_output.py`; post-hoc consumer validators from FR-905/FR-908; array-of-array, `$ref`, recursive-reference, cyclic-alias, union/combinator, or schema-depth-limit support; a new capability or requirement ID; broad example rewrites.

## Revised acceptance criteria

- [ ] AC-01: The FR folds R-1 through R-5 before enforcement begins, including the explicit `is_this_a_graph: no` answer and the exact 14-site committed inventory.
- [ ] AC-02: A RED commit adds `tests/unit/test_fr1054_nested_object_schemas.py`, tagged only with `@pytest.mark.req("REQ-YG-044")`, and fails because an array-of-object schema's generated `items` omits its declared properties; the GREEN implementation lands in a later commit.
- [ ] AC-03: The witness module proves both array-item objects and bare object fields preserve declared nested properties in `model_json_schema()`.
- [ ] AC-04: The witness module proves nested `required` semantics by accepting an omitted optional nested key and raising `pydantic.ValidationError` for an omitted required nested key.
- [ ] AC-05: The witness module proves `{"type": "object"}` without `properties` still maps to `dict` and accepts `{}`, including `[{}]` when used as array items.
- [ ] AC-06: The witness module proves finite two-level recursion (object inside array inside object), validates the resulting nested values, and asserts path-derived nested model names are distinct for two sibling fields.
- [ ] AC-07: The witness module scans committed `examples/**/prompts/*.yaml` `output_schema` blocks, compares every declared nested object-property key set with the generated Pydantic JSON schema, reports every mismatch by file and field path, and passes with zero losses. Run exactly `pytest tests/unit/test_fr1054_nested_object_schemas.py -q --no-cov`.
- [ ] AC-08: Existing primitive-field, primitive-array, enum, description, coding-key-normalization, and output-schema-loading behavior remains green under `pytest tests/unit/test_schema_loader.py tests/unit/test_coding_key_normalization.py -q --no-cov`.
- [ ] AC-09: `reference/prompt-yaml.md` explicitly documents recursive finite inline nested object properties, nested `required`, and the distinction between a declared object shape and an unconstrained `type: object` with no `properties`.
- [ ] AC-10: `pytest tests/unit/test_fr449_agent_structured_anthropic.py::TestOpenAIStrictSchemaFallback::test_fallback_to_function_calling_on_invalid_json_schema -q --no-cov` passes unchanged; no strict-mode or `additionalProperties` behavior is changed.
- [ ] AC-11: A live run uses a temporary copy of `examples/book_reviewer/sample_book.md` with `examples/book_reviewer/graph.yaml`; `examples/book_reviewer/demo-output-fr-1054.log` records the command, provider/model, git SHA, successful exit, and at least one `criteria` item with non-empty `name` and `justification` plus an integer `score`, and contains no empty `criteria` object. The log is supporting evidence, not a substitute for AC-02 through AC-10.
- [ ] AC-12: `ruff check yamlgraph/schema_loader.py tests/unit/test_fr1054_nested_object_schemas.py`, `pytest tests/ -q`, `python scripts/req_coverage.py --strict`, and `lint-imports` all exit 0.
- [ ] AC-13: The FR implementation-status section records the RED and GREEN commit SHAs, the exact 14-site scan result, the live-run evidence path, and any deviation from the frozen scope; the changelog fragment and diary Distill entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into the committed FR. | GATE |
| C-2 | Keep implementation to `build_pydantic_model_from_json_schema` and a small private recursive type helper; do not change the native `schema:`/`fields:` path. | GATE |
| C-3 | Use CAP-12 / REQ-YG-044 for every new witness; do not create a capability or requirement for this repair. | GATE |
| C-4 | Preserve unconstrained object behavior and the FR-458 function-calling fallback exactly; strict-schema closure is separate work. | GATE |
| C-5 | Do not add a depth cap or support for arrays of arrays, references, cycles, or JSON-Schema combinators. Encountering one during enforcement stops the work for a separate FR. | GATE |
| C-6 | Do not edit any shipped prompt or graph artifact under this FR; validate the existing declarations through the committed inventory test and the named live example. | GATE |
| C-7 | Preserve RED and GREEN as separate commits and run every exact command in AC-07, AC-08, AC-10, and AC-12 before claiming enforcement complete. | GATE |

Authority granted: after the revisions are folded, the enforcer may add recursive nested-object construction to the JSON-Schema model builder, its REQ-YG-044 witnesses and real-tree inventory assertion, the precise reference documentation update, the named live-run evidence, and the required FR/changelog/diary records—nothing else.
