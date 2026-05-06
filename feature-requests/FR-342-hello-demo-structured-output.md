# Feature Request: FR-342 Structured output for hello world demo

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-06

## Summary

Add an inline prompt schema to `examples/demos/hello/prompts/greet.yaml` so the hello demo returns structured greeting output with `greeting`, `emoji`, and `formality_level`, then refresh demo proof artifacts and directly coupled tests to validate the new contract.

## Value Statement

YAMLGraph maintainers and new users get a canonical first demo that visibly enforces schema-based outputs, proving the "typed LLM output" doctrine at the smallest possible surface.

## Problem

GitHub issue #342 requests structured output for the canonical hello demo to serve as a full-pipeline acceptance signal. Today, `examples/demos/hello/prompts/greet.yaml` has no inline schema, so the node returns raw text instead of typed fields.

Current gaps:

1. The hello prompt is untyped (`system` + `user` only), despite framework support for inline schema-based structured output.
2. The hello demo is used as a canonical smoke path in docs/tests, so it is the right place to encode the doctrine but currently does not.
3. Existing `examples/demos/hello/demo-output.log` does not demonstrate successful structured fields and currently contains a failed run.

## Research: Existing Patterns and Prior Art

1. **Framework support already exists (no runtime feature work needed).**
   - Inline prompt schema is already supported through node output-model resolution:
     - `yamlgraph/node_factory/base.py` (`get_output_model_for_node` loads schema from prompt YAML)
     - `yamlgraph/executor.py` (`llm.with_structured_output(output_model)` path)
   - Prompt schema usage is documented in `reference/prompt-yaml.md`.

2. **Many examples already use inline schema; hello demo is an outlier.**
   - Existing schema-bearing prompts appear across demos/examples (for example `examples/questionnaire/prompts/opening.yaml`, `examples/demos/router/prompts/classify_tone.yaml`).
   - `examples/demos/hello/prompts/greet.yaml` currently lacks `schema:`.

3. **Hello demo is a shared smoke fixture, so contract changes must be explicit.**
   - Hello graph appears in multiple integration/unit paths (for example `tests/integration/test_native_streaming.py`, `tests/integration/test_fr323_vertex_gemini31_hello_smoke.py`, `tests/integration/test_thinking_budget_integration.py`).
   - At least one test currently assumes scalar greeting content (`"World" in result["greeting"]`), which will require direct, scoped assertion updates when greeting becomes structured.

4. **Requested topic source file is missing in this worktree.**
   - Requested input `.chaplain/processing/gh-342.md` is not present on this branch.
   - Canonical planning source used: GitHub issue #342.

## Objectives

1. Make hello demo output structured fields (`greeting`, `emoji`, `formality_level`) via inline prompt schema.
2. Keep the change minimal and demo-scoped (no new node types, no runtime abstraction changes).
3. Provide executable proof via updated demo output artifact and acceptance tests.

## Constraints

1. Scope must remain limited to hello demo assets and directly coupled tests/documentation.
2. Use inline `schema:` in prompt YAML (not new Python schema classes).
3. Do not add dependencies, new graph nodes, or provider/runtime refactors.
4. Preserve demo-gate expectations by updating `demo-output.log` with a successful run that demonstrates the structured contract.

## Proposed Solution

### In scope

1. Update `examples/demos/hello/prompts/greet.yaml`:
   - add `schema:` with fields:
     - `greeting: str`
     - `emoji: str`
     - `formality_level: str`
2. Update `examples/demos/hello/graph.yaml` only if needed for schema-compatible state naming/clarity.
3. Refresh `examples/demos/hello/demo-output.log` with successful execution evidence reflecting structured output fields.
4. Update directly coupled tests that currently assert scalar greeting where required by the new output shape.

### Out of scope

1. Changes to YAMLGraph runtime schema/executor internals.
2. Changes to non-hello demos (`hellograph-speed`, `mastra-integration`) in this FR.
3. New CLI flags, new node types, or provider-specific behavior changes.

## Acceptance Criteria

- [x] **AC-01:** `examples/demos/hello/prompts/greet.yaml` contains inline `schema:` with `greeting`, `emoji`, and `formality_level` fields.
- [x] **AC-02:** Running hello demo returns structured output (mapping/object), not raw scalar greeting text.
- [x] **AC-03:** `examples/demos/hello/demo-output.log` is refreshed and includes evidence of successful run with structured greeting fields.
- [x] **AC-04:** Directly coupled tests/assertions for hello output shape are updated and pass with the structured contract.
- [x] **AC-05:** No runtime feature changes outside demo-scoped files and directly coupled tests/docs.

## Failing Acceptance Tests (RED)

Create:

- `tests/integration/test_fr342_hello_structured_output_demo.py`

Planned RED tests:

1. `test_ac01_greet_prompt_defines_inline_schema_fields`
2. `test_ac02_hello_graph_returns_structured_greeting_fields`
3. `test_ac03_demo_output_log_contains_structured_success_evidence`
4. `test_ac04_hello_coupled_contract_tests_expect_structured_shape`

RED commands (expected to fail before implementation):

```bash
pytest tests/integration/test_fr342_hello_structured_output_demo.py -q --no-cov
rg -n "schema:|formality_level|emoji" examples/demos/hello/prompts/greet.yaml
rg -n "formality_level|emoji|greeting:" examples/demos/hello/demo-output.log
```

## Alternatives Considered

1. **Keep hello as raw text and only document schemas elsewhere**
   - Rejected: does not satisfy issue #342 or provide pipeline-level proof on the canonical starter demo.

2. **Use `output_schema` JSON Schema instead of native `schema:`**
   - Rejected: valid format, but issue asks inline schema and existing doctrine/examples frequently use native `schema:`.

3. **Apply same schema change to all similar greet prompts (`hellograph-speed`, `mastra-integration`) now**
   - Rejected: expands scope beyond single-responsibility hello demo change.

## Related

- GitHub issue #342: <https://github.com/sheikkinen/yamlgraph/issues/342>
- `examples/demos/hello/prompts/greet.yaml`
- `examples/demos/hello/graph.yaml`
- `examples/demos/hello/demo-output.log`
- `reference/prompt-yaml.md`
- `yamlgraph/node_factory/base.py`
- `yamlgraph/executor.py`
- `tests/integration/test_fr323_vertex_gemini31_hello_smoke.py`
- `tests/integration/test_native_streaming.py`
- Topic source requested: `.chaplain/processing/gh-342.md` (not present in this worktree)
