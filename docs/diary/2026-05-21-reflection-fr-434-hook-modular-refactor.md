# Reflection: FR-434 modular post-edit hooks

## Trap
Monolith growth was already visible, but change cost stayed hidden because each new requirement still had a place to fit. That delayed boundary extraction.

## Insight
Splitting by concern with a shared helper reduced coupling without changing behavior. The key was preserving input normalization and output format at the boundary.

## Heuristic
When a hook script starts carrying unrelated concern branches, split by event-purpose first and share only parsing/logging primitives.

Seed: Should we add a structural gate that fails when any hook script exceeds a line-budget threshold unless a modularization exception is documented?
