# Judgement: FR-852 Preserve Graph-Authoring Briefs as Committed Planning Artifacts

**Verdict:** APPROVED WITH REVISIONS — the provenance problem is real and worth fixing, but authority activates only after the FR replaces its uncommitted `tmp/` glob with a durable migration manifest and resolves the contradiction between "no FR cites a gitignored path" and "no retroactive rewriting."

**Reviewed against:** `feature-requests/FR-852-preserve-authoring-briefs.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/SKILL.md`; `.github/skills/graph-authoring/adapters/README.md`; `.gitignore`; `docs/diary/diary-2026-08-15-fr789-brief-is-code.md`; `feature-requests/FR-806-author-sh-brief-preflight.md`; cited provenance examples in `feature-requests/FR-771-vision-demo-executes-manifest-tool.md`, `feature-requests/FR-776-vision-fallback-scanned-pdf.md`, `feature-requests/FR-779-research-agent-demo-rot.md`, `feature-requests/FR-780-research-agent-toolbelt-conversion.md`, `feature-requests/FR-787-api-discovery-recon-step.md`, `feature-requests/FR-789-api-discovery-browser-sniff-step.md`, `feature-requests/FR-790-api-discovery-schema-extract-step.md`, `feature-requests/FR-791-api-discovery-orchestrator.md`, `feature-requests/FR-796-reclassify-watcher2-witness-demos.md`, and `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md`.

## What is sound

The first consumer is concrete: a successor reading an FR that points at `scripts/author.sh tmp/...` cannot recover the authoring input once `tmp/` is cleaned (`feature-requests/FR-852-preserve-authoring-briefs.md:8-11`). The value statement is also narrow and real: recover the exact input closure of authored graph artifacts from the repository rather than from a gitignored path (`feature-requests/FR-852-preserve-authoring-briefs.md:22-23`; `.gitignore:21-24`).

The proposal aligns with existing graph-authoring doctrine. The adapter contract already says the task brief closes the input and is "committed or explicitly provided" (`.github/skills/graph-authoring/adapters/README.md:12-14`), while the authoring doctrine says the task request is the `task_path` brief and must not be inferred from hidden chat narrative or ignored local state (`.github/skills/graph-authoring/doctrine.md:21-31`). Giving briefs a committed home is a boundary fix, not a new framework primitive.

The incident evidence is strong enough to justify preserving briefs as planning artifacts. The FR-789 diary records that the brief itself caused the failed run and names the brief as a pipeline component carrying defects (`docs/diary/diary-2026-08-15-fr789-brief-is-code.md:8-24`), then extracts the heuristic that validation premises in briefs need spec-level scrutiny (`docs/diary/diary-2026-08-15-fr789-brief-is-code.md:36-47`). FR-806 subsequently codified the same class by treating the brief as untrusted input at the authoring boundary (`feature-requests/FR-806-author-sh-brief-preflight.md:32-40`, `feature-requests/FR-806-author-sh-brief-preflight.md:64-96`).

## Required revisions

### R-1: Replace the `tmp/*brief*.md` glob with an exact committed migration manifest

Revise the FR to name the exact historical briefs to preserve in a table with at least: old `tmp/` path, new committed path, governing FR or standalone consumer, inclusion rationale, and whether the source was present for migration. The current plan's `cp tmp/*brief*.md` instruction and "uncited scratch briefs ... copied as-is" rule are not judgeable or review-safe because `tmp/` is ignored and outside committed input closure (`feature-requests/FR-852-preserve-authoring-briefs.md:69-74`; `.gitignore:21-24`; `.github/skills/graph-authoring/doctrine.md:21-31`). Do not authorize a wildcard copy from ignored local state.

The evidence inventory must also be corrected. FR-852 says "At least 9 FRs" while listing eleven IDs (`feature-requests/FR-852-preserve-authoring-briefs.md:30-31`), and the cited files are not uniform: FR-771 only says the edit used `scripts/author.sh` without a tmp brief path (`feature-requests/FR-771-vision-demo-executes-manifest-tool.md:78`), FR-789's FR body cites `tmp/draft-authoring-report.md` rather than a brief path (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:73`), and FR-791 records two runs plus `tmp/draft-authoring-report.md` but not the brief filenames (`feature-requests/FR-791-api-discovery-orchestrator.md:122-128`). Keep the problem statement, but make the cited evidence exact.

### R-2: Resolve the provenance-reference contradiction in committed artifacts

