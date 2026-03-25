# Feature Request: FR-203 Linter E302 — Accept `state_key` as Valid Interrupt Text Source

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-25

## Judge Verdict: APPROVE

**Date:** 2026-03-25
**Verdict:** APPROVED — Scope frozen. Authority granted to implement.

### Evaluation

| Criterion | Assessment |
|-----------|-----------|
| Scope clear and minimal? | ✅ Yes — single-rule linter bugfix confined to E302 interrupt validation |
| Contradictions or ambiguities? | ✅ No — `state_key` is already a real interrupt concept and the draft keeps W302/E303 behavior distinct |
| Acceptance criteria measurable? | ✅ Yes — all criteria are verifiable by unit tests and `yamlgraph graph lint` output |
| Implementation approach feasible? | ✅ Yes — a small conditional/message update plus test coverage |
| Aligned with architecture? | ✅ Yes — matches existing interrupt semantics and the linter's role as a structural validator |
| Single responsibility? | ✅ Yes — one concern only: stop false-positive E302 errors for interrupt nodes using state-backed text |

### Implementation Note

The proposed change is correctly scoped to `E302` only. `W302` remains the "both
prompt and message" warning, and `E303` continues to validate that `state_key`
is declared in the graph state. No broader interrupt-node redesign is implied.

## Summary

The E302 linter rule falsely flags interrupt nodes that source their display text from
`state_key` (pre-computed state) rather than from an inline `prompt` or `message` field.

## Value Statement

Graph authors using the questionnaire pattern (schema-driven multi-turn flows) get ~30
false E302 errors across the codebase eliminated, restoring linter signal-to-noise ratio.

## Problem

The questionnaire pattern (interrai-ca, medical triage, PHQ-9, etc.) separates generation
from display: a preceding LLM node (e.g. `generate_opening`) writes a response into
`state.response`, then the interrupt node reads it back via `state_key: response`.
There is no inline `prompt` or `message` because the text already lives in state.

The current E302 check in `yamlgraph/linter/patterns/interrupt.py` lines 42–53:

```python
has_prompt = "prompt" in node_config
has_message = "message" in node_config

if not has_prompt and not has_message:
    # fires E302 — false positive when state_key is present
```

This produces approximately 3 false errors per questionnaire graph × ~10 graphs
= **~30 false E302 errors** across `questionnaire-api/`, masking real lint issues.

## Proposed Solution

Extend the E302 guard to treat `state_key` as a third valid text source.
An interrupt node is valid when it has **any** of: `prompt`, `message`, or `state_key`.

```python
# yamlgraph/linter/patterns/interrupt.py  (check_interrupt_node_structure)
has_prompt = "prompt" in node_config
has_message = "message" in node_config
has_state_key = "state_key" in node_config

if not has_prompt and not has_message and not has_state_key:
    issues.append(
        LintIssue(
            severity="error",
            code="E302",
            message=f"Interrupt node '{node_name}' missing 'prompt', 'message', or 'state_key' field",
            fix="Add 'prompt' (LLM-generated), 'message' (static text), or 'state_key' (pre-computed state)",
        )
    )
```

Example valid interrupt node using `state_key`:

```yaml
nodes:
  ask_question:
    type: interrupt
    state_key: response     # text already in state — valid, no E302
    resume_key: user_answer
```

## Acceptance Criteria

- [ ] `check_interrupt_node_structure` does **not** emit E302 when `state_key` is present
      and neither `prompt` nor `message` is present
- [ ] E302 is still emitted when none of `prompt`, `message`, `state_key` are present
- [ ] W302 (both prompt and message) logic is unchanged
- [ ] E302 error message and `fix` hint updated to mention `state_key` as valid option
- [ ] Existing test `test_missing_prompt_or_message` updated to cover the new three-way
      guard, and a new test `test_state_key_satisfies_e302` added
- [ ] Running `yamlgraph graph lint` on `questionnaire-api/` graphs produces 0 E302 errors
- [ ] `pytest tests/unit/test_linter_patterns_interrupt.py` passes

## Alternatives Considered

- **Suppress E302 on interrupt nodes entirely** — too permissive; nodes with none of the
  three fields are still genuinely misconfigured.
- **New error code for missing-all-sources** — unnecessary complexity; E302 already
  captures the "no display text source" failure. Updating the message is sufficient.

## Related

- `yamlgraph/linter/patterns/interrupt.py` lines 42–53
- `tests/unit/test_linter_patterns_interrupt.py`
- `questionnaire-api/` graphs (current false-positive victims)
- E303 check in the same file (correctly handles `state_key` for state declarations)
