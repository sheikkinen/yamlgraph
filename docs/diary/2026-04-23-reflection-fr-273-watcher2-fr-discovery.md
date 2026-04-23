# Diary: FR-273 Watcher2 FR Discovery Bug

**Date**: 2026-04-23
**FR**: FR-273 (Phase 5 prerequisite)
**Trap**: downstream_fix — symptom manifested in enforcement picking wrong FR, but root cause was missing state propagation from plan step

## Insight

The watcher2 pipeline used `find feature-requests/ | head -1` to discover which FR to enforce. In a worktree containing 200+ historical FR files, this returns an arbitrary file — not the one just created by the plan step.

The plan step correctly created FR-268 for gh-180, but the enforce step picked FR-246 (A2A docs) because `find` doesn't guarantee order and `head -1` takes whatever comes first.

## Heuristic

**Pipeline state must flow forward explicitly.** When step N creates an artifact that step N+M consumes, the path must be captured at creation time — not re-discovered by searching a directory containing historical artifacts. `find | head -1` in a directory with accumulated state is always a bug.

## Seed

Could the pipeline state JSON carry a `created_artifacts` list that each step appends to, making the full provenance chain inspectable at any point?
