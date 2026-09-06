# Feature Request: Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Priority:** LOW
**Type:** Enhancement (docs; Scripture edit — human gate C-4)
**Status:** **REJECTED** 2026-09-06 by the operator — PR #627 closed unmerged after 4 judgement rounds and 3 review rounds. Not because the change was wrong (the edits were correct and are re-filed unchanged) but because the process around it became the deliverable: a 20-line docs sweep grew a 413-line FR, a 261-row sha256 baseline, a 421-line witness pinning every Chaplain-matching line in the repository to commit `36591389` forever, and a new requirement (REQ-YG-668) — a maintenance tripwire, not a witness. Each judge/review round found more to say because each fold gave it more to read; roughly half the later findings were defects introduced while fixing the previous round (rebase-churned SHAs, a merge-order sentence, a link depth, a `git cat-file` design that cannot run in a depth-1 CI checkout). Superseded by [FR-1019-chaplain-doctrine-sweep.md](FR-1019-chaplain-doctrine-sweep.md), the short form; the diary is `docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`. This text and its judgement file are kept as the record. Branch `feat/fr1013-doctrine-sweep` (head `cf9b915e`) holds the closed implementation; nothing from it is on `main`. Prior status history follows.
**Previous status:** Judged round 4 (2026-09-06) — APPROVED WITH REVISIONS … (see § Judgement).
See [FR-1013-chaplain-doctrine-sweep.judgement.md](FR-1013-chaplain-doctrine-sweep.judgement.md)
(all rounds).
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 3 of 5; prerequisite FR-1012 **merged** (FR-1010 C-3). At filing (2026-09-06) FR-1012 is judged, unenforced; `docs/archive/chaplain.md` does not yet exist. `BASE = 36591389e2fdfedf9ba5ae6362effad1c64cd06e` (PR #623 squash merge, 2026-09-06 13:25 UTC; human merge by the operator — the PR carried no GitHub review object).
**First consumer / first event:** a new agent session reading
`.github/copilot-instructions.md` → "Sermon of the Chaplain" → following
`docs/development-process.md § 3 "The Chaplain: Autonomous Plan → Judge →
Enforce"` → `.chaplain/scripts/start-system.sh`, which no longer exists.
The first ENOENT on a doctrine-cited path is the event; today that chain is
three hops long and every hop is live text.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered-r-1-six-solution-classes);
the sweep inventory below is the evidence record (line refs read
2026-09-06). `is_this_a_graph`: **no** — a fixed list of documents with
known line numbers; a grep, not a corpus.
**Prior art:**
- [FR-193-mass-graduation-scripture-patterns.md](FR-193-mass-graduation-scripture-patterns.md)
  — the last Scripture-wide edit; established that Scripture edits go
  through judge + human review and never same-session with the observation
  that motivated them (`guard_widening_when_caught` at Scripture scale).
- [FR-207-standalone-scripture-methodology-repo.md](FR-207-standalone-scripture-methodology-repo.md)
  — `ramp/`. **Correction (R-2):** there is no `ramp/render.sh`; the only
  renderer is `ramp/salvage/render.sh`, preserved as an unwired pattern
  reference (`ramp/salvage/README.md:13-17`). The judge-doctrine asset is
  declared `mirror_exact` in `ramp/manifest.yaml` (byte-equal to the live
  file, drift-tested by
  `tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes`),
  not `curation_diff`. So: edit the canonical doctrine, copy byte-for-byte,
  leave `ramp/curation-diffs.md` untouched.
- [FR-1011-relocate-chaplain-live-parts.md](FR-1011-relocate-chaplain-live-parts.md)
  — already changed the one *path* mention in Scripture (`:163`,
  `.chaplain/inbox/` → `proposals/`). This FR changes *wording*; the
  boundary is deliberate: FR-1011 was a relocation, this is doctrine.
- [FR-1012-chaplain-subtree-archive-and-removal.md](FR-1012-chaplain-subtree-archive-and-removal.md)
  — wrote `docs/archive/chaplain.md`, the single page this sweep may
  point to.

## Summary

Make every doctrine and reference document describe the SDLC that is
actually practised — operator-driven plan → `scripts/judge.sh` → worktree
enforcement → `scripts/review.sh` → human merge — and stop describing the
FSM daemon as the process. One archive pointer replaces the runtime
narrative wherever it appeared as live instruction; historical FRs, changelog
and `docs/memento/` are untouched, and so is pre-existing diary history —
the only `docs/diary/` write is this FR's own Distill entry (D-10).

## Value Statement

Doctrine stops sending readers to a directory that no longer exists, and
`docs/development-process.md`'s own § 3.1 ("the manual rite dominates —
83 % of commits are direct") becomes the description rather than the
footnote.

## Problem

Pre-merge sweep inventory (`grep -ciE chaplain`, 2026-09-06 on `main`
@ `1c0b083f`, **before** FR-1011/FR-1012). This table is the *planning*
inventory; R-1 requires it to be **re-run at `BASE`** and the refreshed
result committed in § Inventory at BASE before any edit. A newly
discovered live artifact stops the phase (FR-1010 C-10).

