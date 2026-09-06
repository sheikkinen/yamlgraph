# Feature Request: Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Priority:** LOW
**Type:** Enhancement (docs; Scripture edit — human gate C-4)
**Status:** Amended for **round-3 judgement** (2026-09-06) after `scripts/review.sh` on PR #627 returned seven blocking findings — the round-2 verdict was `SPLIT` and granted Concern A no authority, yet the branch `feat/fr1013-doctrine-sweep` was enforced (step 0 `24015cf8`, RED `09818086`, GREEN `b5a80c5b`, diary `6e6523ab`). That branch is a **candidate**, not an enforcement: the round-3 verdict governs it, and every passage it left live (review P2), its file-level residual test (P3), its REQ tagging (P4) and its AC-10 command (P5) are re-specified below and will be re-enforced under whatever round 3 grants. Confession repair moved out to PR #628 (P6, merged `b71d0083`). History: APPROVED WITH REVISIONS (round 1, 2026-09-06); **SPLIT** (round 2, 2026-09-06) after review P5 added a closure script — Concern A (this docs-only sweep) continues here; Concern B (post-merge closure automation) is **not** filed, see § Post-merge closure.
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
narrative wherever it appeared as live instruction; historical FRs, diary,
changelog and `docs/memento/` are untouched.

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
`docs/archive/chaplain-system.md` may be written under `docs/archive/`.

### Inventory at BASE (R-1) — committed before any edit

```bash
BASE=<FR-1012 merge SHA>
git merge-base --is-ancestor "$BASE" HEAD || exit 1
git ls-files '*.md' '*.py' '*.sh' '*.yaml' '*.yml' \
  | grep -vE '^(feature-requests|changelog|docs/diary|docs/memento|docs/ebook|docs/archive)/|^docs/research-|^docs/context/fr-698\.md$|^ramp/curation-diffs\.md$' \
  | xargs grep -nE '\.chaplain|Chaplain|chaplain|watcher2?\b|Inquisitor|inquisitor|label: chaplain|`chaplain` label'
```

**Result at BASE `36591389`** (run 2026-09-06 from `feat/fr1013-doctrine-sweep`; `git merge-base --is-ancestor` exit 0): **2586 matches in 261 files**. Raw list (`file:line` per match; the full-text form is 509 KB and trips the large-file gate, and every line is reproducible from `BASE`): [docs/census/fr1013-inventory-at-base-36591389.txt](../docs/census/fr1013-inventory-at-base-36591389.txt); one disposition per file (covering every match in it): [docs/census/fr1013-inventory-at-base-36591389.dispositions.md](../docs/census/fr1013-inventory-at-base-36591389.dispositions.md) — kept out of this file because 261 rows would breach the 450-line file gate. No **stop** row: nothing under `.chaplain/` survives and no live consumer of a `.chaplain/` artifact was found; stale `.chaplain` *defaults* in code (`research_tools.py`, `diary_recurrence.py`, `cap_journey_census/extract.py`) are code, outside this docs-only FR, and filed as a spark. The grep's `watcher2?\b` arm also matches the unrelated FR-885 worktree watcher and the file-hook/DeviantArt watchers — false positives, kept.

**Edit set (13 files; every implementation edit is one of these):**

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
   (`capabilities/CAP-264-chaplain-runtime-retired.yaml`) — `REQ-YG-667`:
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
   REQ under an existing CAP, tagged only by the documentation assertions.
   Alternative for the judge: name an existing REQ that covers doctrine
   consistency directly; the author found none (REQ-YG-192 is KG-shape,
   REQ-YG-195 is `fsm/CLAUDE.md` mirroring, REQ-YG-613 is ramp bytes).
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

## Acceptance Criteria (from judgement, verbatim; R-4)

