# Feature Request: Preserve Graph-Authoring Briefs as Committed Planning Artifacts

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented (2026-08-22)
**Effort:** 0.5 days
**Requested:** 2026-08-22
**First consumer / first event:** the next session that reads an FR citing
`scripts/author.sh tmp/fr-XXX-authoring-brief.md` and needs the brief to
understand the authored artifact's input closure — today that path is
gitignored and the provenance is gone the moment tmp/ is cleaned.

## Summary

Give graph-authoring task briefs a committed home
(`feature-requests/authoring-briefs/`), require new briefs to be
committed there, and copy the existing tmp/ briefs over as a one-time
chore so FR provenance references stop dangling.

## Value Statement

FR readers and successor sessions recover the exact input closure of any
authored graph artifact, instead of hitting a dangling gitignored path.

## Problem

Graph-authoring briefs are load-bearing planning artifacts stored in a
gitignored directory:

- Ten committed FRs cite a tmp/ brief path by name as their sole-route
  execution record: FR-776, FR-779, FR-780, FR-787, FR-790, FR-795,
  FR-796, FR-809, FR-819, FR-851 (verified by grep 2026-08-22).
  FR-771 records `scripts/author.sh` without a brief path; FR-789 and
  FR-791 cite `tmp/draft-authoring-report.md` rather than the brief.
  tmp/ is gitignored — every such citation is a dangling provenance
  reference.
- Graph-authoring doctrine defines input closure as "task brief +
  committed repository artifacts + files the brief explicitly names".
  The brief is the ONLY non-repo input to an authored artifact; if it is
  not preserved, the artifact's provenance is unrecoverable.
- `adapters/README.md` already states the brief is "a committed or
  explicitly provided markdown file" — committed is the first-listed
  expectation, but no committed home exists.
- diary-2026-08-15-fr789-brief-is-code.md established the brief is code
  and carries defects (FR-789's brief shipped a bug that burned an
  adapter run). Code is preserved; the brief is not.
- Asymmetry with the judge pipeline: `tmp/draft-judgement.md` graduates
  to a committed `.judgement.md`; briefs have no equivalent graduation.

34 brief files sit in tmp/ (oldest from Aug 4), plus report/scratch
files excluded from migration (see manifest exclusions).

## Ideal Result

Every graph artifact authored via the sole route has its task brief
committed at a predictable path, cited by the governing FR, so that any
future reader can reconstruct the authoring input closure from the repo
alone. No FR cites a gitignored path as provenance.

## Proposed Solution

1. **Committed home:** `feature-requests/authoring-briefs/` with the
   naming convention `fr-XXX-<slug>-brief.md` for FR-bound briefs and
   `<slug>-brief.md` for standalone demo briefs.
2. **Doctrine update:** amend
   `.github/skills/graph-authoring/doctrine.md` and `SKILL.md` (and
   `adapters/README.md` wording) — the requesting session writes the
   brief under `feature-requests/authoring-briefs/` (or moves it there
   before commit) and the FR cites the committed path. `author.sh`
   continues to accept any path; the commit requirement is on the
   requesting session, enforced by review, not by the wrapper.
3. **Chore — migrate existing briefs per the manifest below:** copy
   ONLY the manifest-listed files (no wildcard from tmp/), renamed to
   the convention, committed in a single `chore(doctrine)` commit
   after human review of the manifest and migrated content (judgement
   C-2/C-3).
4. **Durable provenance mapping (judgement R-2):** commit
   `feature-requests/authoring-briefs/INDEX.md` mapping every old
   tmp/ path → new committed path → governing FR/consumer, AND append
   a one-line provenance note to each affected FR's implementation
   record citing the new committed brief path. No other FR prose is
   rewritten.

### Migration manifest (judgement R-1 — exact, no glob)

All 34 sources verified present in tmp/ on 2026-08-22. Destination
directory: `feature-requests/authoring-briefs/`. Excluded by C-4/AC-07:
`tmp/draft-judgement*.md`, `tmp/draft-review*.md`,
`tmp/fr819-authoring-report.md`, `tmp/fr777-demo-topic.md`,
`tmp/fr777-enforcer-demo-fr.md`, `tmp/consumed-regulated-evidence-profile.md`
(reports/scratch, not briefs).

