# Judgement: FR-1011 Relocate the live parts out of `.chaplain/` (Phase 1 of FR-1010)

**Verdict:** APPROVED WITH REVISIONS — the extraction is the right atomic Phase 1 boundary, but implementation authority activates only after R-1 through R-6 are folded into the FR, FR-1014 is implemented and merged with all three authoring-guard surfaces synchronized, and this advisory judgement is human-reviewed.

**DRAFT:** Advisory until human-reviewed.

**Prior art:** see FR-1011's own Prior Art field (FR-196, FR-745, FR-744, FR-767, FR-889) — this judgement reviews and dispositions those same citations; FR-1010/FR-1014 are the governing plan and prerequisite phase, not precedent.

**Reviewed against:** committed HEAD `3b403de3`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-1014-dir-aware-authoring-guard.md`; `feature-requests/FR-1014-dir-aware-authoring-guard.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `ARCHITECTURE.md`; `docs/development-process.md`; `.pre-commit-config.yaml`; `.gitignore`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/checks/triage_gate.py`; `.github/hooks/scripts/checks/fr-checks.sh`; `.github/skills/feature-request/SKILL.md`; `.github/skills/session-introspection/SKILL.md`; `scripts/check_authoring_proof.py`; `scripts/vscode/now.py`; `scripts/finalize_merge.sh`; `.chaplain/graphs/fr_triage/graph.yaml`; `.chaplain/graphs/world_distill/graph.yaml`; `.chaplain/graphs/world_distill/tools.py`; `.chaplain/graphs/philosopher/graph.yaml`; `.chaplain/graphs/philosopher/README.md`; `.chaplain/graphs/philosopher/tools.py`; `.chaplain/lib/diary.py`; `examples/philosopher/README.md`; `tests/unit/test_fr_triage.py`; `tests/unit/test_world_distill.py`; `tests/unit/test_philosopher.py`; `tests/unit/test_chaplain_graph_compile.py`; `tests/unit/test_finalize_merge.py`; `capabilities/CAP-75-portable-chaplain.yaml`; `capabilities/CAP-114-automated-post-merge-finalization.yaml`; `capabilities/CAP-205-world-distill.yaml`; `capabilities/CAP-206-fr-triage-graph.yaml`; and committed repository path searches for `.chaplain/graphs`, `.chaplain/inbox`, `.chaplain/lib`, `finalize_lib`, and the three relocated graph paths.

## What is sound

The underlying problem and phase order are real. The triage hook, world-orientation hint, finalizer, graph tests, capability registry, and philosopher diary proxy all point into a directory that Phase 2 is intended to remove (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:41-86`). FR-1010 already froze extraction before deletion and preserved the live finalizer rather than reversing the dependency direction (`feature-requests/FR-1010-chaplain-archival-plan.judgement.md:98-114,125-134`). Moving each consumer with its artifact is smaller and safer than introducing aliases or symlinks.

The proposal also handles the local-only inbox honestly. It does not pretend that an ignored directory can be migrated by a PR worktree, and it assigns the 13-item manifest, eight hash-verified carries, three drops, one forward, and empty-source confirmation to the operator's main checkout (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:88-102,212-224,254-257`). That preserves evidence without committing proposal contents.

Against the eight rubric criteria:

