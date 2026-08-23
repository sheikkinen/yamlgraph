# Feature Request: scripture-dev Salvage and Retirement

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 day
**Requested:** 2026-08-23
**Parent:** FR-864 (SPLIT) — child D per R-3
**First consumer / first event:** the next agent looking for the
governance upstream. Today it finds two — this repo and a five-month-old
copy — and cannot tell which is authoritative. First event: running
`salvage_classify` over `scripture-dev` and reading the disposition
list.

**Prior art:** **FR-207** created `scripture-dev` and is the FR this one
closes out; it must be updated, not contradicted — its goal was right,
its mechanism decayed. **FR-865** consumes the *lift* output but does
not depend on this FR completing. **FR-866** is non-overlapping:
`salvage_classify` classifies a source repo's assets for retirement,
which is not target tailoring. **FR-858** (retire committed fr-board) is
the nearest precedent for a retirement FR in this repo. No REJECTED
prior art occupies this territory.

## Summary

Classify every artifact in `scripture-dev` against this repo's current
equivalent, lift what is genuinely missing here, update FR-207 with the
outcome, and archive the repo — with explicit human approval before any
GitHub state changes.

## Value Statement

One authoritative governance upstream instead of two, and whatever the
old one knew that the new one forgot is recovered before the lights go
out.

## Problem

`scripture-dev` (FR-207) is a stale distributor:

| | value |
|---|---|
| last commit | 2026-03-29 (~5 months) |
| pre-commit hooks | 16, vs 45 here |
| hook scripts / templates / scripts | 8 / 3 / 3 |
| `.pre-commit-hooks.yaml` (provider manifest) | none |
| its own `scripture.yaml` | `project_name: my-minesweeper` |
| consumers | `my-minesweeper`, `my-minesweeper2` |
| contributions back | zero |

Leaving it in place is an active hazard: it is the repo whose *name*
says it holds the process, and it is the wrong answer.

Not all of it is dead. It was rendered from this repo at a point when
some hooks may have been simpler or better factored, and it holds
`render.sh` plus a `scripture.yaml` parameterisation idea that this repo
has no equivalent of. That must be checked, not assumed either way.

## Ideal Result

A dated disposition table covering **every** artifact with no
"unknown" rows; anything worth keeping already merged here with
attribution; FR-207 closed with the outcome and the reason its mechanism
failed; the repo archived read-only so its history and FR record survive
while its name stops competing.

## Proposed Solution

### `salvage_classify` graph

- python node enumerates the target ref's tracked files (the count is
  determined by the run, not asserted in advance)
- **map** over each artifact → `{path, category, verdict:
  duplicate|lift|obsolete, rationale, yamlgraph_equivalent, target_path}`
- for `duplicate`, the equivalent path here must exist (validated
  mechanically after the run)
- merge → `tmp/ramp/salvage-disposition.{md,json}`, count-in ==
  count-out over enumerated files

Authored through the governed route; writes drafts only; no commits
(parent C-3, C-7).

### Lift and close

1. Human reviews the disposition list.
2. `lift` items are merged into this repo's ramp assets (FR-865's
   manifest) with attribution in the commit message.
3. FR-207 gains an outcome section: implemented, unconsumed, superseded
   by FR-864's family, mechanism diagnosis (`asset_source_must_be_a_consumer`).
4. **Human approves**; then the repo is archived on GitHub.

## Acceptance Criteria

Exhaustive for this surface alone.

- [ ] AC-01: the classified ref (commit SHA) of `scripture-dev` is
      recorded in this FR before the run.
- [ ] AC-02: `salvage_classify` passes `yamlgraph graph lint` and was
      authored through the governed route, report retained.
- [ ] AC-03: **every** enumerated tracked file receives a verdict; zero
      `unknown`; count-in == count-out reported.
- [ ] AC-04: every `duplicate` verdict names an equivalent path that
      exists in this repo; a test validates each.
- [ ] AC-05: every `lift` verdict names a concrete destination path
      under this repo's ramp assets.
- [ ] AC-06: the disposition draft is read raw before any lift decision
      is executed — ≥ 3 entries quoted in the FR with a concrete detail
      each (`read_raw_output_first`).
- [ ] AC-07: lifted artifacts are committed here with attribution to
      `scripture-dev` and its SHA.
- [ ] AC-08: if the lift list is empty, the FR states that explicitly
      with the rationale — an empty result is a finding, not a failure.
- [ ] AC-09: FR-207 is updated with the outcome, the mechanism
      diagnosis, and a pointer to FR-864's family.
- [ ] AC-10: **archive happens only after recorded human approval**;
      the approval line is in this FR before the action (parent C-4).
- [ ] AC-11: `scripture-dev` is archived, **not deleted**; its history
      and FR record remain readable, verified after the fact.
- [ ] AC-12: `my-minesweeper` and `my-minesweeper2` are checked for
      dependence on it; if either would break, the FR records the impact
      and the archive still proceeds (archive is read-only, not removal).
- [ ] AC-13: no secrets or token-bearing content are lifted; the diff is
      scanned.

## Risks

**Archiving something still in use.** Archive is read-only, not
deletion, and AC-12 checks the two known consumers. Reversible by the
owner at any time.

**Classifying by filename rather than content.** A hook with the same
name may differ materially after five months. The rationale field and
AC-04's equivalence validation force the comparison to be stated.

**Lifting stale code back into a current repo.** The `lift` bar is
"missing here and still correct", not "different". AC-06's raw read is
the check against a plausible-sounding disposition list.

**FR-207 was judged APPROVED and implemented.** Closing it out is not a
reversal of that judgement — the FR delivered what it promised. What
failed was the mechanism's durability, and that is the finding to
record, not a verdict on the original decision.

## Alternatives Considered

- **Leave it dormant.** Rejected: a repo named for the process, holding
  a stale third of it, is a trap for the next agent — and unproposed
  accretion is the risk the operator asks to have surfaced.
- **Revive it as the hook-provider upstream.** Rejected in FR-864: a
  distributor that is not a consumer has nothing forcing it to stay
  true; that is precisely how it reached this state.
- **Delete it.** Rejected: it holds FR-207's record and the
  counter-example's evidence, which this family's diaries cite.
- **Classify by hand.** ~30 artifacts × "does this exist here, better?"
  is a classification fan-out, and by-hand is what has not happened for
  five months.

## Related

- `feature-requests/FR-864-ramp-spike-to-governed.md` (parent, SPLIT) and its judgement
- `feature-requests/FR-207-standalone-scripture-methodology-repo.md` — the FR being closed out
- `feature-requests/FR-865-ramp-installer.md` — destination for lifted assets
- `feature-requests/FR-858-retire-committed-fr-board.md` — retirement-FR precedent
- `docs/diary/diary-2026-08-23-process-transfers-by-practice.md` — the mechanism diagnosis
