# Reflection: "Fallback" should require confession, if not outright ban

## Context

Grepping for "Fallback" across the codebase reveals 20+ occurrences spanning error handlers (`on_error: fallback`), message parsing strategies, router race candidates, CI remediation paths, and even a stub `BaseAction` class docstring. The term has become load-bearing infrastructure vocabulary — but its semantics are dangerously overloaded.

## Observation

Every use of "fallback" in production code is a silent substitution: when the primary path fails, quietly use something else. This is exactly the `plausible_wrong_answer` trap from the Scripture Knowledge Graph — the output passes the shape check but is semantically wrong. The hedging check (`scripts/hedging_check.py`) already catches the `x = expr or fallback` pattern at the AST level, and linter W017 warns on `on_error: skip`. But the word "fallback" itself escapes scrutiny.

## The Problem

1. **Semantic overload**: "fallback" means at least four different things — error recovery strategy, default route, stub class, and message parsing last resort. Each carries different risk profiles.
2. **Silent failure legitimization**: Naming something a "fallback" makes silence feel intentional. A crash is visible; a fallback is invisible until production diverges from intent.
3. **Confession gap**: `# noqa` suppressions require CONF-XXX documentation in `docs/confessions.md`. Silent fallbacks have no equivalent accountability mechanism. The hedging check is advisory (`--strict` fails CI, but allowlisted entries bypass without documented rationale).

## Proposed Heuristic

Every use of the word "fallback" in production code should require one of:
- A confession entry (CONF-XXX) documenting what fails silently and why that is acceptable
- An explicit error log at WARNING or higher when the fallback path activates
- Replacement with a more precise term: `default_route`, `stub`, `last_resort`, `degraded_mode`

If it cannot be confessed, it should not exist.

## Trap and Heuristic

- Trap: `plausible_wrong_answer` + `downstream_fix`
- Heuristic: "A named fallback is a silent failure wearing a suit. Require confession or ban the word."

## Seed

Seed: Can `hedging_check.py` be extended to flag the literal word "fallback" in variable names, comments, and docstrings — treating it as a hygiene signal like `# noqa` — with an allowlist-and-confess workflow?