| File | Lines | What is there | Change |
|---|---|---|---|
| `.github/copilot-instructions.md` | 204 | `## Sermon of the Chaplain` heading | rename → `## Sermon` (the seven steps are unchanged). Heading only — no added sentence (review P7; AC-11 limits the Scripture diff to this heading and the sources clause) |
| `.github/copilot-instructions.md` | 176 | canonical-sources line names `docs/development-process.md (doctrine, chaplain pipeline, enforcement rings)` | drop "chaplain pipeline" |
| `.github/copilot-instructions.md` | 163 | `diary_graduation_pipeline` seed already says `proposals/` (FR-1011) | verify only |
| `docs/development-process.md` | 24–38 | opening topology mermaid: `H[Human proposal .chaplain/inbox/*.md]`, `GH[GitHub Issue label: chaplain]`, `PH[Philosopher proposals]`, `IQ[Inquisitor proposals]`, `subgraph PIPELINE["Chaplain pipeline (autonomous)"]` | inbox → `proposals/`; drop `GH` and `IQ`; `PH` → `graphs/philosopher` (dormant); PIPELINE subgraph → "Rite (operator-driven)": author.sh → FR → judge.sh → worktree → review.sh → merge (R-3) |
| `docs/development-process.md` | 121–176 § 3; 177–… § 3.1 | § 3 describes the dual-FSM as the process; § 3.1 says the manual rite dominates | § 3 → "The rite as practised" (operator + author/judge/review scripts + worktree-per-PR), ≤ 15 lines; § 3.1's measurement sentence kept verbatim; two sentences on the FSM + archive link; `stateDiagram` deleted |
| `docs/development-process.md` | 292–304 § 6 | self-correction mermaid names `.chaplain/inquisitor.sh`, `INBOX[.chaplain/inbox/]`, "Chaplain pipeline" edge | inquisitor node deleted (retired); inbox → `proposals/`; edge → "FR via judge.sh" (R-3) |
| `docs/development-process.md` | 324–330 § 7 | dogfooding row "Chaplain plan/judge/enforce/diary phases … (`.chaplain/graphs/`)" | row → "judge/review/author/outsider adapters are YAMLGraph graphs (`.github/skills/*/adapters/graph.yaml`); fr_triage/world_distill in `graphs/`" (R-3) |
| `reference/onepager-development-process.md` | 31, 45, 138, 154 | inbox path, "or open a GitHub issue with the `chaplain` label", flow step 1, sources line | `proposals/`; drop the issue-label route (importer is gone); flow step 1 → "Write spark → `proposals/`"; sources: `docs/context/chaplain-system.md` → `docs/archive/chaplain-system.md` |
| `reference/audit-index.md` | 65–71 | seven rows: Chaplain Pipeline, Dispatcher FSM, Pipeline FSM, Inquisitor, Philosopher, Author allowlist, ID registry | delete six; Philosopher row → `graphs/philosopher/graph.yaml`; add one row "Chaplain (archived)" → `docs/archive/chaplain.md` |
| `reference/graph-yaml.md` | 610, 1469 | comment "Based on .chaplain/watcher2.sh pattern"; prose "(chaplain …)" example for `path:` vs `module:` | drop the comment; example → `graphs/fr_triage` |
| `examples/README.md` | 57, 74, 171 | philosopher stub row; note "relocated to `.chaplain/graphs/`"; "witnesses live under `.chaplain/demos/`" | delete row (stub gone, FR-1011); note → `graphs/`; witnesses line deleted (demos gone, FR-1012) |
| `CLAUDE.md` | — | `grep -c chaplain` → 0 on main 2026-09-06 | verify only |
| `.github/skills/feature-request/SKILL.md` | description front-matter "submitting a proposal to the chaplain inbox"; § Submitting (already `proposals/` after FR-1011) | description → "submitting a proposal to `proposals/`" |
| `.github/skills/judge-fr/doctrine.md` | 133, 135 | "chaplain-era prompts used APPROVE/AMEND"; "Chaplain runtime (`.chaplain/`) is the historical origin" | keep 133 (true history); 135 → point at `docs/archive/chaplain.md` |
| `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` | 133, 135 | `mirror_exact` copy of the above | `cp` byte-for-byte after editing the canonical (R-2); `ramp/curation-diffs.md` and `ramp/manifest.yaml` unchanged |
| `docs/context/chaplain-system.md` | 53 lines (whole file) | full FSM description | **move** to `docs/archive/chaplain-system.md` (`git mv`) and link from `docs/archive/chaplain.md` |
| `docs/archive/chaplain.md` | (created by FR-1012) | archive note | **one edit permitted**: add the link to `docs/archive/chaplain-system.md` (R-3 resolves the allowlist contradiction) |
| `docs/context/fr-698.md` | 347, 357, 359 | historical FR context naming `.chaplain/lib/watcher/*` | leave (historical record) |

Allowlist (untouched): `feature-requests/`, `changelog/`, `docs/diary/`,
`docs/memento/`, `docs/ebook/`, `docs/research-*.md`, `docs/context/fr-698.md`,
`ramp/curation-diffs.md`. **Exception (R-3):** exactly
`docs/archive/chaplain.md` (link line) and the new
`docs/archive/chaplain-system.md` may be written under `docs/archive/`. **Exception (round-4 D-10):** exactly `docs/diary/2026-09-06-reflection-fr-1013-the-inventory-that-was-fifteen-times-the-plan.md` may be added under `docs/diary/`; every other `docs/diary/` path is immutable.

### Inventory at BASE (R-1) — committed before any edit

```bash
BASE=<FR-1012 merge SHA>
git merge-base --is-ancestor "$BASE" HEAD || exit 1
git ls-files '*.md' '*.py' '*.sh' '*.yaml' '*.yml' \
  | grep -vE '^(feature-requests|changelog|docs/diary|docs/memento|docs/ebook|docs/archive)/|^docs/research-|^docs/context/fr-698\.md$|^ramp/curation-diffs\.md$' \
  | xargs grep -nE '\.chaplain|Chaplain|chaplain|watcher2?\b|Inquisitor|inquisitor|label: chaplain|`chaplain` label'
```

