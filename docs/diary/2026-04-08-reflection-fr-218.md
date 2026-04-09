# Reflection: FR-218 Import-Linter Code Review

**Date:** 2026-04-08
**Trigger:** Code review of PR #82 — FR-218 import-linter architectural boundary enforcement.

## Cognitive Traps Encountered

**`infrastructure_self_exempt`**: The pre-commit hook hardcoded `.venv/bin/lint-imports`. The
guardrail was fragile by the exact pattern it was meant to prevent: trusting a path that only
works in one specific environment. CI uses system PATH; the hook assumed `.venv/`. Fixed by
using `PATH="$PWD/.venv/bin:$PATH" lint-imports`, which works in both environments.

**`silent_unmonitored`**: Three top-level modules (`mcp_server`, `a2a_server`, `a2a_message`)
were absent from every layer declaration in `.importlinter`. import-linter silently ignores
modules not assigned to any layer — meaning violations in those files would never be caught.
The contract appeared complete but had blind spots. Lesson: verify coverage, not just passage.

**`internal_api_coupling`**: The test called `importlinter.cli.lint_imports_command` via
`subprocess -c`. This coupled the test to an internal symbol that could be renamed without
breaking the tool. The correct approach is `Path(sys.executable).parent / "lint-imports"` —
the same binary the pre-commit hook and CI invoke.

## Heuristic

> A passing contract that excludes modules is not enforcement — it is selective enforcement.
> Audit coverage before trusting a gate.

## Seed

When a new module is added to the codebase, how do we ensure it is assigned to exactly one
layer in `.importlinter`? Could `req_coverage.py` or a separate check verify that every
`yamlgraph/*.py` file appears in the contract — so the silent exclusion trap is caught at
commit time rather than at review time?
