# Diary Reflection: FR-319 — Lint Unanchored Prompt Variables

**Date:** 2026-05-03
**FR:** FR-319

## Trap

**Silent contract drift.** A graph node declares `variables:` that its prompt never references. The variable value vanishes silently — the LLM improvises a target from ambient context instead of the intended input.

This is `plausible_wrong_answer` from the Knowledge Graph: output passes shape check but is semantically wrong.

## What Happened

Issue #306 reported that `fr_path` was passed to a prompt but never rendered. The LLM picked an unrelated FR from context. No lint warning, no runtime error — completely silent failure.

## Root Cause

The linter validates missing variables (E001/E002) but had no inverse check: declared node variables that the prompt template never references. The runtime (`validate_variables`) only enforces missing required vars. Extra variables are accepted and ignored per `test_validate_extra_variables_ok`.

## What Worked

- Pattern match to existing `W001` (unused tool references) provided the implementation template.
- `extract_variables()` in `template.py` already handles both `{key}` and `{{ key }}` syntax.
- Judge AMEND loop enforced TDD: plan had to write acceptance tests before approval was granted.
- Third plan attempt succeeded after two revisions.

## Seed

Should the linter distinguish between "variable declared but unused by prompt" (current W023) and "variable declared, unused by prompt, but referenced via `{{ state.key }}`" — are these semantically different enough to warrant separate codes?