1. **Scope:** extracting every still-needed artifact before Phase 2 removes `.chaplain/` is a coherent atomic phase. The graph directories, diary helper, finalizer library, inbox route, and their direct consumers all serve the one deletion-readiness boundary (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:41-59,173-224`). It must not absorb FR-1014's widening or Phase 2/3 retirement work.
2. **Consistency:** the selected direction agrees with FR-1010, but the claims “pure relocation,” “update every consumer,” and “nothing outside `.chaplain/` refers to anything inside it” conflict with the intentional inbox contract change and omitted live references (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:4,47-54,183-211`). R-1, R-2, and R-5 make those claims exact.
3. **Measurability:** focused tests, hash checks, graph validation, strict traceability checks, and absence checks are appropriate. The current rename command cannot report the promised similarity score, the residual-path sweep is under-enumerated, and the three-graph smoke criterion names only one graph command (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:226-266`). R-4 and R-6 replace those with executable witnesses.
4. **Feasibility:** filesystem relocation and path updates use existing repository mechanisms. `fr_triage` and `world_distill` already use graph-relative tools, and the philosopher can become self-contained by moving `diary.py` beside `tools.py` (`.chaplain/graphs/philosopher/tools.py:363-375`). The untracked inbox remains feasible only if the documented submission command creates `proposals/`; R-5 closes that boundary.
5. **Architecture alignment:** process graphs belong under the existing `graphs/` root, graph-relative dependencies conform to CAP-75's established mechanism, and `scripts/lib/` is a suitable home for a script-owned library. Material graph moves correctly enter the sole authoring route (`.github/skills/graph-authoring/doctrine.md:9-16,54-83`). The missing committed authoring brief is an alignment defect, not a reason to invent a second route.
6. **Single responsibility:** this is one extraction phase whose invariant is “Phase 2 can remove `.chaplain/` without removing a live consumer.” The separate authoring-guard widening remains FR-1014, and runtime/test retirement remains FR-1012 (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:126-130,268-285`). No split is required.
7. **Strategic classification:** **pattern documentation / repository maintenance**. The FR adds no framework primitive or new use case; existing graph, hook, script-library, capability, and ignored-inbox abstractions suffice. Its value is subtraction and canonical placement, not a new abstraction.
8. **Testability:** destination existence, source absence, path consumers, proxy loading, finalizer behavior, graph lint/smoke, and inbox hashes can all be tested directly. The proposed RED currently changes module-level import paths and explicitly expects collection failure (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:151-171`), which would test missing fixtures rather than missing relocation behavior. R-3 requires assertion-level RED witnesses.

## Required revisions

### R-1: Make FR-1014 a complete, verified prerequisite

Amend the dependency and enforcement conditions to require FR-1014 to be implemented, human-reviewed, and merged before any FR-1011 relocation write. “Judged” is not sufficient. The prerequisite witness must prove the same dir-style contract in all three enforcement surfaces:

1. `.github/hooks/scripts/pre-command-guard.sh` `governed_path()`;
2. `scripts/check_authoring_proof.py` `GOVERNED`; and
3. `.pre-commit-config.yaml`'s `authoring-proof` `files:` selector.

The third surface still matches only flat `graphs/*.yaml` and flat `.chaplain/graphs/*.yaml` (`.pre-commit-config.yaml:29-35`), so a commit containing only `graphs/<name>/graph.yaml` or `graphs/<name>/prompts/*.yaml` would not invoke the backstop. FR-1011 must not widen that selector itself: amend FR-1014, or file and merge a separately judged prerequisite correction. FR-1011 may then delete only the obsolete `.chaplain/graphs` alternative from the selector while retaining FR-1014's dir-style `graphs/` alternatives.

Record the merged prerequisite SHA and human-review reference in FR-1011's Implementation Record. If the three surfaces do not agree before relocation begins, authority remains inactive.

### R-2: Replace the incomplete consumer claim with an exact live-path inventory

Expand the Phase 1 inventory and GREEN steps to cover the committed live/package-local references the current table omits:

- `.pre-commit-config.yaml:34`: delete the obsolete `.chaplain/graphs` selector alternative after R-1 is satisfied;
- `.github/hooks/scripts/pre-command-guard.sh:143-145,267-270,375`: update the authoring-contract comment, denial text, and branch-create guidance, not only the predicate and pre-filter;
- `scripts/check_authoring_proof.py:8-10`: update the published governed-path contract as well as the pattern tuple;
- `.chaplain/graphs/philosopher/README.md:8-40`: replace the dead wrapper, graph path, inbox path, portability claim, and watcher-relative links with truthful relocated usage or remove obsolete sections;
- `.chaplain/graphs/philosopher/tools.py:261,364-371`: update the inbox and diary-proxy documentation together with the sibling lookup;
- `.chaplain/graphs/philosopher/graph.yaml:5,12,21`: update the relocation and inbox descriptions;
- CAP-75, CAP-114, CAP-205, and CAP-206: update both module paths and prose that assigns the old location semantic, then regenerate `ARCHITECTURE.md`.

Do not turn this into a repository-wide historical rewrite. Replace the false Summary claim at lines 51-54 with the narrower invariant: no **Phase 1 live consumer or relocated package documentation** points at the extracted `.chaplain/graphs`, `.chaplain/lib/finalize_lib.sh`, or `.chaplain/inbox` paths. Explicitly allow the historical records, `chaplain-ops`, legacy ID-registry surfaces, Phase 2 runtime/tests, and Phase 3 doctrine/docs that FR-1010 assigns elsewhere. Freeze that residual allowlist in the relocation test instead of using an unexplained “Phase 2 test set” exclusion.

### R-3: Make RED fail on relocation assertions, not collection errors

Replace the RED instruction that rewrites module-level `TOOLS` paths and “collection fails until GREEN” (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:151-156`). The RED commit must collect successfully and fail assertions that directly describe missing implementation:

- each required destination path does not yet exist;
- each old source still exists;
- live consumers still name the old path;
- the philosopher proxy does not yet resolve a sibling `diary.py`;
- the finalizer still sources the old library; and
- the documented proposal submission route does not yet create/use `proposals/`.

Move existing tests' module-level import constants in GREEN with the files, or refactor their loaders in RED so imports happen only after explicit existence assertions. The RED commit must carry `SKIP=pytest` and demonstrate failed assertions, never `FileNotFoundError`, import failure, or missing-fixture collection failure. Keep the requirement markers on the smallest witness that exercises each existing requirement rather than placing all four REQs on unrelated textual sweeps.

### R-4: Close the graph-authoring inputs and define three safe smoke witnesses

Add and cite the mandatory committed task brief:

`feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-brief.md`

The brief must name the three source and destination graph directories, the moved prompts/tools/README files, the sibling `diary.py`, all intended graph-content path-only edits, and the prohibition on semantic graph/prompt rewrites. This is required by `.github/skills/graph-authoring/doctrine.md:17-31`; `scripts/author.sh` alone does not close the authoring input.

Replace the ambiguous “committed under `docs/spikes/` or cited in the PR body” report disposition (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:232-233`). Keep `tmp/draft-authoring-report.md` as the adapter artifact and copy its required `Artifacts`, `Precedent`, `Validation`, `Repairs`, and `Blocked validation` record into FR-1011's committed Implementation Record. Record exact commands and outcomes.

List three separate lint commands; do not rely on one brace-expanded multi-path CLI invocation. Define one side-effect-contained smoke per graph:

- run `fr_triage` against a temporary copy of a Proposed FR under `tmp/`, never against committed FR-1010;
- run `world_distill` with `output_path` under `tmp/`, never overwrite `docs/world-context.md`;
- run `philosopher` with temporary `diary_dir` and `inbox_dir` paths and an explicit date/prefix, never write proposals or diary entries into tracked project directories.

FR-1010 AC-08 requires a real smoke record for all three relocated graphs (`feature-requests/FR-1010-chaplain-archival-plan.judgement.md:114`). A missing credential or dependency may be recorded honestly in the adapter report, but it blocks this phase's merge until the required real smoke succeeds; `python scripts/vscode/now.py` is an orientation-path witness, not a `world_distill` smoke.

### R-5: Make the untracked `proposals/` contract executable and name its behavior change

Change the Type/Summary wording from “pure relocation, no behaviour change” to “path relocation with no graph or finalizer semantic change.” The inbox route intentionally changes: the old path disappears, the remote-issue paragraph is removed, and writes move to a new untracked directory (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:203-224`). That is a small, authorized behavior change and must be stated rather than denied.

Use the root-anchored ignore rule `/proposals/`, not the repository-wide pattern `proposals/`. Rewrite the feature-request skill's executable example to create the ignored directory before writing, for example `mkdir -p proposals` followed by the existing safe heredoc shape. Add a clean-worktree/fresh-checkout witness showing that the documented command creates `proposals/<topic>.md`, `git check-ignore -q proposals/<topic>.md` succeeds, and `.chaplain/inbox/<topic>.md` is neither created nor silently redirected.

Keep the operator migration outside the PR, but make it a pre-merge GATE. The committed Implementation Record must contain the 13 names and SHA-256 values, destination verification for all eight carries, named disposition of all three drops and the one forward, removal of `ninchat_voice/`, creation of the new spark, and confirmation that the old inbox is empty. Proposal contents remain uncommitted.

### R-6: Replace ambiguous acceptance checks and add the human gate

Replace the rename criterion's `git diff --stat` command with `git diff --name-status -M90% <recorded-base-sha>...HEAD` (or an equivalent command that actually emits rename scores), and enumerate every expected old→new pair. Record the immutable base SHA; do not use a moving local `main` name.

Replace broad prose criteria with exact commands and assertions:

- the frozen live-consumer list contains no forbidden old path;
- the frozen residual allowlist contains only artifacts assigned to Phase 2/3, historical records, `chaplain-ops`, or the legacy ID registry;
- all focused relocation/finalizer tests and the full non-slow unit suite pass;
- `python scripts/req_coverage.py --strict` and `python scripts/validate_capabilities.py --strict` pass;
- generated `ARCHITECTURE.md` agrees with the four edited CAP files;
- the authoring brief and report record satisfy R-4;
- the FR-1010 live-parts table remains unchanged, or discovery stops enforcement and returns both FRs to judgement under FR-1010 C-10--not “amended before merge” while work continues.

Add a mandatory human-review record before merge. This phase deletes obsolete clauses from the graph-authoring guard/backstop and edits `.github/copilot-instructions.md`; enforcement infrastructure is adversarial input even when the diff is deletion-only (`.github/skills/judge-fr/doctrine.md:98-100`). Human review must cover the final hook, pre-commit selector, Scripture path edit, inbox manifest, and graph-authoring report.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1011-relocate-chaplain-live-parts.md`: fold R-1 through R-6, revised criteria, immutable base SHA, prerequisite SHA/review, inbox manifest, authoring report record, RED/GREEN SHAs, and final human-review record. |
| D-2 | `feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-brief.md`: committed, artifact-closed brief for the three graph relocations and path-only graph/package edits. |
| D-3 | `.chaplain/graphs/{fr_triage,world_distill,philosopher}` → `graphs/{fr_triage,world_distill,philosopher}` and `.chaplain/lib/diary.py` → `graphs/philosopher/diary.py`, including truthful relocated package comments/README and no semantic graph or prompt rewrite. |
| D-4 | `.chaplain/lib/finalize_lib.sh` → `scripts/lib/finalize_lib.sh`; update `scripts/finalize_merge.sh` without changing CAP-38/REQ-YG-125 or CAP-45/REQ-YG-144 behavior. |
| D-5 | Direct live consumers: triage hook/reminder, world refresh hint, feature-request and graph-authoring skills, session-introspection row, root Scripture seed path, philosopher package-local references, and finalizer source path. |
| D-6 | Guard/backstop cleanup only: delete obsolete `.chaplain/graphs` and `.chaplain` routing text from `.github/hooks/scripts/pre-command-guard.sh`, `scripts/check_authoring_proof.py`, and `.pre-commit-config.yaml` after the merged FR-1014 contract is verified; add no predicate grammar. |
| D-7 | `tests/unit/test_fr1011_relocation.py` plus path updates in the five named unit-test files; assertion-level RED and behavior-preserving GREEN witnesses. |
| D-8 | CAP-75, CAP-114, CAP-205, CAP-206 and generated `ARCHITECTURE.md`: path/prose relocation only, with no new CAP/REQ and no retirement. |
| D-9 | Root `.gitignore`, executable `proposals/` submission documentation, operator-owned inbox migration, and committed manifest metadata; proposal contents remain ignored and uncommitted. |
| D-10 | Delete `examples/philosopher/`; add the FR-1011 changelog fragment and the doctrine-required diary reflection with a Seed. |

Not authorized under FR-1011: widening or otherwise redesigning authoring predicates; changing sentinel lifecycle or `scripts/author.sh`; adding a symlink, fallback, alias, or old-path shim; tracking proposal contents; changing proposal durability beyond the selected ignored top-level directory; changing graph/prompt semantics, providers, models, schemas, nodes, or routing; retiring philosopher, finalizer behavior, CAPs, REQs, runtime tests, watcher code, or any `.chaplain/` subtree assigned to Phase 2; sweeping historical records or Phase 3 doctrine/docs; changing the ID registry; deleting hooks; or beginning FR-1012 work.

## Revised acceptance criteria

- [ ] AC-01: R-1 through R-6 are folded into committed FR-1011, and its Type/Summary state “path relocation with no graph or finalizer semantic change” while naming the intentional inbox-route change.
- [ ] AC-02: FR-1014 is implemented, human-reviewed, and merged before the FR-1011 RED commit; FR-1011 records its merge SHA and review reference.
- [ ] AC-03: An automated truth table proves `pre-command-guard.sh`, `check_authoring_proof.py`, and `.pre-commit-config.yaml` all cover FR-1014's flat, direct-child-YAML, and prompt-subdirectory `graphs/` contract before old `.chaplain/graphs` alternatives are deleted.
- [ ] AC-04: The committed authoring brief exists at the frozen path, is cited by FR-1011, names every expected graph artifact, and forbids semantic graph/prompt rewrites.
- [ ] AC-05: The RED commit carries `SKIP=pytest`, collects successfully, and fails only relocation assertions; it contains no import, `FileNotFoundError`, or missing-fixture collection failure.
- [ ] AC-06: `git diff --name-status -M90% <recorded-base-sha>...HEAD` reports every enumerated graph, prompt, tool, README, `diary.py`, and `finalize_lib.sh` old→new pair as a rename with score at least 90%.
- [ ] AC-07: The frozen live-consumer list contains none of `.chaplain/graphs/{fr_triage,world_distill,philosopher}`, `.chaplain/lib/finalize_lib.sh`, or `.chaplain/inbox/`; every remaining old-path occurrence is on the explicit Phase 2/3, historical, `chaplain-ops`, or legacy-ID residual allowlist.
- [ ] AC-08: The relocated philosopher README, graph comments, and tool docstrings name `graphs/philosopher`, sibling `diary.py`, and `proposals/` truthfully; no dead `.chaplain/philosopher.sh` usage or standalone-portability claim remains.
- [ ] AC-09: `scripts/finalize_merge.sh` sources `scripts/lib/finalize_lib.sh`; the old library is absent; focused finalizer tests pass without behavior changes to CAP-38/REQ-YG-125 or CAP-45/REQ-YG-144.
- [ ] AC-10: CAP-75, CAP-114, CAP-205, and CAP-206 name the new paths and preserve their active requirements; generated `ARCHITECTURE.md`, `python scripts/validate_capabilities.py --strict`, and `python scripts/req_coverage.py --strict` agree.
- [ ] AC-11: `/proposals/` is the root-anchored ignored inbox; the documented fresh-checkout command creates the directory and a proposal file; `git check-ignore -q proposals/<fixture>.md` succeeds; no old-path file or symlink is created.
- [ ] AC-12: FR-1011's committed Implementation Record contains the 13-item names+SHA-256 manifest, eight verified destination hashes, three named drops, one named forward, removed empty directory, new spark name, and operator confirmation that `.chaplain/inbox/` is empty; no proposal content is committed.
- [ ] AC-13: Separate `yamlgraph graph lint` commands pass for `graphs/fr_triage/graph.yaml`, `graphs/world_distill/graph.yaml`, and `graphs/philosopher/graph.yaml`.
- [ ] AC-14: Side-effect-contained real smoke commands pass for all three relocated graphs; outputs are confined to `tmp/`; the exact commands and outcomes appear in the authoring report record.
- [ ] AC-15: The triage hook imports `graphs/fr_triage/tools.py`, an actual staged `feature-requests/*.md` fixture runs `triage-gate` without `FileNotFoundError`, and `python scripts/vscode/now.py` prints the new world-distill path.
- [ ] AC-16: `pytest tests/unit/test_fr_triage.py tests/unit/test_world_distill.py tests/unit/test_philosopher.py tests/unit/test_chaplain_graph_compile.py tests/unit/test_finalize_merge.py tests/unit/test_fr1011_relocation.py -q --no-cov` and `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` pass.
- [ ] AC-17: `examples/philosopher/` is absent; the FR-1011 changelog fragment and diary reflection exist; the reflection contains a `**Seed:**`.
- [ ] AC-18: Discovery of any additional live artifact stops enforcement and returns FR-1010 and FR-1011 for amendment/rejudgement before work resumes.
- [ ] AC-19: A human reviews the final hook/pre-commit deletion diff, Scripture path edit, graph-authoring report, and inbox manifest; FR-1011 records the reviewed PR or commit before merge.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 and the revised acceptance criteria are folded into FR-1011 before implementation begins. | GATE |
| C-2 | FR-1014's implemented, human-reviewed commit is merged and proves agreement across the hook predicate, proof predicate, and pre-commit selector before any relocation write. | GATE |
| C-3 | All graph relocation runs through the committed FR-bound authoring brief and sole authoring route; the returned report records three lint and three real smoke successes. | GATE |
| C-4 | The RED commit precedes GREEN, carries `SKIP=pytest`, and fails by direct assertion rather than import/collection failure. | GATE |
| C-5 | No graph/prompt semantics, authoring predicate grammar, sentinel behavior, finalizer behavior, proposal durability model, CAP/REQ status, or Phase 2/3 artifact may change. | GATE |
| C-6 | The operator-owned inbox migration is complete and recorded before merge; no local proposal is silently lost, redirected, or committed. | GATE |
| C-7 | Human review of this advisory judgement and the final enforcement/Scripture/inbox diff is recorded before merge. | GATE |
| C-8 | Any newly discovered live artifact stops the phase and returns the frozen FR-1010 inventory and this FR to judgement. | GATE |
| C-9 | FR-1012 may not begin until FR-1011 is merged and its manifest, tests, traceability checks, lints, and real smokes all satisfy the revised criteria. | GATE |

Authority granted: after R-1 through R-6 are folded, FR-1014 is implemented and merged with the complete three-surface authoring contract, and this judgement is human-reviewed, implement only the frozen Phase 1 relocations, direct consumer/path updates, behavior-preserving witnesses, traceability regeneration, ignored-inbox migration record, changelog, and diary reflection.
