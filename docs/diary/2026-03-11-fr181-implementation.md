# 2026-03-11: FR-181 Implementation — Python→YAML LLM Migration Complete

**Date:** 2026-03-11
**Feature:** FR-181 (and FR-178) — Eliminate `execute_prompt()` from probe_recap

## What Happened

The session completed FR-181: the `extract_answers` Python tool node that called
`execute_prompt()` directly was replaced in **both** outcaller and incaller. The
fix follows the canonical split pattern:

1. `extract_answers` → `type: llm`, writes structured output to `extraction_result`
2. `merge_extraction` → `type: python`, reads `extraction_result` from state, merges non-null values into `extracted`, increments `probe_count`

The edge fan was updated: `extract_answers → merge_extraction → [goodbye_refused | check_missing]`.

Tests extended in `tests/unit/test_probe_recap.py` covering `parse_targets`,
`merge_extraction`, `check_missing`, and `apply_corrections` — all pure functions,
no LLM mocking needed. FR-181 status moved from Approved → Implemented.

Alongside: FR-179 (Asterisk ARI + AudioSocket provider) was written into
`feature-requests/` — currently in Amend cycle. FR-185 (NC Voice barrier state
naming + I/O activity logs) was written and approved but not yet started.

A merge conflict in `docs/diary/2026-03-10-chaplain.md` (Added/Added on both
branches) was resolved by keeping both entries: FR-179 Changelog Approved and
FR-178 Eliminating Python Execute Prompt are separate chaplain cycles on the same
date.

## Cognitive Traps

**working_system_inertia**: The outcaller had carried the `execute_prompt()`
anti-pattern for multiple sessions because it _worked_. `OC-012` added a
`metadata: provider: google` guard as a stopgap rather than addressing the root
cause. The trap: "it works" blocked seeing the structural defect.

**partial_remediation**: The incaller copy of `extract_answers.yaml` lacked
the `metadata: provider: google` header that outcaller had. The fix was applied
to incaller only after the outcaller version exposed the pattern. Partial fixes
leave sibling copies in inconsistent states — the diff shows the incaller prompt
needed the same `metadata` block added.

**symptom_patch vs. root_cause**: The provider guard was a symptom patch. The
three-layer architecture is the constraint: LLM calls belong in YAML graph nodes,
not Python tools. The boundary is where normalization happens.

## What I Learned

The `llm node + merge node` split is the idiomatic pattern when a Python tool was
previously doing: (a) call LLM, (b) apply business logic to result. The two
responsibilities are now separated at the correct layer boundary. This also makes
testing _cheaper_: `merge_extraction` tests stub `extraction_result` directly in
state — no `execute_prompt` mock chain needed.

The `extraction_result` intermediate state key is intentional: it is the raw LLM
boundary output, present in state for observability (LangSmith traces the llm
node's span), before the pure Python node applies merge logic.

When a FR status moves Approved → Implemented, the acceptance criteria checklist
serves as a mechanical review record. Every criterion was checked in sequence —
not just "tests pass" globally, but each criterion independently. This prevents
the plausible_wrong_answer trap where a passing test suite masks an unchecked
criterion.

## Seed

The `merge_extraction` pattern (llm node → state key → pure Python merge) will
recur anywhere structured LLM output must be merged into existing state. Should
this become a first-class YAML node type (e.g., `type: merge`) that declaratively
specifies the source state key and merge strategy (non-null overwrite, list
append, etc.)? What would the minimal YAML schema look like, and where in the
graph loader would the merge logic live?
