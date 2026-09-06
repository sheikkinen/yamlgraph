# Feature Request: Supersede FR-975 / FR-980 under FR-1010 (Phase 1½)

**Priority:** LOW
**Type:** Enhancement (docs-only status amendment)
**Status:** Proposed
**Effort:** 0.25 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 1½ of 5; merges after FR-1011, before FR-1012 (FR-1010 C-3)
**First consumer / first event:** FR-1012's census, at the moment it must
mark `.chaplain/id-registry.yaml`, `scripts/id_registry.py`,
`scripts/validate_id_registry.py`, the `validate-id-registry` hook and
`tests/unit/test_fr754_id_registry_package_boundary.py` as `delete` rows —
it needs a committed authority that the program which reserved those
artifacts is closed. Without this FR, FR-1012 would contradict FR-970's
judgement (`:77-80`) and FR-980's AC-11.
**Research:** none required beyond FR-1010 § "ID-allocation decision (R-2)"
— this FR executes a recorded operator decision; § Alternatives Considered
records what "supersede" excludes. `is_this_a_graph`: **no**.
**Prior art:**
- [FR-970-load-bearing-atomic-id-allocation.md](FR-970-load-bearing-atomic-id-allocation.md)
  — SPLIT 2026-09-03 into FR-975 + FR-980; no implementation authority.
  Superseded here as the parent of the program.
- [FR-975-id-ledger-reservation-protocol.md](FR-975-id-ledger-reservation-protocol.md)
  — APPROVED WITH REVISIONS 2026-09-03, authority inactive pending human
  review, **unimplemented**: no CAP file cites it, no code or test names
  `id_ledger`/`id-ledger` (verified `grep -rlE 'FR-975|FR-980|id_ledger|id-ledger' tests/ scripts/ yamlgraph/ .github/hooks`
  → empty, 2026-09-06). Superseded.
- [FR-980-id-ledger-route-enforcement.md](FR-980-id-ledger-route-enforcement.md)
  — APPROVED WITH REVISIONS 2026-09-03, authority inactive pending FR-975;
  unimplemented (same grep). Its AC-11 assigned the legacy purge to a
  post-bootstrap commit; that purge moves to FR-1012 under this FR's
  authority. Superseded.
- [FR-180-plan-phase-id-reservation.md](FR-180-plan-phase-id-reservation.md)
  — the legacy registry these three FRs were replacing. Its artifacts are
  deleted by FR-1012, not by this FR; this FR only closes the successor
  program so the deletion has one owner.
- [FR-701-capability-registry-consistency-gate.md](FR-701-capability-registry-consistency-gate.md)
  — `validate_capabilities.py::validate_registry()` duplicate-ID gate.
  **Not** touched (FR-1010 C-7): it remains the post-hoc collision detector
  after the legacy reservation registry goes.

## Summary

Set FR-970, FR-975 and FR-980 to `Superseded by FR-1010 (2026-09-06)`,
record the operator's decision and its rationale in each, and name the
ID-allocation contract that is actually in force so the deletion in
FR-1012 leaves no undocumented gap.

## Value Statement

FR-1012 can delete the legacy ID-registry artifacts with a single committed
authority instead of contradicting three judged FRs.

## Problem

FR-1010's judgement (R-2) found that the plan's proposed deletion of
`.chaplain/id-registry.yaml` collided with three live FRs: FR-970's
judgement withholds deletion authority explicitly; FR-975 bootstraps the
canonical ledger from the legacy file; FR-980 AC-11 owns the purge. The
operator decided (FR-1010 § "ID-allocation decision"): **supersede**.
A decision recorded only in FR-1010 leaves FR-975/FR-980 reading as
`Judged — APPROVED WITH REVISIONS`, i.e. as work awaiting enforcement; the
next agent that greps for open judged FRs would find them and might start.

What is actually in force today, and has been since the registry froze on
2026-04-19: allocation by **mechanical enumeration at filing** —
`max(FR/CAP/REQ ids on main ∪ all remote branches ∪ open PR titles) +
headroom ≥ 3` (`one_session_one_repo`, `collision_by_increment`), with
`validate_capabilities.py::validate_registry()` (FR-701) as the post-hoc
collision gate. ~170 CAPs and ~400 REQs were allocated this way while the
registry said `next_cap: 94`.

