# Diary Entry: The Pre-Existing README Trap

**Date:** 2026-03-10
**Author:** Copilot Enforce Agent
**Context:** FR-182 Hello Demo Documentation (smoke test)

## Trap: TDD Against Pre-Existing Artifacts

When the acceptance criteria (`README.md exists`, `run command documented`) are already satisfied by pre-existing code, writing tests that immediately pass violates the RED-GREEN spirit. The temptation is to declare victory and skip the cycle.

**Classification:** `working_system_inertia` — "'It works' blocks seeing it clearly."

## Cure: Discover the Undocumented Gap

The CLAUDE.md quickstart showed `yamlgraph graph lint` as a validation step, but the hello README omitted it. This gap created a legitimate RED test that drove a real improvement. The principle: even documentation-only FRs benefit from measuring against the broader ecosystem (CLAUDE.md, demo.sh, reference/) rather than just the stated ACs.

## Heuristic

**Documentation TDD needs a broader oracle.** When testing docs, don't just test what the FR says — test what the ecosystem implies. Cross-reference quickstarts, CLI help, and sibling demos to find genuine gaps.

## Seed

Could a linter rule (W018?) automatically verify that every demo README documents all CLI verbs used by that demo's `demo.sh` entry? The `demo_hello()` function calls `run_demo` with specific args — the README should mirror those.
