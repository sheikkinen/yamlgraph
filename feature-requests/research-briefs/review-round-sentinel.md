# Problem brief: the review loop has no terminating condition and no countable record

**Prior art:** FR-1022 (judge round sentinel: `scripts/judge.sh` counts
`**Verdict:**` lines in the FR's adjacent `.judgement.md`; at two, the third
run writes a fixed `REJECTED` verdict and exits 77 with no model call — the
direct precedent, on the sibling wrapper); NC-413 / NC-414 (review and judge
sole routes; lineage sentinels `REVIEW_EXECUTION` / `JUDGE_EXECUTION`;
"doctrine states, wrapper enforces"); NC-412 (the adapter prompt is a thin
pointer and may carry no doctrine); FR-960 (per-backend-per-FR judge draft
path — the review draft `tmp/draft-review.md` never received the same
treatment); FR-1004 (retired the outsider ledger: a committed file every PR
appended to conflicted pairwise; "the posted PR comment is the only durable
record of a run"); FR-865 (ramp mirror: `.github/skills/review-pr/doctrine.md`
must stay byte-identical to `ramp/assets/tier2/github/skills/review-pr/doctrine.md`
or `test_mirror_exact_entries_match_live_bytes` fails — the same test PR #633
is failing on for the judge doctrine right now); `reference/command-book.md`
entry 11 (`review`: transient `tmp/draft-review.md`; durable = fix commits /
disposition comments on the PR); FR-1013 (REJECTED after four judge rounds and
three review rounds); `docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`
and `docs/diary/2026-09-06-reflection-fr-1022-the-count-the-model-cannot-argue-with.md`
(the latter's Seed asks this exact question).

## Problem statement

`scripts/review.sh <pr> <fr>` launches the review graph on the same PR and
the same FR any number of times. The reviewer is a model; it reads the whole
diff plus FR plus judgement and returns findings roughly proportional to the
text. Each fold makes the PR and FR longer; the longer artifact yields a new
list. The review→judge ping-pong is the other half of the FR-1013 loop: a
review finding of scope creep triggers a re-judge, whose revisions trigger a
re-review. FR-1022 capped the judge half at two model rounds per FR file.
The review half is uncapped.

Unlike the judge, the review has no countable record at all. The judge's
rounds accumulate as `**Verdict:**` lines in a committed `.judgement.md`
adjacent to the FR. The review draft goes to one fixed, git-ignored path,
`tmp/draft-review.md`, that the next run of any PR deletes (`rm -f`) — not
per PR, not per FR, not committed. The command book names the PR comment as
the durable review record, but FR-1013's three review rounds produced zero
review comments and zero GitHub review objects on PR #627; the findings
were folded into FR prose as "Review of PR #627 … folded" paragraphs. The
only signal of how many times a PR has been reviewed is a human reading FR
prose. A wrapper cannot count prose.

So the question has two parts that must be answered together: where does
a review round leave a mark that a shell script can count, without
recreating the shared-file contention FR-1004 retired; and at what count,
with what fixed sentence, does the wrapper stop launching the model and
hand the merge decision back to the human — the decision that the review
doctrine already says is the human's.

## Classification

enforcement/latency-critical

## Constraints

- NC-412 / NC-413: no doctrine in `adapters/prompts/review.yaml`; any rule
  is stated in `.github/skills/review-pr/doctrine.md` or the adapter README
  and enforced in `scripts/review.sh`, following the FR-1022 shape.
- FR-865: `.github/skills/review-pr/doctrine.md` is a byte-exact mirror of a
  ramp asset. Editing one without the other fails the unit suite. FR-1022's
  own PR (#633) is failing CI on exactly this for the judge doctrine.
- The mechanism must not be a model call and must key on a committed or
  wrapper-owned artifact, never on agent discipline alone (an agent that
  can skip the recording step has an unlimited loop).
- The count must be per FR file, not per PR number: FR-1013's three review
  rounds spanned PR #617 and PR #627.
- No override input. The human exits already exist: merge on the human's
  own read, or close the PR and re-file the FR shorter (FR-1013 → FR-1019).
- The verdict taxonomy is closed: `Merge-approved` or `Not approved` on line
  one (`review.template.md`, and `review.sh` checks line one). The sentinel
  must use one of the two (FR-1022 R-1 precedent: `REWRITE` was refused).
- The review graph must never comment, approve, merge, or commit. Whether
  the wrapper (not the graph) may append to a tracked file is open.
- FR-1004 precedent: a committed file that every PR mutates is the
  contended artifact class to avoid. A per-FR file mutated only by that
  FR's PRs is the class the repo already accepts (`.judgement.md`).
- Existing guard precedence must hold: usage (64), FR missing (66),
  re-entry (70) before the new check; lock (73/75) after it; artifact
  contract (65) unchanged.

## Witnessed incidents

- FR-1013 (2026-09-06): review 1 on PR #617 — 7 blocking findings; review 2
  on PR #627 head `59b11461` — 6 findings; review 3 — 1 finding. Interleaved
  with judge rounds 2, 3, 4. Zero review comments posted on either PR; the
  record is FR prose. Operator closed PR #627 unmerged after review 3.
- FR-1004 (2026-09-05): status line records "three review rounds enforced"
  on PR #602. The record is a status-line phrase.
- `scripts/review.sh` line 12 / line 46: `ARTIFACT="$WORKDIR/tmp/draft-review.md"`;
  `rm -f "$ARTIFACT"` before every run. A review of PR A destroys the draft of
  PR B on the same workstation — the same clobber FR-960 fixed for the judge
  on 2026-09-02.
- PR #633 (FR-1022, 2026-09-06): CI job `test (3.13)` fails
  `test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes` —
  the judge doctrine gained the sentinel bullet, the ramp mirror did not.
