# Diary: FR-221 — Ruff C901 Cognitive Complexity Gate

**Date:** 2026-04-12
**FR:** FR-221
**Trap encountered:** detection_without_enforcement

## Observation

The codebase had radon CC gating at grade D (≥ 21), which counts branches but ignores nesting depth. Functions with deeply nested closures — like `create_node_function` at C901=35 — sailed through radon while being genuinely hard to reason about. The gap between "measured" and "enforced" created false confidence: the metric was green, but the complexity was real.

## Insight

Enabling C901 at threshold 15 exposed 16 violations in `yamlgraph/`. Most were genuinely complex functions that deserved refactoring. The key decision was separating refactoring (reducing complexity below 15) from confession (documenting why a function legitimately needs its complexity). Three functions received `# noqa: C901` with confessions: they're integration points where complexity is inherent, not accidental.

The per-file-ignores for `examples/`, `projects/`, and `scripts/` was a scoping decision, not an exemption. FR-221 explicitly targets the core package; extending enforcement to examples is a future FR.

## Heuristic

**Gate at the boundary, not the report**: A lint rule without a blocking gate is advisory at best, misleading at worst. When adding a new lint check, wire it into the pre-commit/CI gate in the same commit. Detection and enforcement must ship together.

## Seed

Could the C901 threshold be made progressive — starting at 15 for new functions but allowing existing functions a grace period with per-function thresholds that ratchet down over time? This would incentivize gradual improvement without blocking all work.
