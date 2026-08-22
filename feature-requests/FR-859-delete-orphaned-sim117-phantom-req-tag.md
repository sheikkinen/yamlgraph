# Feature Request: Delete Orphaned SIM117 Test Carrying Phantom REQ-YG-287 Tag

**Priority:** LOW
**Type:** Bug
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-08-22
**First consumer / first event:** the FR-850 implementation census
(`python scripts/req_coverage.py --implementation`) and the FR-851
witness audit — both currently list SIM117 tests as witnesses for
CAP-131 prompt caching; the first clean report after deletion is the
consuming event.

**Prior art:** FR-281-watcher2-remediation-loop-crash-fix.md
[Implemented] — the *origin* of this defect, not a competing solution:
FR-281's enforcement introduced the SIM117 test with the reused
REQ-YG-287 tag (commit 127d5077). Its watcher2 remediation feature was
since retired and its unit tests deleted by FR-465; this FR completes
that retirement by removing the orphaned sibling FR-465 missed.

## Summary

`tests/integration/sim117_remediation/test_sim117_auto_fix.py` is tagged
`@pytest.mark.req("REQ-YG-287")`, but REQ-YG-287 is CAP-131 "System
segments schema validation and parsing" (Anthropic prompt caching,
FR-276). The test exercises ruff's `--unsafe-fixes` SIM117 auto-fix
against temp files — it tests ruff's behavior, not ours, and its only
consumer (watcher2 ruff remediation) was retired. Delete the directory.

## Value Statement

The requirement-traceability census stops laundering two unrelated
tests as prompt-caching witnesses, and CAP-131's roster becomes honest.

## Problem

Two independent instruments flagged the same phantom on 2026-08-22:

- **FR-850 census** (stored:
  `docs/diary/2026-08-22-fr850-implementation-report.txt.gz`):
  REQ-YG-287's witness roster includes
  `test_sim117_auto_fix::test_nested_with_statements_auto_fix` and
  `::test_ruff_unsafe_fixes_flag_available` — semantically unrelated to
  system-segments parsing.
- **FR-851 audit** (`tmp/req-audit/report.md` L105): REQ-YG-287
  verdict `[partial]` — "two unrelated tests (SIM117) appear
  misclassified → remove or reclassify."

Provenance of the phantom:

1. FR-276 (08e92e42) registered REQ-YG-287 in CAP-131.
2. FR-281 (watcher2 `ruff --unsafe-fixes`, 127d5077) tagged its tests
   with REQ-YG-287 without registering its own requirement — ID reuse.
3. FR-465 (caf6c034) deleted the retired watcher2 tests including
   `test_fr281_watcher2_ruff_unsafe_fixes.py` and "fixed REQ
   traceability" — but missed the sibling integration test
   (`partial_remediation` trap).

Liveness check (2026-08-22): zero references to SIM117 or
`unsafe-fixes` in `yamlgraph/`, `scripts/`, or `.github/` (hooks audit
log excluded). The test spawns `ruff` subprocesses against tempfiles;
no yamlgraph code is exercised.

## Ideal Result

REQ-YG-287's witness roster contains only genuine prompt-caching tests;
no test file in the tree carries a REQ tag whose requirement it does not
witness; the retired watcher2 remediation leaves no orphaned artifacts.

## Proposed Solution

Delete `tests/integration/sim117_remediation/` (one test file plus
pycache). No registry edit: REQ-YG-287 keeps its genuine FR-276
witnesses (`test_prompt_caching_fr276::TestPromptSegmentSchema`, 2
coverage-linked tests), so the strict req-coverage gate stays green.

## Acceptance Criteria

- [ ] `tests/integration/sim117_remediation/` no longer exists.
- [ ] `python scripts/req_coverage.py --strict` exits 0 (REQ-YG-287
      still covered by FR-276 witnesses).
- [ ] REQ-YG-287 census section in
      `python scripts/req_coverage.py --implementation` lists no
      sim117 tests.
- [ ] Fast unit suite green (`pytest tests/unit/ -q --no-cov -m "not
      slow" -n auto`).
- [ ] Changelog fragment (`type: removal`) + diary entry.

## Alternatives Considered

- **Retag instead of delete:** no current requirement covers "ruff
  auto-fix behavior"; registering one would certify a third-party
  tool's behavior with no consumer — `growth_as_default`. Rejected.
- **Broader stale-REQ remediation in this FR:** the FR-851 audit
  produced 10 `[no]` + 235 `[partial]` verdicts; most are driven by the
  fast-suite recording gap (no-link-unrecorded), not phantom tags.
  That remediation is mechanical-first (full-suite `ctrace` recording,
  re-audit, then triage residue) and belongs to its own FR — this FR
  stays the one-file deletion with complete provenance. Rejected here;
  see FR-851 follow-up disposition.

## Implementation Notes

Squash-merge title: `fix(tests): FR-859 delete orphaned SIM117 test
with phantom REQ-YG-287 tag`.
