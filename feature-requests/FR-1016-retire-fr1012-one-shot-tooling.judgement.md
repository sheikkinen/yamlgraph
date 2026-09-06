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


---

# Round 2 (2026-09-06, after review of PR #630)

# Judgement: FR-1016 Retire the FR-1012 one-shot tooling

**Verdict:** APPROVED WITH REVISIONS - the amended deletion remains a coherent maintenance subtraction, but authority to merge activates only after R-1 through R-4 are folded into the FR, the outstanding evidence gates pass, and a human records review of this round-two draft and exact final diff.

**Reviewed against:** `feature-requests/FR-1016-retire-fr1012-one-shot-tooling.md`; `feature-requests/FR-1016-retire-fr1012-one-shot-tooling.judgement.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`; `docs/census/chaplain-postmerge.run.json`; `capabilities/CAP-264-chaplain-runtime-retired.yaml`; `docs/archive/chaplain.md`; `docs/confessions.md`; `docs/diary/diary-2026-09-06-reflection-fr-1010-the-agent-graded-its-own-exam.md`; `docs/diary/diary-2026-09-06-reflection-fr-1016-the-census-kept-its-own-scaffold.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The proposal still removes only the completed FR-1012 execution routes, their private adapters, and direct tests while retaining the regressible end-state witness and immutable run records (`FR-1016:46-49, 80-96, 102-141`). Removing four confessions whose cited source lines are deleted is a direct consistency consequence, not a second feature (`FR-1016:164-166`; `docs/confessions.md:2031-2053`). |
| Consistency | The amended AC-01 now preserves the observed value `untracked_files_left_in_chaplain == 10`, matching the committed JSON rather than rewriting evidence (`FR-1016:143`; `docs/census/chaplain-postmerge.run.json:1-18`). The remaining chronology and completion-state inconsistencies are narrow and mechanically repairable under R-1 through R-3. |
| Measurability | Exact deleted-path sets, exact CAP module lists, generated-registry checks, focused tests, merge-diff surfaces, and baseline node-ID set comparison are all mechanically checkable (`FR-1016:143-164`). R-2 and R-3 correct false completion marks; R-4 supplies the missing exact confession witness. |
| Feasibility | The implementation record identifies separate RED and GREEN commits, and the current CAP already has the proposed sole module and durable end-state claim (`FR-1016:180-187`; `CAP-264:1-28`). The remaining work is record correction, four stale confession deletions, and final evidence collection. |
| Architecture alignment | Retiring event-bound scripts follows the repository's Purge and `growth_as_default` doctrine instead of inventing a generic archive/census abstraction before the repo-split consumer is judged (`FR-1016:69-78, 156-166`; `.github/copilot-instructions.md:58-75`). The shared corpus-census graph is expressly excluded. |
| Single responsibility | The one concern remains retirement of FR-1012's one-shot tooling. CAP narrowing, generated architecture, source-recovery documentation, direct-test removal, stale-confession cleanup, changelog, FR record, and Distill entry are coupled consequences of that deletion. |
| Strategic classification | **Pattern documentation / maintenance subtraction.** No framework primitive is proposed. Git history and committed run records preserve the reusable skeleton, while the sole live witness preserves the state that can regress (`FR-1016:80-96, 125-132, 156-166`). |
| Testability | The exact absence and CAP assertions already produced an identified RED, and every remaining criterion can be checked by a named command, parsed field, exact changed-path set, or explicit human-review record (`FR-1016:102-105, 143-164, 180-187`). |

## Required revisions

### R-1: Fold D-7 into the frozen scope instead of proposing it beside an older judgement

Replace the paragraph that says D-1 through D-6 remain frozen by reference while D-7 is merely "proposed" (`FR-1016:166`) with the complete D-1 through D-7 scope table and not-authorized list below. Update the consumer boundary inherited from the first judgement so `docs/confessions.md` is an authorized, known reference surface. A new scope item cannot be both outside the frozen judgement and authorized by prose that points back to that judgement.

### R-2: Record the historical gate violation without pretending it can occur before RED

Change AC-01's opening from "Before RED" to "Before merge" (`FR-1016:143`). RED and GREEN already exist (`FR-1016:180-182`), while the cited FR-1012 implementation record still contains pending pre-merge and post-merge fields (`FR-1012:450-452`). Add a deviation stating that the first judgement's before-RED prerequisite was not satisfied as recorded and that round-two authority is closure authority only.

Before merge, update the committed FR-1012 implementation record with the actual post-merge follow-up identity and witness outcome so no post-merge field is pending; then record that corrective commit and ancestry in FR-1016. Do not rewrite `docs/census/chaplain-postmerge.run.json`: its observed value of 10 compiled cache files is evidence, and FR-1012 already records that they were removed by hand (`FR-1012:454`; `FR-1016:143,185-187`).

### R-3: Make completion marks agree with the implementation evidence

Untick AC-10. Its required clean-worktree run at `BASE` and required Linux CI are not present: the implementation record says the recorded baseline is `36591389`, not `BASE`, and says the BASE run is still to be recorded and Linux CI is awaited (`FR-1016:160,184,186-187`). Tick AC-10 only after recording both exact commands, both commit identities, both failed/error node-ID sets, their empty HEAD-minus-BASE difference, and the green Linux check.

After D-7 is applied, replace the stale AC-12 implementation note that the prior merge diff contained exactly D-1 through D-6 (`FR-1016:186`) with the final PR-base SHA, final PR-head SHA, exact command, and exact D-1 through D-7 changed-path output. Keep AC-12 unchecked until that final witness exists.

### R-4: Add an exact witness for stale-confession removal

Add AC-13 below. AC-12 currently permits `docs/confessions.md` to change but does not prove that only CONF-462 through CONF-465 were removed. The new criterion must establish both absence of those four IDs and preservation of every other confession entry, then run the repository's existing `noqa` coverage gate.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Extend `tests/unit/test_fr1012_chaplain_removed.py` with exact absence assertions for the three scripts, four Chaplain census-adapter files, three direct test files, and CAP-264's sole surviving module. |
| D-2 | Delete exactly `scripts/chaplain_census.py`, `scripts/chaplain_archive.sh`, `scripts/chaplain_postmerge_witness.sh`, `examples/demos/corpus_census/adapters/chaplain_adapters.py`, `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml`, `examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml`, `examples/demos/corpus_census/adapters/chaplain_rubric.md`, `tests/unit/test_fr1012_chaplain_census.py`, `tests/unit/test_fr1012_chaplain_archive.py`, and `tests/unit/test_fr1012_chaplain_postmerge_witness.py`. |
| D-3 | Narrow `capabilities/CAP-264-chaplain-runtime-retired.yaml` and generated `ARCHITECTURE.md` to the durable end-state claim, with `fr: FR-1012, FR-1016` and only `tests/unit/test_fr1012_chaplain_removed.py` as the module. |
| D-4 | Add only the FR-1016 tooling-retirement/source-recovery paragraph to `docs/archive/chaplain.md`; preserve all other archive identities and content. |
| D-5 | Add one FR-1016 `removal` fragment under `changelog/unreleased/` naming the three retired scripts. |
| D-6 | Update FR-1016's status, implementation record, decisions, deviations, and evidence; add one `docs/diary/` Distill entry containing `**Seed:**`. Correct FR-1012's pending post-merge implementation-record fields as the prerequisite record repair required by R-2. |
| D-7 | Remove exactly CONF-462, CONF-463, CONF-464, and CONF-465 from `docs/confessions.md`, with no other confession change. |

Not authorized under FR-1016: rewriting any file under `docs/census/`; changing the generic `examples/demos/corpus_census` graph, prompts, schemas, reducer, non-Chaplain adapters, or demo proof; generalizing or replacing the deleted scripts; changing the five older one-shot scripts; performing FR-1013 doctrine/reference work or editing its archive-system link; changing hooks, CI, YAMLGraph runtime, unrelated capabilities, requirements, tests, confession entries, archive tag, or archived repository; deleting or rewriting historical run records.

## Revised acceptance criteria

- [ ] AC-01: Before merge, `docs/census/chaplain-postmerge.run.json` is tracked on main and its parsed JSON has `fr == "FR-1012"`, `step == "post-merge witness"`, `main_head == "36591389e2fdfedf9ba5ae6362effad1c64cd06e"`, `worktree_sync == "ok"`, empty `git_ls_files_chaplain`, `untracked_files_left_in_chaplain == 10`, `now_py_rc == 0`, `now_py_mentions_chaplain is false`, and `all_checks_pass is true`. FR-1012's implementation record names the committed follow-up and witness outcome with no pending post-merge field, records that all 10 observed files were `__pycache__/*.pyc` removed by hand, and FR-1016 records the corrective commit as an ancestor of HEAD. The JSON remains byte-unchanged.
- [ ] AC-02: `git merge-base --is-ancestor "3f3fe6c6" HEAD` exits 0; FR-1013 has not been enforced concurrently and is rebased onto the eventual FR-1016 merged head before its own enforcement.
- [ ] AC-03: `git ls-files -- scripts/chaplain_census.py scripts/chaplain_archive.sh scripts/chaplain_postmerge_witness.sh` prints nothing at GREEN and merged HEAD.
- [ ] AC-04: `git ls-files -- examples/demos/corpus_census/adapters/chaplain_adapters.py examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml examples/demos/corpus_census/adapters/chaplain_rubric.md` prints nothing; the changed-path set under `examples/demos/corpus_census/` is exactly those four deletions.
- [ ] AC-05: `tests/unit/test_fr1012_chaplain_removed.py` contains the exact tooling-absence witness and passes; the changed-path set under `tests/` is exactly that modified witness plus deletion of `test_fr1012_chaplain_census.py`, `test_fr1012_chaplain_archive.py`, and `test_fr1012_chaplain_postmerge_witness.py`.
- [ ] AC-06: Parsed CAP-264 has `fr == "FR-1012, FR-1016"`; both capability and REQ-YG-666 module lists equal `["tests/unit/test_fr1012_chaplain_removed.py"]`; its description and requirement name no deleted script or adapter as a live route; the requirement retains the absent-runtime, immutable archive identities, and enacted census-set claims.
- [ ] AC-07: `git diff --exit-code "3f3fe6c6"...HEAD -- docs/census/` exits 0.
- [ ] AC-08: `docs/archive/chaplain.md` identifies commit `36591389` as the last complete source for each deleted top-level script via valid `git show 36591389:<path>` commands, distinguishes those paths from the `.chaplain` subtree archive, and describes only the recoverable skeleton named in the FR. No other existing archive-note content changes.
- [ ] AC-09: `python scripts/aggregate_capabilities.py` followed by `git diff --exit-code -- ARCHITECTURE.md` exits 0; `python scripts/validate_capabilities.py --strict`, `python scripts/req_coverage.py --strict`, `lint-imports`, `ruff check tests/unit/test_fr1012_chaplain_removed.py`, and `pytest tests/unit/test_fr1012_chaplain_removed.py -q --no-cov` pass.
- [ ] AC-10: Identical `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` runs are recorded from clean Windows worktrees at `3f3fe6c6` and final HEAD; the record names both commits and both failed/error node-ID sets, and the set at HEAD minus the set at `3f3fe6c6` is empty. The removal PR's required Linux CI is green.
- [ ] AC-11: RED and GREEN are separate commits; RED fails only the new absence/module assertions and was committed with `SKIP=pytest`; every later implementation commit passes the focused checks. The implementation record explicitly records that the original before-RED prerequisite was missed and that round-two authority covers closure only.
- [ ] AC-12: On final PR HEAD, `git diff --name-only $(git merge-base origin/main HEAD)...HEAD`, equivalently `gh pr diff <n> --name-only`, contains only D-1 through D-7 surfaces: the ten deleted paths; `tests/unit/test_fr1012_chaplain_removed.py`; `capabilities/CAP-264-chaplain-runtime-retired.yaml`; generated `ARCHITECTURE.md`; `docs/archive/chaplain.md`; one `changelog/unreleased/` removal fragment naming the three scripts; `docs/confessions.md`; the FR-1012 and FR-1016 record updates; and one `docs/diary/` Distill entry containing `**Seed:**`. The implementation record names the actual PR-base SHA, PR-head SHA, command, and output.
- [ ] AC-13: Parsed headings in `docs/confessions.md` contain none of `CONF-462`, `CONF-463`, `CONF-464`, or `CONF-465`; its merge diff deletes exactly those four complete confession blocks and changes no other block; `python scripts/noqa_coverage.py` exits 0.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 and the revised acceptance criteria must be folded into the committed FR before authority activates. | GATE |
| C-2 | The FR-1012 implementation record must be corrected as specified by AC-01 before FR-1016 merges; the immutable post-merge JSON must not be rewritten to manufacture a zero. | GATE |
| C-3 | FR-1016 and FR-1013 may not be enforced concurrently; FR-1016 merges first, and FR-1013 must consume its merged head before editing the shared archive note. | GATE |
| C-4 | `docs/census/`, the archive tag, and the archived repository are immutable evidence; any required change to them stops enforcement and returns the FR to judgement. | GATE |
| C-5 | Any consumer of a proposed deletion beyond CAP-264, `docs/archive/chaplain.md`, `docs/confessions.md`, and the named direct tests stops enforcement and returns the FR to judgement. | GATE |
| C-6 | AC-10, AC-12, and AC-13 must be evidenced on final PR HEAD; unchecked or forecast evidence cannot be treated as passed. | GATE |
| C-7 | A human must review this round-two draft and the exact final deletion/evidence-preservation diff, explicitly accept preservation of the observed 10-cache witness value, and record that decision in the FR before merge. | GATE |

Authority granted: after C-1 through C-7 are satisfied, FR-1016 may retain the already implemented D-1 through D-6 subtraction, complete only D-7 and the specified record corrections, and merge the exact frozen surfaces; no fresh tooling, generalized replacement, doctrine sweep, or evidence rewrite is authorized.
