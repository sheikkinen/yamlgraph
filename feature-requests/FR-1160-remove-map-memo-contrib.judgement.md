# Judgement: FR-1160 Remove the FR-1159 Map Memo Contrib and Its Demo

**Verdict:** APPROVED WITH REVISIONS — The bounded removal is justified; authority activates only after R-1 through R-4 are folded into the committed FR and the gates below are satisfied.

**Prior art:** FR-1159 (rejected; the change removed), FR-1158 (rejected, no code), FR-1116 and FR-1120 (memo home and contract, restored unchanged), FR-1134 (retirement shape), FR-1155 (original use case, out of scope) as dispositioned in the FR.

**Reviewed against:** Committed inputs at `933135a2f43af7026fa4f0a6be547b9d49ee376a`, limited to:

- `feature-requests\FR-1160-remove-map-memo-contrib.md`, entire FR.
- `feature-requests\FR-1158-cached-map-node.md` (lines 1-110) and its judgement; `feature-requests\FR-1159-map-memo-contrib.md` (lines 1-115) and its judgement.
- `feature-requests\FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md` (lines 1-185) and its judgement, including the operator override.
- The alternatives passages of `feature-requests\FR-1116-map-memo-file-corpus.md` and `feature-requests\FR-1120-census-map-memo.md`.
- The follow-up passages of `feature-requests\FR-1155-prompt-cache-tokens-in-token-usage.md` and map-spike passages of `feature-requests\FR-1155.research.md`.
- `tests\unit\test_fr1134_retirements.py`, `tests\unit\test_fr335_module_map_compression.py`, and both `examples\shared\map_memo_*.tool.yaml` manifests.
- The committed name/status delta `1c8b0b85~1..1c8b0b85`, the cited memo/manifests diff, and subsequent committed path history through the reviewed HEAD. Tracked-path queries checked the cited CI script and proposed CAP-303 allocation.
- `.github\skills\judge-fr\doctrine.md`, `.github\skills\judge-fr\judgement.template.md`, and repository doctrine supplied from `.github\copilot-instructions.md` and `CLAUDE.md`.

No author transcript, uncommitted adapter content, local CI script, or working notes informed this verdict. The referenced `tmp\fr1156_w_ci.sh` is not tracked at the reviewed HEAD; its contents were not consumed. This is a draft only, not a promoted judgement.

## What is sound

The strongest case against removal is that FR-1159 addressed a genuine distribution boundary and already received conditional approval. A useful contrib helper does not become technically defective merely because it answers a different request. Nevertheless, the committed operator decision now explicitly withdraws that product direction, and FR-1160 preserves the two existing example consumers instead of destroying their memo implementation (FR-1160 lines 7-35, 184-189). The original FR-1155 follow-up concerns prompt-cache warm-first dispatch, not persistent result reuse. The distinction is substantive.

The proposed historical baseline makes this unusually auditable: the cited squash contains the listed move, direct reference repairs, demo, registry additions and budget change. No subsequent committed changes were found on the inspected restoration surfaces through the reviewed HEAD. Restoring those surfaces is feasible without a new abstraction.

The retirement precedent is correctly reusable, but its authority must be read accurately: FR-1134 initially received SPLIT and was implemented under the recorded operator override. This proposal does not repeat that bundle; retiring this contrib and its directly dependent demonstration is one concern.

| Rubric criterion | Assessment |
|---|---|
| 1. Scope | Cohesive and minimal: reverse the FR-1159 delivery surface, retain its historical record, and preserve the original memo consumers (FR lines 37-43, 125-155). No replacement map feature is needed. |
| 2. Consistency | Needs R-2/R-3: the later-change hand-merge branch conflicts with unconditional baseline equality, and the planned zero-hit search excludes fewer paths than AC-04 (lines 82-87, 163-171). |
| 3. Measurability | Baseline diffs, absence assertions, registry coverage and statuses are checkable. AC-06 depends on an uncommitted script rather than a reproducible committed recipe (lines 108, 174-176); R-4 fixes this. |
| 4. Feasibility | The cited squash and existing manifests support the reversal. CAP-303 is not allocated in the reviewed tracked tree. R-3 addresses strict registry generation during RED, using the actual FR-1134 implementation lesson. |
| 5. Architecture alignment | Restoring example-local `path:` loading and preserving memo behavior aligns with FR-1116/FR-1120. A terminal workaround after a guard denial is not authorized by doctrine (FR line 87); R-1 removes it. |
| 6. Single responsibility | One retirement, including the demo, packaging reference, witnesses and registry that exist solely because of the removed relocation. No SPLIT is required. |
| 7. Strategic classification | **Contrib/example retirement**, not a framework primitive. Two existing consumers retain the existing example abstraction; the warm-first feature remains a separate FR (lines 25-35, 188-189). |
| 8. Testability | The proposed absence and manifest witnesses can fail by assertion on the current tree, without missing imports or fixtures (lines 115-123). R-3 makes RED registry-consistent; R-4 makes preservation and CI validation executable. |

