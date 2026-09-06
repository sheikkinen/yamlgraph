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