**Result at BASE `36591389`** (run 2026-09-06 from `feat/fr1013-doctrine-sweep`; `git merge-base --is-ancestor` exit 0): **2586 matches in 261 files**. Raw list (`file:line` per match; the full-text form is 509 KB and trips the large-file gate, and every line is reproducible from `BASE`): [docs/census/fr1013-inventory-at-base-36591389.txt](../docs/census/fr1013-inventory-at-base-36591389.txt); one disposition per file (covering every match in it): [docs/census/fr1013-inventory-at-base-36591389.dispositions.md](../docs/census/fr1013-inventory-at-base-36591389.dispositions.md) — kept out of this file because 261 rows would breach the 450-line file gate. No **stop** row: nothing under `.chaplain/` survives and no live consumer of a `.chaplain/` artifact was found; stale `.chaplain` *defaults* in code (`research_tools.py`, `diary_recurrence.py`, `cap_journey_census/extract.py`) are code, outside this docs-only FR, and filed as a spark. The grep's `watcher2?\b` arm also matches the unrelated FR-885 worktree watcher and the file-hook/DeviantArt watchers — false positives, kept.

**BASE match-bearing source set (13 files — the only files whose *matching lines* change):**

| File | Matches | Disposition |
|---|---|---|
| `.github/copilot-instructions.md` | 4 | **edit** — edit — :205 heading `## Sermon of the Chaplain` → `## Sermon`; :177 drop "chaplain pipeline, " from the sources clause. :52 (`audit` boundary) and :162 (`inquisitor_auto_escalation` seed) are Knowledge Graph entries — unchanged |
| `.github/skills/graph-authoring/SKILL.md` | 1 | **edit** — edit — :3 description drops "deciding whether graph work belongs in Chaplain instead" |
| `.github/skills/graph-authoring/doctrine.md` | 2 | **edit** — edit — :58 "escalate to Chaplain instead" and :128 "Enforce via Chaplain." → file an FR (`proposals/` → judge); live doctrine naming a retired route (found at BASE, not in the planning table) |
| `.github/skills/judge-fr/doctrine.md` | 2 | **edit** — edit — :135 → `docs/archive/chaplain.md`; :133 kept (true history) |
| `docs/context/chaplain-system.md` | 58 | **edit** — edit — `git mv` → `docs/archive/chaplain-system.md`; linked from `docs/archive/chaplain.md` |
| `docs/development-process.md` | 28 | **edit** — every active-process passage (round-1 R-3 wording, review #627 P2): topology mermaid (24–66); § 3 (121–176) → "The rite as practised"; § 3.1 (177–219): the measurement sentence byte-identical, every other sentence that prescribes routing to the inbox / `.chaplain/failed/` / the FSM rewritten in the past tense as a bounded historical comparison or deleted (the dispatch heuristic and the 2026-07-07 caveat prescribe an inbox that no longer exists — deleted); intro :5–7 ("its own autonomous developer (the Chaplain/Watcher), its own auditor (the Inquisitor)") → the operator-driven rite; § 2.1 row :113 drops the deleted `chaplain-ops` skill and "via inbox/FRs" → `proposals/`; § 5 bullet :286 `automation_inherits_doctrine` → "scripts and adapters obey the same hooks"; § 6 mermaid (296–306) and bullets :312–320 (Inquisitor feeds the inbox; 2026-07-07 asymmetry) → Philosopher only, asymmetry bounded as history; § 7 row (330). Kept verbatim: § 3.1 measurement sentence; :366 ("meta-tooling (hooks, chaplain scripts) historically drifted" — already past tense) |
| `examples/README.md` | 3 | **edit** — edit — :57 row deleted; :74 note → `graphs/`; :171 witnesses line deleted |
| `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` | 2 | **edit** — edit — `cp` byte-for-byte from the canonical after editing (mirror_exact, R-2) |
| `reference/audit-index.md` | 8 | **edit** — edit — :65–71 six rows deleted, Philosopher → `graphs/philosopher/graph.yaml`, one `Chaplain (archived)` row → `docs/archive/chaplain.md`; :57 Inquisitor-audits row kept (the diary entries exist) |
| `reference/command-book.md` | 1 | **edit** — edit — :76 "Sermon of the Chaplain" → "Sermon" (follows the heading rename) |
| `reference/graph-yaml.md` | 2 | **edit** — edit — :610 comment dropped; :1469 example → `graphs/fr_triage` |
| `reference/onepager-development-process.md` | 9 | **edit** — edit — :11 column, :26 heading, :31 inbox path, :45 submission route, :90 hook row, :126, :138 flow step, :146, :154 sources |
| `reference/patterns/fsm-as-conductor.md` | 8 | **edit** — edit — :169–170, :235 link targets → `docs/archive/chaplain-system.md`; the Chaplain remains a case study in the pattern (historical) |

**Writable surface (R-2; exhaustive — every path the PR changes from `BASE` is one of these):**

| # | Path | Class |
|---|---|---|
| 1 | the 13 match-bearing files above | frozen content edits (D-2, D-3, D-5) |
| 2 | `docs/archive/chaplain.md` (one link line), `docs/archive/chaplain-system.md` (move destination) | archive exception (D-4) |
| 3 | `capabilities/CAP-264-chaplain-runtime-retired.yaml`; `ARCHITECTURE.md` **only** as `scripts/aggregate_capabilities.py` output of that edit | registry + generated (D-6) |
| 4 | `tests/unit/test_fr1013_doctrine_sweep.py` | witness (D-7) |
| 5 | `changelog/unreleased/fr-1013-doctrine-sweep.md` | fragment (D-8) |
| 6 | `feature-requests/FR-1013-chaplain-doctrine-sweep.md`, `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`, `docs/census/fr1013-inventory-at-base-36591389.txt` (unchanged), `docs/census/fr1013-inventory-at-base-36591389.dispositions.md` (only to encode the residual policy) | records (D-1) |
| 7 | `docs/diary/2026-09-06-reflection-fr-1013-the-inventory-that-was-fifteen-times-the-plan.md` | Distill (D-10, authorized round 4) — this exact path only; no other `docs/diary/` write |

No other path may change (C-5); the PR surface is D-1…D-8 plus D-10 (AC-02); D-9 is the operator's post-merge action.

**Residual contract (R-3; what the witness enforces):** (1) every BASE file outside the match-bearing set: multiset of matching line texts at HEAD equals BASE's; (2) every match-bearing or generated file: each HEAD match equals an exact residual line listed for that file in the test (empty list = zero matches); (3) a matching file absent from BASE fails unless it is an enumerated new artifact of this FR (the witness test itself, the disposition file, the changelog fragment, this FR's judgement); (4) the stale code defaults (`research_tools.py`, `diary_recurrence.py`, `cap_journey_census/extract.py`) are `keep-out-of-scope-code` — unchanged, not reclassified as historical; (5) any new or reworded unmatched residual stops enforcement (FR-1010 C-10).

