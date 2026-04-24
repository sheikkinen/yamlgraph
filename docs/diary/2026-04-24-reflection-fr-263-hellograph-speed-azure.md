# Reflection: FR-263 Hellograph Speed Azure Variant Demo

**Date:** 2026-04-24
**FR:** FR-263 (Azure OpenAI Provider)
**Scope:** Adding Azure variant to the hellograph-speed multi-provider comparison demo

## Cognitive Process

The hellograph-speed demo already existed for Google/Vertex providers. Adding an Azure variant
was straightforward YAML work — the provider abstraction in `llm_factory.py` means a new demo
graph is just a `provider: azure` declaration.

## Trap: Branch Divergence from Stale Remote

The branch had diverged from its remote tracking branch because main had been rebased into it
locally but the remote still pointed at the old fork point. The fix was a force push after
confirming local was correct and ahead.

## Trap: Pre-existing Test Failures Block Unrelated Commits

Pre-commit hooks run the full test suite. The `test_fr275` tests used hardcoded `"python"` binary
which doesn't exist on macOS (only `python3`). This blocked committing the changelog fix even though
the change was unrelated. Fix: commit the test fix (`sys.executable`) first.

## Heuristic

**Boundary normalization applies to subprocess calls too.** Just as LLM provider responses must be
normalized at the boundary, subprocess invocations must use `sys.executable` — the Python binary
name is an OS-level boundary where the assumption `python == python3` breaks.

## Seed

Could the pre-commit test gate run only tests affected by the changed files (pytest --co + dependency
analysis) instead of the full suite? This would prevent unrelated failures from blocking commits
while maintaining the safety net.
