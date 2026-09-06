# Judgement: FR-1016 Retire the FR-1012 one-shot tooling

**Verdict:** APPROVED WITH REVISIONS — the deletion is a coherent, minimal maintenance subtraction, but authority activates only after R-1 through R-5 are folded into the FR, the missing FR-1012 post-merge evidence is committed, and this draft is human-reviewed.

**Reviewed against:** `feature-requests/FR-1016-retire-fr1012-one-shot-tooling.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.judgement.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`; `capabilities/CAP-264-chaplain-runtime-retired.yaml`; `tests/unit/test_fr1012_chaplain_removed.py`; `tests/unit/test_fr1012_chaplain_census.py`; `tests/unit/test_fr1012_chaplain_archive.py`; `tests/unit/test_fr1012_chaplain_postmerge_witness.py`; `scripts/chaplain_census.py`; `scripts/chaplain_archive.sh`; `scripts/chaplain_postmerge_witness.sh`; `docs/archive/chaplain.md`; `docs/census/chaplain-archive.run.json`; `docs/census/chaplain-test-disposition.run.json`; tracked-path and commit-object evidence for `docs/census/chaplain-postmerge.run.json` and `36591389`.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The proposal removes only the three completed one-shot routes, their private adapters, and their direct tests while preserving the end-state witness and immutable evidence (`FR-1016:46-49,102-141`). The five older one-shots and generic replacement tooling are explicitly excluded (`FR-1016:139-141,158-163`). |
| Consistency | The ideal, deletion set, and surviving CAP/test claim agree on the intended end state (`FR-1016:87-96,102-135`). Two chronology claims do not yet agree with committed evidence and are corrected by R-1 and R-2. |
| Measurability | The proposed path and module absences, exact CAP modules, strict registry checks, generated architecture, and focused witness are mechanically observable (`FR-1016:143-152`). R-4 replaces the unresolved base and non-exact diff/baseline language. |
| Feasibility | Commit `36591389` contains all three scripts; CAP-264 currently enumerates the scripts and direct tests; and `test_fr1012_chaplain_removed.py` already checks the durable runtime, census-set, CAP-retirement, archive-identity, and `now.py` end states. The remaining implementation is deletion plus narrow documentation/registry edits. |
| Architecture alignment | This follows the repository's Purge rule rather than creating a generic tool before the repo-split consumer is judged (`FR-1016:69-78,159-162`; `.github/copilot-instructions.md:211`). The shared `corpus_census` graph remains untouched. |
| Single responsibility | One concern is present: retire completed FR-1012 execution machinery. Capability truth, generated architecture, documentation, changelog, and tests are required consequences of that deletion, not separate features. |
| Strategic classification | **Pattern documentation / maintenance subtraction.** No framework primitive is proposed; git history and committed run records preserve the reusable pattern, while one live test preserves the regressible end state (`FR-1016:80-96,125-132`). |
| Testability | A failing RED can assert the exact absent paths and CAP module set before deletion (`FR-1016:102-105`). The surviving witness directly exercises the state that may regress, rather than importing deleted subjects. |

## Required revisions

### R-1: Complete FR-1012 before claiming its one-shot events are finished

Replace the unsupported claim that all three steps are done (`FR-1016:22-27,63-67`) with the actual committed state: `docs/census/chaplain-postmerge.run.json` is not tracked, while FR-1012 still records its post-merge follow-up and outcome as pending (`FR-1012:450-453`). FR-1012 AC-20 requires that carrier before FR-1013 starts (`FR-1012:405-406`; judgement `:224-228,265-266`).

Before FR-1016 receives enforcement authority, run the existing post-merge witness on main, commit `docs/census/chaplain-postmerge.run.json` in the FR-1012 follow-up, and update FR-1012's implementation record so no post-merge field remains pending. Then amend FR-1016's Prior art and Problem with the actual follow-up commit SHA and the record's `main_head`, `all_checks_pass`, `git_ls_files_chaplain`, `untracked_files_left_in_chaplain`, `now_py_rc`, and `now_py_mentions_chaplain` values. Do not delete the witness script or its tests before that evidence exists.

### R-2: Freeze one chronology with FR-1013 and acknowledge the shared file

Replace “after FR-1013 or in parallel; no shared files” (`FR-1016:31-34`) with this order:

