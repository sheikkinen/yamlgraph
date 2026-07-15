# Feature Request: FR-732 output_schema Parity — enum, constraints, defaults

**Priority:** MEDIUM
**Type:** Fix
**Status:** Judged
**Effort:** 0.5 day
**Requested:** 2026-07-15
**Judged:** 2026-07-15 — scope frozen; blast radius corrected by two verification finds (parse_json bypass, nested enum)
**Spawned by:** FR-731 F2 (constraint fidelity holds only for the native
`schema:` path) — the reference-doc audit that judgement mandated found
`reference/prompt-yaml.md` promising what `build_pydantic_model_from_json_schema`
does not deliver.

## Summary

`output_schema:` (JSON Schema format) silently drops `enum`, numeric/string
constraints (`minimum`/`maximum`/`minLength`/`maxLength`/`pattern`), and
`default` when building the Pydantic model. The docs claim *"Both formats
produce identical Pydantic models at runtime"* and list enum values as
`output_schema:`'s strength. Raise the implementation to parity where
mechanical, and fix the doc claim to a support matrix.

## Problem

The runtime path is `llm.with_structured_output(output_model)`
(`executor_base.py:397`): the provider sees only the **generated model's**
JSON schema. Consequences today:

1. **`enum` is hollow both ways** — degraded to bare `str`
   (`schema_loader.py`, `elif "enum" in field_def: field_type = str`), so
   values are neither validated client-side nor visible to the provider
   through the schema channel. A model returning `complexity: "trivial"`
   against `enum: [simple, medium, complex]` passes validation and flows
   downstream — the `plausible_wrong_answer` trap, canonized by
   `test_enum_type_becomes_string` (tests/unit/test_schema_loader.py:381),
   which asserts the degradation as correct.
2. **Numeric/string constraints silently dropped** — the builder reads only
   `type`/`description`/`items`/`enum`. Live evidence:
   `examples/npc/prompts/npc_stats.yaml` declares **12 `minimum`/`maximum`
   bounds** (ability scores 1–30) that have never been enforced or sent.
3. **`default` unsupported** — only `None`-for-optional.
4. **Ecosystem workaround fossilized**:
   `examples/cost-router/prompts/classify_complexity.yaml` duplicates its
   enum values in prose and carries the comment *"Schema kept for
   documentation and future use"*.

Commandment 6: no silent fallbacks — a declared constraint that does
nothing must either work or raise.

## Proposed Solution

All changes in `build_pydantic_model_from_json_schema`
(`yamlgraph/schema_loader.py`):

1. **`enum` → `Literal[*values]`** (~3 lines). `Literal` serializes as
   `enum` in `model_json_schema()`, restoring both client-side validation
   and provider-visible constraint. String values only (matching current
   doc examples); non-string enum members raise `ValueError` naming the
   field.
2. **Constraint mapping** (~10 lines):
   `minimum→ge`, `maximum→le`, `exclusiveMinimum→gt`, `exclusiveMaximum→lt`,
   `minLength→min_length`, `maxLength→max_length`, `pattern→pattern` —
   passed as `Field(**kwargs)`, symmetric with the native format's
   `constraints:` block.
3. **`default`** (~3 lines): `field_def["default"]` wins over the
   `None`-for-optional fallback; a field with a default is not required.
4. **Nested `object` properties: explicitly NOT implemented** — stays
   `dict`, same ceiling as the native format. Documented, not raised
   (raising would break existing legitimate dict usage).
5. **Docs**: replace the *"identical Pydantic models"* claim in
   `reference/prompt-yaml.md` with a support matrix (what each format
   enforces vs. drops); update the "When to Use Which" table so enum is an
   honest strength; delete the stale workaround comment in
   `cost-router/classify_complexity.yaml`.

## Example Blast Radius (verified 2026-07-15, `grep -rln '^output_schema:'`)

28 `output_schema:` usages; per-file feature scan
(`awk '/^output_schema:/,0' | grep -c enum/bounds/default`):

**Behavior changes (enum → Literal enforcement) — must be tested:**

*(corrected at judgement — see F1/F2: cost-router and beautify removed)*

| File | New enforcement |
|---|---|
| examples/fsm-router/graphs/prompts/classify.yaml | 1 top-level enum |
| examples/npc/prompts/encounter_decide.yaml | 1 top-level enum |
| examples/npc/prompts/npc_behavior.yaml | 1 top-level enum |
| examples/npc/prompts/npc_identity.yaml | 1 top-level enum |
| examples/npc/prompts/npc_personality.yaml | 1 top-level enum |

**Behavior changes (bounds now enforced):**

| File | New enforcement |
|---|---|
| examples/npc/prompts/npc_stats.yaml | 12 minimum/maximum bounds (1–30 ability scores) |

**No behavior change (plain shapes)**: beautify/mermaid, book_reviewer (2),
dungeon_master (2 + 6 purgatory), fsm-router responses (3),
npc perceive/knowledge/stats-description-only fields, ocr_cleanup.
**No behavior change (F1/F2)**: cost-router/classify_complexity — its node
sets `parse_json: true`, so `output_model = None` and the builder never
runs (docs-comment cleanup only); beautify/analyze — its enum is nested
inside `items: {type: object}`, unreachable while nested objects stay
`dict` (documented in the AC-05 matrix).

**ninchat_voice: NOT affected** — zero `output_schema:` in
`projects/ninchat_voice/` prompts/config (only a SKILL.md doc example and
an FR quote). Its prompts use the native `schema:` format exclusively.

