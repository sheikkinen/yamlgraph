# Diary: FR-310 — Separation of Enforcement and Quality Gating

**Date:** 2026-05-03
**FR:** FR-310
**Trap:** infrastructure_self_exempt, downstream_fix

## What Happened

The enforce copilot session was responsible for both implementing code AND running pre-commit/pytest quality gates on its own output. This is the equivalent of letting a student grade their own exam. The pipeline appeared to work — the agent would run pre-commit, see failures, fix them, and report success — but there was no mechanical guarantee that the gate was actually passed. The agent could skip checks, misreport results, or get stuck in an infinite self-repair loop without the FSM knowing.

## The Trap Chain

1. **infrastructure_self_exempt**: The enforcement agent was exempted from the gate it was supposed to enforce. It ran pre-commit inside its own session, meaning it controlled both the test and the verdict. The Scripture says: "apply same rules to the guardrail as to what it guards."

2. **downstream_fix**: Early attempts tried to make the enforce prompt "more careful" about running pre-commit. But prompt instructions are advisory — the real fix was to move the gate outside the agent's control entirely, into a mechanical FSM state with its own action type.

## Root Cause

The v2 pipeline had no separation between enforcement (writing code) and validation (checking code). Both lived in the same `enforce_session` state. The `precommit` action type already existed with retry logic, but it wasn't wired into the pipeline.

## What Worked

- **Mechanical separation**: New `validate` state (copilot session for ruff/pytest remediation) and `precommit_check` state (mechanical pre-commit action with max_attempts=5) create a fail-closed boundary.
- **Action type reuse**: The existing `precommit` action type already had 3-way routing (pass/retry/error) — exactly what was needed. No new action code required.
- **Prompt pruning**: Removing pre-commit responsibility from the enforce prompt made it simpler and more focused. Less scope = less drift.

## Seed

Can the validate→precommit_check loop be instrumented to track which hooks fail most often, building a feedback signal that improves the enforce prompt over time?