**Keep set (248 files), grouped:**

| Volume | Disposition |
|---|---|
| 1015 matches | keep — historical record / generated file (CHANGELOG, ARCHITECTURE) — not live instruction |
| 706 matches | keep — FR-1011/FR-1012 deliverable — census, archive tooling, witnesses, evidence |
| 391 matches | keep — authored content about the Chaplain era (book chapters, prompts) — historical |
| 163 matches | keep — capability record (retired by CAP-264 / FR-1012 census); registry history |
| 83 matches | keep — test kept by the FR-1012 census (old-string witness or unrelated match) |
| 38 matches | keep — code/tooling comment or stale default path — outside a docs-only FR; the stale `.chaplain` defaults are filed as a spark (`proposals/stale-chaplain-paths-in-code.md`) |
| 37 matches | keep — "watcher" false positive (FR-885 / file-hook / DeviantArt watcher) or historical example prose |
| 7 matches | keep — historical prose |
| 7 matches | keep — FR-1011 relocated graph; comments record provenance |
| 6 matches | keep — history note ("former chaplain arm removed by FR-1011") or CI comment — SPLIT boundary forbids hook/CI edits |
| 5 matches | keep — lineage/provenance metadata (MANIFEST, adapter header) |

The residual test encodes this as: the set of files with matches at HEAD ⊆ the 261 files at BASE; every edit-file's named old strings are gone; the three route-critical strings (`Sermon of the Chaplain`, `.chaplain/inbox`, `start-system.sh`) appear in no edit-set file.

## Ideal Result

The R-1 residual grep at HEAD returns only rows dispositioned
`keep-historical` in § Inventory at BASE.
`grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` → 0.
`docs/development-process.md` § 3 describes what § 3.1 measured, and its
topology, § 6 and § 7 name the surviving route. `reference/audit-index.md`
has one Chaplain row pointing at the archive.
`cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md`
exits 0.

## Proposed Solution

One PR, docs-only, judged and **human-reviewed before merge** (Scripture
edit; FR-1010 C-4). Never in the same session that observed the need —
this FR is filed in the planning session; enforcement happens later, from
`BASE`.

0. Record `BASE`; run and commit § Inventory at BASE (gate).
1. `.github/copilot-instructions.md:204` heading; `:176` sources clause.
   Nothing else in Scripture.
2. `docs/development-process.md`: every passage enumerated in the edit-set
   row (topology, § 3, § 3.1 minus the measurement sentence, intro, § 2.1
   row, § 5 bullet, § 6, § 7). Test: after the edit the file's only
   remaining matches of the R-1 regex are the lines listed in the test's
   `DEV_PROCESS_RESIDUAL` allowlist (the measurement sentence, the
   archive-link sentences in § 3, the past-tense comparison in § 3.1, the
   :366 self-exemption note) — each quoted verbatim, so a new live claim
   fails the test by being absent from the list.
3. Reference files per the table.
4. `git mv docs/context/chaplain-system.md docs/archive/chaplain-system.md`;
   one link line added to `docs/archive/chaplain.md`.
5. Edit canonical `.github/skills/judge-fr/doctrine.md:135`; `cp` to
   `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`; `ramp/manifest.yaml`
   and `ramp/curation-diffs.md` untouched (R-2).
6. Witness `tests/unit/test_fr1013_doctrine_sweep.py`, **match-level**
   (review #627 P3 — a file-level allowlist lets a new reference hide in any
   of the 261 BASE files): (a) for every tracked file in the R-1 scope that
   is *not* in the edit set, the multiset of matching line texts at HEAD
   equals the multiset at `git show "$BASE":<path>` — unchanged files pass
   trivially, a new or reworded reference anywhere else fails; (b) for every
   edit-set file, each remaining matching line must equal, verbatim, an
   entry in that file's residual allowlist in the test (historical
   sentences and archive links only) — an empty allowlist means zero
   matches; (c) files not in the R-1 scope at BASE that match at HEAD fail,
   except the test module itself and the census disposition file (both
   self-referential by construction, named in the test). Heading gone; Sermon step names equal
   `git show "$BASE":.github/copilot-instructions.md`'s; `docs/archive/chaplain-system.md`
   exists; `reference/audit-index.md` has exactly one `Chaplain` row
   linking `docs/archive/chaplain.md`; `cmp -s` on the mirror pair.