The in-body research record covers six genuine reversal/delivery choices and dispositions the rejected core-node precedent and retained example contracts. It is not a strawman record. R-1 supplies its missing explicit `is_this_a_graph` answer. This is deterministic removal, not measurement tooling; no new raw-sample or provider-spend gate applies.

## Required revisions

### R-1: Remove the guard workaround and complete the research disposition

Replace the Planned Operations branch at FR line 87 with: "Delete the listed demo artifacts using ordinary repository-approved operations. If a guard denies the operation, stop and report the denial; do not retry through a different tool to evade it. Any required routing or guard correction must receive separate authority."

Using `git rm` as an ordinary deletion operation is not itself prohibited. Selecting it because a file-tool deletion was denied is the defect. This FR grants no authority to alter guards, sentinels, adapters or enforcement policy.

Add to the in-body research record: "`is_this_a_graph`: No -- deterministic reversal, registry reconciliation and absence witnesses; no model stage or new graph/prompt artifact is required." Preserve the six alternatives and the separation from warm-first work. Explicitly identify FR-1134's retirement implementation as proceeding under its recorded operator override, rather than implying its original SPLIT verdict granted authority.

### R-2: Make restoration equality conditional on intervening changes

Reconcile the Summary, Ideal Result, GREEN steps and AC-02/AC-03 with the hand-merge branch at FR line 86:

- Record the implementation base SHA and check every restored path, including `examples\shared\map_memo.py` and generated registry sources, for changes after `1c8b0b85`.
- For a path with no intervening changes, require byte equality with `1c8b0b85~1` after restoration.
- For a path with intervening changes, preserve unrelated changes and reverse only the FR-1159 hunks. Record the path, intervening commits and retained differences in the completion reconciliation table; unconditional baseline equality does not apply to that path.
- Regenerate `ARCHITECTURE.md` from the complete current registry. Do not restore an old generated file over newer registry output. Its change relative to the implementation base must be explained by retiring CAP-302 and adding the retirement capability, preserving unrelated generated content.

Do not silently expand scope if an intervening semantic change prevents a behavior-preserving reversal; stop and seek revised authority. At the reviewed HEAD the inspected restoration history is clear, so this is a precise concurrency boundary, not permission for discretionary refactoring.

### R-3: Make RED and reference checks internally consistent

Add regeneration of `ARCHITECTURE.md` to the RED commit immediately after registering CAP-303 / REQ-YG-727. The FR-1134 precedent explicitly records that strict requirement coverage required the capability and generated architecture alongside its new tagged witness (FR-1134 AC-01, lines 174-183). Regenerate again in GREEN when CAP-302 is deleted. Confirm the CAP/REQ IDs remain unallocated at implementation time; do not overwrite another capability.

