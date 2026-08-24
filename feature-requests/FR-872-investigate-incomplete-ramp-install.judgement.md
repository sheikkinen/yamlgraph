# Judgement: FR-872 Investigate the Incomplete Ramp Install in deviant-daily

**Prior art:** `FR-872-investigate-incomplete-ramp-install.md` is the FR under judgement, not precedent. `FR-864` (family parent, SPLIT) and `FR-867` (the application whose gaps this investigates) are dispositioned inside the FR's own Prior art line and reviewed below as governing records. `FR-798` matches only on the word "investigate" — different territory (test-suite failure classification), no overlap.

**Verdict:** APPROVED WITH REVISIONS -- the investigation is the right next step and should not become remediation, but authority activates only after the FR removes pre-judged conclusions, resolves its label/cardinality contradictions, and freezes a read-only cross-repo evidence boundary.

**Reviewed against:** `feature-requests/FR-872-investigate-incomplete-ramp-install.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-865-ramp-installer.judgement.md`; `feature-requests/FR-865-ramp-installer.amendment.judgement.md`; `feature-requests/FR-866-ramp-tailoring-graphs.md`; `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md`; `feature-requests/FR-867-ramp-deviant-daily.md`; `feature-requests/FR-867-ramp-deviant-daily.judgement.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`; `docs/plan-ramp-spike-to-governed.md`; `docs/diary/diary-2026-08-24-twenty-gates-and-a-human-found-the-fire.md`; `ramp/manifest.yaml`; `ramp/curation-diffs.md`; `ramp/assets/tier2/scripts/judge.sh`; `ramp/assets/tier2/scripts/review.sh`; `ramp/assets/tier2/github/skills/judge-fr/SKILL.md`; `ramp/assets/tier2/github/skills/review-pr/SKILL.md`; committed target checkout `sheikkinen/deviant-daily` at `12bd530`, specifically `docs/ramp-manifest.md`, `scripts/judge.sh`, `scripts/review.sh`, `.github/workflows/tests.yml`, `AGENTS.md`, `.github/skills/judge-fr/`, `.github/skills/review-pr/`, and `capabilities/`. No author chat narrative was consumed, and no judge route was invoked.

## What is sound

The problem is real and time-sensitive. FR-872 records that the Tier-3 `deviant-daily` ramp installed 20 hash-verified assets but left several governance surfaces stubbed, absent, or unusable (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:25-29`, `41-51`). The target's committed install manifest corroborates the 20 installed rows and records `reviewed_source_sha: pending-human-review` (`/Users/sheikki/Documents/src/deviant-daily/docs/ramp-manifest.md:7-32`), while the installed `AGENTS.md` is explicitly still a stub (`/Users/sheikki/Documents/src/deviant-daily/AGENTS.md:1-9`) and the installed CI workflow declares itself an inert setup stub, not an active gate (`/Users/sheikki/Documents/src/deviant-daily/.github/workflows/tests.yml:1-18`).

The FR correctly chooses investigation before remediation. The gaps plausibly come from different authorities: FR-865's generic installer, FR-866's draft-producing graphs, FR-867's target-application steps, and deliberate design decisions. FR-872 explicitly says fixing without attribution would put target-specific content into the generic installer (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:70-75`), which aligns with the repo cure `investigation_before_fix` (`.github/copilot-instructions.md:111`). That is a strong scope boundary.

The proposed evidence set is feasible. `ramp/manifest.yaml` is a closed manifest of installed assets and does not include adapter graph artifacts under skill directories (`ramp/manifest.yaml:45-122`); the curated judge/review scripts both reference adapter graph paths and fail if those paths are absent (`ramp/assets/tier2/scripts/judge.sh:20-23`, `ramp/assets/tier2/scripts/review.sh:21-24`). The target checkout at `12bd530` is clean and contains the same installed scripts and skill directories without an `adapters/` directory, so the central closure question can be answered from committed artifacts.

The work is a single responsibility: a disposition table and routing record, not a fix. It is not a YAMLGraph framework primitive and not a new graph-authoring task. Strategic classification: **investigation / pattern documentation** within the ramp governance tooling, with any resulting implementation defects routed to follow-up FRs.