Risk statement: enum/bounds enforcement turns previously-tolerated loose
LLM outputs into `ValidationError` at the structured-output boundary. This
is the intended crash-over-plausible-wrong-answer. Nodes with
`parse_json: true` bypass the model entirely and are untouched (F1).
Providers receiving the enriched schema should comply *more* often, not
less; the residual risk is retry/error-path exercise in examples, covered
by AC-04.

## Acceptance Criteria

- [ ] AC-01 RED — condemning tests: enum value outside `Literal` set raises
      `ValidationError`; `minimum/maximum/minLength/maxLength/pattern`
      survive to `model_json_schema()` (`minimum`/`maximum` keys present);
      `default` honored and field not required.
      `test_enum_type_becomes_string` flipped from canonizing to condemning.
- [ ] AC-02 GREEN — `build_pydantic_model_from_json_schema` implements
      enum→Literal, constraint mapping, defaults; non-string enum members
      raise with field name.
- [ ] AC-03 — parity witness: the same logical schema written in both
      formats produces models whose `model_json_schema()` agree on
      enum/bounds/required/defaults (field-by-field assertion, not dict
      equality — model names differ).
- [ ] AC-04 — blast-radius run: unit suites touching npc and fsm-router
      pass; `yamlgraph graph lint` clean on npc, fsm-router, beautify,
      cost-router graphs; one live smoke of **fsm-router classify** (F1:
      cost-router is parse_json-inert — smoking it would witness nothing)
      recorded in the FR.
- [ ] AC-05 — docs: prompt-yaml.md support matrix replaces the "identical
      models" claim; stale cost-router comment removed.
- [ ] AC-06 — changelog fragment (fix); REQ under CAP-04, id ≥ 556 verified
      free at enforce (`grep -rho 'id: REQ-YG-[0-9]*' capabilities/ | sort`);
      diary reflection.

## Alternatives Considered

- **Docs-only fix (lower the claim):** honest but leaves 12 declared
  bounds and 7 enums dead in shipped examples, and keeps the
  prose-duplication workaround as the recommended pattern. Rejected:
  the constraint is already written where it belongs (the schema); the
  framework just ignores it.
- **Raise on unsupported constructs instead of implementing:** correct for
  what stays unsupported (non-string enums), wrong for enum/bounds — the
  implementation cost is smaller than the migration cost of erroring on
  7 working examples.
- **Recursive nested-object models:** real scope, no current consumer
  (zero nested `properties` in the 28 usages); purged.

## Related

- FR-731 F2 (constraint fidelity through the inline-schema path)
- `yamlgraph/schema_loader.py` — `build_pydantic_model_from_json_schema`
- `reference/prompt-yaml.md` §"JSON Schema Format"
- `tests/unit/test_schema_loader.py` — `TestBuildPydanticModelFromJsonSchema`

## Judgement (2026-07-15)

**Verdict: APPROVED — with 6 findings.** Every blast-radius row was
verified against its consuming node config and the actual schema nesting
before freeze; two rows fell.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **cost-router is inert**: its classify node sets `parse_json: true`, and `llm_nodes.py:101` then forces `output_model = None` — the builder under change never executes. The proposal's AC-04 "live smoke of cost-router" would have smoked a path where the fix is dead code — a witness witnessing nothing | Smoke target moved to **fsm-router classify**; cost-router reduced to the docs-comment cleanup. Risk statement corrected: parse_json nodes bypass entirely |
| F2 | **beautify's enum is nested** inside `items: {type: object, properties: {type: {enum: …}}}` — unreachable while nested objects stay `dict` (which this FR deliberately keeps) | beautify removed from the behavior-change table. The AC-05 matrix must state the ceiling explicitly: *enum is enforced on top-level properties only*; nested/item-level enums remain prompt-prose territory. Scalar-array item enums (`items: {type: string, enum: []}`): zero current usage — NOT implemented, listed in the matrix as unsupported |
| F3 | Proposal pinned "string values only" for enum, but restricting to str costs *more* code than accepting what `Literal` + JSON natively support | Accept str/int/bool enum members (`Literal[*values]` handles all three; all serialize correctly); raise `ValueError` naming the field for dict/list/null members. Minimalism cuts the other way here |
| F4 | `exclusiveMinimum`/`exclusiveMaximum` are boolean in draft-4, numeric in 2020-12 — the mapping table assumed numeric silently | Numeric form only; the boolean draft-4 form raises `ValueError` (loud boundary, zero current usage). Documented in the matrix |
| F5 | `default` + `required` can contradict (a field listed in `required` that also carries `default`) | Default wins — the field becomes optional-with-default, matching both Pydantic semantics (a field with a default is never required) and the native format. One test witnesses the precedence |
| F6 | **Dead config surface found during verification**: `models/node_schema.py` declares node-level `output_schema:` and `schema:` (schema_ref) fields that no node_factory code consumes — declared-but-nonfunctional, the same defect class this FR fixes, one layer up | OUT of scope (no smuggling). Separate proposal to `.chaplain/inbox/`: purge or implement (Commandment 8 — no false idols) |

**Scope frozen.** Enforce order: AC-01 RED (condemning tests incl. the
`test_enum_type_becomes_string` flip) → AC-02 GREEN → AC-03 parity
witness → AC-04 blast-radius run → AC-05/06 paperwork. Purge list stands
(no recursion, no scalar-item enums, no node-level schema work).
