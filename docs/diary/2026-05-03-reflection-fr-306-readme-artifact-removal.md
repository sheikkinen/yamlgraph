# Diary: FR-306 — Tiny Artifacts, Real Trust Damage

**Date:** 2026-05-03
**FR:** FR-306 (README hook test artifact removal)
**Trap:** quick_confidence

## What Happened

The defect looked trivial: delete one stray line from README. That can trigger quick confidence and a rushed merge because the surface diff is small.

## The Trap

**quick_confidence**: "When I feel certain → Judge instead."

A tiny change still lives inside a large, evolving repo where unrelated failures can surface during enforcement.

## Insight

Small documentation defects are trust defects. Readers treat README as source-of-truth; accidental internal artifacts weaken confidence disproportionately.

## Heuristic

**Treat one-line public-doc fixes as production-facing changes: apply minimal edit, then run full enforcement gates before declaring done.**

## Seed

Should we add a lightweight README-tail guard that detects common accidental tokens (like `hook test`) without introducing broad new lint noise?
