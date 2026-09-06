# Judgement: FR-1019 Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

## Round 1 (2026-09-06, copilot backend via scripts/judge.sh) — REJECTED, R-1..R-5 folded into the FR


**Verdict:** REJECTED — the documentation sweep is a sound small change, but this newly created FR has no mandatory committed research reference and its proposed permanent witness cannot satisfy requirement traceability without violating the FR's own no-new-REQ boundary; no implementation authority is granted.

**DRAFT:** Advisory until human-reviewed.

**Reviewed against:** `feature-requests/FR-1019-chaplain-doctrine-sweep.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.judgement.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`; cited baseline commit `36591389`; cited closed PR #627 metadata, body, and file list at head `cf9b915ed21c734815e8600361bbeeccbd93e10b`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `ARCHITECTURE.md`; `capabilities/CAP-72-knowledge-graph-mass-graduation-fr193.yaml`; `capabilities/CAP-128-chaplain-documentation.yaml`; `capabilities/CAP-244-ramp-installer.yaml`; `capabilities/CAP-264-chaplain-runtime-retired.yaml`; `docs/archive/chaplain.md`; `docs/context/chaplain-system.md`; `ramp/manifest.yaml`; and committed searches of the proposed doctrine, skill, process, reference, example, capability, and test surfaces for the retired Chaplain paths and relevant REQ IDs.

## What is sound

The problem is real and the proposed implementation is materially smaller than the rejected predecessor. The current Scripture still names `chaplain pipeline` and `Sermon of the Chaplain`, while active process/reference surfaces still direct readers to `.chaplain/inbox/`, `.chaplain/scripts/start-system.sh`, and other removed paths (`.github/copilot-instructions.md:177,205`; `docs/development-process.md:5-7,24-25,113,124,154,189,201,299-301,330`; `reference/onepager-development-process.md:31,45,138`). FR-1019 names a concrete first consumer and failure event and limits the intended Scripture edit to two lines (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:8-9,14,18,22-28`).

The prior-art disposition captures the important lesson from FR-1013: preserve the document edits while dropping the census, baseline, new requirement, and 421-line regression fixture that made the process larger than the change (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:8,10,30,42-44`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:5-9`). The prerequisite is also real: FR-1012 is merged as `36591389`, and the archive page now records both the removed runtime and its surviving operator-driven replacements (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:5-12`; `docs/archive/chaplain.md:1-18,20-36`).

Against the eight rubric criteria:

1. **Scope:** the intended documentation reconciliation is minimal and single-purpose, but the declared “docs only” surface also requires a new test, changelog, diary, FR mutation, and post-merge umbrella closure without listing those writable surfaces (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:4,22-30,38-40`).
2. **Consistency:** AC-2 forbids `.chaplain/` in every edited file, while the authorized archive move preserves a historical system document whose content necessarily contains many `.chaplain/` paths; the archive index itself intentionally records `.chaplain/` recovery instructions (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:28,35`; `docs/context/chaplain-system.md:1-31`; `docs/archive/chaplain.md:3,7-18`). The acceptance condition is therefore impossible as written.
3. **Measurability:** AC-1, AC-3, and AC-4 have direct witnesses, but AC-2 does not define its archival exception or exact file set, AC-5 gives no executable tracked-file command, and AC-7 says “closes” FR-1010 without naming the exact status/criteria fields to update (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:34-40`).
4. **Feasibility:** the document edits, `git mv`, and `mirror_exact` copy are feasible using existing repository mechanisms. The mirror contract is already declared in `ramp/manifest.yaml:56-60`, and PR #627 demonstrates that the same document edits can be made.
5. **Architecture alignment:** pointing active guidance at the operator-driven scripts and preserving historical design under `docs/archive/` aligns with the surviving architecture (`docs/archive/chaplain.md:20-36`). The proposed untraced test does not align with the mandatory test-to-requirement contract (`.github/copilot-instructions.md:169`).
6. **Single responsibility:** the implementation concern is pattern documentation/repository maintenance, not a framework primitive or contrib example. Changelog and Distill are process artifacts of that concern, but the post-merge FR-1010 closure is a separate operator action and must not be represented as part of the pre-merge implementation.
7. **Strategic classification:** **Pattern documentation**. Existing archive, script, mirror, and documentation conventions suffice; no new abstraction is justified.
8. **Testability:** direct one-time acceptance checks can be derived for the fixed document set, and existing REQ-YG-192 and REQ-YG-613 witnesses can protect Knowledge Graph preservation and mirror equality. No existing requirement covers the proposed broad documentation-consistency test: REQ-YG-666 covers runtime absence, archive identities, census reconciliation, and retired one-shot tooling (`capabilities/CAP-264-chaplain-runtime-retired.yaml:15-28`); REQ-YG-192 covers the FR-193 Knowledge Graph entries (`capabilities/CAP-72-knowledge-graph-mass-graduation-fr193.yaml:13-22`); REQ-YG-613 covers ramp provenance and exact mirrors (`capabilities/CAP-244-ramp-installer.yaml:57-72`). Leaving the remaining test untagged is forbidden, not a confessable exception (`.github/copilot-instructions.md:169`).

## Required revisions

### R-1: Add the mandatory committed research reference

Add a top-level `**Research:**` field. It may point to the already committed FR-1010 alternatives section if the FR states why that record applies to this final documentation phase and includes the explicit answer `is_this_a_graph: no` for the fixed deterministic edit set. The record must retain genuine solution classes, precedent, and disagreement; a link to FR-1013's implementation history alone is not research.

FR-1019 was created after the prospective FR-890 gate, but lines 3-10 contain no `**Research:**` field. The template says an absent or dangling field grants no authority (`feature-requests/TEMPLATE.md:11-20`), and judge doctrine requires rejection or return to planning for that defect (`.github/skills/judge-fr/doctrine.md:118-128`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:156-170`).

### R-2: Separate live-document cleanup from preserved archive content

Replace AC-2 with an exact list of live files in which the retired operational strings must be absent. Exclude `docs/archive/chaplain.md` and the moved `docs/archive/chaplain-system.md` from that absence rule; instead require the moved document to retain its historical content and require active documents to link to it only as history.

Define the edited live set exactly as the non-archive paths in the Change table. For those files, require absence of `.chaplain/inbox`, `.chaplain/scripts`, `start-system.sh`, `label: chaplain`, `chaplain-ops`, and `Chaplain/Watcher`, except for an exact past-tense archive sentence explicitly listed in the FR. Do not introduce a repository-wide baseline, hash inventory, or historical-content rewrite.

### R-3: Remove the untraceable permanent witness

Delete `tests/unit/test_fr1019_doctrine_sweep.py` from the plan and replace AC-5 with one-time executable acceptance commands over the exact live edit set. Keep the existing requirement-owned witnesses:

- `tests/unit/test_knowledge_graph_fr193.py` under REQ-YG-192 for preservation of the Knowledge Graph;
- `tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes` under REQ-YG-613 for the doctrine mirror; and
- `tests/unit/test_fr1012_chaplain_removed.py` under REQ-YG-666 for the already-delivered runtime-removal contract.

Do not tag documentation-consistency assertions with REQ-YG-666 or REQ-YG-192, and do not leave a test function unmarked. This resolves traceability without reviving FR-1013's new requirement or permanent repository census.

### R-4: Freeze the complete writable and post-merge surfaces

Add the changelog fragment, one exact new diary path, and the FR implementation record to the Change table. State that all other diary and historical content remains untouched. Move FR-1010 closure into a separately labeled post-merge operator condition that names the exact FR-1010 fields/criteria updated and cannot be satisfied in the implementation PR.