7. Traceability (R-5): a table in § Implementation Record mapping each
   test function → surviving REQ ID → quoted requirement text, filled
   after the R-1 census. REQ-YG-192 may tag **only** the assertion that
   the Knowledge Graph entries are unchanged (`ARCHITECTURE.md:1242-1250`).
   If no live REQ directly covers an assertion, enforcement **stops** and
   this FR returns to judgement (judgement `:50-53`; review P3). No CAP or
   REQ is invented during enforcement. **Round-3 question (review #627
   P4):** REQ-YG-666 covers runtime removal, archive identity and census
   integrity — not documentation consistency; the eight documentation
   assertions have no direct REQ. Proposed resolution, for the judge to
   grant or replace: add **one** requirement to the existing CAP-264
   (`capabilities/CAP-264-chaplain-runtime-retired.yaml`) — `REQ-YG-668`:
   "Live doctrine and reference documents (`.github/copilot-instructions.md`,
   `.github/skills/*/doctrine.md`, `docs/development-process.md`,
   `reference/*.md`, `examples/README.md`) describe the operator-driven
   author → judge → worktree → review → human-merge route; no
   non-historical passage names a `.chaplain/` path, `start-system.sh`, the
   issue-label importer or the Inquisitor as a live component; every
   Chaplain pointer resolves to `docs/archive/chaplain.md` or
   `docs/archive/chaplain-system.md`; verified by
   `tests/unit/test_fr1013_doctrine_sweep.py`." This is the judged
   exception to the Purge-list "no capability or requirement change": one
   REQ under an existing CAP, tagged by every residual/documentation-consistency
   assertion; REQ-YG-192 only on the Knowledge-Graph test, REQ-YG-613 only on
   the mirror test.
   Round 3 granted it as **REQ-YG-668** (REQ-YG-667 is CAP-265's) with the
   judge's wording ("The post-FR-1012 tracked-text census remains reconciled …";
   quoted in full in § Implementation Record); CAP-264 `fr` names FR-1012 and
   FR-1013, its modules add the documentation surfaces and the witness test;
   `ARCHITECTURE.md` changes only as `scripts/aggregate_capabilities.py` output.
8. Old-string doc-witness tests: named **only after** FR-1012's census
   decides which survive (the four listed in the first draft —
   `test_chaplain_readme_documentation.py`, `test_concurrency_safety_doc.py`,
   `test_fr748_fr_atlas.py`, `test_knowledge_graph_fr193.py` — are
   candidates, not a commitment).
9. Changelog fragment `type: removal`, scope `doctrine`.

### Post-merge closure (operator-owned; not a PR deliverable — round-2 R-1)

After this PR merges, the operator records its merge SHA here, executes
FR-1010 AC-12 and AC-13 on merged `main`, records the phase results, and
pushes an FR-1010-only closure commit. The PR merge gate requires only
human review + a recorded intent to finalize. **No closure script or its
test is part of this FR** (AC-A13).

Concern B of the round-2 SPLIT — automating that closure
(`scripts/fr1010_closure.sh`, proposed by PR #617's review P5) — is not
filed. If it ever is, its FR must first disposition
`scripts/finalize_merge.sh` (CAP-38/REQ-YG-125; the repo already has a
post-merge finalizer that updates FR status and commits) and CAP-114, and
specify the success path as precisely as the error paths (judgement round
2 R-2, R-3, AC-B01..B05). The review's scriptability finding and the
judge's scope finding disagree; the judge governs scope (`review-pr`
doctrine: review output is advisory).

## Acceptance Criteria (round 4, verbatim; supersede round 3)