## Required revisions

### R-1: Replace contradictory disposition labels with a primary-plus-secondary schema

Resolve the FR's cardinality contradiction before enforcement. The summary says seven governance surfaces are placeholders or non-functional (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:25-29`), the Problem table lists nine surfaces including working ones (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:41-51`), AC-01 requires exactly one disposition per surface (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:103-105`), and the Risks section says contested rows get both labels (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:128-131`).

Fold this by replacing AC-01 and the Problem-table language with a closed row set and explicit fields: `primary_disposition` is exactly one of `installer-defect`, `fr-867-step`, or `deliberate`; `secondary_dispositions` is optional and may contain additional contributing labels; every label must cite the deciding artifact. State whether the live `.pre-commit` and Copilot guard rows are in scope as positive controls or excluded from the gap count.

### R-2: Reframe the `judge.sh`/`review.sh` failure as a hypothesis until reconciled with curation evidence

Remove the claim that `scripts/judge.sh` is "the one unambiguous defect" and already an installer defect (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:53-64`). The cited implementation record says the curated wrappers intentionally add an adapter-graph existence check because the installer ships no graphs (`feature-requests/FR-865-ramp-installer.md:297-300`), and the curation record states the adapter graph "must be authored in the target per its own doctrine" rather than shipped by the installer (`ramp/curation-diffs.md:45-54`, `56-62`). At the same time, the installed skill wrapper says `adapters/` is part of the bundle map and the YAMLGraph adapter is the sole permitted route (`ramp/assets/tier2/github/skills/judge-fr/SKILL.md:22-40`; `ramp/assets/tier2/github/skills/review-pr/SKILL.md:23-40`).

Fold this by making `judge.sh` and `review.sh` ordinary investigation rows. Their disposition must reconcile all four artifacts: manifest entries, curation-diff rationale, installed script references, and installed skill bundle maps. If the final label is `installer-defect`, the table must state why FR-865's curation rationale is insufficient. If the final label is `deliberate` or `fr-867-step`, the table must state the concrete route by which the target obtains usable judge/review adapters before it can govern its own FRs.

### R-3: Freeze the evidence boundary and permitted writes

Clarify AC-07 so it does not contradict AC-08. AC-07 says no source file in either repository is modified (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:116-118`), while AC-08 requires adding the disposition table to this FR and referencing it from FR-867 (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:119-120`). The Proposed Solution also routes deliberate outcomes to `docs/plan-ramp-spike-to-governed.md` (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:96-99`).

Fold this by defining the boundary exactly: the target repository is read-only; yamlgraph runtime code, ramp assets, graph artifacts, prompts, hooks, CI, and skill doctrine are read-only; permitted yamlgraph writes are limited to `feature-requests/FR-872-investigate-incomplete-ramp-install.md`, the FR-867 reference, and any explicitly named documentation/proposal artifact needed to route a row. The enforcement record must include before/after `git status --short` and HEAD for both repositories, proving the target did not change.

### R-4: Make routing mechanically complete per row

Add a routing field to the disposition table. The current Proposed Solution says installer defects go to an FR-865 follow-up, unfinished steps go to FR-867, and deliberate outcomes go to `docs/plan-ramp-spike-to-governed.md` (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:96-99`), but the acceptance criteria only require adding a table to FR-872 and referencing it from FR-867 (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:119-120`).

