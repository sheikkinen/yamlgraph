# Reflection: FR-331 Static Module Map for Tier-2 Context

**Date:** 2026-05-05
**FR:** FR-331
**Tags:** context-building, static-analysis, ast, documentation, orientation

## What Was Built

A deterministic AST-based module map generator (`scripts/generate_module_map.py`) that produces
`reference/module-map.md` — a structured index of `yamlgraph/` modules including exports,
signatures, import dependencies, and a module-to-test mapping. Wired into `CLAUDE.md` so
enforcement agents have immediate structural orientation.

## Cognitive Traps Encountered

**Trap: Over-scoping under time pressure.**
The first impulse was to include a dynamic context planner (LLM-based relevance classifier) in
scope. The research phase clarified that the static map is the independently judgeable minimal
unit; the LLM classifier is a separate problem that requires the static map as a prerequisite.
The split saved the feature from speculative extensibility.

**Trap: Treating the artifact as documentation, not as a gate artifact.**
Initial framing treated `reference/module-map.md` as "just docs." The correct framing: it is a
machine-readable contract with the generator as the single source of truth. Tests enforce the
contract's shape (sections, test-map determinism, AC checklist), not just the file's existence.

**Trap: Skipping test-map determinism verification.**
A naïve implementation could produce different module→test path orderings across runs (dict
iteration order, filesystem walk order). Locking the output to sorted traversal at the script
level made determinism an enforced property rather than an accidental one.

## Heuristics Learned

**Heuristic:** When a static artifact is generated from live source, the generator is the
source of truth and the artifact is its read replica. Test the generator contract (inputs →
deterministic output shape), not the artifact's transient content.

**Heuristic:** Minimal-scope research gates (is the problem already solved elsewhere in the
codebase?) prevented re-inventing what `ast.parse()` already covers — the same pattern used in
`scripts/req_coverage.py` and `scripts/hedging_check.py`.

## What Went Well

- Stdlib-only approach kept dependency surface flat (AC-06 trivial to satisfy).
- TDD red→green cycle was fast because the acceptance criteria were mechanically precise.
- Referencing the existing diary research files (`2026-05-05-research-context-building.md`) as
  planning context avoided duplicate discovery work.

## Seed

If the static module map proves high-value for orientation, the natural next question is:
**Can the map be used as a retrieval index — filtered by "changed files in this PR" — so an
enforcement agent receives only the modules actually in scope, rather than the full tree?**

That would be the smallest step toward dynamic Tier-2 context selection without requiring an
LLM classifier at all (pure structural filter).
