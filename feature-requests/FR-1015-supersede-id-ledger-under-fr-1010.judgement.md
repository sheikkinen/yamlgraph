# Judgement: FR-1015 Supersede FR-975 / FR-980 under FR-1010 (Phase 1½)

**Verdict:** APPROVED WITH REVISIONS — the docs-only closure of the unimplemented FR-975/FR-980 program is sound, but authority activates only after the FR removes FR-970 from the edit set, quotes FR-1010's replacement contract exactly, drops the premature FR-1010 AC-03 update, and replaces the incomplete acceptance checks.

**DRAFT:** Advisory until human-reviewed.

**Prior art:** see FR-1015's own Prior Art field (FR-970, FR-975, FR-980, FR-180, FR-701) — this judgement reviews and dispositions those same citations; FR-1010/FR-1011/FR-1012 are the governing plan and adjacent phases, not precedent.

**Reviewed against:** `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md`; `feature-requests/FR-975-id-ledger-reservation-protocol.md`; `feature-requests/FR-975-id-ledger-reservation-protocol.judgement.md`; `feature-requests/FR-980-id-ledger-route-enforcement.md`; `feature-requests/FR-980-id-ledger-route-enforcement.judgement.md`; `feature-requests/FR-180-plan-phase-id-reservation.md`; `feature-requests/FR-701-capability-registry-consistency-gate.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `.pre-commit-config.yaml`; `tests/unit/test_id_registry.py`; `tests/unit/test_fr754_id_registry_package_boundary.py`; `tests/unit/test_fr441_precommit_files_patterns_red.py`; committed searches for `FR-975`, `FR-980`, `id_ledger`, and `id-ledger` under `capabilities/`, `tests/`, `scripts/`, `yamlgraph/`, `.github/hooks/`, and `.github/workflows/`; and the committed filename inventory matching `tests/**/*id*registry*`.

## What is sound

The governing product decision is explicit and human-owned. FR-1010 records option (ii), superseding the unimplemented FR-975/FR-980 program before FR-1012, while preserving FR-701's duplicate-registry validator (`feature-requests/FR-1010-chaplain-archival-plan.md:137-166`). FR-1015 therefore does not invent a product decision during judgement; it turns the already-recorded decision into visible status at the two files where a future enforcer would otherwise see inactive but still-open authority (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:23-32,54-63`).

The separation from destructive work is also correct. FR-1015 limits itself to status and rationale records, assigns actual legacy-artifact deletion to FR-1012's reviewed census, and keeps FR-701 untouched (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:33-40,103-111,127-141`). That is a useful single-purpose authority record rather than deletion hidden in an administrative change.

