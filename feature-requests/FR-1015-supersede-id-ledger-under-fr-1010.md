# Feature Request: Supersede FR-975 / FR-980 under FR-1010 (Phase 1½)

**Priority:** LOW
**Type:** Enhancement (docs-only status amendment)
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-06). R-1..R-4 folded
below; see [FR-1015-supersede-id-ledger-under-fr-1010.judgement.md](FR-1015-supersede-id-ledger-under-fr-1010.judgement.md).
Enforcement gated on FR-1011 merged and FR-1012 not started.
**Effort:** 0.25 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 1½ of 5; merges after FR-1011, before FR-1012 (FR-1010 C-3)
**First consumer / first event:** FR-1012's census, at the moment it must
mark `.chaplain/id-registry.yaml`, `scripts/id_registry.py`,
`scripts/validate_id_registry.py`, the `validate-id-registry` hook,
`tests/unit/test_id_registry.py` and
`tests/unit/test_fr754_id_registry_package_boundary.py` as `delete` rows —
it needs a committed authority that the program which reserved those
artifacts is closed. Without this FR, FR-1012 would contradict FR-980's
AC-11 (and FR-970's judgement `:77-80`, which explains why deletion could
never happen under FR-970's own authority).
**Research:** none required beyond FR-1010 § "ID-allocation decision (R-2)"
— this FR executes a recorded operator decision; § Alternatives Considered
records what "supersede" excludes. `is_this_a_graph`: **no**.
**Prior art:**
- [FR-970-load-bearing-atomic-id-allocation.md](FR-970-load-bearing-atomic-id-allocation.md)
  — SPLIT 2026-09-03 into FR-975 + FR-980; no implementation authority.
  **Not edited by this FR** (R-1): it remains `Judged — SPLIT`, its
  judgement remains authoritative history, and it never granted deletion
  authority — that is exactly why the two successors, not the parent, are
  the records whose visible status must close.
- [FR-975-id-ledger-reservation-protocol.md](FR-975-id-ledger-reservation-protocol.md)
  — APPROVED WITH REVISIONS 2026-09-03, authority inactive pending human
  review, **unimplemented**: `git grep -n -E 'FR-975|FR-980|id_ledger|id-ledger' HEAD -- tests scripts yamlgraph .github/hooks .github/workflows .pre-commit-config.yaml`
  → empty; `git grep -n -E 'fr:[[:space:]]*FR-(975|980)' HEAD -- capabilities`
  → empty (2026-09-06). Its mention of CAP-170 / REQ-YG-580 (`:50`) is a
  historical corpus reference ("the live corpus is past…"), not an owned
  registry entry. Superseded.
- [FR-980-id-ledger-route-enforcement.md](FR-980-id-ledger-route-enforcement.md)
  — APPROVED WITH REVISIONS 2026-09-03, authority inactive pending FR-975;
  unimplemented (same greps). Its AC-11 assigned the legacy purge to a
  post-bootstrap commit; that purge moves to FR-1012 under FR-1010's
  decision (ii). Superseded.
- [FR-180-plan-phase-id-reservation.md](FR-180-plan-phase-id-reservation.md)
  — the legacy registry these three FRs were replacing. Its artifacts are
  deleted by FR-1012, not by this FR; this FR only closes the successor
  program so the deletion has one owner.
- [FR-701-capability-registry-consistency-gate.md](FR-701-capability-registry-consistency-gate.md)
  — `validate_capabilities.py::validate_registry()` duplicate-ID gate.
  **Not** touched (FR-1010 C-7): it remains the post-hoc collision detector
  after the legacy reservation registry goes.

## Summary

Set FR-975 and FR-980 to `Superseded by FR-1010 (2026-09-06)`, record the
operator's decision and its rationale in each, and reproduce FR-1010's
replacement contract verbatim so the deletion in FR-1012 leaves no
undocumented gap. FR-970 (the SPLIT parent) is not edited.

## Value Statement

FR-1012 can delete the legacy ID-registry artifacts with a single committed
authority instead of contradicting two judged, unimplemented FRs.

## Problem

FR-1010's judgement (R-2) found that the plan's proposed deletion of
`.chaplain/id-registry.yaml` collided with three FRs. They play two
different roles:

- **FR-970** (SPLIT) is the historical parent: its judgement withholds
  deletion authority, which explains why the legacy registry could not be
  removed under FR-970 and why FR-975/FR-980 were created. Its status is
  already terminal; nothing about it needs to change.
- **FR-975** and **FR-980** are the *active* successor records: both read
  `Judged — APPROVED WITH REVISIONS`, i.e. work awaiting enforcement. The
  next agent that greps for open judged FRs finds them and might start.
  FR-975 bootstraps the canonical ledger from the legacy file; FR-980 AC-11
  owns the purge.

The operator decided (FR-1010 § "ID-allocation decision"): **supersede**.
A decision recorded only in FR-1010 leaves the two successor records
visibly open.

What is in force, quoted from FR-1010 (frozen; not restated here):

> Direct Plan/Enforce CAP/REQ allocation remains mechanical enumeration at
> filing: `max(ids on main + all open PR heads) + headroom`. FR-701's
> `scripts/validate_capabilities.py::validate_registry()` remains the
> post-hoc duplicate gate. No new allocator is introduced.

## Ideal Result

`grep -c '^\*\*Status:\*\* Superseded by FR-1010 (2026-09-06)'` → `1` for
`FR-975-…md` and `FR-980-…md`; FR-970 still reads `Judged — SPLIT`; each
of the two carries exactly one `## Superseded (2026-09-06)` block naming
the decision, the rationale, the verbatim replacement contract, FR-701's
unchanged role, and FR-1012 as the deleting FR. No other line of either
FR changes; their `.judgement.md` siblings and FR-1010 are untouched.

## Proposed Solution

One enforcement commit, docs-only, in a worktree, **after** FR-1011 has
merged and **before** FR-1012 starts (GATE):

1. In `FR-975-…md` and `FR-980-…md` replace the `**Status:**` line with
   `**Status:** Superseded by FR-1010 (2026-09-06) — see § Superseded.`
2. Insert in each, immediately after the header block:

   ```markdown
   ## Superseded (2026-09-06)

   **By:** FR-1010 § "ID-allocation decision (R-2)", operator decision (ii).
   **Why:** the Chaplain runtime that hosted `.chaplain/id-registry.yaml` is
   being archived (FR-1010); this ledger program was never implemented — no
   CAP entry (`fr: FR-975|FR-980`), no code, test, hook, workflow or
   pre-commit entry cites it.
   **Replacement contract (FR-1010, verbatim):** Direct Plan/Enforce CAP/REQ
   allocation remains mechanical enumeration at filing:
   `max(ids on main + all open PR heads) + headroom`. FR-701's
   `scripts/validate_capabilities.py::validate_registry()` remains the
   post-hoc duplicate gate. No new allocator is introduced.
   **Deletion of legacy artifacts:** FR-1012 (Phase 2), only as reviewed
   census `delete` rows.
   ```
3. Changelog fragment `changelog/unreleased/fr-1015-supersede-id-ledger.md`
   (`type: removal`, scope `fr`) — describing retirement of the
   unimplemented ledger *program*, not deletion of its legacy artifacts
   (that is FR-1012's fragment).
4. Record AC-01..AC-08 command results in § Implementation Status below.
   **FR-1010 is not edited** (R-3): its AC-03 also depends on FR-1015's
   merge order and FR-1012's census, which this PR cannot truthfully
   claim.

No test changes: `tests/unit/test_id_registry.py` and
`tests/unit/test_fr754_id_registry_package_boundary.py` are legacy-registry
tests and remain untouched here as FR-1012 census inputs. No CAP changes:
none is owned by FR-975/FR-980.

## Acceptance Criteria (from judgement; exact)

- [ ] AC-01: `grep -c '^\*\*Status:\*\* Superseded by FR-1010 (2026-09-06)' feature-requests/FR-975-id-ledger-reservation-protocol.md feature-requests/FR-980-id-ledger-route-enforcement.md`
      → `1` each; `grep -c '^\*\*Status:\*\* Judged — SPLIT' feature-requests/FR-970-load-bearing-atomic-id-allocation.md`
      → `1` (unchanged).
- [ ] AC-02: FR-975 and FR-980 each contain exactly one
      `## Superseded (2026-09-06)` block with: FR-1010 decision (ii); the
      unimplemented-program rationale; the verbatim contract sentence;
      FR-701's unchanged role; FR-1012 as the deleting FR.
- [ ] AC-03: `git diff --unified=0 "$(git merge-base HEAD origin/main)"...HEAD -- feature-requests/FR-975-id-ledger-reservation-protocol.md feature-requests/FR-980-id-ledger-route-enforcement.md`
      shows exactly one Status-line replacement and one inserted block per
      file; both `.judgement.md` siblings unchanged.
- [ ] AC-04: `git grep -n -E 'fr:[[:space:]]*FR-(975|980)' HEAD -- capabilities`
      → empty (no owned CAP entry to retire).
- [ ] AC-05: `git grep -n -E 'FR-975|FR-980|id_ledger|id-ledger' HEAD -- tests scripts yamlgraph .github/hooks .github/workflows .pre-commit-config.yaml`
      → empty. Any hit stops enforcement and returns this FR to judgement
      (FR-1010 C-10).
- [ ] AC-06: The enforcement commit's changed-path set is exactly: this FR
      (evidence record), `FR-975-…md`, `FR-980-…md`, the changelog
      fragment. No FR-970, FR-1010, code, capability, test, hook, workflow,
      pre-commit, graph, prompt, or judgement edit.
- [ ] AC-07: § Implementation Status records AC-01..AC-06 command outputs
      and names `tests/unit/test_id_registry.py` and
      `tests/unit/test_fr754_id_registry_package_boundary.py` as untouched
      FR-1012 census inputs.
- [ ] AC-08: `prior-art-gate`, `triage-gate`, markdown and changelog checks
      pass on the changed files.
- [ ] GATE: FR-1011 merged before enforcement; FR-1012 not started.

## Purge list

- No new allocator, script, hook, or CAP.
- No edit to FR-701's `validate_registry()` or its tests.
- No edit to FR-970, FR-1010, or any `.judgement.md`.
- No restatement of the allocation contract beyond FR-1010's sentence.

## Alternatives Considered

| Option | Why not |
|---|---|
| Leave FR-975/FR-980 `Judged` and let FR-1012 delete the registry anyway | FR-1010 C-7: deletion may not contradict a recorded disposition; three FRs would read as open work whose input file had vanished. |
| Implement FR-975 first (bootstrap ledger from the legacy registry), then let FR-980 purge | Operator decision (ii) rejected this; the program is unimplemented and the registry it bootstraps from has been wrong for five months — a bootstrap would import `next_cap: 94`. |
| Mark `Rejected` instead of `Superseded` | They were approved; the world changed. `Superseded` keeps the judgements valid as history and names the successor. |
| Fold the status edits into FR-1012 | FR-1012 is a deletion PR needing human review for destructive ops; a docs-only authority record should merge on its own so the deletion PR has one concern. |
| Also mark FR-970 `Superseded` (first draft) | Withdrawn per R-1: FR-970 is already terminal (`SPLIT`); rewriting a historical verdict with a later product disposition FR-1010 did not order is not status-recording. |

## Related

- FR-1010 (plan), FR-1011 (must merge first), FR-1012 (consumer)

## Implementation Status

_pending enforcement — AC-01..AC-08 outputs recorded here._

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1015-supersede-id-ledger-under-fr-1010.judgement.md](FR-1015-supersede-id-ledger-under-fr-1010.judgement.md).
R-1 (FR-970 out of the edit set), R-2 (FR-1010 contract verbatim; wider
no-implementation evidence incl. `capabilities/`, `.github/workflows/`,
`.pre-commit-config.yaml`), R-3 (no FR-1010 edit), R-4 (exact ACs; both
legacy tests named as FR-1012 inputs) folded above.
