# Watcher2 Sanity Check — FR-409 CI Co-authored-by Gate Generalization

**Date:** 2026-05-18
**FR:** FR-409 — Generalize CI trailer gate to reject any `Co-authored-by:` identity trailer
**Reviewer:** watcher2 post-validate

---

## Trap

`gate_checks_shape_not_substance` — A CI gate that enumerated two specific Copilot literal strings instead of matching the policy's structural boundary (`Co-authored-by:` as a class), leaving all non-Copilot trailer identities undetected.

## What Happened

Issue #408 exposed an enforcement gap in `copilot-trailer-gate`: matching was anchored to `TRAILER_SHORT` and `TRAILER_FULL` Copilot literals. Any `Co-authored-by:` trailer with a different identity (e.g. `Co-authored-by: Test <test@example.com>`) silently passed. FR-409 was raised, scoped to widening the grep pattern to `^[[:space:]]*Co-authored-by:[[:space:]]+`, updating traceability in CAP-148, REQ-YG-358, ARCHITECTURE.md, and CLAUDE.md, and extending tests to cover non-Copilot identities.

## Root Cause

FR-385 (the original gate FR) was written against a specific exemplar (Copilot) rather than the underlying policy intent (no identity trailers). The implementation faithfully reproduced the spec's narrowness. The gate checked for known-bad values (blocklist pattern) instead of any instance of the structural form (policy pattern). Classic `gate_checks_shape_not_substance`.

## What Worked

- **Minimal, surgical CI change:** Two hardcoded constants removed; one case-insensitive regex pattern substituted. The fix is smaller than the original code yet broader in coverage.
- **FR-385 test conflict handled explicitly:** The Implementation Notes section of FR-409 identified the conflict (FR-385 asserted `TRAILER_SHORT`/`TRAILER_FULL` exist) and directed the implementer to update those tests. The update was made correctly.
- **All 6 acceptance criteria have behavioral tests:** Each AC maps 1:1 to a named test function. Tests invoke the actual CI shell script via subprocess against real temporary git repos — behavioral evidence, not shape checking.
- **Traceability chain complete:** CAP-148, REQ-YG-358, CLAUDE.md, ARCHITECTURE.md all use generalized language. `test_ac06` verifies the language programmatically.
- **Proportionality:** 9 files changed, 404 insertions(+), 32 deletions(-). Scope tightly matches the 6 ACs. No speculative extensions.

## Verdict

**PASS.** Implementation is proportional, test quality is behavioral, FR/code alignment is complete across all 6 acceptance criteria.

## Seed

**Seed:** When a policy gate is broadened (e.g. from Copilot-only to any-identity), what mechanism ensures that future legitimate exceptions (human pair-programming trailers) are surfaced as policy changes rather than silent code bypasses? Is there a path from "we want to allow X" to a traceable FR, rather than a hotfix that erodes the gate?
