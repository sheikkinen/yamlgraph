# Judgement: FR-1012 Subtree-split `.chaplain/` to a source-only archive and remove the runtime

**Verdict:** APPROVED WITH REVISIONS — the archive-and-removal phase is a coherent, evidence-backed subtraction, but authority activates only after the FR uses the shipped census skeleton, closes its corpus/schema and archive-provenance gaps, resolves the RED-versus-green-commit contradiction, freezes traceability, records prerequisite merges, and receives the required human decisions and review.

**DRAFT:** Advisory until human-reviewed.

**Prior art:** see FR-1012's own Prior Art field (FR-276, FR-317, FR-465, FR-466, FR-701, FR-851, FR-892, FR-1015, FR-889) — this judgement reviews and dispositions those same citations; FR-1010 and its sibling phase FRs are the governing plan, not precedent.

**Reviewed against:** `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.judgement.md`; `feature-requests/FR-1014-dir-aware-authoring-guard.md`; `feature-requests/FR-1014-dir-aware-authoring-guard.judgement.md`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md`; `feature-requests/FR-276-retire-old-pipeline-scripts.md`; `feature-requests/FR-317-retire-obsolete-watcher2-components.md`; `feature-requests/FR-465-watcher2-test-cleanup.md`; `feature-requests/FR-466-cap-retirement-support.md`; `feature-requests/FR-701-capability-registry-consistency-gate.md`; `feature-requests/FR-851-requirement-witness-audit.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `reference/patterns/corpus-map-reduce.md`; `examples/demos/corpus_census/README.md`; `scripts/req_coverage.py`; `capabilities/CAP-165-watcher2-baseline-dead-code-removal.yaml`; `tests/unit/test_fr305_watcher_pipeline_v2.py`; `tests/unit/test_fr_triage.py`; `.chaplain/README.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem and end state are real. The FR names the dormant runtime, its test/CAP coupling, the shared-REQ fan-in hazard, and the exact operational truth expected after removal (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:44-82,86-96`). Deletion is constrained by a reviewed disposition artifact rather than filename intuition, preserving the parent plan's census-first rule (`feature-requests/FR-1010-chaplain-archival-plan.md:298-334,384-394`).

The archive is correctly scoped as historical source rather than a runnable distribution, and the phase preserves the relocated finalizer while leaving FR-701's registry gate untouched (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:24-42,138-180,223-228`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md:125-134`). The human gates around repository creation, tag push, hook removal, and mass deletion are the right safety boundary.

The retirement precedents are correctly applied. FR-317 requires path, documentation, capability, requirement, and test reconciliation around removal; FR-465 and FR-466 establish that dead witnesses and CAP retirement move together; FR-701 makes an inconsistent intermediate state fail (`feature-requests/FR-317-retire-obsolete-watcher2-components.md:29-38,52-87`; `feature-requests/FR-465-watcher2-test-cleanup.md:37-54`; `feature-requests/FR-466-cap-retirement-support.md:106-127`; `feature-requests/FR-701-capability-registry-consistency-gate.md:19-36`).

Against the eight rubric criteria:

