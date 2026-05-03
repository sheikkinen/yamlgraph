# Reflection: FR-312 Post-Merge Main Sync

**Date:** 2026-05-03
**FR:** FR-312

## Trap

**downstream_fix**

## What Happened

The existing watcher2 flow attempted `git pull --ff-only` in neighboring lifecycle scripts, but post-merge cleanup itself did not normalize main when local edits were present. That let drift accumulate at the exact boundary where merges should reconcile state.

## Root Cause

Synchronization logic lived outside the decisive post-merge boundary and used best-effort pull behavior that could fail on dirty trees without halting control flow.

## What Worked

Applying **normalize at the boundary** solved it: main-sync was moved into `post_merge.sh` with explicit stash → pull --rebase → stash pop sequencing and non-zero error propagation when stash/pull/pop fails.

## Seed

How can watcher2 centralize all main-branch reconciliation logic into a single shared helper so preflight, teardown, and post-merge cannot drift into inconsistent pull semantics again?
