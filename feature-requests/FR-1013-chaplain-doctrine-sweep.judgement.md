# Judgement: FR-1013 Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Verdict:** APPROVED WITH REVISIONS — the documentation-only retirement sweep is sound and single-purpose, but authority activates only after FR-1012 is merged, the inventory is refreshed against that merge, the nonexistent ramp renderer is replaced with the repository's `mirror_exact` workflow, and the contradictory/pre-merge acceptance checks are corrected.

**Reviewed against:** `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-193-mass-graduation-scripture-patterns.md`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; cited `docs/archive/chaplain.md` (absent in the judged tree); `docs/context/chaplain-system.md`; `docs/development-process.md`; `reference/onepager-development-process.md`; `reference/audit-index.md`; `reference/graph-yaml.md`; `examples/README.md`; `CLAUDE.md`; `.github/skills/feature-request/SKILL.md`; `ramp/manifest.yaml`; `ramp/curation-diffs.md`; `ramp/salvage/README.md`; `ramp/salvage/render.sh`; `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`; `ARCHITECTURE.md`; `tests/unit/test_knowledge_graph_fr193.py`; `tests/unit/test_ramp_installer.py`; `tests/unit/test_chaplain_readme_documentation.py`; `tests/unit/test_concurrency_safety_doc.py`; `tests/unit/test_fr748_fr_atlas.py`.

## What is sound

**Prior art:** see FR-1013's own Prior Art field (FR-193, FR-207, FR-1011, FR-1012) — this judgement reviews and dispositions those same citations; FR-1010 and its sibling phase FRs are the governing plan, not precedent.

The problem is real and the selected change is smaller than preserving retired runtime instructions behind banners. The first-consumer chain is concrete, the ideal result is observable, and moving the long-form design record into `docs/archive/` preserves history without presenting the daemon as an active route (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:9-13,45-50,79-85,136-142`).

The proposal is one responsibility: reconcile active doctrine and reference surfaces after the separately governed runtime removal. It does not bundle runtime deletion, graph relocation, hook changes, or archive-repository creation. That separation conforms to FR-1010's ordered phase boundary and human gate (`feature-requests/FR-1010-chaplain-archival-plan.judgement.md:127-128`).

The intended Scripture edit is deliberately narrow, preserves the seven Sermon steps, and requires human review. The archive move, audit-index cardinality, stale-path census, exact mirror check, and targeted tests are all directly testable once their baselines and commands are repaired.

Strategic classification: **Pattern documentation**. This adds no framework primitive and no example; it makes the documented operator-driven plan → judge → enforce → review route agree with the surviving system.

## Required revisions

### R-1: Rebase every evidence claim and the sweep inventory on the merged FR-1012 tree

Replace the unsupported statement that FR-1012 is merged with a recorded immutable FR-1012 merge SHA, and make that SHA the implementation baseline. No enforcement authority exists until `git merge-base --is-ancestor <FR-1012-merge-sha> HEAD` succeeds. In the judged tree FR-1012 is still `Status: Proposed`, its judgement is pending, and `docs/archive/chaplain.md` does not exist (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:5,244`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:8,33).

After that merge, rerun the complete case-sensitive and case-insensitive inventories for `.chaplain`, `Chaplain`, `chaplain`, `watcher`, `Inquisitor`, and the retired issue-label/importer route across every non-historical Markdown/doctrine/reference surface. Record the command, baseline SHA, every match, and its disposition in the FR before enforcement. Replace stale future-tense claims about what FR-1011/FR-1012 "already" changed with merge-SHA-backed facts. Correct the `docs/context/chaplain-system.md` inventory size from the post-merge file rather than retaining the unsupported "53 lines" claim (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:21-34,55-76`).

This refresh is a gate, not permission to absorb new work: a newly discovered live artifact stops the phase under FR-1010 C-10 and returns the frozen inventory to judgement (`feature-requests/FR-1010-chaplain-archival-plan.judgement.md:134`).

### R-2: Replace the nonexistent ramp renderer with the `mirror_exact` contract

Delete every instruction and criterion that invokes `ramp/render.sh`. That path does not exist. The only renderer is `ramp/salvage/render.sh`, explicitly preserved as an unwired pattern reference, not as ramp asset generation machinery (`ramp/salvage/README.md:13-17`).

The judge doctrine asset is declared `mirror_exact`, not `curation_diff`: edit the canonical `.github/skills/judge-fr/doctrine.md`, copy it byte-for-byte to `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`, leave `ramp/curation-diffs.md` unchanged, and witness the contract with `cmp -s` plus `pytest tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes -q` (`ramp/manifest.yaml:56-60`; `tests/unit/test_ramp_installer.py:469-477`). Amend the FR-207 prior-art disposition to state that its renderer was superseded and that current ramp provenance is governed by the manifest; FR-207 itself records that supersession (`feature-requests/FR-207-standalone-scripture-methodology-repo.md:295-315`).

### R-3: Reconcile the stated objective with the complete documentation surface

Expand the frozen line-level inventory within the already named documentation files so it covers every active-process passage, not only `docs/development-process.md` §3/§3.1 and four one-pager lines. The current development-process document also presents the retired route in its opening topology, §6 self-correction loop, and §7 dogfooding table (`docs/development-process.md:24-38,292-304,324-330`). The one-pager also names the daemon as current enforcement, retains a "Chaplain Pipeline" section, and retains the Inquisitor/Chaplain loop outside the four listed lines (`reference/onepager-development-process.md:11,26,126`).

Replace those active claims with the surviving operator/scripts/worktree/review route or, where the text is genuinely historical, an explicit link to `docs/archive/chaplain.md`. Replace "No rewrite ... beyond §3/§3.1" with an exact paragraph/section allowlist derived from R-1. Do not rewrite unrelated gate, traceability, or architecture content.

Resolve the direct allowlist contradiction: the solution authorizes editing `docs/archive/chaplain.md` to add the long-form link, while the purge list says no allowlisted path may be edited (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:73-76,96-97,132-133`). Permit exactly `docs/archive/chaplain.md` and the new `docs/archive/chaplain-system.md`; keep all other historical allowlist content immutable.

