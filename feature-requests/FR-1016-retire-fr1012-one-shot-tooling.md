# Feature Request: Retire the FR-1012 one-shot tooling (census driver, archive script, post-merge witness)

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
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
git history — no external alternatives exist to survey).
**Prior art:**
[FR-1012-chaplain-subtree-archive-and-removal.md](FR-1012-chaplain-subtree-archive-and-removal.md)
— created the three scripts as Steps 0, 1 and 3 of the removal; this FR
retires them now that all three steps are DONE (merge `36591389`, witness
record `docs/census/chaplain-postmerge.run.json`). FR-1012's AC-19 required
them to be "checked in with focused tests"; that criterion was for the
removal's audit trail, which the committed run records now carry.
[FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) —
the governing plan; it names four phases and no phase for retiring the
retirement machinery, which is the gap this FR fills.
[FR-1013-chaplain-doctrine-sweep.md](FR-1013-chaplain-doctrine-sweep.md) —
docs-only by its judgement (SPLIT, round 2); this FR is the code-deletion
sibling it cannot carry. Sequenced after FR-1013 or in parallel; no shared
files.
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

## Acceptance Criteria

- [ ] AC-01: `git ls-files scripts | grep chaplain_` prints nothing on the merged head.
- [ ] AC-02: `git ls-files examples/demos/corpus_census/adapters | grep chaplain` prints nothing; the generic `corpus_census` graph, its other adapters and its demo proof are unchanged (`git diff --stat` shows no other file under `examples/demos/corpus_census/`).
- [ ] AC-03: `tests/unit/test_fr1012_chaplain_removed.py` passes on the merged head and contains the new tooling-absent witness; the three deleted test files are gone; no other test file changes.
- [ ] AC-04: CAP-264 `modules:` lists exactly `tests/unit/test_fr1012_chaplain_removed.py`; REQ-YG-666's description names no script; `fr:` lists FR-1012 and FR-1016; `validate_capabilities --strict` and `req_coverage --strict` pass.
- [ ] AC-05: `docs/census/` is byte-identical before and after (`git diff --stat <base> HEAD -- docs/census/` is empty).
- [ ] AC-06: `docs/archive/chaplain.md` names `36591389` as the last commit holding the three scripts and says what a future split FR would lift from them.
- [ ] AC-07: RED and GREEN are separate commits; the removal PR's Linux CI is green; the Windows non-slow suite shows no failure new against the main baseline.
- [ ] AC-08: A `changelog/unreleased/` fragment of type `removal` names the three scripts.

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

## Judgement (pending)

Rendered by the sole route (`scripts/judge.sh`), folded into
`FR-1016-retire-fr1012-one-shot-tooling.judgement.md`.
