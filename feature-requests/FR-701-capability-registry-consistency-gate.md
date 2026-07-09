# Feature Request: Capability Registry Consistency Gate

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-09

## Summary

Extend `scripts/req_coverage.py` (or add a companion check wired into pre-commit) to fail on capability-registry inconsistencies that today enter silently: duplicate CAP/REQ ids, dangling `fr:` references, missing `status:` fields, and live test marks pointing at retired requirements.

## Value Statement

The registry is the traceability spine (ADR-001); a gate that validates its substance keeps CAP/REQ ids unique and cross-references resolvable without human audits.

## Problem

A 2026-07-08 incident proved duplicates enter undetected: parallel FR-692 (chaplain) and FR-700 (interactive session) both allocated **CAP-195**, and FR-692 also claimed **REQ-YG-531**. The registry silently merged two capabilities under one id — `req_coverage.py` reported one requirement with the union of both test sets ("1/1 reqs, 21 tests") and **no gate failed**. The collision was found only by a human reading `git log` after a rejected push, and fixed manually in f04b1ad3.

A follow-up audit (2026-07-09) of all 179 capability files found three more latent inconsistency classes:

1. **`status:` present in only 18/179 files** (11 active, 7 retired). Absence-means-active is `gate_checks_shape_not_substance`: a typo'd key (`staus: retired`) silently keeps a capability active.
2. **`fr:` references resolve inconsistently**: 24 CAPs use `fr: legacy` (sanctioned), but CAP-02 → FR-032 and CAP-96 → FR-069 point at FRs stored under old-style filenames (`032-node-level-caching.md`, `069-map-node-timeout.md`); glob resolution by `feature-requests/FR-XXX-*` reports them missing.
3. **Retired CAPs retain live test marks**: 7 retired capabilities declare REQs and most still have running `@pytest.mark.req` tests (REQ-YG-428: 3 files; REQ-YG-286/294/307/308/429/468: 1 each) — tests witnessing retired requirements are mislabeled or dead weight.

Root cause of the duplicate class: "next free id" is read locally from the filesystem with no reservation and no uniqueness validation at any boundary (`recent_changes_blindness` for agents; no lock for parallel allocators). The registry loader normalizes nothing at its entry boundary — `the_one_law` violation.

## Proposed Solution

Add a `validate_registry()` pass that runs before coverage computation in `scripts/req_coverage.py` (already wired into pre-commit as `req-coverage-strict` and consumed by CI), failing with exit 1 on:

| Check | Rule | Severity |
|-------|------|----------|
| CR-1 duplicate CAP id | Same `id:` in two capability files, or same `CAP-NNN` filename prefix | error |
| CR-2 duplicate REQ id | Same `- id: REQ-YG-NNN` declared in more than one capability file | error |
| CR-3 filename/id mismatch | `CAP-NNN` filename prefix ≠ `id:` field | error |
| CR-4 missing status | No `status:` field → error (explicit `active` required; one-time mechanical backfill of the 161 files ships with this FR) | error |
| CR-5 dangling fr | `fr: FR-XXX` with no `feature-requests/FR-XXX-*.md` → resolve old-style `XXX-*.md` too; error only if neither exists. `fr: legacy` stays sanctioned | error |
| CR-6 retired REQ with live tests | `status: retired` CAP whose REQ ids appear in `@pytest.mark.req` marks under `tests/` | error |

Known-offender remediation ships in the same FR (all mechanical, no judgement):
- Backfill `status: active` in the 161 files lacking it (CR-4).
- CR-5: accept old-style filename resolution — no file renames (rename would break existing links).
- CR-6: retag or delete the offending marks after checking each test against the successor capability; if a test still witnesses live behavior, it belongs to an active REQ.

Non-goals: no id-reservation service, no changes to chaplain allocation flow (the gate at commit boundary suffices — parallel allocation still races, but the loser now fails pre-commit/CI instead of silently merging).

## Acceptance Criteria

- [ ] `validate_registry()` fails with exit 1 and a named check id (CR-1…CR-6) for each violation class; fixture-based unit tests cover all six (RED first)
- [ ] Reintroducing the 2026-07-08 collision (two files with `id: CAP-195`, shared REQ-YG-531) in a fixture fails CR-1 and CR-2
- [ ] All 179 capability files pass after mechanical remediation (status backfill, retired-REQ mark cleanup)
- [ ] `pre-commit run req-coverage-strict --all-files` green; no new hook added if extension of the existing one suffices
- [ ] Tests tagged with a new REQ under a new CAP (registry self-validation) — the gate is not exempt from itself (`infrastructure_self_exempt`)
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Alternatives Considered

1. **Id-reservation service / allocation lock** — solves the race at write time, but adds coordination infrastructure for an event that a commit-boundary gate catches at near-zero cost. Rejected (enforcement_at_merge_boundary suffices).
2. **Standalone lint script, advisory** — `detection_without_enforcement`; the Scripture requires a blocking gate or no claim. Rejected.
3. **Rename old-style FR files to FR-XXX-\*** — breaks existing inbound links and git-log archaeology for two files; accepting both naming schemes in resolution is cheaper. Rejected.

## Related

- Incident: CAP-195 / REQ-YG-531 collision, fixed in commit f04b1ad3 (2026-07-09)
- `scripts/req_coverage.py`, `scripts/aggregate_capabilities.py`, `.pre-commit-config.yaml` (`req-coverage-strict`)
- CAP-163 (cap-retirement-support) — retirement semantics this gate must respect
- Scripture: `gate_checks_shape_not_substance`, `substance_over_presence`, `infrastructure_self_exempt`, `enforcement_at_merge_boundary`
- Repo memory: cap-req-id-allocation-race
