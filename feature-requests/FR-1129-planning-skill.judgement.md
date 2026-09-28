# Judgement: FR-1129 Planning skill — state the operations, not the effort

**Prior art:** see FR-1129's own Prior art field — this judgement reviews those citations; FR-1047, FR-765 and FR-945 match only on the noun "skill" (other skills' judgements) and are not precedent for FR planning.

**Verdict:** APPROVED WITH REVISIONS — replacing the uninformative effort field with a concrete operations record is sound, but authority activates only after the plan removes the redundant standalone skill, resolves its reconciliation contradiction, and makes evidence, prior art, tests, and requirement ownership complete.

**Reviewed against:** `feature-requests/FR-1129-planning-skill.md`; `feature-requests/FR-1129.research.md`; `feature-requests/research-briefs/planning-operations-list.md`; `feature-requests/TEMPLATE.md`; `.github/skills/feature-request/SKILL.md`; `ramp/manifest.yaml`; `feature-requests/FR-746-ideal-result-slot.md`; `feature-requests/FR-965-graduate-map-reduce-corpus-cure.md`; `feature-requests/FR-1022-judge-round-sentinel.md`; `feature-requests/FR-452-standalone-planner-demo.md`; `feature-requests/FR-096-fr-template-demo-plan.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `docs/development-process.md`; `capabilities/CAP-243-requirement-witness-audit.yaml`; `tests/unit/test_ramp_installer.py`.

## What is sound

- **Scope and value:** The first consumer and first event are concrete (`feature-requests/FR-1129-planning-skill.md:7-10`), and the proposed record exposes decisions that a duration estimate cannot: probes, branches, delegations, waits, and audit-visible commands (`:27-37`, `:90-110`). Removing the template's `**Effort:**` field is a direct subtraction from the witnessed problem (`:41-46`).
- **Research substance:** The committed research record carries its brief, run date, five executed personas, alternatives, precedents, and an explicit `is_this_a_graph` answer (`feature-requests/FR-1129.research.md:3-5`, `:32-38`). It also catches and rejects the phantom `fr-planner` precedent (`:7-15`). The selected solution is correctly classified as **pattern documentation**: one demonstrated consumer, no graph requirement, and an existing FR-authoring abstraction.
- **Architecture alignment:** The proposal preserves sole routes, keeps the standard pipeline implicit, leaves historical FRs unchanged, and identifies the Ramp template's `mirror_exact` obligation (`feature-requests/FR-1129-planning-skill.md:76-82`, `:92-112`; `ramp/manifest.yaml:45-50`).
- **Feasibility and testability:** The template and guidance are static artifacts whose headings, front matter, YAML sample, mirror bytes, and prohibited duration tokens can be tested directly. The existing Ramp test already establishes byte-exact mirror verification.
- **Single responsibility:** Removing a misleading field and replacing it with the operations that planning needs are one artifact-shape change. The deterministic audit-log reconciler is correctly recognized as separate implementation work, provided this FR stops claiming that automation as part of its delivered result.

## Required revisions

### R-1: Keep FR planning in the existing `feature-request` skill

Delete the proposed `.github/skills/planning/SKILL.md` deliverable and fold the section contract, no-duration rule, worked I1 sample, timing guidance, and completion-reconciliation guidance into `.github/skills/feature-request/SKILL.md`. That skill already declares “writing a feature request” and “planning a feature” as triggers and owns the Plan step (`.github/skills/feature-request/SKILL.md:2-4`, `:11-15`). A second skill owning one section of the same FR would duplicate routing rather than resolve overlap, contrary to the research constraint (`feature-requests/research-briefs/planning-operations-list.md:64-67`).

Rename the FR and revise its Summary, Proposed Solution, template pointer, acceptance criteria, and purge list accordingly. The template must point to the existing `feature-request` skill, not to a new `planning` skill.

### R-2: Make manual reconciliation the explicit boundary of this FR

The research brief requires deterministic LLM-free reconciliation (`feature-requests/research-briefs/planning-operations-list.md:60-63`), while this FR defers that mechanism (`feature-requests/FR-1129-planning-skill.md:121`, `:161`) yet promises comparison with the audit record (`:35-37`) and only asks for an unspecified “reconciliation paragraph” and implementation status (`:71-72`, `:153-154`).

Fold one coherent contract:

1. State that FR-1129 delivers a human-readable, manually reconciled record, not an automated verifier.
2. Replace the vague paragraph with an exact completion table schema: `Planned operation | Outcome (ran / did not run / changed) | Witness`, followed by an `Unplanned operations` list whose empty value is explicitly `None`.
3. Require command witnesses to cite an audit-log match, commit, CI run, or named human decision; a claim without a witness is not reconciled.
4. Narrow the Value Statement and Ideal Result from automated/checkable reconciliation to operator-visible manual comparison.
5. Keep the deterministic audit-log reconciler explicitly not authorized and require it to re-enter the pipeline as a separate FR after session-to-FR mapping is designed.

This preserves one concern without silently violating the research constraint.

### R-3: Commit or remove the quantitative evidence

The problem relies on effort/active-time statistics and audit-command counts (`feature-requests/FR-1129-planning-skill.md:41-51`), but the cited research brief says the measurement output exists only at `tmp/fr_effort_vs_actual.txt` in another checkout (`feature-requests/research-briefs/planning-operations-list.md:75` onward), and the audit log is untracked. Neither is available to this input-closed judgement.

Before authority activates, either:

- promote a reproducible command plus its raw aggregate output into a committed FR-1129 evidence artifact and cite it from the FR; or
- remove the unavailable numbers and narrow the rationale to committed, directly inspectable facts: the template requires the field, the field has no repository parser, and the operations section exposed the cited dry-run blockers.

Do not retain precision that the committed evidence cannot reproduce.

### R-4: Disposition every retrieved precedent in the FR

Add explicit Prior art dispositions for the five retrieval hits listed in `feature-requests/FR-1129.research.md:25-30`: FR-578, FR-845, FR-291, FR-514, and FR-587. A collective statement in the research header is useful but does not satisfy the template's one-clause-per-entry rule (`feature-requests/TEMPLATE.md:21-29`). Preserve the existing dispositions of FR-746, FR-853, FR-965, FR-1022, FR-452, FR-096, and the phantom `fr-planner`.

### R-5: Close the witness-test and requirement contract

Replace the unspecified “new REQ ID” (`feature-requests/FR-1129-planning-skill.md:148-151`) with these concrete deliverables:

1. Name `tests/unit/test_fr1129_planned_operations.py` as the witness-test file.
2. Allocate a free `REQ-YG-XXX` immediately before RED and declare it in a new `capabilities/CAP-XXX-fr-planned-operations.yaml`; regenerate the corresponding `ARCHITECTURE.md` row. The capability owns the FR template, its Ramp mirror, the `feature-request` skill guidance, and this test.
3. Give the worked sample unique begin/end markers so the test extracts exactly one fenced YAML document rather than guessing among code blocks.
4. Require the parsed document to have exactly the keys `probes`, `branches`, `delegations`, `waits`, and `commands`, each containing a non-empty list of strings.
5. Define the no-duration check case-insensitively over numeric values followed by milliseconds, seconds, minutes, hours, days, weeks, months, or years, including common abbreviations; the current expression misses values such as `30 seconds`, `2 months`, and `1 year` (`feature-requests/FR-1129-planning-skill.md:83-88`).
6. Require the witness test to verify the exact manual reconciliation schema from R-2, the canonical template/inline-template changes, mirror equality, sample parsing, and the absence of a standalone `.github/skills/planning/` skill.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/TEMPLATE.md`: remove `**Effort:**`; add `## Planned Operations` directly after `## Ideal Result`; point to the existing `feature-request` skill |
| D-2 | `ramp/assets/tier2/feature-requests/TEMPLATE.md`: byte-exact mirror of D-1 |
| D-3 | `.github/skills/feature-request/SKILL.md`: Plan-step guidance, inline template, exact operations contract, no-duration rule, marked I1 sample, and manual completion-reconciliation schema |
| D-4 | `tests/unit/test_fr1129_planned_operations.py`: RED witness for the frozen artifact contract |
| D-5 | `capabilities/CAP-XXX-fr-planned-operations.yaml` and generated `ARCHITECTURE.md` requirement row |
| D-6 | One FR-1129 changelog fragment under `changelog/unreleased/` |
| D-7 | One FR-1129 diary entry under `docs/diary/` with a `**Seed:**` |
| D-8 | `feature-requests/FR-1129-planning-skill.md`: folded revisions, status/decisions, and completed manual reconciliation table |
| D-9 | A committed measurement evidence artifact only if the quantitative claims retained by R-3 require it |

