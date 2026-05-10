# Diary: FR-362 Watcher2 Sanity-Check Reflection

**Date:** 2026-05-10
**FR:** FR-362 Copilot instrumentation process-mining POC
**Author:** watcher2 (post-validate sanity reviewer)

---

## What Happened

FR-362 delivered a local Copilot process-mining POC in three committed artifacts:

1. `scripts/copilot_instrument.sh` — disposable-worktree runner capturing per-phase artifacts (prompt, stdout JSONL, stderr log, `--share` markdown, OTel JSONL, Copilot debug log, git status/diff snapshots) for `plan` and resumed `implement` phases.
2. `scripts/extract_copilot_events.py` — Pydantic-validated JSONL event extractor consuming OTel span data and git diff snapshots, emitting `CopilotProcessEvent` records with required `case_id`, `phase`, `event_type`, `timestamp`, `summary` fields.
3. `docs/copilot-instrumentation-poc.md` — findings document with all four required headings (`Captured Artifacts`, `Observed Event Sequence`, `Candidate Node Types`, `Next FR`).

All 8 acceptance criteria are ticked. All 3 RED tests pass (0.35 s). No changes to `yamlgraph/node_factory/copilot_node.py` or `CopilotResult` — the FR's "no framework integration" constraint is intact.

Diff scope: 7 files changed, +704 / -310 lines. The large deletion count reflects the FR document itself being heavily restructured during the enforce phase; the runtime artifact additions are proportional (213 lines shell script, 160 lines Python extractor, 64 lines findings doc, 90 lines tests).

---

## Trap

**`data_boundary_as_scope_creep`** — When writing the extractor, the natural impulse is to also parse `stdout.jsonl` (CLI structured output) and `share.md` (markdown session transcript) because both contain richer semantic content than early OTel spans. The FR constraint says two sources: OTel JSONL and git diff. Stopping at that boundary kept the extractor under 200 lines and the acceptance tests simple.

The related trap observed: the existing `docs/diary/2026-05-10-reflection-fr-362-copilot-instrumentation-poc.md` diary entry was already committed by the enforcer with a proportionality self-assessment table — a reviewable artifact that accelerated watcher2 analysis. That self-assessment was accurate and matched the independent diff review here.

---

## Root Cause

No defect identified. This is a greenfield POC with a correctly scoped deliverable. The only discipline challenge was the "while I'm here" impulse to expand event sources before the minimal contract was tested. The FR constraint explicitly names two sources; the tests verify exactly those two.

---

## What Worked

1. **Minimal event boundary**: Two source types (OTel span, git diff) with a Pydantic model at the boundary catches malformed inputs early without coupling the extractor to all artifact types.
2. **Disposable worktree safety**: `copilot_instrument.sh` creates and destroys a fresh worktree per run, enforcing the data boundary between instrumentation and development state.
3. **Self-documenting script**: The shell script's `usage()` function documents both phases and the `--resume` contract in-band, making the two-phase contract readable without a separate README section.
4. **Enforcer self-assessment in diary**: The pre-committed FR-362 diary entry already included a proportionality table, giving watcher2 a written claim to validate rather than reconstruct from scratch.

---

## Proportionality Assessment

| Signal | Verdict |
|--------|---------|
| Diff scope vs FR scope | ✅ Proportional — 3 deliverables, zero runtime changes, deletion count explained by FR document restructure |
| Test assertions check behavior | ✅ Structural and behavioral: file existence, script text contains phase labels, extractor runs against synthetic fixture and emits Pydantic-valid events |
| No speculative flags or extensibility | ✅ Two event types only; no conformance scorer; no CI automation |
| Data boundary respected | ✅ `outputs/` gitignored; only scripts and doc committed |
| No FSM pipeline log | ℹ️ No `logs/fsm-pipeline-*.log` present in worktree; not a blocker for a local POC FR |

---

## Seed

> When a POC extractor is intentionally limited to two artifact sources (OTel span, git diff) and the minimal contract is proven by tests, what is the minimum observable signal — span count, diff hunk count, or elapsed phase time — that would justify promoting a POC phase into a stable YAMLGraph `python` node rather than keeping it as a shell script step?

A future FR could define a "stabilization threshold": if N consecutive runs produce the same span sequence and diff shape (within a diff-size tolerance), the phase is considered deterministic enough to codify as a typed node. The extractor already emits all the data needed to compute this threshold; it just needs an aggregator step.
