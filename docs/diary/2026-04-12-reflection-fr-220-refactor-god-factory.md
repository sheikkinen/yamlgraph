# Diary: FR-220 — Refactor God Factory

**Date:** 2026-04-12
**FR:** FR-220
**Trap encountered:** working_system_inertia

## Observation

The `compile_node()` function was a 15-branch if/elif chain that "worked" — all tests passed, all node types compiled correctly. The inertia trap whispered: "it works, don't touch it." But Commandment 8 demands entropy be killed, and the function was a textbook case of the Open-Closed Principle violation: every new node type required modifying the dispatch function instead of extending a registry.

## Insight

The refactor was purely structural — no behavioral change for any node type. The key was introducing `NodeCompileContext` as a frozen dataclass to encapsulate all compile-time context, then mapping `NodeType` → handler function in a dict. This made the dispatch O(1) lookup instead of O(n) linear scan, and more importantly, made the set of handled types explicit and auditable.

The "god factory" anti-pattern is a specific instance of the "framework costume" trap: procedural dispatch wearing a function costume. The cure was to make the registry explicit.

## Heuristic

**Registry over elif**: When a function dispatches on a type tag with more than 3 branches, replace with a registry dict. The registry is self-documenting (keys enumerate all cases), testable (verify completeness), and extensible (add entry, not branch).

## Seed

Could the registry pattern be extended to support plugin registration — allowing external packages to register custom node types via entry points? This would complete the Open-Closed arc: new types without modifying YAMLGraph source.
