# Reflection: FR-321 Validate-Fix Gate Diagnostics Handoff

**Date:** 2026-05-04
**FR:** FR-321
**Issue:** gh-318

## Cognitive Process

The validate_fix ↔ validate_gate loop ran 5+ times across multiple issues (gh-304, gh-306, gh-308, gh-318) always failing on diary_parity. The copilot CLI completed in 5-6 seconds — too fast to have done anything. The pattern was consistent: validate_gate caught the problem, but validate_fix never received the diagnostics.

## Trap Encountered

**downstream_fix** — The symptom appeared as "diary-gate failure" but the root cause was upstream: the pipeline config never passed `validate_gate_output` to validate_fix. The LLM saw either a literal `{precommit_output}` placeholder (first pass) or all-green pre-commit output (subsequent passes), so it returned PASS immediately without acting.

**plausible_wrong_answer** — The LLM output passed shape check (exit code 0, no errors) but was semantically wrong: it declared success without fixing anything. The 5-6 second execution time was the signal.

## Insight

Normalize at the boundary where external data enters. The validate_gate action stored diagnostics in context but the pipeline config was the boundary that needed to shuttle them to the next action. A missing variable declaration at the config boundary caused a complete feedback loop failure.

## Seed

Should the FSM engine warn when a context variable is stored but never referenced in any downstream action's vars? A "dead variable" lint could catch this class of plumbing bugs.