### R-4: Make every acceptance command executable at the correct lifecycle point

Define `BASE=<recorded FR-1012 merge SHA>` once and replace `old`, `<base>`, ellipses, and prose-only checks with commands or test assertions using that baseline. Compare Sermon step names with `git show "$BASE":.github/copilot-instructions.md`; check rename detection with `git diff --name-status -M90% "$BASE"...HEAD`; encode the R-1 residual allowlist in `test_fr1013_doctrine_sweep.py`; and replace AC-06 with the `mirror_exact` witnesses from R-2.

Move the current AC-09 out of the PR merge criteria into a named **post-merge closure** step. FR-1010 cannot be ticked with FR-1013's merge SHA before that SHA exists. The PR merge gate may require human review and a recorded intent to finalize; only after merge may the operator record the merge SHA, tick FR-1010 AC-12/AC-13, and set FR-1010 to `Completed` (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:116-124`; `feature-requests/FR-1010-chaplain-archival-plan.md:395-400`).

### R-5: Repair requirement traceability and surviving-test selection

Do not assign all FR-1013 assertions to REQ-YG-192 merely because `test_knowledge_graph_fr193.py` uses it. REQ-YG-192 specifically witnesses the five FR-193 process entries, the seeds section, one-line descriptions, and preservation of existing Knowledge Graph entries; it does not cover archive moves, reference sweeps, or process-document accuracy (`ARCHITECTURE.md:1242-1250`).

After the FR-1012 merge and R-1 census, add a traceability table mapping each new test function to the exact surviving requirement text it witnesses. REQ-YG-192 may be used only for an assertion that its existing Knowledge Graph entries remain unchanged. Name only tests that survive FR-1012; do not speculate that the four currently listed old-string tests will remain. If no live requirement directly covers a proposed assertion, return the traceability gap to judgement rather than mis-tagging it or inventing a capability inside enforcement.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Record FR-1012's merge SHA and refresh the post-removal evidence inventory in `feature-requests/FR-1013-chaplain-doctrine-sweep.md` |
| D-2 | Rename only the Scripture heading and remove only the obsolete canonical-sources clause in `.github/copilot-instructions.md`; preserve the seven Sermon steps and Knowledge Graph content |
| D-3 | Reconcile active-process passages identified by R-1 in `docs/development-process.md`, `reference/onepager-development-process.md`, `reference/audit-index.md`, `reference/graph-yaml.md`, `examples/README.md`, and `.github/skills/feature-request/SKILL.md` |
| D-4 | Move `docs/context/chaplain-system.md` to `docs/archive/chaplain-system.md` and add its link to `docs/archive/chaplain.md` |
| D-5 | Update `.github/skills/judge-fr/doctrine.md` and its byte-identical `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` mirror |
| D-6 | Add/update only the post-FR-1012 surviving witness tests, plus `tests/unit/test_fr1013_doctrine_sweep.py` if R-5 establishes valid traceability |
| D-7 | Add `changelog/unreleased/fr-1013-doctrine-sweep.md` and record the human review in FR-1013 |
| D-8 | After merge only, record FR-1013's merge SHA and close FR-1010 AC-12/AC-13 |

Not authorized: runtime, Python, hook, CI, graph, prompt, capability, requirement, ramp manifest, ramp provenance, archive-repository, tag, or worktree behavior changes; edits to historical FRs, diary, memento, ebook, research, changelog history, `docs/context/fr-698.md`, or any archive content except the two paths in D-4; edits to `CLAUDE.md` unless the R-1 inventory disproves its asserted zero-match state; changing the seven Sermon steps or any Knowledge Graph entry; changing `ramp/curation-diffs.md`; marking FR-1010 complete before FR-1013 is merged.

## Revised acceptance criteria