- [ ] AC-01: FR-1013 records `BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e`, links the FR-1012 human-review record, and records `git merge-base --is-ancestor "$BASE" HEAD` exiting 0 before authorized enforcement.
- [ ] AC-02: FR-1013 contains separate exhaustive tables for the BASE match-bearing source set and the complete writable surface D-1 through D-8 plus D-10; every PR path changed from BASE appears in that writable table, while D-9 remains post-merge only.
- [ ] AC-03: The committed raw inventory contains exactly 2,586 match rows after its two header lines, the disposition artifact contains 261 file rows, and the exact BASE SHA and reproducing command remain recorded.
- [ ] AC-04: `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` returns 0; the seven bold Sermon step names equal their `git show "$BASE":.github/copilot-instructions.md` values; the complete Knowledge Graph block is byte-identical to BASE; and the Scripture diff is limited to the heading and canonical-sources clause.
- [ ] AC-05: `docs/development-process.md` describes the operator-driven `scripts/author.sh` -> `scripts/judge.sh` -> worktree enforcement -> `scripts/review.sh` -> human merge route in every frozen active-process passage, while its section 3.1 measurement sentence is byte-identical to BASE.
- [ ] AC-06: The other D-3 skill/example/reference surfaces have exactly their frozen dispositions; `reference/audit-index.md` has exactly one row containing `Chaplain`, and that row links `docs/archive/chaplain.md`.
- [ ] AC-07: `docs/archive/chaplain-system.md` exists, `docs/context/chaplain-system.md` does not, `git diff --name-status -M90% "$BASE"...HEAD` reports a rename score of at least 90%, and `docs/archive/chaplain.md` links the moved document.
- [ ] AC-08: `cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md` exits 0; `pytest tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes -q` passes; and `git diff --exit-code "$BASE"...HEAD -- ramp/manifest.yaml ramp/curation-diffs.md` exits 0.
- [ ] AC-09: The residual witness scans tracked `.md`, `.py`, `.sh`, `.yaml`, and `.yml` files; compares exact matching-line multisets to BASE outside the authorized match-bearing edit set; enforces exact residual lines inside that set; rejects unenumerated matching files; and leaves every `keep-out-of-scope-code` line unchanged.
- [ ] AC-10: `capabilities/CAP-264-chaplain-runtime-retired.yaml` associates FR-1013 with REQ-YG-668; CAP-265 retains REQ-YG-667; `python scripts/aggregate_capabilities.py` followed by `git diff --exit-code -- ARCHITECTURE.md` produces no unstaged drift; `python scripts/validate_capabilities.py --strict` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-11: Every residual/documentation-consistency test in `tests/unit/test_fr1013_doctrine_sweep.py` is tagged REQ-YG-668; only the Knowledge Graph preservation test is tagged REQ-YG-192; only the ramp mirror test is tagged REQ-YG-613; the FR's traceability table quotes each requirement text.
- [ ] AC-12: `pytest tests/unit/test_fr1013_doctrine_sweep.py tests/unit/test_knowledge_graph_fr193.py tests/unit/test_ramp_installer.py -q --no-cov` and `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` pass.
- [ ] AC-13: Human review is recorded in FR-1013 before merge and confirms the restricted Scripture diff, the adversarially reviewed judge-doctrine change, byte-identical mirror, generated-only architecture diff, exact residual policy, unchanged Sermon steps, unchanged Knowledge Graph, and D-10 as the only diary change.
- [ ] AC-14: `changelog/unreleased/fr-1013-doctrine-sweep.md` exists with `type: removal` and `scope: doctrine`.
- [ ] AC-15: The FR-1013 PR contains no closure script or closure-script test.
- [ ] AC-16: `git diff --name-only "$BASE"...HEAD -- docs/diary/` returns exactly `docs/diary/2026-09-06-reflection-fr-1013-the-inventory-that-was-fifteen-times-the-plan.md`; `validate_diary_reflection_file` returns zero for that file; and the file contains literal `## The trap`, `## Heuristic`, and `**Seed:**` markers.
- [ ] AC-17: Post-merge only, the operator records FR-1013's merge SHA in FR-1010, runs and records FR-1010 AC-12/AC-13 on merged `main`, records each phase's completion, and changes FR-1010 to `Completed` in a separate FR-1010-only commit.

AC-16 reading: the PR's `docs/diary/` diff is taken against the merge target (`git diff --name-only origin/main...HEAD -- docs/diary/`); `BASE...HEAD` would also list the two FR-1010 diaries other sessions merged to `main` after BASE, which this PR does not touch. Rounds 1–3 ACs are preserved in the judgement file.

## Purge list

- No new doctrine. No new Knowledge-Graph entry (the diary entry
  `2026-09-06-…-sole-consumer-of-a-dead-file…` may graduate later via its
  own FR; not here).
- No edits under the allowlist except the two `docs/archive/` files named
  in § Problem (R-3) and the single D-10 diary path `docs/diary/2026-09-06-reflection-fr-1013-the-inventory-that-was-fifteen-times-the-plan.md`.
- No `docs/development-process.md` edits outside the passages enumerated
  in the edit-set row; no edit to the § 3.1 measurement sentence.
- No `ramp/manifest.yaml` or `ramp/curation-diffs.md` edit.
- No script, hook, CI, graph, prompt change (round-2 SPLIT boundary). The
  only capability/requirement change is `REQ-YG-668` under CAP-264 (round-3
  R-1/D-6); `ARCHITECTURE.md` only as generated output.

## Alternatives Considered

| Option | Why not |
|---|---|
| Fold into FR-1012 | FR-1012 is a destructive PR; Scripture edits need their own judge + human read (FR-193 precedent; C-4). |
| Delete `docs/context/chaplain-system.md` | It is the only long-form description of a system that ran for six months; the archive repo holds code, this holds the design. Move, don't delete. |
| Keep § 3 and add a "retired" banner | § 3.1 already says the FSM was never the primary path; keeping 55 lines of FSM diagram as the process description is the `working_system_inertia` trap in prose. |
| Rename "Sermon of the Chaplain" to something new | The steps are the sermon; the Chaplain was the reader. `## Sermon` loses nothing. |
| Regenerate the ramp copy via a renderer (first draft) | Withdrawn per R-2: `ramp/render.sh` does not exist; the asset is `mirror_exact`. |
| Limit `docs/development-process.md` edits to § 3/§ 3.1 (first draft) | Withdrawn per R-3: the topology, § 6 and § 7 also present the retired route as live. |

## Related

- FR-1010 (plan; this FR completes it), FR-1012 (prerequisite),
  `docs/archive/chaplain.md`

## Implementation Record

