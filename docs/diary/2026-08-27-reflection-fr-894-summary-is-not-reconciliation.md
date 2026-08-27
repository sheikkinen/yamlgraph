# FR-894: Summary Is Not Reconciliation

**Date:** 2026-08-27
**FR:** FR-894
**Context:** Documenting the corpus map-reduce architecture after using a
Mercury-2 map/reduce to read 1,278 diary files, then considering the same shape
for GitHub commits and pull requests. While the work remained private, remote
main shipped FR-892's reusable corpus-census graph and allocated FR-891 to a
different defect; the documentation FR was rebuilt as FR-894 on current main.

## What changed

The implementation was intentionally only a reference pattern. Existing graphs
already proved all the machinery: deterministic collection, bounded partitions,
cheap-model map calls, code-side reconciliation, hierarchical reduction, and a
durable report. FR-892 then centralized the reusable discover/extract/map/reduce
skeleton while this session was writing. The remaining gap was the contract
connecting execution to exhaustiveness, authority, cost, privacy, and review.

The reference now names six stages and seven invariants. It also separates two
tasks that initially looked like one:

- "What changed?" needs an exhaustive descriptive recap.
- "What changed that was not supposed to change?" needs an independent
  authority plane and the actual diff as a separate reality plane.

Without the first plane, the honest result is surprising or unexplained change,
not unauthorized change. A PR body or commit message cannot authorize itself.

## Trap

**`summary_without_authority`**: a model sees an unexpected diff, compares it
to the change author's own summary, and upgrades surprise into a scope verdict.
The output sounds like review because it names files and intent, but it has no
independent statement of what was permitted. This is `gate_checks_shape_not_substance`
at the review boundary: diff plus prose has the shape of reconciliation while
lacking authority.

The sibling trap is `reducer_erases_primary_evidence`: a polished final recap
can hide which items were skipped or which primary findings disagreed. The
coverage invariant and immutable per-item results prevent the synthesis from
becoming a plausible replacement for the corpus it claims to summarize.

**`private_plan_treats_precedent_as_frozen`** fired at the repository boundary:
the local plan correctly rejected building another graph because FR-857 was
parked, but remote main had already shipped the stronger FR-892 implementation.
The fix was not conflict resolution. It was re-research and rejudgement against
current committed reality, plus a fail-closed update: `on_error: skip` is safe
only because FR-892's reducer makes every missing index fatal.

## Heuristic

**Freeze identity before interpretation; reconcile claims before synthesis;
name authority before alleging drift.** If independent authority is absent,
report observation and uncertainty. If a live PR may be blocked, escalate from
cheap corpus triage to the governed review route rather than granting the
classifier merge authority.

## Seed:

FR-892 now owns the executable skeleton and this reference owns the evidence
contract. At the next N-item analysis request, will the agent both call
`corpus_census` and apply the seven invariants, or will execution and doctrine
remain separately discoverable? The first missed invocation should be recorded
as an adoption defect, not answered with a third corpus instrument.