1. FR-1012 post-merge follow-up is committed.
2. FR-1016 is enforced and merged.
3. FR-1013 rebases onto the FR-1016 merged head before enforcement.

FR-1016 and FR-1013 both edit `docs/archive/chaplain.md`; FR-1013 explicitly authorizes one link-line edit there (`FR-1013:88-96,138-149`). Concurrent enforcement is therefore forbidden. FR-1016 owns only the tooling-retirement paragraph; FR-1013 subsequently owns only its already-frozen archive-system link.

### R-3: Complete the mandatory research record

Add an explicit `is_this_a_graph` disposition to the in-body research record: **No — this is deterministic deletion, registry editing, and witness execution; no LLM judgement or graph orchestration is required.** Preserve the strongest disagreement, not only the status quo label: keeping the scripts until FR-1012 AC-20 and its implementation record are complete protects reproducibility and is mandatory; keeping them after that carrier is committed retains dead executable routes with no remaining event. This makes the otherwise substantive six-alternative table satisfy the repository's prospective research gate.

### R-4: Replace placeholder and aggregate checks with exact witnesses

Replace the acceptance criteria with the revised list below. In particular:

- bind `BASE` to the committed FR-1012 follow-up head after R-1, rather than leaving `<base>` unresolved (`FR-1016:149`);
- compare exact changed-path sets, not `git diff --stat` prose (`FR-1016:146-147`);
- define the Windows baseline as a set comparison of failed/error node IDs from identical commands at `BASE` and `HEAD`, rather than “shows no failure new” without a reproducible method (`FR-1016:151`);
- verify the post-merge JSON's substance before preserving `docs/census/` unchanged; and
- distinguish the runtime source preserved in the `.chaplain` subtree archive from these top-level scripts, whose last complete source is commit `36591389`.

### R-5: Include the required implementation record and Distill artifact

Add the FR implementation-record update and one `docs/diary/` Distill entry containing a `**Seed:**` to the authorized surfaces and acceptance criteria. Repository doctrine requires the FR to record implementation status, decisions, and deviations and requires Distill as the final task (`.github/copilot-instructions.md:26-27,213`). The seed already drafted at `FR-1016:167-170` may be carried into that entry.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Extend `tests/unit/test_fr1012_chaplain_removed.py` with exact absence assertions for the three scripts, four Chaplain census-adapter files, three direct test files, and CAP-264's sole surviving module. |
| D-2 | Delete exactly `scripts/chaplain_census.py`, `scripts/chaplain_archive.sh`, `scripts/chaplain_postmerge_witness.sh`, the four named `examples/demos/corpus_census/adapters/chaplain*` files, and the three named direct test files. |
| D-3 | Narrow `capabilities/CAP-264-chaplain-runtime-retired.yaml` and generated `ARCHITECTURE.md` to the durable end-state claim, with `fr: FR-1012, FR-1016` and only `tests/unit/test_fr1012_chaplain_removed.py` as the module. |
| D-4 | Add only the FR-1016 tooling-retirement/source-recovery paragraph to `docs/archive/chaplain.md`; preserve all existing archive identities and content. |
| D-5 | Add one FR-1016 `removal` fragment under `changelog/unreleased/`. |
| D-6 | Update FR-1016's status, implementation record, decisions, deviations, and evidence; add one `docs/diary/` Distill entry with `**Seed:**`. |

Not authorized under FR-1016: any edit to `docs/census/` after the FR-1012 prerequisite follow-up establishes `BASE`; any change to the generic `examples/demos/corpus_census` graph, prompts, schemas, reducer, non-Chaplain adapters, or demo proof; generalization or replacement of the deleted scripts; changes to the five older one-shot scripts; FR-1013 doctrine/reference work or its archive-system link; changes to hooks, CI, YAMLGraph runtime, unrelated capabilities/requirements/tests, archive tag, or archived repository; deletion or rewriting of historical run records.

## Revised acceptance criteria