1. **Scope:** archive, removal, directly coupled traceability, and one durable archive note form one Phase 2 concern. The proposed second census graph is not necessary scope because FR-892 already shipped the reusable graph (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:100-136`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:29-39,80-95`).
2. **Consistency:** the selected source-only archive and purge list agree, but the FR simultaneously requires a committed failing RED and a green suite at every commit, and it says an archive `README.md` is added although `.chaplain/README.md` is already in the split (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:51-52,65,146-165,201-210`; `.chaplain/README.md:1-18`).
3. **Measurability:** most final-state checks are executable, but hard-coded corpus/count assumptions, prose-only human decisions, and count-only archive verification do not prove exact identity or content (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:65-75,189-221`).
4. **Feasibility:** subtree split, tag push, retirement, and deletion are workable. The existing shared census accepts invocation-bound discovery/extraction adapters and caller-selected model/rubric, so a new graph is unnecessary (`reference/patterns/corpus-map-reduce.md:56-60`; `examples/demos/corpus_census/README.md:3-17,73-83`).
5. **Architecture alignment:** deterministic collection/reconciliation plus typed semantic map decisions fits the corpus pattern, but copying the skeleton conflicts with the explicit “new corpus supplies adapters, not a new graph” contract and omits its hard-ceiling/privacy preflight (`reference/patterns/corpus-map-reduce.md:56-60,196-243,357-385`).
6. **Single responsibility:** the archive and deletion are causally coupled: the archive is the preservation boundary that permits removal, and the census determines the directly coupled test/CAP changes. No split is required after the duplicate graph surface is removed.
7. **Strategic classification:** repository maintenance/subtraction using existing primitives. It is not a new framework primitive or a new contrib graph; the only reusable behavior needed already exists in `corpus_census`.
8. **Testability:** direct witnesses can prove manifest completeness, census/reality equality, archive provenance, removal, CAP retirement, and surviving gates. The current “CAP-165 if it fits, otherwise allocate later” branch and multi-commit GREEN sequence prevent deriving one frozen RED/GREEN contract (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:153-180`; `capabilities/CAP-165-watcher2-baseline-dead-code-removal.yaml:1-17`).

## Required revisions

### R-1: Add a substantive raw-record read before authority

Add a `## Raw Input Read` section with at least five cited current samples spanning: a certain-delete runtime test, a certain-keep relocated test, a shared-REQ test, a wholly runtime-owned CAP, and a mixed/live CAP. For each sample record path/CAP, REQs, deterministic fan-in, cited source lines, proposed disposition, and one concrete surprising detail. The two canary names alone do not demonstrate that the semantic boundary was read (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:113-125`). This is an LLM census whose output authorizes deletion, so the local raw-read gate applies before authority (`.github/copilot-instructions.md:107,208`; `.github/skills/judge-fr/doctrine.md:110-117`).

### R-2: Reuse the shipped `corpus_census` graph

Add FR-892 to Prior Art and replace `examples/demos/chaplain_disposition_census/` with a Chaplain discovery manifest, extraction manifest, rubric/config, and deterministic post-reconciliation code bound to `examples/demos/corpus_census/graph.yaml`. Place the consumer-specific adapters with the existing `examples/demos/corpus_census/adapters/` family and the durable run artifacts under `docs/census/`; do not author a second graph or prompt tree (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:29-39,80-109`; `reference/patterns/corpus-map-reduce.md:56-60,381-385`).

Freeze preflight ceilings for source items, total bytes, per-item input, model calls, and wall-clock time; record the approved provider/data-classification decision before fan-out (`reference/patterns/corpus-map-reduce.md:228-243,357-373`). If the shared graph cannot carry one required invariant, stop and file that generic gap separately rather than copying the graph.

### R-3: Freeze a complete corpus and unambiguous disposition schemas

Replace the constructor's regex plus unnamed “27 CAP files” with one deterministic discovery rule and committed manifest produced after the prerequisites merge. The current test regex omits terms present in the FR's own CAP/search universe, including plain `watcher`, `inbox`, `triage`, and `distill` (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:65-75,102-111`). The manifest must contain every candidate path, item kind, byte count, SHA-256, REQs, per-REQ outside-corpus fan-in, and frozen source SHA.

Define separate typed rows:

- test row: `path, kind=test, verdict=keep|delete, reason, reqs[], fan_in_by_req{}, cites[], manual_review`;
- CAP row: `path, cap_id, kind=cap, current_status, verdict=keep|retire, reason, reqs[], modules[], surviving_witnesses_by_req{}, cites[], manual_review`.

A CAP may be retired only when every requirement and module is runtime-owned or otherwise explicitly dispositioned and no surviving live behavior depends on it. Mixed CAPs must be `keep` plus `manual_review`, and enforcement stops until the FR records a human resolution; “or deleted tests” is not a sufficient retirement rule (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:113-129,191-198`). Reconciliation must reject missing, duplicate, unknown, wrong-kind, malformed-citation, and unresolved-manual-review rows.

### R-4: Record prerequisite completion instead of asserting it

Add an implementation-gate table containing the merge SHA and human-review reference for FR-1014, FR-1011, and FR-1015, plus FR-1011's inbox-manifest location and empty-inbox confirmation. Do not begin the census or any Phase 2 operation while a field is blank. The cited state currently shows FR-1011's implementation record pending and FR-1015 still Proposed, despite FR-1012's header saying all prerequisites are merged (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:8-9`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md:395-401`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md:1-15`). This revision enforces FR-1010 C-3/C-5 rather than weakening them.

### R-5: Freeze traceability and make RED/GREEN history coherent

Do not attach the Phase 2 witness to CAP-165: REQ-YG-466 is specifically about FR-277 watcher2 baseline checkpointing, not removal of the complete Chaplain runtime (`capabilities/CAP-165-watcher2-baseline-dead-code-removal.yaml:1-17`). Allocate and record the exact new CAP and REQ IDs under FR-1015's replacement allocation contract before the RED commit; freeze the CAP path, REQ text, and test marker in this FR.

Replace “every commit is green” with this history contract:

1. the census/evidence commit passes all gates;
2. a dedicated RED commit, carrying `SKIP=pytest`, adds the focused removal witness and records its assertion failure;
3. one atomic GREEN commit performs the coupled local removal, CAP retirement, test deletion, archive-note, registry generation, and changelog changes needed to make that witness and strict gates pass; and
4. every later commit and final HEAD passes the full required checks.

Do not use `git rebase -x` to demand green tests at the designated RED commit. The current wording is internally impossible and conflicts with the repository's separate RED/GREEN history rule (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:51-52,153-180,201-204`; `.github/copilot-instructions.md:196`).

### R-6: Make the archive snapshot exact and provenance-complete

Treat the split's existing root `README.md` as a modification, not a newly added file: prepend the historical-source banner and links on the archive branch, and call it the only post-split content change. Replace `161 + 1` with the frozen manifest count; assert exact path-set equality between the pre-removal `.chaplain/` manifest and the fresh archive clone, and exact SHA-256 equality for every file except the documented README transformation (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:61-65,138-151,207-210`; `.chaplain/README.md:1-18`).

Record three immutable identities in the run record and `docs/archive/chaplain.md`: the pre-removal YAMLGraph commit/tag target, the subtree-split commit, and the final archived-repository HEAD after the README commit. Add fail-closed preflights: the local/remote `chaplain-archive` tag must be absent, and `sheikkinen/yamlgraph-chaplain` must be absent; any existing name stops enforcement for human reconciliation. Verify the archived default branch and exact visibility as well as `isArchived`.

### R-7: Record the operator's archive-visibility decision

Add this explicit decision field before any remote operation:

> Archive visibility: `private` or `public`? Operator, date, rationale, reviewed commit/PR.

An unanswered field authorizes no repository creation; it does not silently select private. After the decision, the command and AC must use the selected visibility and verify it mechanically. Product/privacy decisions belong to the human (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:138-151,216-218,237`; `.github/skills/judge-fr/doctrine.md:97-102`).

### R-8: Replace weak or exit-status-ambiguous checks

Fold the revised acceptance criteria below verbatim. In particular, replace count-only archive verification with manifest equality; replace `grep -c ... -> 0` pipelines with explicit no-match assertions that are correct under `pipefail`; add `git diff --exit-code -- ARCHITECTURE.md` after aggregation; verify every census invariant and unresolved-review count; and separate the expected RED commit from commits required to be green.

### R-9: Include implementation record and Distill

Add an `## Implementation Record` that records census run identity, provider/model, input/tree SHA, raw-read reviewer, canary results, RED/GREEN SHAs, archive/tag identities, human-review reference, validation commands, and deviations. Add the required final `docs/diary/` reflection with a `**Seed:**` and include it in the changelog/traceability GREEN (`.github/copilot-instructions.md:26-27,212`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`: fold R-1 through R-9, exact prerequisite/human decisions, frozen IDs, revised criteria, and implementation record. |
| D-2 | Chaplain-specific discovery/extraction manifests and deterministic adapter/reconciliation code under `examples/demos/corpus_census/adapters/`; reuse `examples/demos/corpus_census/graph.yaml` unchanged. |
| D-3 | `docs/census/chaplain-test-disposition.jsonl`, its human summary, run/provenance record, and preserved raw primary outputs; all tied to the frozen source SHA. |
| D-4 | `tests/unit/test_fr1012_chaplain_removed.py` and the exact new CAP/REQ allocated before RED. |
| D-5 | Census-authorized test deletions and CAP retirements, committed atomically with all other local GREEN changes required by the focused witness. |
| D-6 | Removal of `.chaplain/`, `.github/skills/chaplain-ops/`, `scripts/chaplain-prompts/`, the FR-1015-authorized legacy ID-registry files/hook/tests, and the matching `.gitignore` entries. |
| D-7 | `chaplain-archive` tag, source-only `sheikkinen/yamlgraph-chaplain` repository, transformed archive README, immutable provenance record, and archived/visibility verification. |
| D-8 | `docs/archive/chaplain.md`, generated `ARCHITECTURE.md`, and the complete replacement table required by FR-1010. |
| D-9 | `changelog/unreleased/fr-1012-chaplain-runtime-removed.md` and one `docs/diary/` Distill entry containing a `**Seed:**`. |
| D-10 | Post-merge `scripts/worktree.sh sync` and `scripts/vscode/now.py` witness recorded in the FR implementation record. |

Not authorized under FR-1012: a new or copied census graph/prompt tree; modifications to `examples/demos/corpus_census/graph.yaml`, YAMLGraph runtime, FR-701 validation, surviving CAP-38/CAP-45 or `scripts/finalize_merge.sh`; retirement of a mixed/live CAP without recorded human resolution; deletion outside reviewed census `delete` rows and the explicitly enumerated non-census surfaces; doctrine/Scripture sweep assigned to FR-1013; a runnable-standalone archive claim; symlinks, stubs, deprecated-path shims, public disclosure without the operator's recorded choice, or overwrite/reuse of an existing tag or GitHub repository.

## Revised acceptance criteria

- [ ] AC-01: FR-1014, FR-1011, and FR-1015 merge SHAs and human-review references are recorded; FR-1011's 13-item inbox manifest is linked and `.chaplain/inbox/` is confirmed empty; no Phase 2 command ran before all fields were complete.
- [ ] AC-02: `## Raw Input Read` contains at least five source-cited samples covering certain-delete, certain-keep, shared-REQ, runtime-only CAP, and mixed/live CAP boundaries, each with computed fan-in and a concrete surprising detail.
- [ ] AC-03: The Chaplain census binds only consumer-specific manifests/adapters/rubric to unchanged `examples/demos/corpus_census/graph.yaml`; no `examples/demos/chaplain_disposition_census/` or second graph/prompt tree exists.
- [ ] AC-04: The frozen input manifest records source SHA, path, kind, bytes, SHA-256, REQs, and fan-in for every discovered item; hard item/byte/per-item/call/timeout ceilings and the provider/data-classification decision are recorded before the first model call.
- [ ] AC-05: The run record proves all eight corpus-map-reduce invariants, both withheld canary families, zero missing/duplicate/unknown/wrong-kind rows, valid citations, and zero unresolved `manual_review` rows; raw primary outputs were read by the recorded human before reduction was trusted.
- [ ] AC-06: `docs/census/chaplain-test-disposition.jsonl` and its summary are committed before RED or deletion; the deleted test set equals test `delete` rows, and transitioned CAPs equal CAP `retire` rows.
- [ ] AC-07: The exact new CAP/REQ and `tests/unit/test_fr1012_chaplain_removed.py` are frozen in the FR; the recorded RED commit fails the focused assertions with `SKIP=pytest`, and the immediately following atomic GREEN commit makes the focused test, `python scripts/req_coverage.py --strict`, `python scripts/validate_capabilities.py --strict`, `pytest tests/unit -q -m "not slow" -n auto`, and `lint-imports` pass.
- [ ] AC-08: Every commit except the designated RED passes the checks applicable to its state; final HEAD passes all AC-07 checks. The RED/GREEN SHAs and outputs are recorded.
- [ ] AC-09: `git ls-files .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py` prints nothing, the `validate-id-registry` hook is absent, and no census-authorized deletion exceeds the reviewed `delete` set.
- [ ] AC-10: The operator records `private` or `public`, date, rationale, and reviewed commit/PR before remote operations; preflights prove the tag and repository names unused; the creation command uses the decision and final `gh repo view` output proves visibility, archived status, and default branch.
- [ ] AC-11: `git ls-remote --tags origin refs/tags/chaplain-archive` resolves exactly to the recorded pre-removal commit; `docs/archive/chaplain.md` records that commit, the subtree-split commit, and final archive HEAD.
- [ ] AC-12: A fresh archive clone has exactly the frozen `.chaplain/` path set and file count; every source hash matches except `README.md`, whose sole documented transformation prepends the historical-source banner and links. Its first line contains “not a runnable distribution.”
- [ ] AC-13: `docs/archive/chaplain.md` contains the tag, URL, verified visibility/archive status, immutable SHAs, and a replacement-table row for every FR-1010 live-parts category.
- [ ] AC-14: `python scripts/aggregate_capabilities.py && git diff --exit-code -- ARCHITECTURE.md` succeeds; an explicit no-match assertion proves `python scripts/vscode/now.py` emits no `.chaplain`; CAP-38, CAP-45, and `scripts/finalize_merge.sh` remain live and unchanged in behavior.
- [ ] AC-15: Human review of the exact census, manual resolutions, remote visibility, tag/repository operations, hook removal, mass-deletion diff, RED/GREEN record, and final validation is recorded before tag push, repository creation/archive, or merge.
- [ ] AC-16: Discovery of any new live artifact, existing remote/tag collision, unresolved census row, prerequisite drift, or FR-1010 live-parts change stops enforcement and returns FR-1010/FR-1012 to judgement.
- [ ] AC-17: `changelog/unreleased/fr-1012-chaplain-runtime-removed.md` and a `docs/diary/` Distill entry with `**Seed:**` are committed; the FR implementation record contains all run, archive, review, validation, and deviation evidence.
- [ ] AC-18: After merge, `scripts/worktree.sh sync` succeeds on main and an explicit no-match assertion proves `python scripts/vscode/now.py` emits no `.chaplain`; both outcomes are recorded.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-9 and the revised acceptance criteria are folded into committed FR-1012, and this draft is human-reviewed, before implementation authority activates. | GATE |
| C-2 | FR-1014, FR-1011, and FR-1015 are implemented, human-reviewed, merged in order, and recorded by immutable SHA; FR-1011's inbox migration is complete and empty. | GATE |
| C-3 | The shipped `corpus_census` graph is reused unchanged; only consumer manifests/adapters/rubric and deterministic reconciliation may be added. Any generic graph/runtime gap stops this FR. | GATE |
| C-4 | No deletion or CAP retirement occurs until the exact census is committed, all invariants and canaries pass, raw rows are human-read, and every manual-review row is resolved in the FR. | GATE |
| C-5 | The exact new CAP/REQ is allocated before RED; CAP-165/REQ-YG-466 is not reused for whole-runtime removal. | GATE |
| C-6 | The dedicated failing RED precedes one atomic local GREEN; only the RED is exempt from green-test history, and final HEAD must pass every strict/focused/full check. | GATE |
| C-7 | The operator explicitly chooses archive visibility and human-reviews the final operation plan before tag push, repository creation/archive, hook removal, mass deletion, or merge. | GATE |
| C-8 | Tag and repository name collisions fail closed. Archive provenance must link the pre-removal commit, subtree-split commit, and final archived HEAD, with manifest-level fresh-clone verification. | GATE |
| C-9 | FR-701 validation, CAP-38/CAP-45, `scripts/finalize_merge.sh`, the shared census graph, and FR-1013 doctrine scope remain untouched. | GATE |
| C-10 | Any new live artifact, mixed CAP, unresolved census row, prerequisite drift, or archive mismatch stops enforcement and returns the frozen plan to judgement. | GATE |

Authority granted: after R-1 through R-9 are folded, prerequisite evidence and the operator's visibility decision are recorded, and this judgement is human-reviewed, implement only the frozen shared-census consumer, source-only archive/tag, census-authorized retirement/removal, archive documentation, traceability, changelog, Distill, and post-merge witnesses.


---

# Round 2 (2026-09-06, after review P5 scope widening)

# Judgement: FR-1012 Subtree-split `.chaplain/` to a source-only archive and remove the runtime

**Verdict:** APPROVED WITH REVISIONS — the archive-and-removal phase remains a coherent, evidence-backed subtraction, but authority activates only after the widened scripted scope is reconciled with the shipped census schema, archive provenance and retry behavior are made exact, and the human-review chronology is made possible.

**DRAFT:** Advisory until human-reviewed.

**Reviewed against:** `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1015-supersede-id-ledger-under-fr-1010.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `reference/patterns/corpus-map-reduce.md`; `examples/demos/corpus_census/README.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/prompts/judge_item.yaml`; `examples/demos/corpus_census/tools.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The requested subtraction has a real consumer and a bounded end state. The FR ties removal to a reviewed census, preserves a source-only archive rather than making a false runnable-distribution claim, protects the relocated live surfaces, and leaves FR-701 unchanged (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:13-20,53-96,237-276`). Its five raw samples expose the actual semantic boundaries: filename arithmetic cannot distinguish a dead runtime witness from a relocated live behavior, REQ fan-in is per requirement, marker extraction must use the existing AST boundary, and a CAP can mix live and dead modules (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:100-129`).

The prior revisions were materially folded. The FR now reuses `examples/demos/corpus_census/graph.yaml`, records prerequisites instead of assuming them, allocates a new removal CAP/REQ, separates RED from GREEN, preserves three archive identities, asks the operator for visibility, and adds implementation and Distill records (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:131-197,237-286,289-350`). The P5 move from pasted destructive commands to checked-in scripts is also directionally sound: remote mutation, mass deletion, and post-merge reconciliation deserve reviewable executable witnesses.

Against the eight rubric criteria:

1. **Scope:** source preservation, runtime deletion, directly coupled test/CAP retirement, and the scripts that make those destructive operations reproducible form one Phase 2 concern. The parent plan assigns this exact archive-and-remove boundary to FR-1012 (`feature-requests/FR-1010-chaplain-archival-plan.md:304-340`).
2. **Consistency:** the desired end state is consistent, but three implementation contracts are not: custom model rows conflict with the shared graph's fixed schema; a `tmp/` run record is simultaneously required to be committed; and AC-15 requires final GREEN evidence before the remote operations needed to produce that GREEN (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:173-189,214-229,248-269,305-309`).
3. **Measurability:** most criteria name paths, commands, identities, and equality checks. The remaining weak points are the unprovable negative “no Phase 2 command ran,” the undefined rooted-path comparison, “unchanged in behavior” without named witnesses, and an unspecified persistence carrier for evidence produced after merge (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:291-309`).
4. **Feasibility:** subtree split, archive creation, tag push, deletion, CAP retirement, and post-merge sync are workable. The census as written is not: the unchanged graph invokes the fixed `judge_item` prompt and fixed reducer (`examples/demos/corpus_census/graph.yaml:87-129`), while that prompt can return only `source_index`, `judgement`, `confidence`, `evidence_span`, `abstained`, and `abstain_reason` (`examples/demos/corpus_census/prompts/judge_item.yaml:21-43`).
5. **Architecture alignment:** reuse of the FR-892 graph follows the rule that a new corpus supplies adapters rather than another graph (`reference/patterns/corpus-map-reduce.md:57-61`). Rich Chaplain rows must therefore be constructed at the deterministic post-reconciliation boundary, not claimed as a caller-defined model schema that the graph does not expose.
6. **Single responsibility:** no split is required. The archive is the preservation boundary that permits the removal; the census and scripts are evidence and execution surfaces for that same destructive transition.
7. **Strategic classification:** repository maintenance/subtraction using an existing framework primitive. This is neither a new framework primitive nor a new contrib graph; the reusable census capability already exists.
8. **Testability:** failing witnesses can be written for discovery bounds, reconciliation, archive preflights, partial-run recovery, manifest equality, removal, CAP retirement, and post-merge sync. They cannot be derived faithfully until the fixed graph schema, exact `PRE`, review stages, and durable evidence paths are frozen.

## Required revisions

### R-1: Correct the re-judgement state before claiming authority

Replace the claim that the P5 widening has already been re-judged with a pending re-judgement state until this draft is human-reviewed and folded. The FR currently says “re-judged; see the re-judgement appended,” but the cited judgement contains only the earlier R-1 through R-9 decision (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:355-370`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md:1-146`). Record the reviewed re-judgement reference and activation date before restoring `Judged`.

### R-2: Bind the Chaplain census to the shared graph's actual output contract

Replace the claim that `chaplain_rubric.md` defines two model-output schemas. The unchanged graph has one fixed `CorpusCensusFinding` schema and one fixed `LedgerRow` reducer (`examples/demos/corpus_census/prompts/judge_item.yaml:21-43`; `examples/demos/corpus_census/tools.py:53-66,303-375`).

Freeze this boundary instead:

1. the model emits only a closed verdict label valid for the item kind plus the fixed confidence, exact `evidence_span`, and abstention fields;
2. the shared reducer writes its generic ledger to a distinct raw-ledger path that is never overwritten;
3. a Chaplain-specific deterministic Pydantic reconciler joins each generic ledger row to collector-owned manifest facts and emits the frozen test/CAP disposition schemas;
4. code, not the model, copies `path`, `kind`, REQs, fan-in, modules, module presence, and current status; validates kind/verdict legality; derives `manual_review`; resolves the evidence span to source lines; and rejects abstained, demoted, row-failed, missing, duplicate, unknown, wrong-kind, or unresolved rows; and
5. `docs/census/chaplain-test-disposition.jsonl` is the reconciled authorization artifact, while the generic ledger and raw primary outputs remain separately named evidence.

If one required semantic field cannot be obtained from the fixed verdict-plus-evidence contract, stop and file the generic census gap as a separate FR; do not modify or copy the shared graph under FR-1012.

### R-3: Add one fail-closed census invocation surface

Add a checked-in `scripts/chaplain_census.py` that is the sole Phase 2 census command. It must validate the filled prerequisite gate and immutable source SHA, apply a deterministic sorted/deduplicated discovery rule, classify repository visibility/data policy, reject credential-bearing input, enforce the 120-item, 1.5-MB-total, 48-KB-item, 130-call, and 20-minute limits, invoke the unchanged graph with the exact discover/extract manifests, labels, provider/model, raw-ledger path, brief path/rubric, and then run the Chaplain reconciler.

The item/byte/call checks must occur before the first provider call, and the wrapper must enforce the wall-clock deadline around the whole graph process. Tests must prove every preflight refusal occurs before provider invocation. A prose “run config” is not an executable ceiling, while the corpus contract requires pre-spend rejection and fail-closed data classification (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:145-197`; `reference/patterns/corpus-map-reduce.md:84-85,196-243,358-373`).

### R-4: Freeze `PRE` and compare archive-relative paths from the commit object

Define `PRE` as the human-reviewed census/evidence commit, require it to be a clean commit reachable from `origin/main`, and prove that its `.chaplain` tree identity equals the tree used by the disposition input manifest. Build `docs/census/chaplain-archive-manifest.txt` from the `PRE` commit object, not from the current index or working tree. The current `git ls-files ... | shasum` description does not read an arbitrary commit (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:214-221`).

Store manifest paths archive-relative by stripping the `.chaplain/` prefix. Compare that normalized path set and hashes with the fresh archive root; otherwise the literal parent paths and subtree-root paths cannot be equal. Retain the README-only transformation exception and three immutable identities.

### R-5: Make remote mutation journaled and safely resumable

Move the archive run record from `tmp/chaplain-archive.run.json` to `docs/census/chaplain-archive.run.json`, initialize it atomically before the first remote mutation, and commit the completed journal in GREEN. This resolves the direct conflict between the Step 1 path and AC-19's committed-run-record requirement (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:214-215,309`).

Freeze a resumable state machine for tag creation, repository creation, split push, README commit, verification, and repository archival. On retry, an existing tag or repository may be resumed only when the journal and remote facts exactly match the frozen `PRE`, `SPLIT`, visibility, and expected archive identity; an unrelated or mismatched resource retains the collision exit and stops for human reconciliation. Tests must inject failure after each remote transition and prove exact-state resume plus mismatch refusal. A script that pushes the tag and then treats its own partial result as an unrecoverable collision is not a complete fail-closed operation (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:198-229`).

### R-6: Split human review into chronologically possible gates

Replace AC-15 with two recorded reviews:

1. **Pre-remote review:** exact census and manual resolutions, visibility decision, frozen `PRE`, archive manifest, script/dry-run output, and intended tag/repository operations. This review occurs before tag push or repository creation.
2. **Pre-merge review:** actual remote journal and `gh repo view` evidence, hook removal, exact mass-deletion diff, RED/GREEN SHAs and outputs, final validation, and deviations. This review occurs before merge.

The current criterion requires the final GREEN record and validation before remote operations, but GREEN itself records `PRE`/`SPLIT`/`ARCHIVE_HEAD` produced by those operations (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:248-269,305`). Preserve the parent plan's human gate without requiring evidence from the future (`feature-requests/FR-1010-chaplain-archival-plan.md:410-415`).

### R-7: Give post-merge evidence a committed carrier and make weak checks exact

Write the post-merge witness to `docs/census/chaplain-postmerge.run.json`, not `tmp/`, and freeze a docs-only FR-1012 follow-up commit that records the JSON and completes the FR implementation record before FR-1013 starts. The Phase 2 merge cannot itself contain evidence generated after that merge (`feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md:278-286,308`).

Replace “no Phase 2 command ran before all fields were complete” with positive provenance: the census run's source commit must descend from all three recorded prerequisite merge SHAs, and both run records must name those SHAs. Replace “remain live and unchanged in behavior” with the exact existing focused test commands for `scripts/finalize_merge.sh`, CAP-38, and CAP-45, plus the full non-slow suite. Fold the revised acceptance criteria below verbatim.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`: fold R-1 through R-7, corrected status, exact commands/paths, revised criteria, decisions, and implementation records. |
| D-2 | `scripts/chaplain_census.py`; Chaplain discover/extract manifests, rubric, typed reconciler, and tests under the existing `examples/demos/corpus_census/adapters/` family; `examples/demos/corpus_census/graph.yaml` and its prompts remain unchanged. |
| D-3 | Frozen input manifest, separately named generic ledger/raw outputs/brief, reconciled `docs/census/chaplain-test-disposition.jsonl`, summary, census run record, and human raw-read record. |
| D-4 | `scripts/chaplain_archive.sh`, its fixture/partial-run tests, archive-relative source manifest, and committed `docs/census/chaplain-archive.run.json`. |
| D-5 | Exact new CAP/REQ, `tests/unit/test_fr1012_chaplain_removed.py`, census-authorized test deletions/CAP retirements, and the explicitly enumerated non-census removals in one atomic GREEN. |
| D-6 | `chaplain-archive` tag and source-only `sheikkinen/yamlgraph-chaplain` repository with README-only transformation, verified visibility/archive state, and three immutable identities. |
| D-7 | `docs/archive/chaplain.md`, generated `ARCHITECTURE.md`, replacement table, changelog fragment, and one `docs/diary/` Distill entry containing a `**Seed:**`. |
| D-8 | `scripts/chaplain_postmerge_witness.sh` and the committed follow-up `docs/census/chaplain-postmerge.run.json` plus completed FR implementation record. |

Not authorized under FR-1012: changes to the shared census graph, prompts, generic reducer, YAMLGraph runtime, FR-701 validation, CAP-38, CAP-45, or `scripts/finalize_merge.sh`; a second census graph or prompt tree; deletion outside reconciled `delete` rows and the enumerated non-census set; retirement of a mixed/live CAP without recorded human resolution; doctrine work assigned to FR-1013; a runnable-standalone archive claim; symlinks, stubs, path shims, unreviewed public disclosure, destructive collision cleanup, or reuse/overwrite of a mismatched tag or repository.

## Revised acceptance criteria

- [ ] AC-01: FR-1014, FR-1011, and FR-1015 merge SHAs and human-review references are recorded; FR-1011's 13-item inbox manifest is linked and `.chaplain/inbox/` is confirmed empty; the census source SHA descends from all three merge SHAs.
- [ ] AC-02: `## Raw Input Read` retains at least five source-cited samples covering certain-delete, certain-keep, shared-REQ, runtime-only CAP, and mixed/live CAP boundaries, each with per-REQ fan-in and a concrete surprising detail.
- [ ] AC-03: `scripts/chaplain_census.py` binds Chaplain manifests and rubric to unchanged `examples/demos/corpus_census/graph.yaml`; no second graph/prompt tree or modification to the shared graph, prompts, or reducer exists.
- [ ] AC-04: The census model output uses the fixed `CorpusCensusFinding` schema; the generic ledger is preserved separately; a deterministic Pydantic reconciler emits the frozen test/CAP rows and rejects illegal kind/verdict pairs, abstained/demoted/failed rows, missing/duplicate/unknown rows, invalid evidence spans, and unresolved manual reviews.
- [ ] AC-05: Before the first provider call, the census wrapper records source SHA, visibility/data classification, provider/model, item paths/kinds/bytes/SHA-256, marker-AST REQs, per-REQ fan-in, CAP modules/presence/status, and rejects any breach of the 120-item, 1.5-MB-total, 48-KB-item, 130-call, credential, or policy ceilings; the whole graph process has a 20-minute enforced timeout.
- [ ] AC-06: The run record proves all eight corpus-map-reduce invariants, both withheld canary families, exact generic-ledger-to-manifest coverage, valid citations, and zero unresolved rows; a named human records reading the raw primary outputs before trusting the disposition artifact.
- [ ] AC-07: The census/evidence commit contains the manifests, wrapper, adapters, rubric, raw/generic/reconciled artifacts, run record, exact CAP/REQ allocation, and human-read record; it passes all applicable gates before RED.
- [ ] AC-08: The dedicated RED commit adds only the frozen focused removal witness, is marked `SKIP=pytest`, and records its expected assertion failures; the immediately following atomic GREEN makes that witness, `python scripts/req_coverage.py --strict`, `python scripts/validate_capabilities.py --strict`, `lint-imports`, and `pytest tests/unit -q -m "not slow" -n auto` pass.
- [ ] AC-09: Every commit except the designated RED passes the checks applicable to its state; final Phase 2 PR HEAD passes every AC-08 command, with RED/GREEN SHAs and outputs recorded.
- [ ] AC-10: The deleted test set equals reconciled test `delete` rows; transitioned CAPs equal reconciled CAP `retire` rows; `git ls-files .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py` prints nothing; the hook and matching `.gitignore` lines are absent; no other deletion occurs.
- [ ] AC-11: Pre-remote human review records the exact census/manual resolutions, visibility decision, frozen `PRE`, archive manifest, archive-script dry run, and intended remote operations before tag push or repository creation.
- [ ] AC-12: `PRE` equals the reviewed census/evidence commit; its `.chaplain` tree equals the disposition input tree; the archive manifest is generated from the commit object with archive-relative paths and SHA-256 values.
- [ ] AC-13: The archive script writes an atomic durable journal before mutation; unrelated tag/repository collisions fail with the frozen typed exits; injected partial failures resume only when journal and remote `PRE`/`SPLIT`/visibility identities match exactly; mismatches stop for human reconciliation.
- [ ] AC-14: `git ls-remote --tags origin refs/tags/chaplain-archive` resolves exactly to `PRE`; final `gh repo view` proves the selected visibility, archived state, and default branch; the committed archive journal records `PRE`, `SPLIT`, `ARCHIVE_HEAD`, manifest SHA-256, transitions, and timestamps.
- [ ] AC-15: A fresh archive clone has exactly the archive-relative frozen path set and file count; every source hash matches except `README.md`, whose only content change is the prepended historical-source banner and links; its first line contains "not a runnable distribution."
- [ ] AC-16: `docs/archive/chaplain.md` records the tag, URL, verified visibility/archive status, three immutable SHAs, and one replacement row for every FR-1010 live-parts category.
- [ ] AC-17: `python scripts/aggregate_capabilities.py && git diff --exit-code -- ARCHITECTURE.md` succeeds; explicit no-match assertions prove `scripts/vscode/now.py` emits no `.chaplain`; the named existing focused tests for `scripts/finalize_merge.sh`, CAP-38, and CAP-45 pass, as does the full non-slow suite.
- [ ] AC-18: Pre-merge human review records the actual remote journal/state, hook removal, exact mass-deletion diff, RED/GREEN record, final validation, and deviations before merge.
- [ ] AC-19: `scripts/chaplain_archive.sh`, `scripts/chaplain_postmerge_witness.sh`, and `scripts/chaplain_census.py` are checked in with focused tests for every refusal, success, and partial-recovery path; the census and archive were produced by those scripts, and their committed run records match the reviewed invocations.
- [ ] AC-20: After merge, `scripts/chaplain_postmerge_witness.sh` exits 0 on main, proving sync succeeded, `.chaplain` is untracked-empty, and `now.py` emits no `.chaplain`; a docs-only FR-1012 follow-up commit records `docs/census/chaplain-postmerge.run.json` and completes the implementation record before FR-1013 starts.
- [ ] AC-21: Any new live artifact, prerequisite or `.chaplain` tree drift, unresolved census row, provider-policy failure, archive mismatch, or mismatched remote/tag state stops enforcement and returns FR-1010/FR-1012 to judgement.
- [ ] AC-22: `changelog/unreleased/fr-1012-chaplain-runtime-removed.md` and a `docs/diary/` Distill entry with `**Seed:**` are committed; the implementation record contains every census, archive, review, validation, follow-up, and deviation reference.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-7 and AC-01 through AC-22 are folded into committed FR-1012, and this draft is human-reviewed, before implementation authority activates. | GATE |
| C-2 | FR-1014, FR-1011, and FR-1015 are implemented, human-reviewed, merged in order, and recorded by immutable SHA; the inbox migration is complete and empty. | GATE |
| C-3 | The fixed-schema shared census graph is reused byte-for-byte; Chaplain richness is added only by deterministic collector/reconciler code. Any generic graph/schema gap stops this FR. | GATE |
| C-4 | No RED, remote mutation, deletion, or CAP retirement occurs until the exact census is committed, all invariants/canaries pass, raw rows are human-read, every manual row is resolved, and the exact new CAP/REQ is frozen. | GATE |
| C-5 | Pre-remote human review covers the immutable census, visibility, `PRE`, archive manifest, and dry-run plan before any tag or repository mutation. | GATE |
| C-6 | Remote operations use the journaled state machine; only an exact owned partial state may resume. Mismatched existing resources stop without overwrite or cleanup. | GATE |
| C-7 | The dedicated failing RED precedes one atomic GREEN; only RED is exempt from green history, and final Phase 2 PR HEAD passes every strict, focused, and full check. | GATE |
| C-8 | Pre-merge human review covers actual remote state, hook removal, mass deletion, RED/GREEN evidence, and final validation. | GATE |
| C-9 | FR-701 validation, CAP-38/CAP-45, `scripts/finalize_merge.sh`, shared census artifacts, and FR-1013 doctrine scope remain untouched. | GATE |
| C-10 | The post-merge witness and docs-only evidence commit complete FR-1012 before FR-1013 enforcement begins. | GATE |

Authority granted: after R-1 through R-7 are folded and human-reviewed and C-1 through C-5 are satisfied, implement only the frozen fixed-schema census consumer, journaled source-only archive/tag, census-authorized retirement/removal, archive documentation, traceability, changelog, Distill, and post-merge evidence surfaces listed above, subject to C-6 through C-10 at their stated stages.