| Old tmp/ path | New filename | Governing FR / consumer | Rationale |
|---|---|---|---|
| tmp/book-summary-brief.md | fr-773-book-summary-brief.md | FR-773 | book-summary demo authoring input |
| tmp/book-summary-harden-brief.md | fr-774-book-summary-harden-brief.md | FR-774 | scale-hardening authoring input |
| tmp/book-summary-loop-brief.md | fr-775-book-summary-loop-brief.md | FR-775 | loop-redesign authoring input |
| tmp/book-summary-retry-brief.md | fr-775-book-summary-retry-brief.md | FR-775 | retry witness (AC-10) authoring input |
| tmp/fix-research-agent-vars-brief.md | fix-research-agent-vars-brief.md | standalone — research_agent demo maintainer | stale-vars fix authoring input (no FR) |
| tmp/fr-787-authoring-brief.md | fr-787-authoring-brief.md | FR-787 (cites path) | recon step authoring input |
| tmp/fr-789-authoring-brief.md | fr-789-authoring-brief.md | FR-789 (diary brief-is-code) | browser-sniff authoring input; carried the FR-789 incident bug |
| tmp/fr-790-authoring-brief.md | fr-790-authoring-brief.md | FR-790 (cites path) | schema-extract authoring input |
| tmp/fr-791-authoring-brief.md | fr-791-authoring-brief.md | FR-791 | orchestrator authoring input |
| tmp/fr-795-authoring-brief.md | fr-795-authoring-brief.md | FR-795 (cites path) | probe-repair authoring input |
| tmp/fr-796-authoring-brief.md | fr-796-authoring-brief.md | FR-796 (cites path) | demo-reclass authoring input |
| tmp/fr776-vision-brief.md | fr-776-vision-brief.md | FR-776 (cites path) | vision fallback authoring input |
| tmp/fr777-convert-brief.md | fr-777-convert-brief.md | FR-777 | toolbelt conversion authoring input |
| tmp/fr779-green-brief.md | fr-779-green-brief.md | FR-779 (cites path) | demo-rot green run input |
| tmp/fr780-green-brief.md | fr-780-green-brief.md | FR-780 (cites path) | toolbelt conversion green run input |
| tmp/fr781-authoring-brief.md | fr-781-authoring-brief.md | FR-781 | file-hook demo authoring input |
| tmp/fr782-author-brief.md | fr-782-author-brief.md | FR-782 | self-portrait authoring input (iteration 1) |
| tmp/fr782-author-brief-2.md | fr-782-author-brief-2.md | FR-782 | iteration 2 |
| tmp/fr782-author-brief-3.md | fr-782-author-brief-3.md | FR-782 | iteration 3 |
| tmp/fr809-brief-a.md | fr-809-brief-a.md | FR-809 (cites path) | v2 recon iteration a |
| tmp/fr809-brief-b.md | fr-809-brief-b.md | FR-809 | iteration b |
| tmp/fr809-brief-b1.md | fr-809-brief-b1.md | FR-809 | iteration b1 |
| tmp/fr809-brief-b2.md | fr-809-brief-b2.md | FR-809 | iteration b2 |
| tmp/fr809-brief-c.md | fr-809-brief-c.md | FR-809 | iteration c |
| tmp/fr809-brief-d.md | fr-809-brief-d.md | FR-809 | iteration d |
| tmp/fr809-brief-final.md | fr-809-brief-final.md | FR-809 (cites path); tamper-forensics diary | final accepted brief |
| tmp/fr851-audit-graph-brief.md | fr-851-audit-graph-brief.md | FR-851 (cites path) | req-witness audit graph authoring input |
| tmp/gitclaw-authoring-brief.md | fr-827-gitclaw-authoring-brief.md | FR-827 | gitclaw orchestrator authoring input (cross-repo artifact) |
| tmp/gitclaw-push-race-brief.md | fr-827-gitclaw-push-race-brief.md | FR-827 | push-race fix authoring input |
| tmp/gitclaw-toolnodes-brief.md | fr-827-gitclaw-toolnodes-brief.md | FR-827 | tool-node fold authoring input |
| tmp/gitclaw-verdict-gate-brief.md | fr-827-gitclaw-verdict-gate-brief.md | FR-827 | verdict-gate authoring input |
| tmp/shared-vision-tool-model-pin-brief.md | shared-vision-tool-model-pin-brief.md | standalone — shared vision tool demo maintainer | model-pin change input (no FR) |
| tmp/task-brief-deviant-daily.md | fr-826-deviant-daily-brief.md | FR-826 (AC-03) | deviant-daily pipeline authoring input |
| tmp/task-brief-fr819-digest-graph.md | fr-819-digest-graph-brief.md | FR-819 (cites path) | digest graph authoring input |

## Acceptance Criteria (revised per judgement R-3)

- [ ] AC-01: This FR contains the migration manifest above enumerating
      every old tmp/ brief path, new committed path, governing
      FR/consumer, and inclusion rationale.
- [ ] AC-02: `feature-requests/authoring-briefs/` exists; every file in
      it is manifest-listed; every manifest-listed available source has
      a committed destination.
- [ ] AC-03: FR-bound destinations follow `fr-XXX-<slug>-brief.md`;
      standalone destinations follow `<slug>-brief.md` with a named
      consumer in the manifest.
- [ ] AC-04: `feature-requests/authoring-briefs/INDEX.md` maps every
      old tmp/ path → new path → governing FR/consumer; each affected
      FR cites the new committed brief path in its implementation
      record.
- [ ] AC-05: graph-authoring `doctrine.md`, `SKILL.md`, and
      `adapters/README.md` state that FR-bound task briefs go under
      `feature-requests/authoring-briefs/` and are cited by the
      governing FR.
- [ ] AC-06: No wrapper, hook, graph, prompt, judge, or review route
      behavior changes — documentation/provenance migration only.
- [ ] AC-07: No reports, logs, draft judgements, draft authoring
      reports, or unlisted scratch from tmp/ are committed.
