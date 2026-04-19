# Feature Request: Guardrails Pattern Documentation

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-19

## Summary

Document the guardrails pattern (echo → validate → respond) as Pattern 11 in `reference/patterns.md`. The `openai_proxy` example already implements this pattern, but it is not documented as a reusable pattern that graph authors can discover and apply independently.

## Value Statement

Graph authors learn how to build input validation guardrails directly from the patterns reference, reducing time to implement content moderation and audit-trail pipelines.

## Problem

The guardrails pattern — intercepting user input with echo/audit and validation nodes before the LLM responds — is a production-critical safety pattern. It exists as a working example in `examples/openai_proxy/` but is invisible in the patterns reference. New users building content moderation, compliance, or audit-trail pipelines must reverse-engineer it from example code.

## Proposed Solution

Add **Pattern 11: Input Guardrails** to `reference/patterns.md` between Pattern 10 (Batched Map Processing) and Pattern 12 (Quality Gate for Map Output). The pattern documents:

1. **Problem** — LLM receives raw user input without validation or audit trail
2. **Solution** — Linear pipeline: echo (audit) → validate (content check) → respond (LLM)
3. **Graph YAML** — Complete example showing python tool nodes and LLM node
4. **Python tools** — Echo and validate implementations
5. **Prompt** — LLM prompt that references validation status
6. **Key points** — When to use, extension ideas (content filtering, PII detection, rate limiting)
7. **Related** — Link to `examples/openai_proxy/` and safety-guards demo

### Graph Structure

```yaml
version: "1.0"
name: guardrails-pattern

tools:
  echo_input:
    type: python
    module: myproject.guardrails
    function: echo_input

  validate_input:
    type: python
    module: myproject.guardrails
    function: validate_input

nodes:
  echo:
    type: python
    tool: echo_input

  validate:
    type: python
    tool: validate_input

  respond:
    type: llm
    prompt: respond
    state_key: response

edges:
  - from: START
    to: echo
  - from: echo
    to: validate
  - from: validate
    to: respond
  - from: respond
    to: END
```

## Acceptance Criteria

- [x] Pattern 11 exists in `reference/patterns.md` with heading "## Pattern 11: Input Guardrails"
- [x] Pattern includes Problem, Solution, Graph YAML, Python tools, Prompt, and Key Points sections
- [x] YAML example in pattern is valid YAML (parseable)
- [x] Pattern references `examples/openai_proxy/` as production example
- [x] `examples/README.md` "By Feature" section includes a Guardrails entry
- [x] REQ-YG-254 added to ARCHITECTURE.md
- [x] CAP-106 capability YAML created
- [x] Tests added with `@pytest.mark.req("REQ-YG-254")`
- [x] Changelog fragment created

## Alternatives Considered

- **Dedicated reference page** (`reference/guardrails.md`): Rejected — the patterns page is the canonical location for reusable graph patterns.
- **Only updating examples/README.md**: Insufficient — the pattern needs a structured explanation beyond the example listing.

## Related

- `examples/openai_proxy/` — Production implementation of this pattern
- `examples/demos/safety-guards/` — Related but distinct (execution safety, not input validation)
- Pattern 12 (Quality Gate) — Complementary output-side validation
