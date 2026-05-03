# Diary: FR-306 README Artifact Removal

**Date:** 2026-05-03
**FR:** FR-306
**Trap:** quick_confidence

## What Happened

The requested change was a one-line README cleanup, but full-suite enforcement exposed unrelated integration tests that assumed live provider keys. The temptation was to treat those failures as outside scope and proceed with the documentation-only fix.

## The Trap

**quick_confidence**: "When I feel certain -> Judge instead."

A small change can still trigger full-pipeline obligations. Assuming "this can't affect tests" would have produced a branch that satisfies the visible FR but fails the required execution contract.

## Insight

The right boundary fix was in tests: make integration scenarios deterministic when external credentials are absent, instead of weakening runtime behavior with silent fallbacks.

## Heuristic

**When the feature is tiny but the enforcement surface is large, keep product edits minimal and harden test boundaries explicitly.**

## Seed

Can provider-dependent integration tests be split into an explicit "credentialed" marker group so baseline enforcement remains deterministic without reducing coverage expectations?