| Field | Value |
|---|---|
| `BASE` (FR-1012 merge SHA) + human-review ref | `36591389e2fdfedf9ba5ae6362effad1c64cd06e` — PR #623, merged by the operator 2026-09-06 |
| § Inventory at BASE commit | `24bf566c` (after the P6 rebase onto `b71d0083`) — `docs/census/fr1013-inventory-at-base-36591389.{txt,dispositions.md}` |
| Candidate commits on the branch (pre-round-3) | RED `c1ef6669` (SKIP=pytest, 9 fail / 11 pass at BASE), GREEN `76605ae2`, diary `bca73b0f` |
| Round-4 (D-10) | diary authorized as D-10; AC-16: `validate_diary_reflection_file` exit 0, markers `## The trap`, `## Heuristic`, `**Seed:**` present (4 hits); PR diary diff vs `origin/main` = exactly the D-10 path |
| Round-3 commits (GitHub PR #627 IDs, recorded after the last rebase; the branch has since advanced only by merge) | fold `b2417ca3`; RED `c27e642d`; GREEN `59b11461`; diary addendum `a43469f4`; review-2 fixes `65681486`; round-4 fold `81dee7a2`; pre-round-3: step 0 `24bf566c`, RED `c1ef6669`, GREEN `76605ae2`, diary `bca73b0f`, amendment `b017dda6` (test + CAP-264/REQ-YG-668 + generated ARCHITECTURE.md; `req_coverage --strict` requires the REQ to exist before the tagged test can be committed, so registry and test share the RED commit; the doc edits stayed out, keeping 3 assertions red); GREEN `59b11461` |
| Baseline source (review #627/3 P1) | CI checks out depth 1, so `git cat-file BASE:path` is unavailable there; the witness reads the committed baseline instead — a `BASE lines sha256` column in `docs/census/fr1013-inventory-at-base-36591389.dispositions.md` (sha256 of the sorted matching lines at BASE, per file; 261 rows, counts cross-checked against the raw inventory by `test_baseline_record_is_complete_and_agrees_with_the_raw_inventory`) and `DELTA_HEAD_SHA256` for the three delta files. The BASE blob is used only to explain a mismatch when history is present. Verified in a `--depth 1` clone without the BASE object: 41 passed |
| Residual witness at GREEN | 40 tests: clause 1 (248 BASE files line-multiset-equal via committed sha256), clause 2 (12 match-bearing files × exact residual lines; CAP-264 / ARCHITECTURE.md / confessions exact deltas), clause 3 (no unenumerated matching file), clause 4 (3 stale-default code files unchanged) |
| Traceability: test function → REQ → quoted text | see table below |
| Surviving old-string witness tests | `test_concurrency_safety_doc.py`, `test_fr748_fr_atlas.py`, `test_knowledge_graph_fr193.py` (present after FR-1012; `test_chaplain_readme_documentation.py` was deleted by the census). Their strings (`docs/concurrency-safety.md`, the FR atlases, the Knowledge Graph) are all in the keep set — untouched; all three pass |
| Human review (AC-13) | _pending — operator, on the PR_ |
| Post-merge closure (AC-17): merge SHA, FR-1010 ticks | _pending (operator)_ |

**Traceability (round-1 R-5, round-3 R-1).** REQ-YG-668 (CAP-264, granted round 3) tags every residual/documentation-consistency test; REQ-YG-192 only the Knowledge-Graph-unchanged assertion; REQ-YG-613 only the mirror assertion. `ARCHITECTURE.md` regenerated by `scripts/aggregate_capabilities.py` (pre-commit) — witness: `git diff --exit-code -- ARCHITECTURE.md` after regeneration.

| Test function | REQ | Quoted requirement text (`ARCHITECTURE.md` / CAP) |
|---|---|---|
| residual/documentation-consistency tests (`test_residual_*`, `test_edit_set_*`, `test_sermon_heading_*`, `test_sources_clause_*`, `test_development_process_*`, `test_audit_index_*`, `test_chaplain_system_doc_*`) | REQ-YG-668 (CAP-264) | "The post-FR-1012 tracked-text census remains reconciled: active doctrine, skill instructions, process/reference documentation, and examples describe the operator-driven author -> judge -> worktree enforcement -> review -> human-merge route; no new or reworded Chaplain-runtime match appears outside the frozen, dispositioned BASE set; non-historical Chaplain pointers in those documentation surfaces resolve to `docs/archive/chaplain.md` or `docs/archive/chaplain-system.md`; witnessed by `tests/unit/test_fr1013_doctrine_sweep.py`." |
| `test_knowledge_graph_block_is_byte_identical_to_base` | REQ-YG-192 (CAP-72) | "… all descriptions are one-liners following k[nowledge-graph style]; no existing traps/cures/process entries changed" — the KG block hash equals BASE's |
| `test_judge_doctrine_ramp_mirror_is_byte_identical` | REQ-YG-613 (CAP-244) | "every mirror_exact entry matches its live counterpart byte-for-byte" |

**Deviations.** (1) The R-1 grep at BASE returned 2586 matches in 261 files — far wider than the planning table's 17 — because `chaplain|Chaplain|watcher2?\b|inquisitor` matches historical prose (diaries, plans, book chapters, capability records) and the unrelated FR-885 worktree watcher; dispositions are per file (one disposition covering all matches in the file) and live in `docs/census/` because 261 rows would breach the 450-line file gate. (2) Three doctrine/reference files not in the planning table were found live at BASE and added to the edit set at inventory time, before any edit: `.github/skills/graph-authoring/{doctrine.md,SKILL.md}` ("escalate to Chaplain"), `reference/command-book.md` (names the heading), `reference/patterns/fsm-as-conductor.md` (links the moved file). (3) FR-1012 shipped `# noqa: S603` lines citing confession IDs that were never written, so the repo-wide `noqa_coverage --strict` gate blocked every commit on this branch; the repair (CONF-462…465) was first committed here, then split out at review #627 P6 into PR #628 (merged `b71d0083`) and this branch rebased onto it — no confession change remains in this PR. (4) Stale `.chaplain` *defaults in code* found by the inventory are outside a docs-only FR and filed as `proposals/stale-chaplain-paths-in-code.md`; the witness pins them unchanged (clause 4). (5) Clause 1 has one exception that is neither BASE content nor a new artifact of this FR: `docs/confessions.md` gained four matching `**File**:` lines on `main` via PR #628 between BASE and this PR. Rather than reclassify them, the witness freezes that exact four-line delta (`DELTA["docs/confessions.md"]`) and the disposition record names its source; any further drift fails the test (C-4). (6) `docs/development-process.md` residual lines are 7 (all archive links, the measurement sentence, the past-tense comparison heading, and the :366 self-exemption note) — listed verbatim in `RESIDUAL`.


## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1013-chaplain-doctrine-sweep.judgement.md](FR-1013-chaplain-doctrine-sweep.judgement.md).
R-1 (`BASE` gate + inventory refresh), R-2 (`mirror_exact`, no renderer),
R-3 (topology/§ 6/§ 7 in scope; `docs/archive/` exception), R-4
(executable ACs; post-merge closure), R-5 (traceability table; REQ-YG-192
scope) folded above.

**Review of PR #617 (2026-09-06, `scripts/review.sh`) folded:** P3 (no CAP
invented at enforcement — hard stop + return to judgement), P7 (heading
only; no added Scripture sentence). P5 (closure script) was folded, then
**reversed** by the round-2 judgement.

**Round-2 judgement (2026-09-06) — SPLIT.** R-1 folded: closure script,
its tests, the scripted closure subsection and AC-14 removed; AC-13
restored to the operator-owned post-merge record; AC-A13 added. R-2/R-3
(Concern B) are the entry conditions for a separate FR that is not filed.
Round-2 text appended to the judgement file.

**Review of PR #627 (2026-09-06, `scripts/review.sh`) — Not approved, seven
blocking findings, folded for round 3:** P1 (no post-SPLIT authority; four
edit-set files outside D-3) → this round-3 request with the committed edit
set; P2 (`docs/development-process.md` :5–7, :110, :145–174, :275–281 still
present the Chaplain/Inquisitor as live) → edit-set row and step 2 widened
to every active-process passage, measurement sentence still byte-identical;
P3 (file-level residual allowlist) → step 6 match-level design; P4
(REQ-YG-666 not direct) → step 7 `REQ-YG-668` proposal for the judge; P5
(AC-10 coverage floor) → `--no-cov`; P6 (confessions out of scope) → PR
#628; P7 (stale SHAs after rebase) → Implementation Record. The outsider
read of #627 (derived NO, six terms) was glossed in the PR body.

**Round-3 judgement (2026-09-06) — APPROVED WITH REVISIONS.** R-1 REQ-YG-668
(667 is CAP-265's); CAP-264 gains the REQ, FR-1013 in `fr`, doc surfaces +
witness in `modules`; `ARCHITECTURE.md` generated only. R-2 writable-surface
table (§ Inventory). R-3 residual contract, five clauses (§ Inventory) —
the pre-round-3 test's set-of-paths check is the defect it replaces. R-4
revised AC-01…16 replace the earlier list; branch commits are candidates
(C-8). Human review of the round-3 draft (C-1) is the operator's read on
the PR before merge, recorded at AC-13. Round-3 text appended to the
judgement file.

**Review of PR #627, round 2 (2026-09-06, head `59b11461`) — Not approved, six
findings, dispositioned:** P1 (automate the post-merge closure) → **refused
here**: round 2 SPLIT it out as Concern B and round 3 lists a closure script
under "Not authorized"; the judge governs scope, review is advisory — the
concern stays unfiled, AC-16 stays operator-owned. P2 (merge step ordering:
`docs/development-process.md` § 3 step 5 and the onepager flow steps 6–9 put
CI/reviews/diary after merge) → fixed: CI → outsider → review → diary → human
merge. P3 (`reference/patterns/fsm-as-conductor.md:235` relative link one
level short) → `../../docs/archive/chaplain-system.md`; residual line updated
in the witness. P4 (pre-rebase SHAs in the record) → recorded from the GitHub
PR after the last rebase; the branch is now advanced only by merge, never
rebase, so the IDs stay stable. P5 (diary not in D-1…D-8) → D-10 proposed,
round-4 judgement requested. P6 (changelog cites REQ-YG-666) → REQ-YG-668.

**Round-4 judgement (2026-09-06) — APPROVED WITH REVISIONS.** D-10: exactly
`docs/diary/2026-09-06-reflection-fr-1013-the-inventory-that-was-fifteen-times-the-plan.md` is the Distill artifact; R-1 diary exclusions reconciled (Summary,
allowlist, Purge list, AC-02); R-2 the CI `diary-gate` claim corrected — the
job runs only for `feat`/`fix` PR titles (`.github/workflows/commitlint.yml`),
so Scripture, not CI, requires the entry; AC-16 added (validator + literal
markers), post-merge AC renumbered AC-17; R-3 round-3 D-1…D-8 remain the
governing scope, the diary commit was a candidate until D-10. Round-4 text
appended to the judgement file.

**Review of PR #627, round 3 (2026-09-06, head `57b3a542`) — Not approved,
one finding:** P1 the witness read BASE via `git cat-file`, absent in the
depth-1 CI checkout → 7 assertions red in the required Python 3.11 job.
Fixed without touching CI (C-4): baseline moved into the committed disposition
record (sha256 per file), delta files pinned by expected HEAD sha256, missing
BASE blob no longer reads as zero matches; reproduced green in a depth-1 clone.
