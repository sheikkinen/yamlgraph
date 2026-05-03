# Reflection: FR-315 yamlgraph stdout without event_map

**Date:** 2026-05-03
**FR:** FR-315

## Trap

**downstream_fix**

## What Happened

Watcher success runs were returning the right event, but the useful planning/enforcement stdout payload disappeared unless an `event_map` branch matched. Operators saw status metadata without the content needed to debug successful-but-wrong outcomes.

## Root Cause

The stdout DEBUG dump existed only inside the event-map match branch. The no-map and empty-map success path had no equivalent boundary log before `success_event` returned.

## What Worked

A narrow boundary fix in `YamlgraphAsyncAction.execute()` resolved it: keep existing routing logic intact and add one capped (`[:2000]`) DEBUG stdout log on the final success path when no `event_map` return occurred. Acceptance tests now cover omitted map, empty map, cap size, and unchanged match routing.

## Seed

Should watcher actions standardize a single "successful subprocess output visibility" contract test helper so every action guarantees inspectable stdout/stderr on both routed and default-success paths?