- [ ] AC-01: FR-1013 records the immutable FR-1012 merge SHA as `BASE`, links its human review, and `git merge-base --is-ancestor "$BASE" HEAD` exits 0 before any FR-1013 enforcement.
- [ ] AC-02: The R-1 post-removal inventory is committed in FR-1013 with its exact commands, baseline SHA, complete match list, and one disposition per match; every implementation edit is in that frozen inventory.
- [ ] AC-03: `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` returns 0, and a `diff` of the seven bold Sermon step names extracted from `git show "$BASE":.github/copilot-instructions.md` and the working tree is empty.
- [ ] AC-04: `docs/development-process.md` describes the operator-driven `scripts/author.sh` → `scripts/judge.sh` → worktree enforcement → `scripts/review.sh` → human merge route; no non-historical passage names `start-system.sh`, the issue-label importer, `.chaplain/inbox`, `.chaplain/failed`, or `.chaplain/graphs`; the May–July measurement sentence remains verbatim.
- [ ] AC-05: `reference/audit-index.md` has exactly one row containing `Chaplain`, and that row links `docs/archive/chaplain.md`; all other active reference/skill/example matches have the R-1 disposition enforced by `test_fr1013_doctrine_sweep.py`.
- [ ] AC-06: `docs/archive/chaplain-system.md` exists, `docs/context/chaplain-system.md` does not, and `git diff --name-status -M90% "$BASE"...HEAD` reports the move at a score of at least 90%; `docs/archive/chaplain.md` links the moved document.
- [ ] AC-07: `cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md` exits 0; `pytest tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes -q` passes; `git diff --exit-code "$BASE"...HEAD -- ramp/manifest.yaml ramp/curation-diffs.md` is empty.
- [ ] AC-08: The broad residual test derived from R-1 checks `.md`, `.py`, `.sh`, `.yaml`, and `.yml` tracked files and fails for every `.chaplain` or active Chaplain-runtime reference outside its exact historical/archive allowlist; its result satisfies FR-1010 AC-12 rather than silently widening that allowlist.
- [ ] AC-09: Every new/updated test is listed with its surviving REQ and quoted requirement text; unrelated assertions are not tagged REQ-YG-192; the selected old-string witness list exactly matches tests still present after FR-1012.
- [ ] AC-10: `pytest tests/unit/test_fr1013_doctrine_sweep.py tests/unit/test_knowledge_graph_fr193.py tests/unit/test_ramp_installer.py -q` and `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` pass.
- [ ] AC-11: Human review is recorded in FR-1013 before merge and confirms the Scripture diff is limited to the heading and canonical-sources clause, the judge doctrine mirror is byte-identical, and no Knowledge Graph entry or Sermon step changed.
- [ ] AC-12: `changelog/unreleased/fr-1013-doctrine-sweep.md` exists with `type: removal` and `scope: doctrine`.
- [ ] AC-13: Post-merge only, FR-1010 records FR-1013's merge SHA, ticks AC-12/AC-13 after their commands pass on merged `main`, records each phase's completion, and changes status to `Completed`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No FR-1013 implementation authority activates until R-1 through R-5 are folded into the committed FR and this draft receives human review. | GATE |
| C-2 | FR-1012 must be merged and its immutable merge SHA must be the recorded baseline before the sweep inventory, RED witness, or documentation edits begin. | GATE |
| C-3 | A post-FR-1012 match absent from the frozen inventory stops enforcement and returns FR-1010/FR-1013 to judgement under FR-1010 C-10. | GATE |
| C-4 | Human review is mandatory before merge for the Scripture edit and both copies of judge doctrine; mirror equality does not replace adversarial review. | GATE |
| C-5 | Only D-1 through D-7 may appear in the PR; D-8 is an operator-owned post-merge closure action because the merge SHA cannot exist earlier. | GATE |
| C-6 | Historical records remain historical: active documents may link to the archive, but no historical FR/diary/memento/ebook/research content may be rewritten to satisfy a grep. | GATE |
| C-7 | Ramp doctrine remains `mirror_exact`; no renderer, provenance change, manifest change, or curation-diff edit is authorized. | GATE |

Authority granted: after R-1 through R-5 are folded, human-reviewed, and the recorded FR-1012 merge prerequisite is satisfied, FR-1013 may implement only D-1 through D-7 and may perform D-8 only after the resulting PR is merged.


---

# Round 2 (2026-09-06, after review P5 added a closure script) — SPLIT

# DRAFT Judgement: FR-1013 Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Verdict:** SPLIT — the doctrine/reference sweep remains sound, but the newly added `scripts/fr1010_closure.sh` is an independent post-merge automation capability that contradicts the docs-only scope and must re-enter the pipeline under its own feature request; no implementation authority activates from this draft.

**Reviewed against:** committed `HEAD` (`6f927fa8`); `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-193-mass-graduation-scripture-patterns.md`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md`; `ARCHITECTURE.md`; `docs/development-process.md`; `docs/context/chaplain-system.md`; `reference/onepager-development-process.md`; `reference/audit-index.md`; `reference/graph-yaml.md`; `examples/README.md`; `CLAUDE.md`; `.github/skills/feature-request/SKILL.md`; `ramp/manifest.yaml`; `ramp/salvage/README.md`; `scripts/finalize_merge.sh`; `tests/unit/test_knowledge_graph_fr193.py`; `tests/unit/test_ramp_installer.py`; `tests/unit/test_chaplain_readme_documentation.py`; `tests/unit/test_concurrency_safety_doc.py`; `tests/unit/test_fr748_fr_atlas.py`. The cited `docs/archive/chaplain.md` is absent at the judged `HEAD`, consistently with the unfulfilled FR-1012 prerequisite.

## What is sound

The documentation concern is real, bounded, and supported by committed evidence. FR-1013 identifies a concrete first consumer and failure event, distinguishes the planning inventory from the required post-FR-1012 inventory, and stops rather than absorbing newly discovered live artifacts (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:11-21,62-66,95-108`). The active documents still present the retired daemon as the current process (`docs/development-process.md:24-43,121-175,292-320,324-330`; `reference/onepager-development-process.md:11,26,31,45,126,138,146,154`; `reference/audit-index.md:65-71`).