Fold this by requiring every row to name `route_target`: an existing FR plus AC number, a new follow-up FR/proposal path, or a documentation section with no implementation action. For each `installer-defect` row, keep AC-05's requirement to name the FR-865 AC that should have caught it or state that none exists (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:112-113`). For each `fr-867-step` row, keep AC-06's requirement to name the owning FR-867 AC (`feature-requests/FR-872-investigate-incomplete-ramp-install.md:114-115`). For each `deliberate` row, cite the controlling design decision or curation record.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-872-investigate-incomplete-ramp-install.md` folding R-1 through R-4 |
| D-2 | Read-only evidence collection from yamlgraph ramp artifacts and committed `deviant-daily` target artifacts |
| D-3 | A dated disposition table in FR-872 with primary/secondary labels, evidence citations, and route targets per row |
| D-4 | A reference from FR-867 to the completed disposition table |
| D-5 | Optional routing-only documentation/proposal artifacts explicitly named by the revised FR |
| D-6 | Before/after repo-boundary record for yamlgraph and `deviant-daily` |

Not authorized: fixing `scripts/judge.sh` or `scripts/review.sh`; adding adapter graphs to `deviant-daily`; changing `ramp/manifest.yaml`, `ramp/assets/`, curation records, yamlgraph hooks, CI, judge/review doctrine, graph-authoring doctrine, or runtime code; running graph authoring; running the judge/review adapter route; landing `AGENTS.md`, RTM entries, test requirement tags, `docs/incidents.md`, or active CI in the target; modifying any target-repo file; copying secrets, token-bearing logs, generated images, archives, nested repos, or submodules across repository boundaries.

## Revised acceptance criteria

- [ ] AC-01: FR-872 is revised to define the closed investigation row set, primary/secondary disposition schema, evidence boundary, permitted write set, and per-row routing contract from R-1 through R-4.
- [ ] AC-02: Before evidence collection, the record captures yamlgraph HEAD/status and `deviant-daily` HEAD/status; the target repo must be clean and remains read-only throughout the investigation.
- [ ] AC-03: Every in-scope row has `primary_disposition` exactly one of `installer-defect`, `fr-867-step`, or `deliberate`, optional `secondary_dispositions`, and at least one deciding committed artifact cited by path and line/section.
- [ ] AC-04: `scripts/judge.sh` and `scripts/review.sh` have their referenced-path closure enumerated from the installed scripts and skill files; every absent referenced path is listed and reconciled against `ramp/manifest.yaml` and `ramp/curation-diffs.md`.
- [ ] AC-05: `ramp/manifest.yaml` is scanned for every shipped launcher or instruction artifact that references paths not shipped by the manifest; the result is stated even if empty.
- [ ] AC-06: A mechanical follow-up check is proposed, not implemented here, that would catch launcher-without-dependency or instruction-without-bundle closure gaps at install validation time.
- [ ] AC-07: Each `installer-defect` row names the FR-865 acceptance criterion that should have caught it, or states that no existing criterion covers it and names the follow-up route.
- [ ] AC-08: Each `fr-867-step` row names the FR-867 acceptance criterion or remaining-step record it belongs to.
- [ ] AC-09: Each `deliberate` row cites the controlling design decision, judgement condition, curation record, or accepted limitation that makes it deliberate.
- [ ] AC-10: The completed disposition table is added to FR-872 and referenced from FR-867; any deliberate-outcome documentation or installer-defect follow-up proposal is limited to the route target named in the table.
- [ ] AC-11: Completion records final yamlgraph and `deviant-daily` HEAD/status; `deviant-daily` is unchanged, and yamlgraph changes are limited to the revised FR/documentation/proposal artifacts authorized by AC-10.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into `feature-requests/FR-872-investigate-incomplete-ramp-install.md`. | GATE |
| C-2 | Do not invoke or re-run the judge, review, authoring, or yamlgraph graph routes while enforcing this investigation. | GATE |
| C-3 | The target repository is read-only; any target modification, including "just fixing" a launcher, moves to FR-867 or a follow-up FR. | GATE |
| C-4 | If the investigation identifies a defect in ramp assets, skill doctrine, wrappers, adapter distribution, hooks, or CI, record and route it; do not repair enforcement infrastructure under FR-872. | GATE |
| C-5 | Generated governance artifacts remain out of scope: no AGENTS replacement, RTM registry entries, requirement tags, incidents document, or active CI may be landed here. | GATE |
| C-6 | Cross-repo evidence must be from committed artifacts or a recorded clean checkout state; no author chat narrative or uncommitted working notes may decide a row. | GATE |

Authority granted: after the required revisions are folded, enforcement may perform the read-only attribution investigation, update the authorized FR/documentation routing records, and stop before any remediation.
