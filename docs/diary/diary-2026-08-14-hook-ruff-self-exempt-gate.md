# 2026-08-14 — The gate that audited everyone but itself (FR-793)

## What happened

A casual "is our process overkill?" review turned into an incident: the
audit log showed 1,818 `error/ruff-missing` entries — the post-edit
Python hook had been silently skipping all ruff feedback for **three
months**, on every edit, because `command -v ruff` fails in the hook
runner's PATH and ruff lives only in `.venv`. FR-414 had made the gap
"visible in the audit trail" — and nothing ever read the trail.

## The trap

`infrastructure_self_exempt` + `detection_without_enforcement`,
compounding: the enforcement layer enforces substance-over-presence on
everyone else, but its own health signal was presence-only (a log line
with no consumer). The failure was masked *twice*: errors went to a
gitignored file nobody reads, and pre-commit's ruff caught the lint
anyway — at commit time, converting an invisible defect into a visible
but unattributed cost (bounced commits, ~3 min hook cycle each).

## What found it

Not instrumentation — *counting the audit log's decision field* during
an unrelated meta-review. The `read_raw_output_first` cure generalizes:
the first diagnostic for "is this system healthy?" is grep on its
rawest artifact, not a dashboard. One `uniq -c` exposed what 51,848
logged invocations had faithfully recorded and no one had aggregated.

## The judge earned its keep

The judgement caught four real defects in my FR: a wrong implementation
surface (`cmd status` is a sentinel intercepted in `pre-command-guard.sh`,
not a file), an undeclared dependency (jq), evidence resting on a
gitignored log, and — best — the test conftest *prepends `.venv/bin` to
PATH*, which would have masked the very bug under test (R-4). The
author cannot see the mask because the author wrote the harness.

## Heuristic

Every audit trail needs a named consumer and a firing moment, or it is
a write-only ritual. The fix's second half (error counts in `cmd
status`) is worth more than the first (the venv fallback): the fallback
fixes one binary; the consumer fixes the *class*.

**Seed:** the hook error counter now surfaces errors when a human asks
for status. Nobody asks for status on a healthy system — should the
SessionStart briefing (FR-743) inject a one-line hook-health warning
when the 7-day error count is nonzero, making the trail self-announcing?