The research record is substantive for the archival program: it compares six genuine solution classes, names precedents and costs, preserves the material disagreement between history-only deletion and a browsable source archive, and answers `is_this_a_graph` (`feature-requests/FR-1010-chaplain-archival-plan.md:449-468`). FR-1013 also dispositions its Scripture, ramp, relocation, and removal precedents rather than merely listing them (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:22-42`). The `mirror_exact` correction agrees with the manifest and the preserved renderer's explicitly unwired status (`ramp/manifest.yaml:56-60`; `ramp/salvage/README.md:13-18`; `feature-requests/FR-207-standalone-scripture-methodology-repo.md:295-315`).

For **scope**, the doctrine/reference concern is minimal: it updates active guidance, moves one historical design document, preserves the seven Sermon steps, and leaves runtime deletion to FR-1012 (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:44-58,68-93,128-159`). For **measurability** and **testability**, AC-01 through AC-12 provide baseline, diff, cardinality, mirror, residual-search, traceability, test, human-review, and changelog witnesses from which direct checks can be written (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:175-186`). For **feasibility** and **architecture alignment**, the named operator route exists, the judge asset is already governed as a byte-identical mirror, and the Scripture change remains human-gated (`.github/copilot-instructions.md:204-212`; `ramp/manifest.yaml:56-60`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md:127-134`).

The defect is isolated by the remaining rubric criteria. **Consistency** fails because "One PR, docs-only" is followed by a new checked-in shell program and tests (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:123-126,161-171,187-188`). **Single responsibility** therefore fails: documentation reconciliation and post-merge state-mutating automation are independently implementable and testable concerns, which requires `SPLIT` under the judge rubric (`.github/skills/judge-fr/doctrine.md:49-50,75-77`). **Strategic classification:** Concern A is **Pattern documentation**; Concern B is a one-use-case repo automation contribution whose fit with an existing abstraction has not been resolved.

## Required revisions

### R-1: Restore FR-1013 to the documentation-only Phase 3 concern

Remove `scripts/fr1010_closure.sh`, its tests, the scripted post-merge-closure subsection, and AC-14 from FR-1013. Replace AC-13 with the operator-owned post-merge record required by the prior judgement: after FR-1013 merges, an operator records the merge SHA, executes FR-1010 AC-12 and AC-13 on merged `main`, records the phase results, and pushes the resulting FR-1010-only closure commit. This action is not a deliverable in the FR-1013 PR.

This restores agreement with the FR's `Type`, Summary, Proposed Solution, and Purge List (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:4,44-51,123-159,190-198`), the parent plan's Phase 3 surface (`feature-requests/FR-1010-chaplain-archival-plan.md:341-351`), and the prior frozen boundary that allowed D-8 only as an operator-owned action after merge (`feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md:55-68,86-98`).

### R-2: File post-merge closure automation as an independent feature request

Create a separate FR for any proposed `scripts/fr1010_closure.sh`. Its research and prior-art sections must explicitly disposition reuse or extension of `scripts/finalize_merge.sh`, CAP-38/REQ-YG-125, and the retiring CAP-114/REQ-YG-261 before selecting a second finalization script. The repository already has a post-merge finalizer that updates FR status and commits the result (`ARCHITECTURE.md:958-966,1645-1653`; `scripts/finalize_merge.sh:1-17,27-38,56-85`); the current FR neither demonstrates why that abstraction cannot fit nor classifies the new automation against it.

The new FR must define the success path as precisely as the error paths: exact checkout and remote identity, temporary-worktree creation and cleanup, branch and commit ownership, allowed file mutations, atomic failure behavior, repeat-run/idempotency behavior, and the boundary between script action and the human decisions to run and push. It must include a success witness plus witnesses for usage error, a SHA not on `origin/main`, a failed acceptance check, and interrupted/partial execution. The present text specifies exits 64-66 but only says the script works "in a worktree," leaving those operational contracts unstated (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:161-171,187-188`).

### R-3: Give the closure capability valid requirement traceability before RED

The closure FR must map every new test to a requirement that directly describes FR-1010 phase verification and closure. REQ-YG-125 covers changelog creation, one FR status update, and a diary stub; REQ-YG-261 covers the retired watch-driven finalization flow, not parent-plan phase reconciliation (`ARCHITECTURE.md:958-966,1645-1653`). If no surviving requirement covers the new behavior, the separate FR must define and register one before its RED commit. FR-1013's "no CAP or REQ is invented during enforcement" rule and pending traceability table cannot simultaneously authorize AC-14's new production script tests (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:147-153,183,188,216-225`).

### R-4: Correct the re-judgement record before either concern proceeds