## Ideal Result

`grep -l 'Status:\*\* Judged' feature-requests/FR-97{0,5}*.md feature-requests/FR-980*.md`
returns nothing; each of the three FRs opens with
`**Status:** Superseded by FR-1010 (2026-09-06)` and a four-line
"Superseded" block naming the decision, the rationale, the replacement
contract, and the FR that performs the deletion. No other line of the
three FRs changes. FR-1010 AC-03 can be ticked.

## Proposed Solution

One commit, docs-only, in a worktree:

1. In each of `FR-970-…md`, `FR-975-…md`, `FR-980-…md` replace the
   `**Status:**` line with
   `**Status:** Superseded by FR-1010 (2026-09-06) — see § Superseded.`
2. Append to each, immediately after the header block:

   ```markdown
   ## Superseded (2026-09-06)

   **By:** FR-1010 § "ID-allocation decision (R-2)", operator decision (ii).
   **Why:** the Chaplain runtime that hosted `.chaplain/id-registry.yaml` is
   being archived; the ledger program this FR belongs to was never
   implemented (no CAP, no code, no test cites it); the de-facto contract
   since 2026-04-19 is mechanical enumeration at filing + FR-701's
   duplicate gate.
   **Replacement contract:** allocate `max(ids on main ∪ remote branches ∪
   open PR titles) + ≥3`; `validate_capabilities.py::validate_registry()`
   remains the collision gate. No new allocator.
   **Deletion of legacy artifacts:** FR-1012 (Phase 2), as census `delete`
   rows.
   ```
3. FR-1010 AC-03: tick, with this FR's merge SHA.
4. Changelog fragment `changelog/unreleased/fr-1015-supersede-id-ledger.md`
   (`type: removal`, scope `fr`).

No test changes: the three FRs have no tests. No CAP changes: none cites
them.

## Acceptance Criteria

- [ ] `grep -c '^\*\*Status:\*\* Superseded by FR-1010' feature-requests/FR-970-*.md feature-requests/FR-975-*.md feature-requests/FR-980-*.md`
      → `1` for each of the three `.md` files (judgement siblings untouched).
- [ ] Each of the three carries a `## Superseded (2026-09-06)` block with
      the four labelled lines above.
- [ ] `git diff --stat` for this PR touches exactly: the three FRs, FR-1010
      (AC-03 tick), one changelog fragment.
- [ ] `grep -rlE 'FR-975|FR-980|id_ledger|id-ledger' tests/ scripts/ yamlgraph/ .github/hooks`
      is still empty (no implementation appeared meanwhile; if it did,
      stop — FR-1010 C-10).
- [ ] `prior-art-gate` and `triage-gate` pass on the modified FRs.
- [ ] Merged after FR-1011, before FR-1012 (FR-1010 C-3).

## Purge list

- No new allocator, script, hook, or CAP.
- No edit to FR-701's `validate_registry()` or its tests.
- No edit to the three `.judgement.md` siblings — they are the record of
  what was judged, not of what happened next.

## Alternatives Considered

| Option | Why not |
|---|---|
| Leave FR-975/FR-980 `Judged` and let FR-1012 delete the registry anyway | FR-1010 C-7: deletion may not contradict a recorded disposition; three FRs would read as open work whose input file had vanished. |
| Implement FR-975 first (bootstrap ledger from the legacy registry), then let FR-980 purge | Operator decision (ii) rejected this; the program is unimplemented and the registry it bootstraps from has been wrong for five months — a bootstrap would import `next_cap: 94`. |
| Mark `Rejected` instead of `Superseded` | They were approved; the world changed. `Superseded` keeps the judgements valid as history and names the successor. |
| Fold the status edits into FR-1012 | FR-1012 is a deletion PR needing human review for destructive ops; a docs-only authority record should merge on its own so the deletion PR has one concern. |

## Related

- FR-1010 (plan), FR-1011 (must merge first), FR-1012 (consumer)

## Judgement (pending)
