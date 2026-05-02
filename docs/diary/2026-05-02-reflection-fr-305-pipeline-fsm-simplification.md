# Diary: FR-305 Watcher Pipeline FSM Simplification

**Date:** 2026-05-02
**FR:** FR-305
**Outcome:** Implementation complete, 43 tests passing, all validators green

## Cognitive Process

The FR was well-specified with a clear state diagram. Most of the implementation already existed (v2 config, enforce graph, plan unified graph). The key missing piece was the **judge model independence** requirement — the existing `step-judge.yaml` resumed the plan session with the same model, violating the FR's core design principle.

## Trap Encountered: Working System Inertia

The existing judge graph "worked" (it would produce verdicts), but it violated the architectural requirement of independent evaluation. The temptation was to skip the judge refactor since the existing graph would technically function. The trap: `working_system_inertia` — "'It works' blocks seeing it clearly."

The cure: create `step-judge-v2.yaml` as a separate artifact that explicitly breaks the session link and uses a different model. The v1 judge graph remains for the old pipeline.

## Trap Encountered: Mechanical Terminal State

The FSM validator caught that `done` (operational state) emits `completed` but had no transition target. The FR said "2 terminals only" but the FSM engine requires a mechanical terminal state for the pipeline to exit. The resolution: add `completed` as the third terminal (pragmatic over dogmatic).

## Insight: Validator as First Reviewer

Running `statemachine-validate --strict` immediately after creating the config caught the missing terminal state before any manual review or runtime testing. The validator is faster and more reliable than human review for structural correctness. This pattern (`spec_kill`: "Cheapest bug is the one killed in the spec") applies to all declarative config.

## Seed

**What would a property-based test look like for FSM reachability?** Given the state graph, can we automatically verify that all operational states can reach at least one terminal state, and that no operational state is a dead end? This would catch the `completed` missing-transition bug at the test level rather than relying on the validator.