- [ ] AC-01: FR-1013 records the immutable FR-1012 merge SHA as `BASE`, links its human review, and `git merge-base --is-ancestor "$BASE" HEAD` exits 0 before any FR-1013 enforcement.
- [ ] AC-02: The R-1 post-removal inventory is committed in FR-1013 with its exact commands, baseline SHA, complete match list, and one disposition per match; every implementation edit is in that frozen inventory.
- [ ] AC-03: `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` returns 0, and a `diff` of the seven bold Sermon step names extracted from `git show "$BASE":.github/copilot-instructions.md` and the working tree is empty.
- [ ] AC-04: `docs/development-process.md` describes the operator-driven `scripts/author.sh` → `scripts/judge.sh` → worktree enforcement → `scripts/review.sh` → human merge route; no non-historical passage names `start-system.sh`, the issue-label importer, `.chaplain/inbox`, `.chaplain/failed`, or `.chaplain/inquisitor.sh`; § 3.1's measurement sentence is byte-identical to `BASE`.
- [ ] AC-05: `reference/audit-index.md` has exactly one row containing `Chaplain`, and that row links `docs/archive/chaplain.md`; all other active reference/skill/example matches have the R-1 disposition enforced by `test_fr1013_doctrine_sweep.py`.
- [ ] AC-06: `docs/archive/chaplain-system.md` exists, `docs/context/chaplain-system.md` does not, and `git diff --name-status -M90% "$BASE"...HEAD` reports the move at a score of at least 90%; `docs/archive/chaplain.md` links the moved document.
- [ ] AC-07: `cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md` exits 0; `pytest tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes -q` passes; `git diff --exit-code "$BASE"...HEAD -- ramp/manifest.yaml ramp/curation-diffs.md` exits 0.
- [ ] AC-08: The broad residual test derived from R-1 checks `.md`, `.py`, `.sh`, `.yaml`, and `.yml` tracked files and fails for every `.chaplain` or active Chaplain-runtime reference outside its exact historical/archive allowlist; its result satisfies FR-1010 AC-12 rather than silently widening the allowlist.
- [ ] AC-09: Every new/updated test is listed with its surviving REQ and quoted requirement text; unrelated assertions are not tagged REQ-YG-192; the selected old-string witness list exactly matches tests still present after FR-1012.
- [ ] AC-10: `pytest tests/unit/test_fr1013_doctrine_sweep.py tests/unit/test_knowledge_graph_fr193.py tests/unit/test_ramp_installer.py -q --no-cov` (the repo's 85 % coverage floor is configured for the full suite; a three-file selection cannot meet it — review #627 P5) and `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` pass.
- [ ] AC-11: Human review is recorded in FR-1013 before merge and confirms the Scripture diff is limited to the heading and canonical-sources clause, the judge doctrine mirror is byte-identical, and no Knowledge Graph entry or Sermon step changed.
- [ ] AC-12: `changelog/unreleased/fr-1013-doctrine-sweep.md` exists with `type: removal` and `scope: doctrine`.
- [ ] AC-13: Post-merge only, the operator records FR-1013's merge SHA in FR-1010, ticks AC-12/AC-13 after their commands pass on merged `main`, records each phase's completion, and changes status to `Completed` in a separate FR-1010-only closure commit.
- [ ] AC-A13 (round 2): The FR-1013 PR contains no closure script or closure-script test.

## Purge list

- No new doctrine. No new Knowledge-Graph entry (the diary entry
  `2026-09-06-…-sole-consumer-of-a-dead-file…` may graduate later via its
  own FR; not here).
- No edits under the allowlist except the two `docs/archive/` files named
  in § Problem (R-3).
- No `docs/development-process.md` edits outside the passages enumerated
  in the edit-set row; no edit to the § 3.1 measurement sentence.
- No `ramp/manifest.yaml` or `ramp/curation-diffs.md` edit.
- No script, hook, CI, graph, prompt change (round-2 SPLIT boundary). The
  only capability/requirement change is the single `REQ-YG-667` entry under
  CAP-264 proposed in step 7 — if round 3 grants it.

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
| § Inventory at BASE commit | `24015cf8` (after the P6 rebase onto `b71d0083`) — `docs/census/fr1013-inventory-at-base-36591389.{txt,dispositions.md}` |
| Candidate commits on the branch (pre-round-3) | RED `09818086` (SKIP=pytest, 9 fail / 11 pass at BASE), GREEN `b5a80c5b`, diary `6e6523ab`; round-3 re-enforcement commits recorded below when they exist |
| Traceability: test function → REQ → quoted text | see table below |
| Surviving old-string witness tests | `test_concurrency_safety_doc.py`, `test_fr748_fr_atlas.py`, `test_knowledge_graph_fr193.py` (present after FR-1012; `test_chaplain_readme_documentation.py` was deleted by the census). Their strings (`docs/concurrency-safety.md`, the FR atlases, the Knowledge Graph) are all in the keep set — untouched; all three pass |
| Human review (AC-11) | _pending — operator, on the PR_ |
| Post-merge closure (AC-13): merge SHA, FR-1010 ticks | _pending (operator)_ |

**Traceability (R-5).** REQ-YG-192 tags only the Knowledge-Graph-unchanged assertion. No CAP or REQ was invented.

| Test function | REQ | Quoted requirement text (`ARCHITECTURE.md` / CAP) |
|---|---|---|
| `test_residual_matches_stay_within_the_frozen_inventory`, `test_edit_set_files_no_longer_name_the_retired_route`, `test_sermon_heading_renamed_and_steps_unchanged`, `test_sources_clause_no_longer_names_the_chaplain_pipeline`, `test_development_process_describes_the_operator_route`, `test_development_process_measurement_sentence_is_byte_identical_to_base`, `test_audit_index_has_exactly_one_chaplain_row_pointing_at_the_archive`, `test_chaplain_system_doc_moved_to_archive_and_linked` | REQ-YG-666 (CAP-264) | "The Chaplain runtime is absent from main; its source is reachable only via the chaplain-archive tag … and the archived repository" — these assertions witness that the *documentation* agrees with that state: no live doctrine or reference presents the absent runtime as the executable route, and every pointer resolves to the archive. This is the closest surviving REQ; if the reviewer holds that documentation consistency is not "directly covered" by REQ-YG-666, this FR returns to judgement per R-5 rather than inventing a REQ. |
| `test_knowledge_graph_block_is_byte_identical_to_base` | REQ-YG-192 (CAP-72) | "… all descriptions are one-liners following k[nowledge-graph style]; no existing traps/cures/process entries changed" — the KG block hash equals BASE's |
| `test_judge_doctrine_ramp_mirror_is_byte_identical` | REQ-YG-613 (CAP-244) | "every mirror_exact entry matches its live counterpart byte-for-byte" |

**Deviations.** (1) The R-1 grep at BASE returned 2586 matches in 261 files — far wider than the planning table's 17 — because `chaplain|Chaplain|watcher2?\b|inquisitor` matches historical prose (diaries, plans, book chapters, capability records) and the unrelated FR-885 worktree watcher; dispositions are per file (one disposition covering all matches in the file) and live in `docs/census/` because 261 rows would breach the 450-line file gate. (2) Three doctrine/reference files not in the planning table were found live at BASE and added to the edit set at inventory time, before any edit: `.github/skills/graph-authoring/{doctrine.md,SKILL.md}` ("escalate to Chaplain"), `reference/command-book.md` (names the heading), `reference/patterns/fsm-as-conductor.md` (links the moved file). (3) FR-1012 shipped `# noqa: S603` lines citing confession IDs that were never written, so the repo-wide `noqa_coverage --strict` gate blocked every commit on this branch; the repair (CONF-462…465) was first committed here, then split out at review #627 P6 into PR #628 (merged `b71d0083`) and this branch rebased onto it — no confession change remains in this PR. (4) Stale `.chaplain` *defaults in code* found by the inventory are outside a docs-only FR and filed as `proposals/stale-chaplain-paths-in-code.md`.


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
(REQ-YG-666 not direct) → step 7 `REQ-YG-667` proposal for the judge; P5
(AC-10 coverage floor) → `--no-cov`; P6 (confessions out of scope) → PR
#628; P7 (stale SHAs after rebase) → Implementation Record. The outsider
read of #627 (derived NO, six terms) was glossed in the PR body.