The research evidence is proportionate to this narrow administrative decision. The `**Research:**` field points to the committed FR-1010 operator decision, preserves an explicit `is_this_a_graph: no` answer, and the FR dispositions four real choices: leave the successors active, implement them first, reject them, or fold their status edits into FR-1012 (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:16-18,134-141`). For a proposal selecting among recorded disposition states rather than designing a new mechanism, that is a substantive equivalent committed alternatives record under the local research rule (`.github/skills/judge-fr/doctrine.md:118-128`).

Against the eight rubric criteria:

1. **Scope:** the minimal sufficient change is to amend FR-975 and FR-980, exactly as FR-1010's decision requires (`feature-requests/FR-1010-chaplain-archival-plan.md:147-160`). Adding FR-970 to the edit set is unnecessary: it is already a completed SPLIT disposition with no implementation authority, while FR-1010 repeatedly names “both” successor FRs rather than their parent (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:5-12`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:20-22,42-47,75-88`).
2. **Consistency:** the title and governing plan say FR-975/FR-980, but the Summary, Ideal Result, solution, and criteria expand to three files (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:1,42-47,73-88,113-120`). The replacement formula also changes FR-1010's frozen `max(main + all open PR heads) + headroom` into “all remote branches,” “open PR titles,” and `+ ≥3`, none of which the operator decision authorized (`feature-requests/FR-1010-chaplain-archival-plan.md:157-160`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:65-71,94-102`).
3. **Measurability:** the status and labelled-block checks are directly checkable, but the implementation-presence grep omits `capabilities/`, `.github/workflows/`, and `.pre-commit-config.yaml` despite claiming no CAP or implementation exists (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:23-27,110-123`). The path-count criterion is also tied to the incorrect three-FR/FR-1010 scope (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:115-120`).
4. **Feasibility:** two status replacements, two explanatory blocks, and a changelog fragment are feasible repository documentation edits. Recording “this FR's merge SHA” inside the commit that must itself merge is not: the final merge SHA does not exist while that content is being authored (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:84-108`).
5. **Architecture alignment:** preserving the judgement siblings as immutable records and leaving deletion to the separately judged FR-1012 follows the plan/judge/enforce history model (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:127-132`; `.github/copilot-instructions.md:206-210`). Editing FR-970 would instead erase its visible SPLIT state even though that judgement was fulfilled by filing FR-975 and FR-980.
6. **Single responsibility:** after removing FR-970 and the umbrella-status update, the work has one concern: close the two unimplemented successor authorities before their legacy dependency is deleted. No split is needed. The actual allocator deletion, tests, hooks, and CAP/REQ reconciliation remain FR-1012 work (`feature-requests/FR-1010-chaplain-archival-plan.md:161-166,319-323`).
7. **Strategic classification:** this is **pattern documentation** under the rubric: it has no reusable capability beyond recording one program disposition, and existing FR status, judgement, changelog, and phase-sequencing conventions suffice (`.github/skills/judge-fr/doctrine.md:51-57`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:3-8,82-111`).
8. **Testability:** direct acceptance witnesses can prove exact statuses, exact inserted blocks, absence of owned CAP/REQ claims or implementation, path confinement, and unchanged judgement siblings. The merge-order rule is a process gate, not a test to satisfy before the future FR-1012 event exists (`feature-requests/FR-1010-chaplain-archival-plan.md:347-353`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:113-125`).

## Required revisions

### R-1: Limit the supersession edits to FR-975 and FR-980

Remove FR-970 from the Summary, Ideal Result, Proposed Solution, acceptance criteria, changed-file set, and “three FRs” language. Keep FR-970 in Prior Art as the unchanged historical SPLIT parent whose two required successors are now being superseded. State that FR-970 remains `Judged — SPLIT`, its judgement remains authoritative history, and it grants no implementation or deletion authority.

Rewrite the Problem to distinguish the historical parent constraint from the two active successor records: FR-970 explains why deletion could not happen under its own authority; FR-975 and FR-980 are the unimplemented authorities whose visible statuses must now close. Do not replace FR-970's SPLIT status with a later product disposition that FR-1010 did not order.

### R-2: Reproduce the frozen replacement contract without embellishment

Replace both invented formulas with FR-1010's exact contract:

> Direct Plan/Enforce CAP/REQ allocation remains mechanical enumeration at filing: `max(ids on main + all open PR heads) + headroom`. FR-701's `scripts/validate_capabilities.py::validate_registry()` remains the post-hoc duplicate gate. No new allocator is introduced.

Do not add “all remote branches,” “open PR titles,” or a numeric `≥3` headroom rule under FR-1015. Those are changes to the operator's frozen decision, not status-recording work.

Add a mechanically checked statement that FR-975 and FR-980 own no CAP/REQ registry entries: CAP-170 and REQ-YG-580 in FR-975 are historical corpus references, not claims. Expand the no-implementation evidence to cover `capabilities/`, `.github/workflows/`, and `.pre-commit-config.yaml` in addition to the current code/test/hook roots. If any owned CAP/REQ entry or implementation appears before enforcement, stop under FR-1010 C-10 rather than superseding it silently.

### R-3: Remove the premature FR-1010 AC-03 update

Delete Proposed Solution step 3 and every claim that this PR ticks FR-1010 AC-03 or records its own merge SHA. Do not modify FR-1010 in this phase. AC-03 requires not only this amendment but also FR-1015's merge before FR-1012 and Phase 2 deletion only through reviewed census rows (`feature-requests/FR-1010-chaplain-archival-plan.md:364-367`); those future facts cannot truthfully be marked complete by FR-1015.

Record FR-1015's implementation evidence in FR-1015 itself without claiming a not-yet-existing merge SHA. FR-1010 remains the umbrella completion record and may be updated only when its criterion is actually complete.

### R-4: Replace the acceptance criteria with exact status, evidence, and boundary checks

Fold the revised acceptance criteria below into FR-1015. Replace “this PR touches exactly” with an enforcement-commit path boundary so planning/judgement artifacts are not confused with implementation scope. Treat sequencing as a GATE: FR-1011 must already be merged before enforcement, and FR-1012 must not have started.

Name both legacy tests currently present — `tests/unit/test_id_registry.py` and `tests/unit/test_fr754_id_registry_package_boundary.py` — as FR-1012 census inputs rather than listing only the package-boundary test (`feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:9-15`; committed `tests/**/*id*registry*` inventory). FR-1015 does not delete or edit either test.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md`: fold R-1 through R-4 and record the docs-only implementation evidence. |
| D-2 | `feature-requests/FR-975-id-ledger-reservation-protocol.md`: replace only the Status line and add the exact Superseded block authorized by FR-1010. |
| D-3 | `feature-requests/FR-980-id-ledger-route-enforcement.md`: replace only the Status line and add the exact Superseded block authorized by FR-1010. |
| D-4 | `changelog/unreleased/fr-1015-supersede-id-ledger.md`: one `removal` fragment with scope `fr`, describing retirement of the unimplemented ledger program rather than deletion of its legacy artifacts. |

Not authorized: any edit to FR-970, FR-1010, FR-975/FR-980 judgement siblings, FR-701, capability files, tests, scripts, hooks, workflows, pre-commit configuration, graph or prompt artifacts; deletion of any legacy ID-registry artifact; a new allocator or allocation rule; a numeric headroom policy not already present in FR-1010; marking FR-1010 AC-03 complete; or starting FR-1012 work.

## Revised acceptance criteria

- [ ] AC-01: `grep -c '^\*\*Status:\*\* Superseded by FR-1010 (2026-09-06)' feature-requests/FR-975-id-ledger-reservation-protocol.md feature-requests/FR-980-id-ledger-route-enforcement.md` reports `1` for each file, while `grep -c '^\*\*Status:\*\* Judged — SPLIT' feature-requests/FR-970-load-bearing-atomic-id-allocation.md` reports `1`.
- [ ] AC-02: FR-975 and FR-980 each contain exactly one `## Superseded (2026-09-06)` block naming: FR-1010 operator decision (ii); the unimplemented-program rationale; the exact `max(ids on main + all open PR heads) + headroom` direct Plan/Enforce CAP/REQ contract; FR-701's unchanged post-hoc duplicate gate; and FR-1012 as the sole owner of census-authorized legacy deletion.
- [ ] AC-03: `git diff --unified=0 "$(git merge-base HEAD origin/main)"...HEAD -- feature-requests/FR-975-id-ledger-reservation-protocol.md feature-requests/FR-980-id-ledger-route-enforcement.md` shows only one Status replacement and one inserted Superseded block in each file; both `.judgement.md` siblings are byte-for-byte unchanged.
- [ ] AC-04: `git grep -n -E 'fr:[[:space:]]*FR-(975|980)' HEAD -- capabilities` returns no output, proving there is no owned CAP registry entry to retire.
- [ ] AC-05: `git grep -n -E 'FR-975|FR-980|id_ledger|id-ledger' HEAD -- tests scripts yamlgraph .github/hooks .github/workflows .pre-commit-config.yaml` returns no output. Any hit stops enforcement and returns FR-1015 to judgement under FR-1010 C-10.
- [ ] AC-06: The enforcement commit's changed-path set is exactly D-1 through D-4. It contains no FR-970 or FR-1010 edit and no code, capability, test, hook, workflow, pre-commit, graph, prompt, or judgement edit.
- [ ] AC-07: FR-1015's Implementation Status records the AC-01 through AC-06 command results and identifies both `tests/unit/test_id_registry.py` and `tests/unit/test_fr754_id_registry_package_boundary.py` as untouched FR-1012 census inputs.
- [ ] AC-08: `prior-art-gate`, `triage-gate`, and the repository's markdown/changelog checks pass on the changed files.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 must be folded into the committed FR and this advisory judgement must receive human review before authority activates. | GATE |
| C-2 | FR-1011 must be merged before FR-1015 enforcement begins; FR-1015 must merge before any FR-1012 enforcement begins. | GATE |
| C-3 | If any FR-975/FR-980 implementation or owned CAP/REQ claim appears before enforcement, stop and return to judgement under FR-1010 C-10. | GATE |
| C-4 | FR-970 remains the historical SPLIT parent and is not edited; FR-975/FR-980 judgement files remain immutable historical records. | GATE |
| C-5 | FR-1015 records authority for later census-governed deletion but performs no deletion, code change, test change, or enforcement-infrastructure change itself. | GATE |
| C-6 | FR-701's `validate_capabilities.py::validate_registry()` and its tests remain unchanged; it is described only as a post-hoc duplicate gate, not as an allocator or collision-prevention protocol. | GATE |
| C-7 | FR-1010 AC-03 remains unchecked until all of its stated conditions, including the later FR-1012 census deletion condition, are true. | GATE |

Authority granted: after R-1 through R-4 are folded, this draft is human-approved, and C-2's sequencing precondition is satisfied, enforcement may amend only FR-975, FR-980, FR-1015, and the FR-1015 changelog fragment as D-1 through D-4 specify.