Replace Planned Operations' zero-hit probe at FR line 83 with AC-04's exact allowlist: `feature-requests\`, `docs\diary\`, and `tests\unit\test_fr1160_retirements.py`. Use literal matching (`git grep -F`) for the five reference tokens so dots are not regex wildcards. Inspect any other hit; do not add open-ended exclusions or delete historical content to force a pass.

Retain an explicit absence assertion for each deleted surface and the restored manifest-source assertions. All new test functions must carry REQ-YG-727 and fail on the pre-removal implementation by assertion, not collection/import errors. Record the actual RED parent and failure output, rather than merely claiming the uncommitted test "fails on" the historical squash.

### R-4: Replace the private CI-script dependency with a committed recipe

Replace FR line 108 and AC-06's opaque "Docker CI-mirror run" with an exact self-contained recipe in the committed FR, or an exact tracked recipe and invocation cited by it. Specify the image, dependency installation, test selection, marker handling, working directory and candidate SHA. Do not rely on `tmp\fr1156_w_ci.sh`: `git ls-files --error-unmatch` cannot find that file in the reviewed commit.

Before the wider mirror run, name one targeted command that includes the new process-marked retirement witness, `test_fr1116_map_memo.py`, `test_fr1120_map_memo_versions.py`, `test_fr1113_meta_map.py`, `test_fr1120_census_memo_graph.py`, and `test_fr335_module_map_compression.py`. The two consumer suites are already identified in the cited FR-1159 judgement; they directly cover the bindings this reversal restores. Do not accidentally deselect the retirement witness with a `not process` filter.

Require strict requirement coverage and the existing applicable formatting/lint/import checks to pass. Record commands, candidate identity and outcomes in FR-1160. Add one scoped removal changelog fragment unconditionally, rather than only when a hook asks, and require the scoped Distill entry with a **Seed:**. Historical FR-1159 documentation and its released-history records remain unchanged apart from the status annotations already committed.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1: Restore the original memo and bindings | Move `yamlgraph\contrib\map_memo.py` back to `examples\shared\map_memo.py`; restore its original docstring, both shared manifests, shared README, CAP-289/CAP-292 paths and the two named memo test modules |
| D-2: Remove the relocation-only delivery | Entire `examples\demos\map_memo\` directory; FR-1159 test module, CAP-302 and unreleased feature fragment; restore `examples\README.md`, contrib initializer, vulture whitelist and module-map test budget |
| D-3: Register and witness retirement | `tests\unit\test_fr1160_retirements.py`, CAP-303 / REQ-YG-727 subject to allocation check, and generated `ARCHITECTURE.md` |
| D-4: Record the decision and completion | Preserve the committed FR-1158/FR-1159 rejection annotations; update FR-1160 implementation/reconciliation evidence; add a scoped removal fragment and diary **Seed:** |

Not authorized: implementing warm-first dispatch or any new node; changing memo logic, store format, identity, failures or result contracts; deleting the FR-1116/FR-1120 consumers; rewriting retained consumer graphs/prompts; recreating the rejected demo; changing compiler, provider, manifest schema or packaging configuration; changing guards, adapters, hooks, CI or doctrine; rewriting historical judgements, briefs or diary entries; restoring whole files over unrelated concurrent changes; provider-backed runs or new spend.

## Revised acceptance criteria

- [ ] AC-01: R-1 through R-4 are folded into the committed FR before implementation. Its research record explicitly answers `is_this_a_graph`, and its operations contain no denial-evasion branch.
- [ ] AC-02: A separate RED commit adds the process-marked REQ-YG-727 witnesses, registers the retirement capability and regenerates architecture. Recorded execution on its actual parent implementation fails by the intended assertions; GREEN makes those same witnesses pass.
- [ ] AC-03: Every listed deletion is absent, `examples\shared\map_memo.py` exists, both shared manifests declare `runtime.path: map_memo.py` without `runtime.module`, and the contrib initializer, vulture whitelist and examples index contain no `map_memo` token.
- [ ] AC-04: The implementation records a per-path intervening-change check. Unchanged restoration paths, including the restored memo, equal `1c8b0b85~1` byte-for-byte; any changed path retains unrelated hunks and has an explicit baseline/base/candidate reconciliation as specified in R-2.
- [ ] AC-05: CAP-302 / REQ-YG-726 are removed from the active registry and replaced by the separately identified retirement capability/requirement. Generated architecture reflects the current registry without losing unrelated entries; strict requirement coverage passes, REQ-YG-727 is covered and no test references REQ-YG-726.
- [ ] AC-06: Literal tracked-file searches for `contrib.map_memo`, `contrib/map_memo`, `demos/map_memo`, `CAP-302` and `REQ-YG-726` have hits only in the three R-3 allowlisted locations.
- [ ] AC-07: The R-4 targeted selection passes, including the process-marked retirement witness, both memo suites, both existing consumer suites and module-map compression with budget 300. No behavioral assertions are weakened to make the reversal pass.
- [ ] AC-08: The committed, fully specified CI-mirror recipe and existing applicable lint/format/import checks pass on the recorded candidate; no acceptance result depends on an uncommitted helper script or an unexplained deselection.
- [ ] AC-09: FR-1158 and FR-1159 retain their committed Rejected statuses, operator reason and FR-1160 links. Their judgements, authoring brief and FR-1159 diary remain unchanged. FR-1160 records implementation status, decisions, commands, results and any authorized restoration exceptions.
- [ ] AC-10: The FR-1159 unreleased feature fragment is deleted, a scoped FR-1160 removal fragment is added, and the completion diary contains a metacognitive insight and **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| GATE-1 | Commit R-1 through R-4 before implementation; this draft alone grants no immediate implementation authority. | GATE |
| GATE-2 | Respect every guard denial. No alternate-tool evasion or enforcement-infrastructure modification is authorized. | GATE |
| GATE-3 | Preserve unrelated intervening changes and the original memo's executable behavior. A conflict requiring semantic redesign stops this removal and returns for revised authority. | GATE |
| GATE-4 | Use separate witnessed RED/GREEN commits with registry-consistent traceability. Keep original example-consumer graph/prompt artifacts unchanged. | GATE |
| GATE-5 | Use the committed reproducible validation recipe; pass the named targeted and wider checks and record the candidate SHA. Uncommitted notes and scripts cannot establish acceptance. | GATE |
| GATE-6 | Respect the operator's recorded removal decision without inventing authority for its replacement. No new product or spend decision is absorbed by this verdict. | GATE |

Authority granted: conditional authority to reverse only FR-1159's contrib relocation and directly dependent demo, test, registry and documentation surfaces, preserve the original example memo, and add the bounded retirement witnesses and delivery record, after the required revisions are committed.