Delete “One judgement round; findings that would add structure to this FR are answered by a sentence, not a table” (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:44`). Judgement count and required output structure are governed by judge doctrine, not by the proposal.

### R-5: Replace shorthand checks with executable acceptance commands

Define `BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e` once. Spell out commands that:

1. compare the seven bold Sermon step lines and the complete Knowledge Graph block against `BASE`;
2. search only the exact live edit set for the forbidden operational strings;
3. verify the archive move and link without applying the live-file absence rule to archive content;
4. run the existing REQ-YG-192 and REQ-YG-613 witnesses; and
5. show that only the two authorized Scripture lines differ from `BASE`.

The full unit suite may remain the final regression gate, but it is not a substitute for these focused witnesses.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Planning revision only: `feature-requests/FR-1019-chaplain-doctrine-sweep.md` may fold R-1 through R-5 and return for a fresh judgement. |

Not authorized by this rejected draft: any implementation edit to Scripture, skills, process/reference/example documentation, archive files, ramp assets, tests, capabilities, requirements, generated architecture, changelog, diary, FR-1010, scripts, hooks, CI, graphs, prompts, or runtime code; cherry-picking any commit from PR #627; creating a census, baseline, per-file hash inventory, permanent broad residual test, new CAP, or new REQ.

## Revised acceptance criteria

- [ ] AC-01: FR-1019 has a non-dangling `**Research:**` reference to committed substantive evidence and records `is_this_a_graph: no`.
- [ ] AC-02: The Change table exhaustively separates live content edits, archive preservation/move, process artifacts, and the post-merge FR-1010 operator action.
- [ ] AC-03: The live-file stale-reference check names its exact path set and exact forbidden strings; archive files are tested for historical preservation and links, not absence of historical `.chaplain/` paths.
- [ ] AC-04: No new test file, CAP, REQ, census, baseline, or per-file hash inventory is proposed; focused acceptance uses executable commands plus the existing REQ-YG-192 and REQ-YG-613 witnesses.
- [ ] AC-05: The seven Sermon steps and complete Knowledge Graph block are compared with full `BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e`; the Scripture diff is limited to the heading and canonical-sources clause.
- [ ] AC-06: The archive move, archive link, audit-index cardinality, judge-doctrine mirror, unchanged ramp manifest/curation file, changelog metadata, exact diary path, and full unit-suite command each have an executable witness.
- [ ] AC-07: Human review of the Scripture and judge-doctrine diffs is a pre-merge gate; FR-1010 closure is an explicitly named post-merge operator action.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | This verdict grants no implementation authority. R-1 through R-5 must be folded into the committed FR and the revised FR must receive a fresh judgement. | GATE |
| C-2 | The resubmission must remain a small fixed-surface documentation change; no census, repository baseline, permanent broad residual witness, new CAP, or new REQ may return. | GATE |
| C-3 | No test may be unmarked or assigned to a requirement whose text it does not witness. | GATE |
| C-4 | Archive content is historical evidence and must not be rewritten merely to satisfy a live-document stale-path search. | GATE |
| C-5 | Scripture and judge-doctrine changes require recorded human review before merge. | GATE |
| C-6 | FR-1010 may be closed only after the implementation PR is merged and its immutable merge SHA is available. | GATE |

Authority granted: none; only the D-1 planning revision is permitted before FR-1019 re-enters judgement.


---

## Round 2 (2026-09-06, copilot backend via scripts/judge.sh, on the FR with round-1 R-1..R-5 folded) — APPROVED WITH REVISIONS, R-1..R-4 folded into the FR


**Verdict:** APPROVED WITH REVISIONS — the small documentation reconciliation is sound, but authority activates only after the live-file outcomes, executable assertions, closed-branch reuse boundary, and FR-1010 succession record are folded into the FR.

**DRAFT:** Advisory until human-reviewed.

**Reviewed against:** `feature-requests/FR-1019-chaplain-doctrine-sweep.md`; `feature-requests/FR-1019-chaplain-doctrine-sweep.judgement.md` (round 1); `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.judgement.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`; cited baseline commit `36591389e2fdfedf9ba5ae6362effad1c64cd06e`; cited closed PR #627 head `cf9b915e` and its diff from the baseline; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/development-process.md`; `.github/skills/feature-request/SKILL.md`; `.github/skills/graph-authoring/SKILL.md`; `.github/skills/graph-authoring/doctrine.md`; `reference/onepager-development-process.md`; `reference/audit-index.md`; `reference/graph-yaml.md`; `reference/command-book.md`; `reference/patterns/fsm-as-conductor.md`; `examples/README.md`; `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`; `capabilities/CAP-72-knowledge-graph-mass-graduation-fr193.yaml`; `capabilities/CAP-244-ramp-installer.yaml`; and `capabilities/CAP-264-chaplain-runtime-retired.yaml`.

## What is sound

The proposal now states a concrete failure event, a narrow ideal result, an exact prerequisite baseline, and a deliberate boundary between active guidance and preserved history (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:8-18`). The cited umbrella research compares six genuine archival classes, preserves the material disagreement between history-only deletion and a browsable archive, names precedent, and answers `is_this_a_graph`; FR-1019 explains why that decision governs this final documentation phase (`feature-requests/FR-1010-chaplain-archival-plan.md:449-468`; `feature-requests/FR-1019-chaplain-doctrine-sweep.md:10-11`).

The round-1 defects are materially resolved. The revised FR separates the exact live set from the byte-identical historical move, removes the untraceable permanent test, reuses only requirement-owned witnesses for mirror equality, Knowledge Graph preservation, and runtime absence, names its changelog and Distill artifacts, and makes umbrella closure explicitly post-merge (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:20-45,51-78`). That is the correct response to FR-1013's rejected census, new requirement, and 421-line broad witness rather than another layer of enforcement machinery (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:3-9`).

Against the eight rubric criteria:

1. **Scope:** the implementation is a fixed documentation reconciliation plus required process artifacts. It does not revive runtime, test, capability, hook, CI, graph, or script work (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:20-45,80-82`).
2. **Consistency:** live and archive content are now separated, but the grouped “pointer fixes” row is less precise than the ideal result, and FR-1010 still names rejected FR-1013 as the phase that must merge (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:16-17,27-32,43-45`; `feature-requests/FR-1010-chaplain-archival-plan.md:341-358,374-376,401-408`). R-1 and R-4 close those remaining contradictions.
3. **Measurability:** the baseline, Scripture preservation, archive move, mirror, targeted witnesses, and suite are directly checkable. Several count commands currently print expected values without asserting them, the combined script count does not prove that all three scripts occur, and AC-5 gives prose rather than executable artifact checks (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:49-78`). R-3 makes those gates fail mechanically.
4. **Feasibility:** the cited closed implementation proves that the document transformations and exact rename are workable, and the repository already declares the judge doctrine asset as `mirror_exact`. Reusing a closed branch must be hunk-based rather than copying whole stale files (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:40`; `capabilities/CAP-244-ramp-installer.yaml:62-69`). R-2 freezes that boundary.
5. **Architecture alignment:** active guidance moves to the surviving author/judge/review scripts while historical FSM design moves under `docs/archive/`; Scripture keeps its seven-step rite and Knowledge Graph unchanged (`feature-requests/FR-1019-chaplain-doctrine-sweep.md:22-38,51-57`).
6. **Single responsibility:** this is one pattern-documentation concern. The changelog, diary, implementation record, and post-merge bookkeeping are lifecycle artifacts, not additional capabilities. No split is warranted.
7. **Strategic classification:** **Pattern documentation**. Existing scripts, archive structure, mirror contract, and requirement witnesses suffice; no framework primitive or contrib example is added.
8. **Testability:** each authorized invariant can be checked by focused shell assertions and the three existing requirement-owned tests. No new production branch or permanent behavior requires a new test; the remaining defects are acceptance-command precision, not a traceability gap.

## Required revisions

### R-1: Replace the grouped pointer row with exact file outcomes

Expand the third live-edit row into mechanically reviewable outcomes for each named file. At minimum, state that:

- `reference/onepager-development-process.md` replaces the active “Chaplain Pipeline,” issue-label importer, inbox flow, Inquisitor loop, and old context link with the operator-driven rite and archive link;
- `reference/audit-index.md` retains exactly one archived Chaplain row and removes the retired runtime component rows;
- `reference/graph-yaml.md` replaces the stale watcher/Chaplain examples with surviving graph paths;
- `reference/command-book.md` renames its Scripture link to “Sermon”;
- `reference/patterns/fsm-as-conductor.md` retains Chaplain only as an explicitly archived historical case and points to `docs/archive/`;
- `examples/README.md` removes the deleted stub/witness claims and points surviving graphs at `graphs/`.

Keep the existing exact rows for Scripture, development process, graph-authoring doctrine, judge doctrine, and the archive move. This is not a new census: it freezes the already selected twelve live files so the stated ideal can be reviewed without relying on private knowledge of PR #627.

### R-2: Define closed-branch reuse as authorized-hunk porting

Replace “cherry-pick them file by file” with an instruction to port only the document hunks enumerated in the frozen Change table from cited head `cf9b915e`. Do not cherry-pick commits, restore whole files from that head, or import its census, test, capability, architecture, confession, diary, FR, or post-merge-record changes.

The cited head contains many changes outside this FR's scope, including `ARCHITECTURE.md`, `capabilities/CAP-264-chaplain-runtime-retired.yaml`, census artifacts, tests, confessions, and other FR/diary records. A path-level checkout can also overwrite changes made after the baseline. Every ported file must therefore be reviewed as a patch against current HEAD.

### R-3: Turn printed expectations into failing assertions

Revise AC-1 through AC-5 so each expected count is asserted, not left as a comment beside output. Use `test` around `grep -c` and `git diff --numstat`, test `scripts/author.sh`, `scripts/judge.sh`, and `scripts/review.sh` separately, and make the two measurement-sentence values byte-equal.

Add executable AC-5 checks for the exact changelog path and its YAML fields and for the exact diary path and `**Seed:**`. In AC-2, record and human-disposition every remaining case-insensitive `Chaplain`, `Inquisitor`, or `.chaplain` match in the exact live set as either an explicitly historical statement, an archive link, or one of the two preserved Knowledge Graph entries. The narrower forbidden-string grep remains useful but cannot alone prove the Ideal Result: for example, an active heading such as “The Chaplain Pipeline” contains none of its forbidden alternatives.

### R-4: Make FR-1019 the recorded successor for umbrella Phase 3

Expand the post-merge operator action and AC-7 to update FR-1010's Phase 3 and phase-order/AC-04 references from rejected FR-1013 to “FR-1019, superseding rejected FR-1013,” then record FR-1019's immutable merge SHA. Only after that correction and the merged-main AC-12 witness may the operator tick FR-1010 AC-12 and AC-13 and set FR-1010 to `Completed`.

Without this fold, FR-1010 still requires FR-1013 itself to receive human review and merge in sequence, which can never occur after FR-1013 was rejected and closed (`feature-requests/FR-1010-chaplain-archival-plan.md:355-376`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:3-9`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Two-line edit only in `.github/copilot-instructions.md` |
| D-2 | Active-process reconciliation in `docs/development-process.md` |
| D-3 | Exact pointer/history edits in `reference/onepager-development-process.md`, `reference/audit-index.md`, `reference/graph-yaml.md`, `reference/command-book.md`, `reference/patterns/fsm-as-conductor.md`, and `examples/README.md` |
| D-4 | Retired-route wording edits in `.github/skills/graph-authoring/SKILL.md`, `.github/skills/graph-authoring/doctrine.md`, and `.github/skills/judge-fr/doctrine.md`; byte-identical copy to `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` |
| D-5 | Byte-identical move from `docs/context/chaplain-system.md` to `docs/archive/chaplain-system.md`; one link line in `docs/archive/chaplain.md` |
| D-6 | `changelog/unreleased/fr1019-doctrine-sweep.md`, `docs/diary/diary-2026-09-06-reflection-fr-1019-chaplain-doctrine-sweep.md`, and FR-1019's implementation record |
| D-7 | Post-merge operator update to FR-1010 replacing FR-1013 with its FR-1019 successor, recording the merge SHA, satisfying AC-12/AC-13, and setting status to `Completed` |

Not authorized: any runtime, Python, hook, CI, graph, prompt, script, test, capability, requirement, architecture, ramp manifest, or ramp curation change; any census, inventory artifact, repository baseline file, or per-file hash registry; any edit to historical FR, diary, changelog, memento, ebook, research, or archive content except D-5 and the expressly post-merge FR-1010 update; any change to a Sermon step or Knowledge Graph entry; any whole-file restoration or commit cherry-pick from closed PR #627.

## Revised acceptance criteria

- [ ] AC-01: `BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e`; `git merge-base --is-ancestor "$BASE" HEAD` succeeds; `.github/copilot-instructions.md` has zero `Sermon of the Chaplain` matches; its numstat against BASE is exactly `2	2`; diffs of the seven bold Sermon steps and complete Knowledge Graph YAML block against BASE are empty.
- [ ] AC-02: The Change table states the exact outcome for every live file in D-1 through D-4. The exact live set has zero forbidden operational-string matches, contains each of `scripts/author.sh`, `scripts/judge.sh`, and `scripts/review.sh` in `docs/development-process.md`, and preserves the measurement sentence byte-for-byte.
- [ ] AC-03: A case-insensitive search for `Chaplain`, `Inquisitor`, and `.chaplain` over the exact live set is recorded in the implementation record; every surviving line is human-dispositioned as explicit history, an archive link, or one of the two untouched Knowledge Graph entries. No surviving line presents the retired runtime as an active route.
- [ ] AC-04: `docs/context/chaplain-system.md` is absent; `docs/archive/chaplain-system.md` exists; `git diff --name-status -M100% "$BASE" --` reports `R100`; `docs/archive/chaplain.md` has exactly one link to it; `reference/audit-index.md` has exactly one `Chaplain` row and that row links `docs/archive/chaplain.md`.
- [ ] AC-05: Canonical and ramp judge doctrine are byte-identical; `ramp/manifest.yaml` and `ramp/curation-diffs.md` are unchanged from BASE; the existing REQ-YG-613, REQ-YG-192, and REQ-YG-666 witness tests named in the FR pass.
- [ ] AC-06: The exact changelog fragment exists and its front matter asserts `type: removal` and `scope: doctrine`; the exact diary file exists and contains `**Seed:**`; the non-slow unit suite passes.
- [ ] AC-07: The FR implementation record lists every changed path and demonstrates that all are D-1 through D-6; it records human review of the Scripture and both judge-doctrine copies before merge.
- [ ] AC-08: No commit or whole file is cherry-picked/restored from `cf9b915e`; only the frozen document hunks are ported and reviewed against current HEAD.
- [ ] AC-09: Post-merge only, FR-1010 identifies FR-1019 as the successor that delivered Phase 3, records its immutable merge SHA, updates the obsolete FR-1013 phase references, records the merged-main residual witness, ticks AC-12/AC-13, and moves to `Completed`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 must be folded into the committed FR before implementation authority activates. | GATE |
| C-2 | This draft and both enforcement-infrastructure diffs (`.github/copilot-instructions.md` and canonical/mirrored judge doctrine) require recorded human review before merge. | GATE |
| C-3 | The two Scripture lines are the complete authorized Scripture change; all seven Sermon steps and the complete Knowledge Graph block remain byte-identical to BASE. | GATE |
| C-4 | Archive content remains historical evidence and may not be rewritten to satisfy the live-file residual checks. | GATE |
| C-5 | No new test, CAP, REQ, census, baseline artifact, hash inventory, script, hook, or CI change may be introduced. | GATE |
| C-6 | Closed PR #627 is evidence and a hunk source only; it is not authority to import any path or commit outside D-1 through D-6. | GATE |
| C-7 | D-7 occurs only after the implementation PR merges and its immutable merge SHA exists. | GATE |

Authority granted: after R-1 through R-4 are folded into the committed FR and this draft is human-reviewed, FR-1019 may implement only D-1 through D-6; the operator may perform D-7 only after that implementation PR merges.
