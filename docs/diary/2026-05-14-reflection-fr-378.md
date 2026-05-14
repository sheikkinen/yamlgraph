# Reflection: FR-378 FR-375 dead helper deduplication (`_handle_optional_exports`)

**Date:** 2026-05-14
**FR:** FR-378
**Branch:** feat/watcher2-gh-378

## Cognitive Process

The task was narrow: remove the duplicate `_handle_optional_exports` definition from `graph_commands.py` and ensure `graph_run_helpers.py` is the single canonical source. The FR-375 helper extraction had already established the alias pattern — `_setup_timeout`, `_teardown_timeout`, `_emit_success_output`, etc. are all aliased from `_graph_run_helpers` at the top of `graph_commands.py`. `_handle_optional_exports` was the only outlier that survived the split.

## Traps Encountered

**Partial remediation trap.** The FR-375 refactor extracted most helpers but left one behind. The symptom was subtle: both modules compiled, both functions behaved identically, and no test caught the duplication. The structural smell was only visible by auditing aliasing patterns across the module. The fix was a one-line alias addition and deletion of the local copy — yet without a targeted acceptance test, the duplication would have survived indefinitely.

**Vulture blind spot.** Vulture (`--min-confidence 60`) did not flag `_handle_optional_exports` in `graph_run_helpers.py` as unused because the symbol name was also defined (and called) in `graph_commands.py`. Name-level dead-code tools cannot detect semantic duplication — two functions with the same name in different modules look like two live symbols. The condemning tests had to be structural (AST / grep), not runtime behavior tests.

## Heuristic

> **Alias pattern completeness check.** When a module uses an alias block to re-export helpers from a submodule, audit whether *all* helpers that logically belong to the submodule are included in that alias block. An outlier local implementation signals an incomplete refactor, not a deliberate boundary.

## Seed

**Seed:** Is there a lightweight static analysis rule (e.g., import-linter contract, custom ruff plugin, or AST walker in CI) that could detect "function defined locally that matches name+signature of a function in the designated helper module"? Automating the alias-completeness check would turn this class of structural debt into a failing gate rather than a code-review concern.
