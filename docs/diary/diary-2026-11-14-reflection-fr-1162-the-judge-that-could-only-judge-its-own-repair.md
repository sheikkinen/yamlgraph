# FR-1162: The judge that could only judge its own repair

**Date:** 2026-11-14
**FR:** FR-1162 (adapter model pin → gpt-6.1-sol)

## What happened

The pinned model `gpt-5.6-sol` was retired. The judge runs on that pinned
model, so the judge could not judge the FR that replaces the pin. Plan, judge,
enforce turned into plan, enforce, judge: the first judgement ran on the
already-repaired pin, and that run also served as the live witness that the
repair worked. The judge then REJECTED the FR (no research record, untested
authoring pin, review and authoring routes not exercised live). The operator
saw the verdict and its human-gate question, and overruled it.

## Trap: bootstrap_inversion

Any gate that runs on the component under repair cannot gate that repair.
The order of the ritual silently inverts. The honest response is to record the
inversion, not to pretend the sequence held.

## Heuristic

When the enforcement tool depends on what is being fixed, its first run after
the fix is a liveness witness first and a verdict second. Record both roles
separately in the FR.

**Seed:** Should sole-route adapters carry a probe-checked fallback pin list,
or would that be the silent fallback Commandment 6 forbids? Cheaper middle
ground: a scheduled availability probe that files an FR before a pin dies.
