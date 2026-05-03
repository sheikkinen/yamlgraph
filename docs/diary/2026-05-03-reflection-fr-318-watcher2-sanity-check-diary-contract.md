# Diary Reflection: FR-318 — Enforce Sanity-Check Diary Contract

**Date:** 2026-05-03
**FR:** FR-318

## Trap

**Chicken-and-egg self-reference.** The fix teaches the pipeline to commit diary files — but the pipeline running this fix doesn't yet have the fix applied. The old prompt hardcodes `fr-316` and never commits the diary, so the very PR that corrects this behavior fails the gate it's correcting.

This is `infrastructure_self_exempt` from the Knowledge Graph: meta-tooling exempted from the gates it enforces.

## What Happened

PRs #296, #299, #301, #302, and now #307 all failed `diary-gate` because `sanity-check-session.yaml` created a diary file but never staged or committed it. The filename was also hardcoded to `fr-316`, causing mismatches for every subsequent FR.

## Root Cause

Two prompt defects in `sanity-check-session.yaml`:
1. Hardcoded `fr-316` in the diary filename instead of deriving from `{{ fr_path }}`.
2. No `git add` / `git commit` step after creating the diary file.

## What Worked

- Pattern recognition across five failed PRs identified the systemic cause.
- Filing gh-305 as a GitHub issue let the pipeline attempt self-repair.
- Manual finalization (adding the missing diary commit) unblocks CI.

## Seed

When a pipeline fix targets its own enforcement gate, should the system detect the circular dependency and skip the gate for that specific PR — or is manual intervention the correct escape valve?