- [ ] AC-01: Before RED, `docs/census/chaplain-postmerge.run.json` is tracked on main; its parsed JSON has `fr == "FR-1012"`, `step == "post-merge witness"`, `main_head == "36591389..."`, `worktree_sync == "ok"`, empty `git_ls_files_chaplain`, `untracked_files_left_in_chaplain == 0`, `now_py_rc == 0`, `now_py_mentions_chaplain is false`, and `all_checks_pass is true`; FR-1012's implementation record has no pending post-merge field. Record that committed follow-up head as `BASE`.
- [ ] AC-02: `git merge-base --is-ancestor "$BASE" HEAD` exits 0; FR-1013 has not been enforced concurrently and is rebased onto the eventual FR-1016 merged head before its own enforcement.
- [ ] AC-03: `git ls-files -- scripts/chaplain_census.py scripts/chaplain_archive.sh scripts/chaplain_postmerge_witness.sh` prints nothing at GREEN and merged HEAD.
- [ ] AC-04: `git ls-files -- examples/demos/corpus_census/adapters/chaplain_adapters.py examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml examples/demos/corpus_census/adapters/chaplain_rubric.md` prints nothing; the changed-path set under `examples/demos/corpus_census/` is exactly those four deletions.
- [ ] AC-05: `tests/unit/test_fr1012_chaplain_removed.py` contains the new exact tooling-absence witness and passes; the changed-path set under `tests/` is exactly that modified witness plus deletion of `test_fr1012_chaplain_census.py`, `test_fr1012_chaplain_archive.py`, and `test_fr1012_chaplain_postmerge_witness.py`.
- [ ] AC-06: Parsed CAP-264 has `fr == "FR-1012, FR-1016"`; both capability and REQ-YG-666 module lists equal `["tests/unit/test_fr1012_chaplain_removed.py"]`; its description and requirement name no deleted script or adapter; the requirement retains the absent-runtime, immutable archive identities, and enacted census-set claims.
- [ ] AC-07: `git diff --exit-code "$BASE"...HEAD -- docs/census/` exits 0.
- [ ] AC-08: `docs/archive/chaplain.md` identifies commit `36591389` as the last complete source for each deleted top-level script via valid `git show 36591389:<path>` commands, distinguishes those paths from the `.chaplain` subtree archive, and describes only the recoverable skeleton named in the FR. No other existing archive-note content changes.
- [ ] AC-09: `python scripts/aggregate_capabilities.py` followed by `git diff --exit-code -- ARCHITECTURE.md` exits 0; `python scripts/validate_capabilities.py --strict`, `python scripts/req_coverage.py --strict`, `lint-imports`, `ruff check tests/unit/test_fr1012_chaplain_removed.py`, and `pytest tests/unit/test_fr1012_chaplain_removed.py -q --no-cov` pass.
- [ ] AC-10: Identical `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` runs are recorded from clean Windows worktrees at `BASE` and `HEAD`; the set of failed/error node IDs at `HEAD` minus the set at `BASE` is empty. The removal PR's required Linux CI is green.
- [ ] AC-11: RED and GREEN are separate commits; RED fails only the new absence/module assertions and is committed with `SKIP=pytest`; every later commit passes the focused checks.
- [ ] AC-12: `git diff --name-only "$BASE"...HEAD` contains only D-1 through D-6 surfaces, including a `changelog/unreleased/` fragment with `type: removal` naming all three scripts and a `docs/diary/` Distill entry containing `**Seed:**`; FR-1016 records final status, commit identities, validation results, and deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No RED, deletion, or CAP edit may begin until R-1 is committed on main and `BASE` is frozen to that follow-up head. | GATE |
| C-2 | R-1 through R-5 and the revised acceptance criteria must be folded into the committed FR before authority activates. | GATE |
| C-3 | FR-1016 and FR-1013 may not be enforced concurrently; FR-1016 merges first, and FR-1013 must consume its merged head before editing the shared archive note. | GATE |
| C-4 | `docs/census/`, the archive tag, and the archived repository are immutable evidence; any required change to them stops enforcement and returns the FR to judgement. | GATE |
| C-5 | Any consumer of a proposed deletion beyond CAP-264, `docs/archive/chaplain.md`, and the named direct tests stops enforcement and returns the FR to judgement. | GATE |
| C-6 | Human review of this draft and of the exact deletion/evidence-preservation diff is required before merge; the judgement remains advisory until recorded in the FR implementation record. | GATE |

Authority granted: after C-1 through C-6 are satisfied, FR-1016 may delete only the frozen one-shot tooling and direct witnesses, narrow CAP-264 to its durable end-state claim, preserve the evidence, and update the explicitly listed documentation, generated registry, changelog, FR record, and diary surfaces.
