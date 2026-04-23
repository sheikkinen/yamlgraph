# FR-276: Test Architecture Fix — Diary Reflection

**Date:** 2026-04-23
**FR:** FR-276
**Type:** Feat

## Cognitive Process

The implementation path had two distinct phases:
1. **Bash script enhancement** — Adding PR reuse logic to `create_pr.sh` using existing patterns
2. **Test architecture overhaul** — Discovering the acceptance tests were fundamentally impossible to pass

The implementation was straightforward, following the established pattern from `.chaplain/watch.sh:183-186`. However, the tests revealed a deeper architectural issue: Python's `unittest.mock.patch("subprocess.run")` intercepts the outer bash execution, not the commands within the script.

## Trap: Infrastructure Exempt from Its Own Rules

The original test design exempted itself from the rule "use real command execution patterns." Instead of following established shell testing patterns in the codebase, it applied Python mocking to a bash context. This is the "infrastructure self-exempt" trap — the test infrastructure didn't follow the same execution patterns it was meant to verify.

## Insight: PATH-Based Command Stubbing

The solution uses PATH-based command stubbing: create temporary fake executables that log calls and respond appropriately, then prepend their directory to PATH. This allows the bash script to run normally while intercepting system calls — a pattern already used elsewhere in the codebase.

**Key heuristic:** When testing shell scripts, use the shell's own mechanisms (PATH, filesystem) rather than language-specific mocking frameworks.

## Verification Pattern

The fix validated both aspects:
- **Behavioral**: All 5 acceptance tests pass, proving the implementation matches requirements
- **Architectural**: PATH-based mocking works for any shell script, not just this one

This establishes a reusable pattern for testing bash scripts throughout the codebase.

## Seed

Could we create a test helper library for PATH-based command stubbing? A pattern like `with_mock_commands({"gh": mock_gh_script, "jq": mock_jq_script})` would reduce boilerplate and standardize this approach for future shell script tests.
