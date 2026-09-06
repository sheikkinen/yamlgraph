# Judgement: FR-1010 Archive the Chaplain runtime (`.chaplain/`) — umbrella plan

**Verdict:** APPROVED WITH REVISIONS — retiring the unused FSM runtime is a sound subtraction program, but authority to file or enforce its phases activates only after the plan resolves the active post-merge finalizer, the FR-975/FR-980 ID-allocation dependency, the non-runnable subtree archive, the untracked inbox migration, and the Phase 1 guard-widening scope; after folding, this umbrella authorizes only separately judged phase FRs.

**DRAFT:** Advisory until human-reviewed.

**Prior art:** see FR-1010's own Prior Art field (FR-276, FR-317, FR-465, FR-466, FR-927, FR-180, FR-970, FR-975, FR-980, CAP-75) — this judgement reviews and dispositions those same citations; FR-1011 and FR-1014 are this plan's phase FRs, not precedent; FR-796 and FR-134 share only the noun and are not in scope.

**Reviewed against:** `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-180-plan-phase-id-reservation.md`; `feature-requests/FR-276-retire-old-pipeline-scripts.md`; `feature-requests/FR-317-retire-obsolete-watcher2-components.md`; `feature-requests/FR-465-watcher2-test-cleanup.md`; `feature-requests/FR-466-cap-retirement-support.md`; `feature-requests/FR-927-retire-fr902-lane-guard-hooks.md`; `feature-requests/FR-927-retire-fr902-lane-guard-hooks.judgement.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md`; `feature-requests/FR-975-id-ledger-reservation-protocol.md`; `feature-requests/FR-975-id-ledger-reservation-protocol.judgement.md`; `feature-requests/FR-980-id-ledger-route-enforcement.md`; `feature-requests/FR-980-id-ledger-route-enforcement.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/feature-request/SKILL.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/session-introspection/SKILL.md`; `reference/patterns/corpus-map-reduce.md`; `.chaplain/README.md`; `.chaplain/scripts/start-system.sh`; `.chaplain/graphs/philosopher/tools.py`; `.chaplain/lib/finalize_lib.sh`; `scripts/finalize_merge.sh`; `scripts/check_authoring_proof.py`; `.github/hooks/scripts/pre-command-guard.sh`; `.pre-commit-config.yaml`; `.gitignore`; `capabilities/CAP-38-post-merge-finalization.yaml`; `capabilities/CAP-45-diary-reflection-enforcement.yaml`; `capabilities/CAP-75-portable-chaplain.yaml`; `capabilities/CAP-114-automated-post-merge-finalization.yaml`; and committed repository searches for `.chaplain`, `finalize_merge.sh`, `finalize_lib.sh`, `id-registry.yaml`, `scripts/id_registry.py`, and `scripts/validate_id_registry.py`.

## What is sound

The problem is real and the end state is directionally correct. FR-1010 distinguishes the inactive dispatcher/worker runtime from four artifacts that still require preservation, identifies external coupling classes, and derives extraction-before-deletion sequencing (`feature-requests/FR-1010-chaplain-archival-plan.md:42-59,68-101,126-143`). This follows the repository's subtraction doctrine: mature systems should retire phantom capability claims rather than preserve dead machinery (`.github/copilot-instructions.md:83-85`).

The umbrella structure is appropriate. FR-1010 grants itself no implementation authority, divides relocation, runtime removal, and doctrine cleanup into separately judged phases, and requires each intermediate `main` to remain working (`feature-requests/FR-1010-chaplain-archival-plan.md:57-59,139-145,223-228`). The three implementation concerns are distinct enough to require separate FRs, but they remain one coherent retirement program, so the umbrella itself does not need a `SPLIT` verdict.

The relocation ordering and graph-authoring boundary are mostly sound. The plan moves `fr_triage`, `world_distill`, and `philosopher` before deleting `.chaplain/`, updates the hook/import/orientation consumers in the same phase, and requires lint and smoke evidence for the moved graph artifacts (`feature-requests/FR-1010-chaplain-archival-plan.md:146-186`). CAP-75 supports graph-root-relative Python tool loading and the philosopher proxy, but only at graph scope (`capabilities/CAP-75-portable-chaplain.yaml:1-29`); it does not establish standalone portability for the entire FSM runtime.

