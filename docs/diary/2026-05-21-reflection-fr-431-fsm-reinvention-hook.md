# Reflection: FR-431 FSM Reinvention Detection Hook

**Date:** 2026-05-21
**FR:** FR-431 FSM Reinvention Detection Hook
**Author:** copilot enforce pass

## Trap

`continuation_bias` - agents can keep generating plausible new FSM plans when they are unaware a project-local FSM integration already exists.

## What Happened

Feature-request authoring in markdown had no post-edit guidance about existing FSM infrastructure, so reinvention patterns could pass initial drafting without friction. FR-431 adds a targeted hook warning for `feature-requests/*.md` when FSM signals appear without known escape-hatch references.

## Root Cause

Knowledge of `statemachine_engine` and the `fsm-as-conductor` pattern was not present at the point of FR authoring. The system had checks for code and YAML edits, but not for FR markdown intent signals.

## What Worked

- Scope stayed narrow and deterministic (keyword threshold, no LLM classification).
- Escape hatches prevented warning noise when existing integration is already referenced.
- Hook tests now cover warning, escape-hatch clean path, and no-signal clean path.

## Seed

Seed: Should capability-awareness checks for FR markdown evolve from keyword thresholds to a capability-registry matcher that maps FR language to known modules and pattern docs?
