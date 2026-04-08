# Reflection: Import-Linter and the Missing Boundary

**Date:** 2026-04-08
**Trigger:** Philosopher asked to reflect on import-linter and whether it belongs in the Scripture.

## Cognitive Process

The question arrived as a tool name, not a problem statement. First move: find where it was mentioned.
Found it in `docs-planning/how-to-critical-analysis.md` — a planning document, never enacted.

That location is itself the trap: `detection_without_enforcement`. The tool was *researched*,
*documented*, but never *contracted*. The three-layer architecture exists as a diagram in
ARCHITECTURE.md and a paragraph in CLAUDE.md. No mechanical gate enforces it.

## The Gap Revealed

The Knowledge Graph `boundaries` list covers every data-flow boundary:
- `schema` — LLM output shape
- `provider` — API response normalization
- `state` — graph state commits
- `streaming` — token shape/timing
- `platform` — OS differences
- `audit` — Inquisitor findings

But not **module structure**. The architectural layers are the oldest boundary in the system —
and the only one without a contract.

## Trap Named

**`architecture_as_diagram`**: Drawing the three-layer box and labeling it "enforcement" is not
enforcement. The diagram is a wish. The `.importlinter` contract is the law. Until import-linter
runs in CI, any module can import any other module and the violation will be invisible until
something breaks at runtime or audit.

## What Was Done

1. Wrote FR proposal to `.chaplain/inbox/` — the Chaplain will generate the full FR (FR-218).
2. Amended the Knowledge Graph in `.github/copilot-instructions.md`:
   - Added `module_structure` to `boundaries`
   - Added `architecture_as_diagram` to `traps`

## Heuristic

> A boundary claimed in documentation but absent from CI is indistinguishable from no boundary at all.

## Seed

If import-linter reveals existing violations when first run, are those violations evidence of
architectural drift, or evidence that the diagram was always aspirational? What does the delta
between "claimed architecture" and "actual import graph" tell us about the health of a codebase?