The retirement precedents are relevant and correctly favor deletion over tombstones. FR-276 removed obsolete orchestrators and rejected symlink/deprecation preservation (`feature-requests/FR-276-retire-old-pipeline-scripts.md:10-19,81-101`); FR-317 required path, documentation, requirement, capability, and test reconciliation around watcher retirement (`feature-requests/FR-317-retire-obsolete-watcher2-components.md:21-35,52-81`); FR-465/FR-466 establish that dead tests and retired CAP requirements must be reconciled together rather than left as skips (`feature-requests/FR-465-watcher2-test-cleanup.md:9-45,47-67`; `feature-requests/FR-466-cap-retirement-support.md:9-31,120-127`).

Against the eight rubric criteria:

1. **Scope:** the umbrella's target is clear, but Phase 1 presently mixes relocation with a repository-wide authoring-guard widening, and Phase 2 includes deletion of a live finalization capability (`feature-requests/FR-1010-chaplain-archival-plan.md:146-180,187-209`).
2. **Consistency:** “pure relocation; no behaviour change” conflicts with making all directory-style `graphs/` artifacts newly governed (`feature-requests/FR-1010-chaplain-archival-plan.md:146-173`), while “nothing else about how work gets done changes” conflicts with deleting `scripts/finalize_merge.sh` (`feature-requests/FR-1010-chaplain-archival-plan.md:126-137,193-197`).
3. **Measurability:** the current umbrella criteria use “accepted” and selected-path prose rather than commands or artifact assertions, and do not gate the approximate `~23` CAP / `59-file` deletion set (`feature-requests/FR-1010-chaplain-archival-plan.md:200-207,230-238`).
4. **Feasibility:** extraction and `git rm` are feasible, but a raw subtree split is not a runnable standalone repository because `start-system.sh` climbs two directories to find the project root, then expects `.chaplain/config`, `.chaplain/actions`, the parent package, and `docs/` (`.chaplain/scripts/start-system.sh:16,23-24,103,194-198`).
5. **Architecture alignment:** moving process graphs to `graphs/`, retiring CAPs through the established status mechanism, and using a corpus census align with repository patterns; deleting the legacy ID allocator without dispositioning its already-judged successors does not (`feature-requests/FR-975-id-ledger-reservation-protocol.md:5,15,131-134`; `feature-requests/FR-980-id-ledger-route-enforcement.md:5,15,251-257`).
6. **Single responsibility:** the umbrella is one coordinated retirement plan, but the dir-aware authoring-guard change is independent enforcement hardening and must not be smuggled into the relocation FR (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:92-121`).
7. **Strategic classification:** this is repository maintenance/subtraction using existing relocation, retirement, archive, and census patterns. It is not a YAMLGraph framework primitive, contrib example, or new reusable abstraction; its value comes from removing operationally false surfaces.
8. **Testability:** direct witnesses exist for path relocation, graph lint/smoke, absence, CAP/REQ reconciliation, and documentation references, but the current plan lacks direct witnesses for local-only inbox transfer, archive usability, exact delete inventory, finalizer preservation, and ID-ledger sequencing.

## Required revisions

### R-1: Replace the three-row research table with substantive research

Revise the `**Research:**` evidence into four to six genuine solution classes, with precedent lines, preserved disagreement, and an explicit `is_this_a_graph` answer. The current A/B/C table is effectively two classes — tombstone versus removal — with C only adding a repository destination to B (`feature-requests/FR-1010-chaplain-archival-plan.md:259-265`). It does not meet the prospective research gate's substance requirement (`.github/skills/judge-fr/doctrine.md:118-128`).

At minimum, disposition: in-place tombstone; tag/history-only deletion; source-only subtree archive; a separately adapted runnable standalone archive; extraction of only live artifacts while retaining dormant runtime source; and full deletion without an external repository. State `is_this_a_graph: yes` only for the 59-file semantic census, which reuses the existing corpus-census pattern; the archival plan itself is deterministic repository work, not a graph.

### R-2: Reconcile FR-975 and FR-980 before deleting ID-allocation artifacts

Add FR-970, FR-975, and FR-980 to Prior Art and disposition them explicitly. FR-970's binding split says deletion of `.chaplain/id-registry.yaml` and `scripts/id_registry.py` is not authorized under FR-970 (`feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:77-80`). FR-975 still uses the legacy registry when bootstrapping the canonical ledger (`feature-requests/FR-975-id-ledger-reservation-protocol.md:125-136`), and FR-980 assigns deletion of the legacy allocator, validator, tests, and pre-commit hook to a separate purge only after FR-975 is implemented and its ledger is bootstrapped (`feature-requests/FR-980-id-ledger-route-enforcement.md:171-186,251-257`).

Record one human decision in FR-1010 before Phase 2 is filed:

> Does Chaplain archival supersede the unimplemented FR-975/FR-980 program, or must FR-975 bootstrap and the still-relevant direct Plan/Enforce route work land before FR-1010 may consume FR-980's legacy purge?

If FR-975/FR-980 remain active, Phase 2 must depend on their required bootstrap/migration boundary and must not duplicate their purge. If they are superseded, amend both FRs and their active CAP/REQ claims first, then define the replacement for direct non-Chaplain allocation; deletion cannot silently decide that product/process question.

### R-3: Remove the unsupported standalone-runtime claim

Define `sheikkinen/yamlgraph-chaplain` as a historical source archive, not a runnable standalone runtime. Update the Ideal Result, Phase 2, archive documentation, and Alternative C accordingly. A subtree split moves `.chaplain/scripts/start-system.sh` to `scripts/start-system.sh`, but the script computes its project root with `../..`, expects `.chaplain/config` and `.chaplain/actions`, invokes installation from the parent package, and writes into parent-repository `docs/` (`.chaplain/scripts/start-system.sh:16,23-24,103,194-198`). CAP-75 guarantees graph-root-relative Python tool loading, not whole-runtime packaging (`capabilities/CAP-75-portable-chaplain.yaml:3-29`).

If a runnable standalone archive remains an objective, file it as a separate researched and judged migration FR with an explicit package/dependency manifest and a fresh-clone smoke test. It is not authorized as an incidental effect of `git subtree split`.

### R-4: Preserve the active post-merge finalizer

Add `.chaplain/lib/finalize_lib.sh` to the live-parts inventory and move it to a non-Chaplain path before Phase 2. Keep `scripts/finalize_merge.sh`, update its source path, and update its focused tests and CAP module references. The script explicitly automates changelog, FR status, and diary obligations and currently sources the Chaplain library (`scripts/finalize_merge.sh:2-25`); CAP-38 and REQ-YG-125 still define it as the post-merge finalization capability (`capabilities/CAP-38-post-merge-finalization.yaml:1-17`), and CAP-45/REQ-YG-144 still include its diary-stub contract (`capabilities/CAP-45-diary-reflection-enforcement.yaml:1-22`).

Retire only CAP-114's dead automatic watcher integration as part of the runtime retirement (`capabilities/CAP-114-automated-post-merge-finalization.yaml:1-27`). Deleting `scripts/finalize_merge.sh` merely because it is the sole consumer of `finalize_lib.sh` reverses the dependency direction and violates the plan's promise that non-Chaplain work practices remain unchanged. A future retirement of the manual finalizer requires its own evidence and judged FR.

### R-5: Split authoring-guard hardening from Phase 1 relocation

Choose FR-1011 option (b): Phase 1 removes the vacuous `.chaplain/graphs` arm and performs relocation only. File FR-1014 for the directory-style `graphs/**/graph.yaml` and `graphs/**/prompts/*.yaml` authoring-guard widening, with its own RED witnesses and human review, and merge it before FR-1011. FR-1011 labels itself “pure relocation, no behaviour change” but recommends option (a), which newly governs all directory-style graphs including `graphs/enforcement/` (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:4,92-121`). Those are different responsibilities and enforcement-infrastructure changes require an explicit human-review gate (`.github/skills/judge-fr/doctrine.md:99-100`).

### R-6: Make the untracked inbox migration an operator-owned, lossless gate

Move the eight carried sparks outside the PR implementation path. FR-1011 acknowledges that `.chaplain/inbox/` is ignored, absent from worktrees, and visible only on one machine, yet its GREEN commands attempt to move those files from the enforcement worktree (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:81-86,176`). Define a pre-merge operator runbook on the main checkout that:

1. freezes the 13-item source inventory with filenames and SHA-256 hashes;
2. copies the eight carried items to `proposals/`;
3. confirms the three drops, one forward, and empty-directory removal against the frozen table;
4. verifies source and destination hashes before deleting the old local copies; and
5. records completion and the manifest in FR-1011 without committing proposal contents.

Phase 2 must not remove `.chaplain/` until this gate is human-confirmed. The separate durability/visibility design may remain a future proposal, but the physical migration cannot be represented as a PR-delivered `mv`.

### R-7: Freeze exact Phase 2 deletion inputs and the corpus-census contract

Replace `~23` CAPs and the category-level `59-file` estimate with a committed, exact Phase 2 inventory before FR-1012 receives authority. The census must record every test path, referenced REQs, shared REQ fan-in, keep/delete reason, and every CAP ID/status transition. It must satisfy all eight corpus-map-reduce invariants, including deterministic identity/coverage reconciliation and a withheld semantic canary (`reference/patterns/corpus-map-reduce.md:198-223`), and must preserve raw primary results for human reading before reduction is trusted (`reference/patterns/corpus-map-reduce.md:380-396`).

FR-1012 may delete only rows marked `delete` in that reviewed artifact. Any newly discovered live artifact amends FR-1010 before deletion, as the sequencing clause already requires (`feature-requests/FR-1010-chaplain-archival-plan.md:223-228`).

### R-8: Replace the umbrella acceptance criteria with mechanical phase gates

Fold the revised acceptance criteria below into FR-1010. The current criteria ask that an inventory and approach be “accepted,” require three files to exist, and then wait for a status word (`feature-requests/FR-1010-chaplain-archival-plan.md:230-238`); they do not prove the archive, relocation, deletions, phase order, or preservation of live behavior.

### R-9: Add explicit human gates for destructive and enforcement changes

Require human review before: FR-1014 changes the authoring guard; FR-1012 creates and archives a GitHub repository, pushes the archival tag, deletes the runtime and tests, or removes a pre-commit hook; and FR-1013 changes Scripture or judge-doctrine mirrors. Record the reviewed commit/PR in each phase FR. The phase judgements remain advisory until those reviews occur.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1010-chaplain-archival-plan.md`: fold R-1 through R-9, record the human ID-allocation decision, freeze the revised phase sequence, and later record completion. |
| D-2 | FR-1010's committed research section or a linked committed research artifact containing four to six genuine solution classes and the graph/no-graph answer. |
| D-3 | FR-1014: independently judged directory-style authoring-guard hardening, merged before relocation. |
| D-4 | FR-1011: relocation only, including extraction of `finalize_lib.sh`, consumer/test/CAP path updates, graph lint/smoke, and the operator-owned inbox migration record. |
| D-5 | FR-1012: exact census, source-only archive repository and tag, runtime/test/CAP deletion, archive note, and only the ID-allocation purge permitted by R-2's recorded decision. |
| D-6 | FR-1013: doctrine/documentation sweep after runtime deletion, with independently judged scope and human review. |

Not authorized under FR-1010: implementing any phase directly from this umbrella; deleting `scripts/finalize_merge.sh`; claiming the subtree archive is runnable standalone; deleting or superseding FR-975/FR-980 artifacts without the R-2 human decision and dependency record; widening authoring guards inside the relocation FR; losing, silently dropping, or committing the local proposal contents; adding a symlink or old-path shim; changing the proposal durability model; changing unrelated hooks, CI, branch protection, YAMLGraph runtime behavior, judge/review behavior, or the FR-701 duplicate-registry backstop.

## Revised acceptance criteria

- [ ] AC-01: FR-1010's `**Research:**` points to committed evidence containing four to six genuine solution classes, precedent lines, preserved disagreement, and an explicit `is_this_a_graph` answer; the selected approach is a source-only archive unless a separate standalone-runtime FR is filed.
- [ ] AC-02: The live-parts inventory names every extracted path, including `.chaplain/lib/finalize_lib.sh`, its `scripts/finalize_merge.sh` consumer, and CAP-38/CAP-45/CAP-114 disposition.
- [ ] AC-03: FR-1010 records the human R-2 decision and links amendments to FR-975/FR-980 or an explicit dependency on their implementation/bootstrap; Phase 2 contains no duplicate or prematurely ordered ID-registry purge.
- [ ] AC-04: FR-1014, FR-1011, FR-1012, and FR-1013 each contain `**Plan:** FR-1010`, limit scope to one phase concern, have a human-reviewed judgement, and are merged in that order.
- [ ] AC-05: FR-1014 has direct RED witnesses for directory-style `graphs/**/graph.yaml` and `graphs/**/prompts/*.yaml` governance, retains flat-graph behavior, and receives human review before merge.
- [ ] AC-06: FR-1011 preserves `scripts/finalize_merge.sh` by relocating its library and updating tests/CAP paths; the focused finalization tests pass after `.chaplain/lib/finalize_lib.sh` is absent.
- [ ] AC-07: FR-1011 records the operator-confirmed 13-item inbox manifest, verifies hashes for all eight carried items, records the three drops and one forward, and confirms `.chaplain/inbox/` is empty before Phase 2 starts.
- [ ] AC-08: Lint and real smoke records exist for `graphs/fr_triage/graph.yaml`, `graphs/world_distill/graph.yaml`, and `graphs/philosopher/graph.yaml` after relocation, and their direct tests plus the triage hook import pass from the new paths.
- [ ] AC-09: FR-1012 commits an exact test/CAP/REQ disposition artifact satisfying all eight corpus-map-reduce invariants; raw primary outputs are reviewed; every deleted test/CAP is named; shared REQ fan-in is reconciled; and `req_coverage --strict` remains green.
- [ ] AC-10: A fresh clone of `sheikkinen/yamlgraph-chaplain` at its archived default branch contains the complete source snapshot and archive README, and that README states the repository is historical source, not a standalone runnable distribution.
- [ ] AC-11: The `chaplain-archive` tag resolves to the documented pre-removal commit on the YAMLGraph remote, and `docs/archive/chaplain.md` records the exact tag, repository URL, archive status, and replacement table.
- [ ] AC-12: After FR-1013, a defined repository-wide search finds no live `.chaplain` runtime/path instruction outside historical FRs, changelog/history, and `docs/archive/chaplain.md`; every allowed residual match is enumerated.
- [ ] AC-13: FR-1010 moves to `Completed` only after all four phase FRs merge in order, the remote tag and archived repository are verified, the local inbox migration is confirmed, and each phase's implementation status is recorded.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No planning or implementation authority activates until R-1 through R-9 are folded into committed FR-1010 and this draft receives human review. | GATE |
| C-2 | FR-1010 grants authority only to file and judge the phase FRs; every code, graph, hook, deletion, remote-repository, tag, and doctrine change requires its phase's independent judgement. | GATE |
| C-3 | FR-1014 must merge before FR-1011; FR-1011 before FR-1012; FR-1012 before FR-1013. A phase may not borrow scope from a later phase. | GATE |
| C-4 | Human review is mandatory for authoring-guard changes, hook deletion, GitHub repository creation/archive, tag push, mass deletion, and Scripture/judge-doctrine edits. | GATE |
| C-5 | Phase 2 must not begin until the operator-confirmed inbox manifest proves all local-only proposals were carried, dropped, forwarded, or removed exactly as dispositioned. | GATE |
| C-6 | `scripts/finalize_merge.sh` and its surviving CAP-38/REQ-YG-125 and CAP-45/REQ-YG-144 behavior must remain operational; only CAP-114's dead watcher automation may retire in this program. | GATE |
| C-7 | No ID-registry/allocator/validator deletion may precede or contradict the recorded FR-975/FR-980 disposition and required bootstrap/migration boundary. FR-701's duplicate-registry validation remains untouched. | GATE |
| C-8 | The archive is source-preserving only. No runnable-standalone claim may be made without a separate judged FR and fresh-clone execution witness. | GATE |
| C-9 | Any material graph or prompt relocation remains subject to the graph-authoring route, lint, smoke, and proof-artifact contract; this judgement itself authorizes no graph write. | GATE |
| C-10 | A newly discovered live artifact stops the active phase and amends FR-1010's frozen inventory before work resumes. | GATE |

Authority granted: after R-1 through R-9 are folded and human-reviewed, FR-1010 may govern the ordered filing and independent judgement of FR-1014, FR-1011, FR-1012, and FR-1013; it grants no direct implementation or deletion authority.