- [ ] AC-08: Changelog fragment under `changelog/unreleased/`.

## Alternatives Considered

- **`FR-XXX-<slug>.brief.md` beside the FR file** (mirroring
  `.judgement.md`): pollutes the flat feature-requests/ listing with a
  second file class; a subdirectory keeps `ls feature-requests/`
  readable. Rejected.
- **Repo-root `authoring-briefs/`:** briefs are FR-adjacent planning
  artifacts; keeping them under feature-requests/ keeps the planning
  spine in one tree. Rejected.
- **Also graduating `tmp/draft-authoring-report.md` to a committed
  artifact:** deferred — the report's validation record is already
  required in the FR body by doctrine; committing the raw report is a
  separate decision with its own consumer question.
- **Wrapper-enforced location (author.sh rejects tmp/ paths):** breaks
  the brief-iteration workflow (FR-789's resumed-brief edit) and
  standalone experiments; review-time enforcement suffices for a
  first strike. Deferred until drift recurs.

## Related

**Prior art:** hook hits on `fr-78X-author*-brief.md` files are the
migration subjects of this FR, not competing proposals — dispositioned
as in-scope cargo. Genuine prior art: FR-806 (brief pre-flight; treats
the brief as a mechanical artifact — complementary, no overlap with
preservation) and the graph-authoring doctrine's "committed or
explicitly provided" wording (FR-765 lineage), which this FR completes
by defining the committed location. No rejected FR occupies this
territory.

- `.github/skills/graph-authoring/doctrine.md` (input closure, sole route)
- `.github/skills/graph-authoring/adapters/README.md` ("committed or
  explicitly provided")
- docs/diary/diary-2026-08-15-fr789-brief-is-code.md
- FR-806 (brief pre-flight — the brief as a mechanical artifact)
- FR-787…FR-796, FR-809 (FRs citing tmp/ brief paths)

## Judgement (2026-08-22)

**Verdict:** APPROVED WITH REVISIONS — full judgement in
`FR-852-preserve-authoring-briefs.judgement.md` (rendered via sole
route `scripts/judge.sh`, model gpt-5.5).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | `cp tmp/*brief*.md` glob from ignored state not judgeable; evidence inventory inexact | Folded: exact 34-row migration manifest above; evidence corrected (10 FRs cite brief paths; FR-771/789/791 exceptions named) |
| R-2 | "No FR cites gitignored path" contradicted "no retroactive rewriting" | Folded: committed INDEX.md + one-line provenance note in each affected FR |
| R-3 | ACs not mechanical | Folded: AC-01…AC-08 |
| R-4 | Ignored-file migration + doctrine edit needs human gate | Folded: C-2 human review of manifest and content before commit |

**Conditions:** C-1 fold revisions (done); C-2 human reviews manifest +
migrated content before commit (GATE); C-3 no wildcard migration
(GATE); C-4 missing sources recorded, never reconstructed (GATE);
C-5 no changes to author.sh, hooks, judge/review doctrine, graphs,
prompts (GATE).

**Purge list:** wildcard migration instruction (replaced by manifest);
commit-message-only provenance mapping (replaced by INDEX.md + FR
notes).

**Scope frozen:** D-1 amended FR (this fold); D-2 authoring-briefs/
with manifest-listed files only; D-3 INDEX.md + affected-FR citations;
D-4 three graph-authoring doc surfaces; D-5 changelog fragment.

### Questions for the human (as options, or 'none')

None — C-2 itself is the human touchpoint: review the manifest and
migrated content before the migration commit.

## Implementation Record (2026-08-22)

- C-2 satisfied: operator reviewed the manifest and issued "enforce".
- D-2: 34 briefs copied with explicit per-file destinations (no
  wildcard, C-3); `feature-requests/authoring-briefs/` contains exactly
  the 34 manifest files + INDEX.md.
- D-3: `feature-requests/authoring-briefs/INDEX.md` maps all old→new
  paths; provenance note appended to all 20 affected FRs (FR-773–777,
  779–782, 787, 789–791, 795, 796, 809, 819, 826, 827, 851).
- D-4: committed-brief-home wording added to graph-authoring
  `doctrine.md` (input closure), `SKILL.md` (session separation), and
  `adapters/README.md` (brief definition). No CORE fence present.
- D-5: changelog fragment `changelog/unreleased/fr-852-preserve-authoring-briefs.md`.
- C-4: no sources missing — all 34 manifest entries migrated.
- C-5: no wrapper/hook/graph/prompt changes.
- Deviation: none from judged scope.
- **Landing commit (provenance correction):** the FR-852 enforcement
  landed in `fc655173` under the sibling session's message
  `docs(fr): FR-853 instrument registry, FR-854 subagent census` — a
  `one_session_one_repo` interleave swept this session's staged work
  into the parallel session's commit mid-hook-cycle. Verified complete:
  64 files, all 34 briefs + INDEX + judgement + doctrine edits + 20 FR
  notes + changelog + diary; `git diff HEAD` empty afterward. History
  is published; not rewritten. This FR file is the authoritative
  provenance record for that commit's FR-852 content.
