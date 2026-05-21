# Watcher2 Sanity-Check Reflection — FR-436

**Date:** 2026-05-21
**FR:** FR-436 — ADR-001 scope contract for hook tests
**Author:** watcher2 post-validate reviewer

## Trap

`gate_checks_shape_not_substance` / `audit_as_ritual` — The original ADR-001 wording
said "every test must have `@pytest.mark.req`" but the enforcement tools
(`scripts/req_coverage.py`, `tests/conftest.py`) had already narrowed scope to
`tests/unit` and `tests/integration`. The specification was global; the
implementation was scoped. Inquisitor audits 244 and 245 faithfully read the
global spec and raised a finding that was technically correct but operationally
wrong — a ritual re-raise with no path to resolution.

## What Happened

The inquisitor prompt used an unscoped sentence:

> "If tests were added, do they have @pytest.mark.req tags?"

This caused two consecutive false-positive audit findings against `.github/hooks/tests/`.
An FR was raised to close the specification-to-implementation gap at its proper
boundary: the documentation.

## Root Cause

Specification drift. The doc text was written before the scope of `req_coverage.py`
was narrowed. The enforcement code was correct; the spec lagged behind and became a
trigger for audit noise. Classic `downstream_fix` trap — the temptation is to add
markers to hook tests; the real fix is to align the spec boundary at its source.

## What Worked

1. **Substance-over-presence tests.** Six acceptance tests assert specific vocabulary
   ("Tier 1", "Tier 2", "infrastructure hook", "exempt", scope-aware phrasing in
   inquisitor.sh) rather than just file existence. All 6 pass GREEN.
2. **Proportional scope.** 8 files changed, 278 insertions. Pure documentation +
   comment alignment, zero hook-behavior changes. FR declared "Bug / doc
   clarification" and that framing held.
3. **All five documented touch-points covered.** ARCHITECTURE.md, ADR-001 doc,
   `req_coverage.py` constants + output, `inquisitor.sh` prompt line, and
   `hooks/README.md` — each AC maps to exactly one file change, making audit
   verification cheap.

## Pipeline Log Note

Latest pipeline log references a prior run (watcher-pipeline-v2,
`feat/watcher2-inquisitor-wip-main-gate`) that failed CI. That run is unrelated to
this FR; no anomalies detected in the current branch.

**Seed:** When the same audit finding recurs on two consecutive days, the inquisitor's
prompt text is the first-order suspect, not the codebase. Could the inquisitor
automatically detect "same finding, consecutive audits" and escalate to an
FR-generation step before the third occurrence — treating repeated findings as
evidence of a spec boundary bug rather than a codebase bug?