Not authorized: `.github/skills/planning/SKILL.md` or any second FR-planning skill; a graph or prompt; an audit-log/session reconciler; hooks, CI, pre-commit, sole-route wrappers, or judge/review doctrine changes; changes to `.github/hooks/logs/audit.jsonl`; duration enforcement across historical FRs; rewriting or deleting historical `Effort:` fields; changing the research artifact's `effort-risk` column; modifying the standalone planner demo; any generic delegation framework.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/TEMPLATE.md` has no `**Effort:**` line and has `## Planned Operations` directly after `## Ideal Result`, with one line directing authors to the existing `feature-request` skill.
- [ ] AC-02: `ramp/assets/tier2/feature-requests/TEMPLATE.md` is byte-identical to `feature-requests/TEMPLATE.md`; the existing Ramp mirror-exact test passes.
- [ ] AC-03: `.github/skills/feature-request/SKILL.md` updates its Plan step and inline template, defines the five-key operations contract, forbids numeric durations while allowing counts and named waits, contains the uniquely marked I1 sample, and defines the exact completion table plus `Unplanned operations` contract from R-2.
- [ ] AC-04: No `.github/skills/planning/SKILL.md` or other new planning skill exists.
- [ ] AC-05: The I1 sample extracts as exactly one YAML document with exactly `probes`, `branches`, `delegations`, `waits`, and `commands`; every value is a non-empty list of strings; no numeric duration with a millisecond-through-year unit or common abbreviation appears, case-insensitively.
- [ ] AC-06: `tests/unit/test_fr1129_planned_operations.py` directly witnesses AC-01..AC-05 and the reconciliation schema, carries the allocated requirement marker on every test, and is committed RED before GREEN.
- [ ] AC-07: A new active capability file owns the planned-operations contract and declares the allocated requirement; `ARCHITECTURE.md` is regenerated; `python scripts/req_coverage.py --strict` and capability validation pass.
- [ ] AC-08: Every prior-art retrieval hit in `feature-requests/FR-1129.research.md:25-30` has an explicit disposition in the FR.
- [ ] AC-09: Every quantitative claim retained in the Problem is reproducible from a committed cited artifact; otherwise the unavailable claim is removed.
- [ ] AC-10: The changelog fragment exists and the diary entry contains a substantive reflection and `**Seed:**`.
- [ ] AC-11: The FR's implementation status contains one row for every planned operation with `ran`, `did not run`, or `changed` plus a concrete witness, and separately records all unplanned operations or `None`.
- [ ] AC-12: Existing FR files retain their historical `Effort:` lines, and the deterministic reconciler and all other not-authorized surfaces have no diff.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority remains inactive until R-1 through R-5 are folded into the FR and the FR no longer claims a standalone planning skill or automated reconciliation. | GATE |
| C-2 | Allocate the capability and requirement IDs from the live registry immediately before the RED commit; do not reserve a colliding or speculative ID in advance. | GATE |
| C-3 | Commit the failing witness test before implementation and preserve separate RED and GREEN commits. | GATE |
| C-4 | Keep the canonical and Ramp templates byte-identical throughout enforcement. | GATE |
| C-5 | Do not edit historical FRs, enforcement infrastructure, graph artifacts, or the deterministic reconciliation surface. | GATE |
| C-6 | Complete D-8 only from audit-visible or repository-visible witnesses; do not mark an operation reconciled from memory alone. | GATE |

Authority granted: after all required revisions are folded, implementation may replace the template effort field with the planned-operations section, document that section within the existing `feature-request` skill, add its traceability and witness test, mirror the template, and record the manually reconciled outcome—nothing else.
