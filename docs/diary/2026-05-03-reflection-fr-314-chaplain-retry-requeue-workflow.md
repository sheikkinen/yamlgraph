# 2026-05-03 Reflection: FR-314 Chaplain Retry/Requeue Workflow

**Date:** 2026-05-03
**FR:** FR-314

## Trap

**downstream_fix** — The risk was documenting only the relabel command (symptom-level) instead of the boundary condition that actually blocks re-import.

## What Happened

The requested workflow looked simple, but the key behavior is in `inbox_sync.sh` dedup gates. A retry can appear to be "done" if we only mention `gh issue edit <NUM> --add-label chaplain`, while the failed marker still prevents ingestion.

## Root Cause

The operational boundary is file presence in `.chaplain/failed/`, `.chaplain/processing/`, and `.chaplain/inbox/`. Missing this boundary rule causes a plausible but wrong runbook.

## What Worked

Encoding the exact four commands and the mandatory skip-behavior explanation directly in README, then locking it with a dedicated docs test that asserts the command lines and the sync-cycle pickup statement.

## Seed

Should we generate this retry/requeue block from a single source (script metadata or doctest fixture) so operator docs and watcher dedup behavior cannot drift over time?