Remove the claim that a re-judgement is already appended until a human-reviewed judgement is actually committed, and change the FR status to reflect this `SPLIT` verdict. Preserve the still-unfulfilled `BASE`, inventory, traceability, and human-review fields as gates rather than representing the prior revisions as implementation-ready (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:5-11,105-108,216-225,227-240`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-A1 | Amended FR-1013: record FR-1012's merge SHA, refresh and freeze the post-removal inventory, reconcile only the identified doctrine/reference/example/skill surfaces, move `docs/context/chaplain-system.md` to `docs/archive/chaplain-system.md`, update the archive link, preserve mirror equality, add validly traced sweep witnesses, add the removal changelog fragment, and record human review |
| D-B1 | Separate closure-automation FR: research and specify the post-merge FR-1010 verifier/finalizer, its architecture and requirement identity, shell implementation, tests, and operator handoff |

Not authorized by this judgement: implementing either concern before its amended or new FR is independently judged; adding `scripts/fr1010_closure.sh` or its tests to the FR-1013 PR; changing runtime, hooks, CI, graphs, prompts, capabilities, requirements, ramp manifest/provenance, archive repository, tags, or worktree policy under the documentation concern; changing any Sermon step or Knowledge Graph entry; rewriting historical FR, diary, memento, ebook, research, or changelog-history content; marking FR-1010 complete before FR-1013 is merged and its merged-state checks pass.

## Revised acceptance criteria

### Concern A — amended FR-1013 doctrine/reference sweep

- [ ] AC-A01: FR-1013 records the immutable FR-1012 merge SHA as `BASE`, links its human review, and records a successful `git merge-base --is-ancestor "$BASE" HEAD` before the inventory or implementation commits.
- [ ] AC-A02: The committed Inventory at BASE contains the exact command, baseline SHA, every match and one disposition per match; every implementation edit is present in that frozen inventory, and an unlisted live artifact stops enforcement under FR-1010 C-10.
- [ ] AC-A03: `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` returns 0, while a `BASE`-to-HEAD extraction of the seven bold Sermon step names is byte-identical and the Scripture diff contains only the heading and canonical-sources clause.
- [ ] AC-A04: `docs/development-process.md` names the operator-driven `scripts/author.sh` → `scripts/judge.sh` → worktree enforcement → `scripts/review.sh` → human merge route in the topology, §3, §6, and §7; the §3.1 measurement sentence is byte-identical to `BASE`.
- [ ] AC-A05: The frozen residual test covers tracked `.md`, `.py`, `.sh`, `.yaml`, and `.yml` files and rejects every active `.chaplain` or Chaplain-runtime instruction outside the exact historical/archive allowlist.
- [ ] AC-A06: `reference/audit-index.md` has exactly one `Chaplain` row and it links `docs/archive/chaplain.md`; every other active reference, example, and skill match has its frozen disposition.
- [ ] AC-A07: `docs/archive/chaplain-system.md` exists, `docs/context/chaplain-system.md` does not, `git diff --name-status -M90% "$BASE"...HEAD` reports a rename of at least 90%, and `docs/archive/chaplain.md` links the moved document.
- [ ] AC-A08: `cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md` succeeds, the existing mirror-exact test passes, and `ramp/manifest.yaml` plus `ramp/curation-diffs.md` are unchanged from `BASE`.
- [ ] AC-A09: Every new or updated test is mapped to a surviving REQ and quoted requirement text before RED; REQ-YG-192 marks only preservation of its existing Knowledge Graph entries; a missing direct requirement stops enforcement and returns FR-1013 to judgement.
- [ ] AC-A10: The targeted FR-1013, Knowledge Graph, and ramp tests and the non-slow unit suite pass.
- [ ] AC-A11: Human review is recorded before merge and confirms the restricted Scripture diff, byte-identical judge-doctrine mirror, unchanged Sermon steps, and unchanged Knowledge Graph.
- [ ] AC-A12: `changelog/unreleased/fr-1013-doctrine-sweep.md` exists with `type: removal` and `scope: doctrine`.
- [ ] AC-A13: The FR-1013 PR contains no closure script or closure-script test. After merge, the operator records the FR-1013 merge SHA and the actual FR-1010 AC-12/AC-13 results in a separate closure commit.

### Concern B — separate post-merge closure automation FR

- [ ] AC-B01: The new FR records a first consumer, first event, ideal result, strategic classification, and a disposition of `scripts/finalize_merge.sh`, CAP-38/REQ-YG-125, and CAP-114/REQ-YG-261.
- [ ] AC-B02: The selected design defines exact repository/remote/SHA validation, worktree and branch lifecycle, allowed mutations, commit ownership, cleanup, idempotency, atomic failure behavior, and the human-owned run/push decisions.
- [ ] AC-B03: A valid capability/requirement mapping directly covers the new behavior before RED; no unrelated surviving REQ is reused as a label of convenience.
- [ ] AC-B04: Tests witness the complete success path, exits 64-66, repeat execution, and failure without a partial FR-1010 completion record or leaked worktree.
- [ ] AC-B05: The automation cannot run successfully until the FR-1013 merge SHA is reachable from `origin/main`, that commit changes the expected FR-1013 path, and FR-1010 AC-12/AC-13 pass against that merged state.
- [ ] AC-B06: A successful run changes only the authorized FR-1010 closure fields, creates a reviewable commit, prints the commit identity, and never pushes without the operator.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | `SPLIT` grants no implementation authority. Concern A and Concern B must each return to independent judgement as committed FR text. | GATE |
| C-2 | Concern A cannot begin until FR-1012 is merged, its immutable SHA is recorded as `BASE`, and the Inventory at BASE is committed. | GATE |
| C-3 | A post-FR-1012 live artifact absent from the frozen inventory stops Concern A and returns it to judgement under FR-1010 C-10. | GATE |
| C-4 | Human review is mandatory before merging any Scripture or judge-doctrine change; mirror equality does not replace adversarial review. | GATE |
| C-5 | Concern B cannot be implemented in the FR-1013 branch or merged before Concern A; the merge SHA and merged-state checks it consumes do not exist earlier. | GATE |
| C-6 | Concern B receives no RED or implementation authority until its relation to the existing finalization capability and its direct REQ traceability are resolved in its own judgement. | GATE |
| C-7 | Historical content and ramp provenance remain immutable except for the two archive paths and byte-identical judge-doctrine mirror explicitly authorized by Concern A. | GATE |
| C-8 | A human retains the decisions to run the closure operation, accept its generated commit, and push it. | GATE |

Authority granted: none; amend FR-1013 to contain only Concern A and file Concern B separately, then submit each committed proposal to independent judgement.

---

# Round 3 (2026-09-06, after PR #627 review P1..P7) — APPROVED WITH REVISIONS

**Verdict:** APPROVED WITH REVISIONS — the round-3 doctrine sweep is a sound, single-purpose documentation retirement, but authority activates only after the occupied requirement ID, generated registry surface, residual-test contract, and frozen edit-set contradictions are corrected in the FR and human-reviewed.

**Reviewed against:** `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md` (rounds 1 and 2); `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; cited research and prior-art records `feature-requests/FR-1010-chaplain-archival-plan.md`, `feature-requests/FR-193-mass-graduation-scripture-patterns.md`, `feature-requests/FR-207-standalone-scripture-methodology-repo.md`, `feature-requests/FR-1011-relocate-chaplain-live-parts.md`, `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`, and `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md`; cited evidence `docs/census/fr1013-inventory-at-base-36591389.txt`, `docs/census/fr1013-inventory-at-base-36591389.dispositions.md`, `docs/archive/chaplain.md`, `tests/unit/test_fr1013_doctrine_sweep.py`, `capabilities/CAP-264-chaplain-runtime-retired.yaml`, `capabilities/CAP-265-static-module-map.yaml`, `ARCHITECTURE.md`, `ramp/manifest.yaml`, `.pre-commit-config.yaml`, `docs/development-process.md`, `scripts/aggregate_capabilities.py`, and `scripts/req_coverage.py`.

## What is sound

**Scope.** The first-consumer failure is concrete: live doctrine still leads a new session through retired Chaplain instructions to a removed entrypoint (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:11-15`). The selected remedy is smaller than preserving a dead route behind banners: update only active doctrine/reference surfaces, retain historical records, and move the one long-form design note into the existing archive (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:43-57,59-92,260-272`).

**Consistency.** The round-2 split has been obeyed. Closure automation is explicitly excluded, while the unavoidable merged-state FR-1010 record remains operator-owned and post-merge (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:225-241,270-272`). The round-3 additions to the documentation edit set answer the cited review findings without reintroducing scripts, hooks, CI, graphs, or prompts (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:109-138,260-272`). The remaining inconsistencies are finite and mechanically repairable under R-1 through R-4.

**Measurability.** The immutable `BASE`, exact inventory command, raw 2,586-match/261-file record, per-file disposition record, Scripture step comparison, rename threshold, mirror equality, targeted tests, and full non-slow suite give the enforcer direct witnesses (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:94-140,243-258`). The inventory artifact's two header lines account for its 2,588 physical lines; its 2,586 match rows and the disposition artifact's 261 rows agree with the FR.

**Feasibility.** The archive target exists and already records the runtime identities and replacements (`docs/archive/chaplain.md:1-35`). The judge doctrine asset is a declared `mirror_exact` entry (`ramp/manifest.yaml:56-60`). The capability registry is the source of truth and `ARCHITECTURE.md` is generated from it (`docs/development-process.md:190-208`; `scripts/aggregate_capabilities.py:1-10`), so the required traceability repair is feasible once its generated surface is admitted explicitly.

**Architecture alignment.** The plan follows existing patterns rather than adding a new runtime abstraction: YAML capability registration, generated architecture documentation, requirement-marked tests, byte-identical ramp mirroring, and mandatory human review for Scripture/enforcement doctrine (`.github/copilot-instructions.md:169-177,180-213`; `.pre-commit-config.yaml:70-85`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:153-224,255-258`).

**Single responsibility.** This is one concern: make active documentation agree with the already completed Chaplain retirement. The requirement record and generated architecture row are traceability for that concern, not an independent user-facing capability. The unrelated closure script remains outside this FR (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:225-241,268-272`).

**Strategic classification:** **Pattern documentation.** Existing author, judge, worktree, review, archive, capability-registry, and mirror abstractions suffice. FR-1013 documents the surviving route and removes stale active guidance; it adds neither a framework primitive nor a contrib example (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:43-57,142-151`).

**Testability.** Direct failing tests can be derived for every authorized outcome: exact residual match sets, Scripture and Knowledge Graph preservation, route wording, archive move, audit-index cardinality, ramp equality, generated requirement documentation, and test-to-REQ mapping (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:175-224,243-258`). R-3 is required because the cited candidate test currently checks only that no new *file* appears and that three route strings vanish from edit-set files; it does not yet implement the FR's promised BASE-to-HEAD line-multiset comparison (`tests/unit/test_fr1013_doctrine_sweep.py:97-121`).

The research gate is satisfied. FR-1010 compares six real solution classes, preserves the disagreement between tag-only and browsable source archives, cites precedents, and answers `is_this_a_graph`; FR-1013 then dispositions the Scripture, ramp, relocation, and removal precedents for this phase (`feature-requests/FR-1010-chaplain-archival-plan.md:449-468`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:17-42`).

## Required revisions

### R-1: Allocate the documentation requirement as REQ-YG-668, not REQ-YG-667

Replace every proposed use of `REQ-YG-667` in FR-1013 with `REQ-YG-668`. `REQ-YG-667` is already owned by CAP-265 Static module map in both the registry and generated architecture table (`capabilities/CAP-265-static-module-map.yaml:19-27`; `ARCHITECTURE.md:583,3249`). Reusing it would make the proposal impossible to register.

Amend `capabilities/CAP-264-chaplain-runtime-retired.yaml` so its `fr` field names both FR-1012 and FR-1013, its modules include the active documentation surfaces and `tests/unit/test_fr1013_doctrine_sweep.py`, and it contains this additional requirement:

> **REQ-YG-668:** The post-FR-1012 tracked-text census remains reconciled: active doctrine, skill instructions, process/reference documentation, and examples describe the operator-driven author -> judge -> worktree enforcement -> review -> human-merge route; no new or reworded Chaplain-runtime match appears outside the frozen, dispositioned BASE set; non-historical Chaplain pointers in those documentation surfaces resolve to `docs/archive/chaplain.md` or `docs/archive/chaplain-system.md`; witnessed by `tests/unit/test_fr1013_doctrine_sweep.py`.

Retag the residual and documentation-consistency tests from REQ-YG-666 to REQ-YG-668. Keep REQ-YG-192 only on the unchanged-Knowledge-Graph assertion and REQ-YG-613 only on the exact ramp-mirror assertion. Update the Proposed Solution, Purge List exception, acceptance criteria, and Implementation Record traceability table to state that mapping. REQ-YG-666 describes runtime removal, archive identity, and census enforcement, not active-document consistency (`capabilities/CAP-264-chaplain-runtime-retired.yaml:27-50`; `ARCHITECTURE.md:3239`).

### R-2: Replace the false 13-file boundary with a complete frozen writable-surface table

Change "Edit set (13 files; every implementation edit is one of these)" to "BASE match-bearing source set" and add a separate, exhaustive writable-surface table. The current claim omits the authorized edit to `docs/archive/chaplain.md`, the move destination `docs/archive/chaplain-system.md`, the witness test, changelog fragment, FR/census records, proposed CAP-264 edit, and generated `ARCHITECTURE.md` update (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:109-140,208-224,254-258,290-308`).

The table must enumerate:

1. The thirteen BASE match-bearing rows already listed in the FR.
2. `docs/archive/chaplain.md` and `docs/archive/chaplain-system.md`.
3. `capabilities/CAP-264-chaplain-runtime-retired.yaml` and generated `ARCHITECTURE.md`.
4. `tests/unit/test_fr1013_doctrine_sweep.py`.
5. `changelog/unreleased/fr-1013-doctrine-sweep.md`.
6. FR-1013 itself and its two committed census evidence files.

State that `ARCHITECTURE.md` may change only as output of `scripts/aggregate_capabilities.py` from the authorized CAP-264 edit. This is not optional: the pre-commit hook regenerates architecture whenever a capability YAML changes, and strict requirement coverage rejects registry requirements absent from architecture (`.pre-commit-config.yaml:70-85`; `scripts/req_coverage.py:419-432`).

Revise AC-02 and the Purge List to distinguish frozen content edits from supporting evidence, tests, registry metadata, generated architecture, and changelog artifacts. No file outside the revised table may change.

### R-3: Make the residual policy match the residual test

Replace AC-08's claim that every `.chaplain` reference outside a historical/archive allowlist fails. The FR deliberately retains frozen code defaults, provenance metadata, false positives, and other out-of-scope residuals (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:105-108,129-140,310`). That policy cannot simultaneously satisfy the current AC-08 wording (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:251`).

Define the residual contract as follows:

1. For every BASE file outside the authorized match-bearing edit set, the multiset of matching line texts at HEAD must equal its BASE multiset.
2. For every authorized match-bearing edit or generated file, every HEAD match must equal an exact residual line listed for that file; an empty list means zero matches.
3. A matching file absent from BASE fails unless it is an explicitly enumerated new artifact created by this FR.
4. The known stale code defaults remain unchanged, named as `keep-out-of-scope-code`, and do not become evidence that they are historical.
5. Any new or reworded unmatched residual stops enforcement under FR-1010 C-10.

Update `tests/unit/test_fr1013_doctrine_sweep.py` to implement those line-level comparisons. The cited candidate's current set-of-paths check permits a new line to hide in any one of the 261 BASE files, exactly the review defect round 3 claims to repair (`tests/unit/test_fr1013_doctrine_sweep.py:97-113`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:175-190,333-343`).

### R-4: Fold the round-3 contract into status, acceptance criteria, and implementation record

Replace the heading "Acceptance Criteria (from judgement, verbatim; R-4)" with the revised criteria below. Record this round-3 verdict in the Judgement section, and describe the existing branch commits only as pre-authority candidates until R-1 through R-4 are folded and human-reviewed. Update the Implementation Record so it does not present REQ-YG-666 as direct coverage for documentation assertions and so it records the regenerated architecture witness.

The prior rounds remain historical and must not be rewritten. Their operative boundaries remain: no closure script in this FR, no implementation authority before the current revisions are folded, and human review before merging Scripture or judge-doctrine changes (`feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md:120-193`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md:313-344`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Amend FR-1013; preserve the BASE raw inventory and update its disposition record only as required to encode the round-3 exact residual policy |
| D-2 | Rename only the Scripture heading and remove only `chaplain pipeline` from the canonical-sources clause in `.github/copilot-instructions.md`; preserve all seven Sermon steps and the complete Knowledge Graph block |
| D-3 | Reconcile the frozen active passages in `.github/skills/graph-authoring/SKILL.md`, `.github/skills/graph-authoring/doctrine.md`, `docs/development-process.md`, `examples/README.md`, `reference/audit-index.md`, `reference/command-book.md`, `reference/graph-yaml.md`, `reference/onepager-development-process.md`, and `reference/patterns/fsm-as-conductor.md` |
| D-4 | Move `docs/context/chaplain-system.md` to `docs/archive/chaplain-system.md` and maintain its single link from `docs/archive/chaplain.md` |
| D-5 | Update `.github/skills/judge-fr/doctrine.md` and its byte-identical `ramp/assets/tier2/github/skills/judge-fr/doctrine.md` mirror |
| D-6 | Add REQ-YG-668 under `capabilities/CAP-264-chaplain-runtime-retired.yaml`; regenerate only the corresponding generated portions of `ARCHITECTURE.md` |
| D-7 | Update `tests/unit/test_fr1013_doctrine_sweep.py` to implement the exact match-level policy and direct REQ mapping |
| D-8 | Add `changelog/unreleased/fr-1013-doctrine-sweep.md` and record the mandatory human review in FR-1013 |
| D-9 | After merge only, record FR-1013's merge SHA and close FR-1010 AC-12/AC-13 in a separate FR-1010-only commit |

Not authorized: a closure script or closure-script test; runtime, production Python, shell, hook, CI, graph, prompt, ramp manifest, ramp provenance, archive-repository, tag, or worktree behavior changes; a new CAP; any requirement other than REQ-YG-668 under CAP-264; manual edits to generated `ARCHITECTURE.md` content beyond the CAP-264/REQ-YG-668 rendering; changes to old witness tests; changes to historical FR, diary, memento, ebook, research, or changelog-history content; changes to archive content beyond the two D-4 paths; changes to any Sermon step or Knowledge Graph entry; changes to `ramp/manifest.yaml` or `ramp/curation-diffs.md`; marking FR-1010 complete before FR-1013 is merged.

## Revised acceptance criteria

- [ ] AC-01: FR-1013 records `BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e`, links the FR-1012 human-review record, and records `git merge-base --is-ancestor "$BASE" HEAD` exiting 0 before authorized enforcement.
- [ ] AC-02: FR-1013 contains separate exhaustive tables for the BASE match-bearing source set and the complete writable surface D-1 through D-8; every PR path changed from `BASE` appears in that writable table.
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
- [ ] AC-13: Human review is recorded in FR-1013 before merge and confirms the restricted Scripture diff, the adversarially reviewed judge-doctrine change, byte-identical mirror, generated-only architecture diff, exact residual policy, unchanged Sermon steps, and unchanged Knowledge Graph.
- [ ] AC-14: `changelog/unreleased/fr-1013-doctrine-sweep.md` exists with `type: removal` and `scope: doctrine`.
- [ ] AC-15: The FR-1013 PR contains no closure script or closure-script test.
- [ ] AC-16: Post-merge only, the operator records FR-1013's merge SHA in FR-1010, runs and records FR-1010 AC-12/AC-13 on merged `main`, records each phase's completion, and changes FR-1010 to `Completed` in a separate FR-1010-only commit.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority activates until R-1 through R-4 and AC-01 through AC-16 are folded into the committed FR and this draft receives human review. | GATE |
| C-2 | `36591389e2fdfedf9ba5ae6362effad1c64cd06e` remains the immutable BASE; if it is not an ancestor of the enforcement head, stop. | GATE |
| C-3 | REQ-YG-667 remains owned by CAP-265. FR-1013 may add only REQ-YG-668 under CAP-264, with generated architecture synchronized before any test is accepted as traced. | GATE |
| C-4 | A matching path or line not represented by the frozen BASE inventory and round-3 residual policy stops enforcement and returns FR-1013 to judgement under FR-1010 C-10. | GATE |
| C-5 | Only D-1 through D-8 may appear in the PR; D-9 is an operator-owned post-merge action because its merge SHA cannot exist earlier. | GATE |
| C-6 | Human review is mandatory before merge for Scripture, judge doctrine, its mirror, and the CAP/ARCHITECTURE contract; mirror equality and generated output do not replace adversarial review. | GATE |
| C-7 | Historical records remain historical, and known stale code defaults remain unchanged and explicitly out of scope; neither class may be silently reclassified to make the residual test pass. | GATE |
| C-8 | The pre-round-3 branch commits are candidates only. Acceptance is determined by the amended FR and the witnesses in this judgement, not by those commits' existence or prior green results. | GATE |

Authority granted: after R-1 through R-4 are folded and human-reviewed, FR-1013 may implement only D-1 through D-8; D-9 may occur only after the resulting PR is merged.
