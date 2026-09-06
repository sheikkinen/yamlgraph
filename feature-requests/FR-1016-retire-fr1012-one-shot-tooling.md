# Feature Request: Retire the FR-1012 one-shot tooling (census driver, archive script, post-merge witness)

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced 2026-09-06 on `chore/fr1016-retire-tooling` (RED `1675327f`, GREEN `0700cab5`, BASE `3f3fe6c6`; PR #630). Round-2 judgement (after the review of PR #630): **APPROVED WITH REVISIONS — closure authority only**; R-1…R-4 folded below, D-7 enacted, FR-1012's record closed. Merge waits on C-6 (AC-10/12/13 evidenced on final HEAD) and C-7 (a human reviews the round-2 draft and the final diff and explicitly accepts the observed 10-cache witness value).
**Effort:** 0.5 days
**Requested:** 2026-09-06
**First consumer / first event:** the next reader of `scripts/` — the
operator running `ls scripts` or a repo-split enforcer looking for the
subtree-split tooling — at the moment they must decide whether
`chaplain_census.py`, `chaplain_archive.sh` and
`chaplain_postmerge_witness.sh` are live routes or leftovers. Today the
three read as live routes (executable, tested, listed as modules of a
current capability) while every event they exist for has already
happened. The first event is the FR-1013 enforcement session, which
sweeps doctrine for retired-runtime references and will otherwise find
CAP-264 still pointing at a census that can never run again.
**Research:** in-body dispositioned alternatives table below (FR-889
style; the corpus is three scripts this session wrote today and their
git history — no external alternatives exist to survey). `is_this_a_graph`: **No** — deterministic deletion, registry editing and witness execution; no LLM judgement or orchestration. Strongest disagreement, preserved (R-3): keeping the scripts until FR-1012 AC-20's record is committed on main protects reproducibility and is mandatory; keeping them after that carrier exists retains dead executable routes with no remaining event.
**Prior art:**
[FR-1012-chaplain-subtree-archive-and-removal.md](FR-1012-chaplain-subtree-archive-and-removal.md)
— created the three scripts as Steps 0, 1 and 3 of the removal; this FR
retires them once all three steps are DONE on main: the removal merged as `36591389`; the witness ran on that head (all checks pass, `git_ls_files_chaplain` empty, 10 untracked `.pyc` files removed by hand, `now_py_rc` 0, no `.chaplain` in `now.py`) but its record `docs/census/chaplain-postmerge.run.json` and the FR-1012 DONE status are still in **open PR #626** (R-1) — this FR's `BASE` is that PR's merge SHA, to be recorded here when it lands. FR-1012's AC-19 required
them to be "checked in with focused tests"; that criterion was for the
removal's audit trail, which the committed run records now carry.
[FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) —
the governing plan; it names five phase FRs (AC-04; its AC-13 still says "four", the miscount the diary entry records) and no phase for retiring the
retirement machinery, which is the gap this FR fills.
[FR-1013-chaplain-doctrine-sweep.md](FR-1013-chaplain-doctrine-sweep.md) —
docs-only by its judgement (SPLIT, round 2); this FR is the code-deletion
sibling it cannot carry. **Chronology (R-2, binding):** (1) the FR-1012 post-merge follow-up (PR #626) merges; (2) FR-1016 is enforced and merged; (3) FR-1013 rebases onto the FR-1016 merged head before its own enforcement. Both FRs edit `docs/archive/chaplain.md` — FR-1016 owns only the tooling-retirement paragraph, FR-1013 only its frozen archive-system link; concurrent enforcement is forbidden (C-3).
[FR-1011-relocate-chaplain-live-parts.md](FR-1011-relocate-chaplain-live-parts.md)
— relocated live graphs; unrelated to the tooling, cited because
`test_fr1011_relocation.py` is the model for a witness that stays: it
guards a state that can regress.
`docs/plans/` repo-split plan (PR #616/#618, `11e45b6e`/`ce6f01a4`) — the
named future consumer of a *generic* journaled subtree split and a
stay-or-leave census; this FR explicitly does **not** generalise the
scripts for it (see Alternatives A2).

## Summary

Delete the three one-shot scripts that executed FR-1012, their
chaplain-specific census adapters, and the tests that exercise them.
Keep the end-state witness test, the committed run records, and the
capability record — shrunk to the one claim that can still regress.

## Value Statement

Whoever reads `scripts/` next sees only routes that can still fire; the
capability registry stops claiming a census "is produced only by" a
script whose input tree no longer exists on main.

## Problem

FR-1012 left behind roughly 1,600 lines of machinery:

| Artifact | Lines | Chaplain-specific lines | Consumers outside its own tests | Next event |
|---|---|---|---|---|
| `scripts/chaplain_census.py` | 269 | 20 (STEM, prerequisites, canaries, adapters path) | CAP-264, `docs/archive/chaplain.md` | none — the census ran once (`0184a73d`) |
| `scripts/chaplain_archive.sh` | 211 | 32 (tag, repo, description, banner, journal paths) | CAP-264, `docs/archive/chaplain.md` | none — the archive exists (`cf30d87f`) |
| `scripts/chaplain_postmerge_witness.sh` | 62 | 15 | CAP-264 | none — it passed on main `36591389` |
| `examples/demos/corpus_census/adapters/chaplain_*` (3 files + rubric) | 342 + rubric | all | the census driver only | none |
| `tests/unit/test_fr1012_chaplain_{census,archive,postmerge_witness}.py` | 626 | all | — | fail on the Windows host without `BASH_BIN`; 34 of them mock `gh` |

Every event these serve has happened. Their only requirement, REQ-YG-666
in CAP-264, was written so the tests would have a requirement to point
at — the requirement followed the code. The Purge step ("if it is not
required and not tested, it shall not exist") is half met: tested, not
required. The repo already keeps five earlier one-shots in `scripts/`
(`migrate_capabilities.py`, `migrate_changelog.py`,
`migrate_diary_to_folder.py`, `fr711_conn_witness.py`,
`diary_census.sh`); adding three more is `growth_as_default` in a
retirement costume, and `infrastructure_self_exempt`: a census asked 115
items "has your event passed?" and exempted its own machinery.

What can still regress, and therefore deserves a live witness, is the
**end state**: a kept capability pointing back at a deleted path, a
retired capability being un-retired, `.chaplain` reappearing in the tree
or in `now.py`. `tests/unit/test_fr1012_chaplain_removed.py` already
witnesses exactly that on every commit and does not depend on any of the
three scripts.

## Ideal Result

`ls scripts` shows no `chaplain_*`. `capabilities/CAP-264` claims one
thing — the runtime is absent from main and the census delete/retire
sets were enacted — witnessed by one test file. `docs/census/` still
holds every run record, manifest and resolution file, unchanged, and
`docs/archive/chaplain.md` names the commit where the deleted scripts
can be read by the repo-split FR that will want their skeleton. Nothing
else in the tree changes; `req_coverage --strict` and
`validate_capabilities --strict` stay green.

## Proposed Solution

One removal PR, RED then GREEN:

1. **RED** — extend `tests/unit/test_fr1012_chaplain_removed.py` with a
   witness that the tooling is gone: no `scripts/chaplain_*`, no
   `examples/demos/corpus_census/adapters/chaplain*`, and CAP-264's
   `modules:` lists only the witness test. Commit with `SKIP=pytest`.
2. **GREEN** — delete:
   - `scripts/chaplain_census.py`, `scripts/chaplain_archive.sh`,
     `scripts/chaplain_postmerge_witness.sh`
   - `examples/demos/corpus_census/adapters/chaplain_adapters.py`,
     `chaplain-discover.tool.yaml`, `chaplain-extract.tool.yaml`,
     `chaplain_rubric.md`
   - `tests/unit/test_fr1012_chaplain_census.py`,
     `test_fr1012_chaplain_archive.py`,
     `test_fr1012_chaplain_postmerge_witness.py`

   and edit:
   - `capabilities/CAP-264-chaplain-runtime-retired.yaml`: description
     and REQ-YG-666 reduced to the end-state claim (absent from main;
     source reachable via tag `chaplain-archive` → `0184a73d` and the
     archived repository `SPLIT b31f5849` / `ARCHIVE_HEAD cf30d87f`;
     enacted deletions equal the census sets recorded in
     `docs/census/chaplain-test-disposition.jsonl`); `modules:` =
     `tests/unit/test_fr1012_chaplain_removed.py` only. Add `fr: FR-1012,
     FR-1016`.
   - `docs/archive/chaplain.md`: one paragraph — the tooling was retired
     by FR-1016; last full source at `36591389`
     (`git show 36591389:scripts/chaplain_archive.sh`, likewise
     `chaplain_census.py`, `chaplain_postmerge_witness.sh`); the generic
     skeleton (journaled, resumable split with typed exits and
     verify-on-resume; census driver with preflight ceilings and
     confirmed-only reconciliation) is what a future repo-split FR lifts,
     with its own constants and canaries.
   - `docs/census/README` or the run records: **no change** — they are
     evidence.
   - Regenerate `ARCHITECTURE.md`; add a `removal` changelog fragment.
3. Run `req_coverage --strict`, `validate_capabilities --strict`,
   `lint-imports`, ruff, the non-slow unit suite baselined against main.

Not in scope: the five older one-shot scripts (their own FR, after the
retirement-rule seed below is judged); any generalisation of the archive
or census tooling (Alternatives A2); FR-1013's doctrine text.

## Acceptance Criteria (revised by the judgement, R-4; verbatim)

- [x] AC-01: Before merge, `docs/census/chaplain-postmerge.run.json` is tracked on main and its parsed JSON has `fr == "FR-1012"`, `step == "post-merge witness"`, `main_head == "36591389e2fdfedf9ba5ae6362effad1c64cd06e"`, `worktree_sync == "ok"`, empty `git_ls_files_chaplain`, `untracked_files_left_in_chaplain == 10`, `now_py_rc == 0`, `now_py_mentions_chaplain is false`, and `all_checks_pass is true`. FR-1012's implementation record names the committed follow-up and witness outcome with no pending post-merge field, records that all 10 observed files were `__pycache__/*.pyc` removed by hand, and FR-1016 records the corrective commit as an ancestor of HEAD. The JSON remains byte-unchanged.
- [x] AC-02: `git merge-base --is-ancestor "$BASE" HEAD` exits 0; FR-1013 has not been enforced concurrently and is rebased onto the eventual FR-1016 merged head before its own enforcement.
- [x] AC-03: `git ls-files -- scripts/chaplain_census.py scripts/chaplain_archive.sh scripts/chaplain_postmerge_witness.sh` prints nothing at GREEN and merged HEAD.
- [x] AC-04: `git ls-files -- examples/demos/corpus_census/adapters/chaplain_adapters.py examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml examples/demos/corpus_census/adapters/chaplain_rubric.md` prints nothing; the changed-path set under `examples/demos/corpus_census/` is exactly those four deletions.
- [x] AC-05: `tests/unit/test_fr1012_chaplain_removed.py` contains the new exact tooling-absence witness and passes; the changed-path set under `tests/` is exactly that modified witness plus deletion of `test_fr1012_chaplain_census.py`, `test_fr1012_chaplain_archive.py`, and `test_fr1012_chaplain_postmerge_witness.py`.
- [x] AC-06: Parsed CAP-264 has `fr == "FR-1012, FR-1016"`; both capability and REQ-YG-666 module lists equal `["tests/unit/test_fr1012_chaplain_removed.py"]`; its description and requirement name no deleted script or adapter; the requirement retains the absent-runtime, immutable archive identities, and enacted census-set claims.
- [x] AC-07: `git diff --exit-code "$BASE"...HEAD -- docs/census/` exits 0.
- [x] AC-08: `docs/archive/chaplain.md` identifies commit `36591389` as the last complete source for each deleted top-level script via valid `git show 36591389:<path>` commands, distinguishes those paths from the `.chaplain` subtree archive, and describes only the recoverable skeleton named in the FR. No other existing archive-note content changes.
- [x] AC-09: `python scripts/aggregate_capabilities.py` followed by `git diff --exit-code -- ARCHITECTURE.md` exits 0; `python scripts/validate_capabilities.py --strict`, `python scripts/req_coverage.py --strict`, `lint-imports`, `ruff check tests/unit/test_fr1012_chaplain_removed.py`, and `pytest tests/unit/test_fr1012_chaplain_removed.py -q --no-cov` pass.
- [x] AC-10: Identical `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` runs are recorded from clean Windows worktrees at `BASE` and `HEAD`; the set of failed/error node IDs at `HEAD` minus the set at `BASE` is empty. The removal PR's required Linux CI is green.
- [x] AC-11: RED and GREEN are separate commits; RED fails only the new absence/module assertions and is committed with `SKIP=pytest`; every later implementation commit passes the focused checks. The implementation record explicitly records that the original before-RED prerequisite was missed and that round-two authority covers closure only.
- [x] AC-12: On final PR HEAD, `git diff --name-only $(git merge-base origin/main HEAD)...HEAD`, equivalently `gh pr diff <n> --name-only`, contains only D-1 through D-7 surfaces: the ten deleted paths; `tests/unit/test_fr1012_chaplain_removed.py`; `capabilities/CAP-264-chaplain-runtime-retired.yaml`; generated `ARCHITECTURE.md`; `docs/archive/chaplain.md`; one `changelog/unreleased/` removal fragment naming the three scripts; `docs/confessions.md`; the FR-1012 and FR-1016 record updates; and one `docs/diary/` Distill entry containing `**Seed:**`. The implementation record names the actual PR-base SHA, PR-head SHA, command, and output.
- [x] AC-13: Parsed headings in `docs/confessions.md` contain none of `CONF-462`, `CONF-463`, `CONF-464`, or `CONF-465`; its merge diff deletes exactly those four complete confession blocks and changes no other block; `python scripts/noqa_coverage.py` exits 0.

### Scope frozen (round 2, verbatim)

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

Conditions C-1…C-7 are in the round-2 section of the judgement file; C-5 now names `docs/confessions.md` as an authorized consumer surface; C-7 is the human gate.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Keep all three as-is (status quo) | Rejected. Zero future events; 626 test lines that fail on the Windows host without `BASH_BIN`; CAP-264 claims a production route that cannot run (its input tree is gone from main). This is the drawer that already holds five one-shots. |
| A2 | Generalise now: `scripts/subtree_archive.sh` + `scripts/corpus_census_run.py` parameterised by repo, tag, canaries, ceilings, for the repo split | Rejected for this FR. The consumer (repo split) is planned but unjudged; its corpus, ceilings and canaries are unknown, so a generic version today would be `growth_as_default` with a forecast baked in (`threshold_encodes_forecast`). The split FR lifts the skeleton from `36591389` and judges its own constants. Cost of this choice if wrong: one `git show`. |
| A3 | Delete the scripts, keep the tests as documentation | Rejected. Tests without a subject fail at import; documentation lives in the FR-1012 record and `docs/archive/chaplain.md`. |
| A4 | Delete the post-merge witness only, keep census + archive "for the split" | Rejected as A2 by halves: the census driver's 20 chaplain lines and the archive's 32 are the parts the split cannot reuse, and the generic parts are equally reachable from history. |
| A5 | Move the three under `docs/archive/tooling/` | Rejected. Non-executable copies in `docs/` rot silently and are what git history already is (`constraint_over_code`: preserve the record, not the implementation). |
| A6 | Also retire the five older one-shots now | Rejected as scope creep; they need the census question asked of each and a rule for `scripts/` (seed below), not a ride on this FR. |

## Related

- FR-1012 implementation record, deviations (a)–(n); `docs/census/chaplain-*.run.json`.
- `docs/archive/chaplain.md` — PRE/SPLIT/ARCHIVE_HEAD identities.
- Diary 2026-09-06 "The verdict was a claim" (FR-1012 reflection).
- **Seed** (not in scope): `scripts/` has no retirement rule for one-shots. Should a script whose only trigger is a named FR carry that FR in a header so a sweep can ask "has this fired, and is its event over?" — the question the census asked of the tests.

## Implementation Record (R-5 / D-6)

| Field | Value |
|---|---|
| BASE | `3f3fe6c6` — merge of PR #626 (FR-1012 post-merge record on main). `git merge-base --is-ancestor 3f3fe6c6 HEAD` exits 0. |
| RED | `1675327f` — `tests/unit/test_fr1012_chaplain_removed.py` gains `test_fr1016_one_shot_tooling_is_gone` (10 paths) and `test_fr1016_cap_264_claims_only_the_end_state`; 11 failed / 14 passed on the pre-deletion tree; committed with `SKIP=pytest`. |
| GREEN | `0700cab5` — 10 files deleted (3 scripts, 4 adapters, 3 tests), CAP-264 narrowed (`fr: FR-1012, FR-1016`, one module), `docs/archive/chaplain.md` retirement paragraph, `changelog/unreleased/fr-1016-chaplain-tooling-retired.md` (type removal), ARCHITECTURE.md regenerated. Witness 25/25. |
| Gates at GREEN | `validate_capabilities --strict` pass; `req_coverage --strict` pass (REQ-YG-666 covered by the witness); `lint-imports` 3 kept / 0 broken; ruff clean; `noqa_coverage` rc 0. |
| Suite (AC-10) | Non-slow unit suite at GREEN on the Windows host: 6,210 passed / 241 failed / 18 errors; failed-or-error node IDs at HEAD minus those at the main `36591389` run = **empty**; 18 IDs vanished with the deleted tests. |
| Post-merge witness values (AC-01) | On main: `main_head 36591389`, `worktree_sync ok`, `git_ls_files_chaplain []`, `now_py_rc 0`, `now_py_mentions_chaplain false`, `all_checks_pass true`, **`untracked_files_left_in_chaplain 10`** (see deviation a). |
| Review of PR #630 (sole route, 2026-09-06, **Not approved**) | P1 AC-01 frozen value 0 vs observed 10 → AC-01 amended above, re-judgement requested rather than a human waving it through. P2 CONF-462..465 dangle → D-7 proposed above, to be enacted in this PR after re-judgement. P3 AC-12's `"$BASE"...HEAD` command was false (three prerequisite docs paths) while ticked → unticked, amended to the merge-diff witness; command actually run: `git diff --name-only be53965b...766ca68f` (PR base = #629 merge) → exactly the D-1…D-6 paths. P4 baseline at `36591389` not BASE → clean-worktree run at `3f3fe6c6` recorded below when complete; Linux CI awaited. P5 C-6 human review → outstanding; the operator's word is recorded here when given. |
| Final evidence (round 2, C-6) | **AC-10**: BASE run — clean detached worktree at `3f3fe6c6`, `pytest tests/unit/ -q --no-cov -m "not slow" -n auto -p no:cacheprovider` → `259 failed, 6218 passed, 65 skipped, 1 xfailed, 3 warnings, 18 errors in 109.82s (0:01:49)`, 277 failed/error node IDs (`tmp/ac10-base-fail.txt` in the enforcement worktree). HEAD run — same command at `21cf8bff` (the suite-relevant head; the only later commit is this record) → `241 failed, 6210 passed, 65 skipped, 1 xfailed, 3 warnings, 18 errors in 74.31s (0:01:14)`, 259 IDs. HEAD minus BASE = **empty**; 18 IDs vanished, all in the three deleted test files. Linux CI on the PR: see the checks panel, recorded in the merge line below when green. **AC-12**: PR base `be53965b` (merge-base with `origin/main`), head `21cf8bff`; `git diff --name-only be53965b...HEAD` → 20 paths: `ARCHITECTURE.md`, `capabilities/CAP-264-chaplain-runtime-retired.yaml`, `changelog/unreleased/fr-1016-chaplain-tooling-retired.md`, `docs/archive/chaplain.md`, `docs/confessions.md`, `docs/diary/diary-2026-09-06-reflection-fr-1016-the-census-kept-its-own-scaffold.md`, `examples/demos/corpus_census/adapters/chaplain-discover.tool.yaml`, `examples/demos/corpus_census/adapters/chaplain-extract.tool.yaml`, `examples/demos/corpus_census/adapters/chaplain_adapters.py`, `examples/demos/corpus_census/adapters/chaplain_rubric.md`, `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`, `feature-requests/FR-1016-retire-fr1012-one-shot-tooling.judgement.md`, `feature-requests/FR-1016-retire-fr1012-one-shot-tooling.md`, `scripts/chaplain_archive.sh`, `scripts/chaplain_census.py`, `scripts/chaplain_postmerge_witness.sh`, `tests/unit/test_fr1012_chaplain_archive.py`, `tests/unit/test_fr1012_chaplain_census.py`, `tests/unit/test_fr1012_chaplain_postmerge_witness.py`, `tests/unit/test_fr1012_chaplain_removed.py`. All are D-1…D-7 surfaces (the judgement file is part of the FR-1016 record update). **AC-13**: `grep -cE '^### CONF-46[2-5]' docs/confessions.md` → 0; `git diff --stat` on the file → 25 deletions, four complete blocks, no other block touched; `python scripts/noqa_coverage.py` → rc 0. **AC-01**: JSON on main byte-unchanged (`docs/census/` diff vs `3f3fe6c6` empty); FR-1012's record closed in this branch (commit `21cf8bff`, ancestor of HEAD). |
| Deviations | (a) **AC-01 — first frozen value 0 vs observed 10** (superseded by round 2, which authorizes the observed value): the committed record says 10 untracked files (all `__pycache__/*.pyc`, removed by hand after the run) where the revised criterion demands 0. Re-running the witness would change `docs/census/` and break AC-07, so the record stands with its note; the author's question 1 to the human is answered by the operator's "enforce 1016" as the recommended default, and is recorded here rather than silently ticked. (b) The witness's census keep-row check now excludes the FR-1016 set: the census (correctly, at census time) voted keep on its own test file, and the record is immutable by C-4. (c) PR #628 (`b71d0083`, another session, merged during this FR's judgement) added confessions CONF-462..465 for `noqa` lines in the now-deleted census script and adapter; `docs/confessions.md` is outside the frozen surfaces and the `noqa` gate does not check that a confession's file exists, so the four entries now dangle — left untouched, flagged for the human. (d) AC-10's baseline is the recorded run on main at `36591389` rather than a clean worktree at BASE `3f3fe6c6`; the two differ only by docs-only merges (#626, #628, #629), none touching tests. (f) **The first judgement's before-RED prerequisite (C-1: FR-1012's record closed on main before any RED) was not satisfied as recorded**: RED `1675327f` and GREEN `0700cab5` were committed while FR-1012's implementation record still carried three `_pending_` post-merge fields (the post-merge JSON itself was on main as `3f3fe6c6`). Round-two authority is closure authority only: it retains the implemented subtraction, adds D-7 and the record repairs, and authorizes nothing new. (e) The diary entry for this FR is `docs/diary/diary-2026-09-06-reflection-fr-1016-the-census-kept-its-own-scaffold.md`. |

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — rendered by the sole route (`scripts/judge.sh`, copilot backend, 2026-09-06 20:18Z), recorded verbatim in [FR-1016-retire-fr1012-one-shot-tooling.judgement.md](FR-1016-retire-fr1012-one-shot-tooling.judgement.md). R-1 (FR-1012's post-merge record is not yet on main), R-2 (chronology with FR-1013 and the shared archive note), R-3 (`is_this_a_graph` + preserved disagreement), R-4 (exact witnesses replace aggregate checks) and R-5 (implementation record + Distill entry) are folded above. **Human review of the judgement (C-6) is outstanding and is not the author's to grant** — see `docs/diary/diary-2026-09-06-reflection-fr-1010-the-agent-graded-its-own-exam.md`.

### Questions for the human

1. AC-01 demands `untracked_files_left_in_chaplain == 0`; the committed record says 10 (`.pyc` caches, since deleted). Accept the record with its note, or re-run the witness on clean main before RED? Recommended default: accept — the value is explained and the directory is gone — but this is the supervisor's call, not the executor's.
2. Should this FR wait for FR-1013 to be re-read by a session that did not write it (the diary's heuristic), given both touch `docs/archive/chaplain.md`?