Choose one durable repair and fold it into the FR: either update every affected FR implementation record to cite the new committed brief path, or add a committed index under `feature-requests/authoring-briefs/` and update the affected FRs to point at that index. The current FR's ideal says "No FR cites a gitignored path as provenance" and the governing FR should cite the committed brief (`feature-requests/FR-852-preserve-authoring-briefs.md:52-55`), but the proposed solution says "no retroactive rewriting of FR prose" and relies on the migration commit message for the map (`feature-requests/FR-852-preserve-authoring-briefs.md:75-76`). A commit message alone is not enough to satisfy the stated reader workflow.

### R-3: Tighten the acceptance criteria into mechanical checks

Replace the current broad criteria (`feature-requests/FR-852-preserve-authoring-briefs.md:80-88`) with checks derived from the manifest and citation strategy: exact file existence, exact naming convention validation, no unlisted brief files in the new directory, old-to-new mapping present in committed markdown, documentation wording updated in the three named graph-authoring surfaces, and changelog fragment present. "Contains the migrated briefs from tmp/" is not measurable until "the migrated briefs" is an enumerated set.

### R-4: Add a human-review gate for ignored-file migration and doctrine edits

Because this FR commits material copied from an ignored planning directory and edits workflow doctrine, add an explicit enforcement condition that a human must review the migration manifest and the migrated content before commit. This follows judge discipline for enforcement/process infrastructure changes and prevents accidentally committing unrelated scratch, private notes, reports, logs, or stale generated artifacts (`.github/skills/judge-fr/doctrine.md:96-103`; `.gitignore:21-24`; `feature-requests/FR-852-preserve-authoring-briefs.md:69-74`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Amended `feature-requests/FR-852-preserve-authoring-briefs.md` with the exact migration manifest and folded revisions |
| D-2 | `feature-requests/authoring-briefs/` containing only manifest-listed preserved brief files |
| D-3 | A committed old-path to new-path provenance index, or affected FR updates that cite the new committed brief paths |
| D-4 | `.github/skills/graph-authoring/doctrine.md`, `.github/skills/graph-authoring/SKILL.md`, and `.github/skills/graph-authoring/adapters/README.md` wording aligned on the committed brief home for future runs |
| D-5 | One changelog fragment for the process/doctrine change |

Not authorized: changes to `scripts/author.sh`, pre-flight behavior, hooks, judge/review doctrine, graph artifacts, prompt artifacts, or any authoring adapter execution semantics; committing `tmp/draft-authoring-report.md`, logs, reports, or unlisted scratch files; broad `cp tmp/*brief*.md` migration; inventing placeholders for missing historical briefs.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/FR-852-preserve-authoring-briefs.md` contains a migration manifest enumerating every old `tmp/` brief path to preserve, its new committed path, its governing FR or standalone consumer, and its inclusion rationale.
- [ ] AC-02: `feature-requests/authoring-briefs/` exists, and every file in it is listed in the manifest; every manifest-listed source that was available during enforcement has a corresponding committed destination file.
- [ ] AC-03: Every FR-bound destination filename follows `fr-XXX-<slug>-brief.md`; every standalone destination follows `<slug>-brief.md` and has a named consumer in the manifest.
- [ ] AC-04: Historical provenance is recoverable from committed artifacts: each affected FR either cites the new committed brief path directly or cites a committed `feature-requests/authoring-briefs/` index that maps its old `tmp/` reference to the new path.
- [ ] AC-05: `.github/skills/graph-authoring/doctrine.md`, `.github/skills/graph-authoring/SKILL.md`, and `.github/skills/graph-authoring/adapters/README.md` state that future requesting sessions should place FR-bound task briefs under `feature-requests/authoring-briefs/` and cite that committed path from the governing FR.
- [ ] AC-06: No wrapper, hook, graph, prompt, judge, or review route behavior changes are included; this FR is documentation/provenance migration only.
- [ ] AC-07: No reports, logs, draft judgements, draft authoring reports, or unlisted scratch notes from `tmp/` are committed.
- [ ] AC-08: A changelog fragment exists under `changelog/unreleased/` describing the authoring-brief provenance change.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into the FR before implementation authority activates. | GATE |
| C-2 | A human must review the migration manifest and migrated brief content before committing any file copied from ignored `tmp/`. | GATE |
| C-3 | Do not use wildcard migration from `tmp/`; copy only manifest-listed files with explicit destinations. | GATE |
| C-4 | If a historical brief source is missing, record it as unavailable in the manifest or index; do not invent, reconstruct, or paraphrase it. | GATE |
| C-5 | Keep enforcement out of `scripts/author.sh`, hooks, judge/review doctrine, graph artifacts, and prompt artifacts. | GATE |

Authority granted: after the required revisions are folded, enforce only the committed brief home, exact historical brief migration, durable provenance mapping, graph-authoring documentation alignment, and changelog fragment described above.

**Prior art:** dispositions in the parent FR `feature-requests/FR-852-preserve-authoring-briefs.md`.
