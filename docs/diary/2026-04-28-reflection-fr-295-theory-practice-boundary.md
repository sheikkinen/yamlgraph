# Reflection: FR-295 — The Theory-Practice Boundary

**Date:** 2026-04-28
**FR:** FR-295 (Watcher-FSM Phase 2: Single-Worker Validation)

## Cognitive Trap: Untested Theory Feels Like Progress

Phases 0–1.5 delivered configs, actions, tests, and path alignment. Each merged PR added confidence. But none of them ran the FSM for real. The unit tests mock everything — they prove the wiring is correct in isolation, not that the system works.

The trap: **passing unit tests feel like completion**. The FSM had never processed a single topic, yet the plan showed 3 phases "complete." Phase 2 is where theory meets reality.

## Insight: The Validation Script Is The Test

The judgement caught this: "Tests added" was vague. For an integration run, the validation script *is* the proof. Inventing unit tests for an end-to-end integration would be testing the test — infinite regress. The script runs, the PR merges, the worktree cleans up. That's the assertion.

## Heuristic

**Demo vs. test boundary**: Unit tests prove constraints hold in isolation. Integration scripts prove the system works as a whole. Don't force one paradigm where the other belongs.

## Seed

When the FSM processes its first real topic, will the LLM outputs match what watcher2.sh would have produced? If not, is the divergence a bug or an improvement? How do you define "same outcome" when LLMs are non-deterministic?
