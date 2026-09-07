# Feature Request: Review round sentinel — the third review is not a model call

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged 2026-09-07 — APPROVED WITH REVISIONS (round 1, [judgement](FR-1023-review-round-sentinel.judgement.md)); R-1..R-3 folded; awaiting human review of the folded plan (C-1, C-7) before enforcement. Research complete (4 of 5 personas, 2026-09-06). Stacked on FR-1022 (PR #633): enforcement base must carry exit code 77, REQ-YG-668 under CAP-211, and the FR-1022 doctrine bullet (C-2).
**Effort:** 0.5 days
**Requested:** 2026-09-06
**First consumer / first event:** the next agent session that runs
`scripts/review.sh <pr> <fr>` on an FR whose adjacent `<fr>.review.md`
already records two review rounds. Today that run launches a third model
review and the review→judge ping-pong continues; after this FR it receives a
fixed verdict and stops. Second consumer: the reviewer in round 2, who for
the first time can read what round 1 said.
**Research:** [FR-1023.research.md](FR-1023.research.md) — brief
`feature-requests/research-briefs/review-round-sentinel.md`, run 2026-09-06,
4 of 5 personas executed (data_process failed schema validation on its own
`solution_class` field; its finding — same class — is recorded in the
failure line). All four converge on the class (wrapper-written per-FR
record, shell count before the model call) and split on the threshold
(3, 3, 1, unstated); the FR selects 2 and dispositions both variants under
Alternatives.
**Prior art:** [FR-1022-judge-round-sentinel.md](FR-1022-judge-round-sentinel.md)
— the judge half of the same loop; this FR is its review counterpart and
copies its shape (count → fixed text → exit 77 → no override). Differs in
one respect: the judge counts a record the agent promotes; the review has no
such record, so the wrapper writes it (see Problem).
[FR-960-claude-judge-variant.md](FR-960-claude-judge-variant.md) — gave the
judge a per-backend-per-FR draft path; the review draft path is still the
single clobbered `tmp/draft-review.md`. Parked, not in scope (Alternatives).
[FR-1004-retire-outsider-ledger.md](FR-1004-retire-outsider-ledger.md) —
retired a committed file that every PR appended to. The file this FR
introduces is per FR, mutated only by that FR's own PRs: the `.judgement.md`
class, not the ledger class. Distinguished, not contradicted.
[FR-865-ramp-installer.md](FR-865-ramp-installer.md) —
`.github/skills/review-pr/doctrine.md` is a byte-exact mirror of a ramp
asset; any doctrine edit here re-copies the mirror (PR #633 is failing CI
for omitting exactly this on the judge side).
[FR-1013-chaplain-doctrine-sweep.md](FR-1013-chaplain-doctrine-sweep.md) —
REJECTED; the witnessed incident (three review rounds, zero durable review
records), not a competing solution.

## Summary

`scripts/review.sh` gains two mechanical steps, both in the wrapper, none
in the graph or prompt:

1. **Record.** After a conforming draft passes the artifact contract, the
   wrapper appends the draft under a round heading to `<fr>.review.md`
   (adjacent to the FR, same lifecycle as `<fr>.judgement.md`). The human
   commits it with the fold, as they commit the judgement.
2. **Stop.** Before taking the lock, the wrapper counts round headings in
   that file. Zero or one: the graph runs (round 1, round 2; round number on
   stderr). Two or more: no model is launched, no lock is taken; the wrapper
   writes a fixed line to the draft path and exits 77:

   ```
   **Merge verdict:** Not approved — Operator: Two model reviews were not enough. The third read is the human's: merge on your own judgement, or close the PR and re-file the FR shorter.
   ```

   This is the binding sentence (R-1; operator Q-1 default accepted).
   Replacing it is a material amendment that re-runs the judge. No flag or
   variable bypasses the sentinel.

Combined with FR-1022, one FR file can consume at most two judge rounds and
two review rounds of model time. FR-1013 consumed seven.

## Value Statement

Agent sessions stop ping-ponging between reviewer and judge: the third
review on any FR is the operator's sentence, every time, and round 2 can see
round 1 — so the only moves left are the human's, and they are made with the
record in front of them.

## Problem

The reviewer is a model; findings scale with text read; folding adds text.
FR-1022 states this for the judge and caps it. The review half is uncapped,
and worse: it has no record to count.

Raw record (main, 2026-09-06):

- `scripts/review.sh:12,46` — the draft path is the fixed `tmp/draft-review.md`,
  git-ignored, deleted with `rm -f` at the start of every run for any PR.
- FR-1013: reviews on PR #617 (7 findings), PR #627 (6), PR #627 (1). GitHub
  holds **0** review objects and **0** review comments on either PR; the
  three rounds survive only as "Review of PR #627 … folded" prose inside the
  FR. FR-1004's status line says "three review rounds enforced" — a phrase.
- `reference/command-book.md` entry 11 names "fix commits / disposition
  comments on the PR" as the durable record. The witnessed rounds produced
  neither in countable form.

A wrapper cannot count prose. So the sentinel needs a substrate before it
needs a threshold, and the substrate cannot depend on the agent choosing to
record — the agent in the loop is the one with the incentive to skip it.
That is why the wrapper writes the record here, where the judge leaves
promotion to the agent: the judge's record already existed by convention;
the review's never did.

## Ideal Result

A reviewer that runs at most twice per FR file, whose rounds leave a
committed, per-FR, human-readable trail the second round can read, and
whose third invocation is the operator's sentence delivered by the shell.
The merge decision was always the human's; after this FR the wrapper
returns it to them at a fixed, known moment. Nothing else in the review
route changes.

## Proposed Solution

### `scripts/review.sh` — exact order

1. usage / FR-existence (exit 64 / 66) — unchanged
2. `REVIEW_EXECUTION` re-entry guard (exit 70) — unchanged, still wins
3. `mkdir -p "$WORKDIR/tmp"`; round count — **new**
4. sentinel write and exit 77 when count ≥ 2 — **new**
5. lock (73 / 75), executor resolution (69), graph run — unchanged
6. artifact contract (65) — unchanged
7. append round record to `<fr>.review.md` — **new**; then exit 0

```bash
# FR-1023 round sentinel: two recorded review rounds on this FR file → the
# third review is fixed text, not a model call. No override exists.
RECORD="${FR_PATH%.md}.review.md"
ROUND=0
[ -f "$RECORD" ] && ROUND=$(grep -c '^## Review round [0-9][0-9]* — ' "$RECORD")
if [ "$ROUND" -ge 2 ]; then
  printf '%s\n' "**Merge verdict:** Not approved — Operator: Two model reviews were not enough. The third read is the human's: merge on your own judgement, or close the PR and re-file the FR shorter." > "$ARTIFACT"
  echo "review.sh: round $((ROUND + 1)) on $FR_PATH — sentinel verdict written: $ARTIFACT (no model run; human exits: merge on your own read, or close the PR and re-file a shorter FR)" >&2
  exit 77
fi
echo "review.sh: round $((ROUND + 1)) on $FR_PATH" >&2
```

After the artifact contract passes (step 7):

```bash
# FR-1023: the wrapper, not the agent, records the round (the review had no
# durable record before this; FR-1013 left three rounds as prose). The
# draft is model text — untrusted — so every line of it is quoted (R-2, C-4);
# only the wrapper's own unquoted heading can ever match the count grammar.
[ -f "$RECORD" ] || printf '# Review record: %s\n' "$(basename "$FR_PATH")" > "$RECORD"
{
  printf '\n## Review round %d — PR %s — %s\n\n' "$((ROUND + 1))" "$PR" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sed 's/^/> /' "$ARTIFACT"
} >> "$RECORD"
echo "review.sh: round $((ROUND + 1)) recorded in $RECORD (commit it with the fold)" >&2
```

Decisions, with the alternative each rejects:

- **Count the wrapper's own heading grammar**, not `**Merge verdict:**`
  lines, and **quote every appended draft line with `> `** (R-2). The
  drafts are free text a model writes; the headings are text the wrapper
  writes. Quoting makes the provenance claim true mechanically: a draft
  body containing `## Review round 99 — PR 999 — 2026-01-01T00:00:00Z` at
  column zero lands in the record as `> ## Review round 99 …` and cannot
  increment the count (AC-08).
- **Full draft appended, not line one.** Line one alone gives a count; the
  full draft gives round 2 its input and gives the FR the durable review
  record it never had. The cost is file length the human reads, which is
  the judgement file's cost too.
- **The sentinel round is not recorded.** No model ran; nothing to record;
  the file stays at two rounds and every later run returns the same exit.
- **Exit 77 reused from FR-1022** — same meaning in both wrappers: "sentinel
  verdict written, no model run". A caller distinguishing the two reads the
  script name in stderr.
- **Uncommitted record in a discarded worktree is lost.** Accepted: a round
  whose fold was never committed led nowhere; the next PR on that FR starts
  its own count from what was committed. The record travels with the fold.

### Doctrine and documentation

- `.github/skills/review-pr/doctrine.md` — one bullet at the end of "Review
  discipline", stating the record file, the two-round cap, the exact sentinel
  line, exit 77, the two human exits, and that the record is the durable
  review artifact. **Re-copy `ramp/assets/tier2/github/skills/review-pr/doctrine.md`
  in the same commit** (FR-865 mirror; AC-10).
- Input closure (same bullet): the reviewer MAY read `<fr>.review.md`; in
  round 2 it SHOULD, and should say which round-1 findings it re-checked.
- `.github/skills/review-pr/adapters/README.md` — one paragraph under the
  operator command: exit 77, the sentinel, the record file.
- `reference/command-book.md` entry 11 — durable column gains
  `feature-requests/FR-NNNN-<slug>.review.md`; the check column gains
  `grep -c '^## Review round' <fr>.review.md`.
- `adapters/graph.yaml` and `adapters/prompts/review.yaml` are not touched
  (NC-412; AC-10).

### Tests — `tests/unit/test_fr758_judge_review_wrappers.py`

Reuse `_run`, `_write_stub`, `fr_file`. New marker stub for the review side
(leaves `tmp/executor-ran`). Each test tagged `@pytest.mark.req("REQ-YG-669")`
(free on main and on the FR-1022 branch at filing — re-grep immediately
before allocation). REQ-YG-669 is added to
`capabilities/CAP-211-sole-route-judge-review.yaml` and `ARCHITECTURE.md`
regenerated. No new CAP.

## Acceptance Criteria

Binding set per judgement R-3 (replaces the originally filed AC-01..AC-14).
"The sentinel line" is the exact `**Merge verdict:** Not approved — Operator:
…` line in the Summary.

- [ ] AC-01: With no adjacent `.review.md`, the stubbed executor runs once,
      the wrapper exits 0, stderr contains `round 1`, and `<fr>.review.md`
      contains exactly one wrapper heading matching
      `^## Review round 1 — PR 123 — ` followed by the complete stub draft
      with every line prefixed by `> `.
- [ ] AC-02: With one recorded round, the executor runs once, exits 0, stderr
      contains `round 2`, and the record holds exactly two wrapper headings;
      every byte that existed before the run is unchanged.
- [ ] AC-03: With two recorded rounds, the wrapper exits 77; the executor
      marker and review lock are absent; `tmp/draft-review.md` consists
      exactly of the sentinel line plus one newline; and `<fr>.review.md` is
      byte-identical to before the run.
- [ ] AC-04: Two recorded rounds carrying different PR numbers, 617 and 627,
      produce the AC-03 result, proving the count is per FR file.
- [ ] AC-05: With two recorded rounds and `REVIEW_EXECUTION=1`, the existing
      re-entry contract wins: exit 70, no sentinel artifact, no executor
      marker, no lock, and an unchanged record.
- [ ] AC-06: Missing-FR exit 66 and usage exit 64 win before round
      processing: no sentinel artifact, no executor marker, no lock, and no
      record write.
- [ ] AC-07: When the graph produces no artifact, an empty artifact, or a
      draft whose first line is not `**Merge verdict:**`, the wrapper exits
      65 and appends nothing.
- [ ] AC-08: A conforming draft containing the exact string
      `## Review round 99 — PR 999 — 2026-01-01T00:00:00Z` at column zero in
      its body is recorded with that line prefixed by `> `; the next
      invocation counts only the wrapper heading and reports round 2.
      Indented, quoted, partial, and `**Merge verdict:**` body lines likewise
      do not increment the round.
- [ ] AC-09: Setting an otherwise unused `REVIEW_FORCE=1` or passing an
      extra `--force` argument does not alter the AC-03 result.
- [ ] AC-10: The doctrine rule, adapter README, and command-book entry 11
      agree on the record format, two-round cap, exit 77, the exact sentinel
      line, two human exits, and advisory status.
- [ ] AC-11: `tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes`
      passes, and `git diff --exit-code <base> -- .github/skills/review-pr/adapters/graph.yaml .github/skills/review-pr/adapters/prompts/review.yaml`
      succeeds.
- [ ] AC-12: New tests live in `tests/unit/test_fr758_judge_review_wrappers.py`,
      each is tagged `@pytest.mark.req("REQ-YG-669")`, and the committed RED
      test precedes the GREEN implementation commit.
- [ ] AC-13: REQ-YG-669 appears under CAP-211 in both `ARCHITECTURE.md` and
      `capabilities/CAP-211-sole-route-judge-review.yaml`;
      `python scripts/req_coverage.py --strict` passes; and
      `pytest tests/unit/test_fr758_judge_review_wrappers.py -q --no-cov`
      passes without a real review graph.
- [ ] AC-14: The changelog fragment exists, and the FR-1023 diary entry
      contains `**Seed:**`.

## Alternatives Considered

- **Count PR comments via `gh`** (command-book substrate) — rejected: needs
  network inside the wrapper; FR-1013's three rounds posted zero comments,
  so the count would have been 0; per-FR counting across PRs needs a search.
- **Agent-promoted `.review.md`** (exact judge parity) — rejected: the
  review record never existed by convention, and the agent in the loop is
  the party with the incentive to skip promotion. The wrapper writes; the
  human commits. Revisit if wrapper-written tracked files prove hostile in
  worktree flows.
- **Count in `.judgement.md`** — rejected: mixes two records; the judge
  sentinel would miscount.
- **Threshold 1 (block the second review)** (Subtractionist persona) —
  rejected for now: FR-1013's round 2 found six real items, half of them
  defects introduced by folding round 1; round 2 is the fold check. Parity
  with FR-1022's choice.
- **Threshold 3 (block the fourth review)** (os_infra and yamlgraph_native
  personas) — rejected: FR-1013's review 3 found one item and the operator
  closed the PR after it; a cap that permits the round the operator stopped
  at is not a cap. FR-1022 chose 2 for the judge on the same evidence.
- **Little-loops `.iter_counter` per artifact** (librarian) — same class as
  the selected design; confirms the count belongs in a per-artifact file
  read at the loop boundary, not in the loop body.
- **Per-PR draft path `tmp/draft-review-<pr>-<slug>.md`** (FR-960 analogue)
  — parked as its own FR; the record file removes the reason to keep drafts
  in `tmp/`, and the stub harness pins the current path.
- **Prompt-level refusal** — rejected: NC-412, and FR-1022's
  `prompt_as_mechanism` trap.
- **Override flag** — rejected: `--no-verify` by another name; the human
  exits already exist.

## Related

- `scripts/review.sh`, `.github/skills/review-pr/doctrine.md`,
  `.github/skills/review-pr/adapters/README.md`, `reference/command-book.md`
- `ramp/assets/tier2/github/skills/review-pr/doctrine.md` (mirror)
- `tests/unit/test_fr758_judge_review_wrappers.py`
- `docs/diary/2026-09-06-reflection-fr-1022-the-count-the-model-cannot-argue-with.md`
  (the Seed this FR answers)

## Judgement (2026-09-07, round 1)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1023-review-round-sentinel.judgement.md](FR-1023-review-round-sentinel.judgement.md)
(sole route, `scripts/judge.sh`, backend copilot, from the stacked worktree
on branch commit `bf7a85bc`; the FR-1022 sentinel reported `round 1`).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Q-1..Q-3 left the sentinel sentence and doctrine surface provisional; status line stale | Folded: operator defaults recorded below; sentence made binding; status line updated |
| R-2 | "Wrapper-only heading provenance" was a claim, not a mechanism — appended model text could match the heading grammar | Folded: every appended draft line is quoted with `> ` (`sed 's/^/> /'`); AC-01/02/08 specify the quoted body; C-4 treats review text as untrusted |
| R-3 | AC set replaced with the binding AC-01..AC-14 | Folded verbatim |

**Purge list:** the "provisional sentence" wording; the unquoted `cat "$ARTIFACT"` append; the pre-fold AC-08 ("inside a body") wording.

**Scope frozen:** D-1..D-10 as listed in the judgement. Not authorized:
edits to `adapters/graph.yaml` or `adapters/prompts/review.yaml`; a new
capability; a second counter file; per-PR draft paths; prompt-level refusal;
override flag or variable; automatic commits, PR comments, merge decisions,
FR rejection, or re-filing; changes to judge-round behaviour; rewriting
historical review or judgement records.

### Questions for the human (as options, or 'none')

1. **Q-1 The fixed sentence.** (a) the drafted sentence — *default*;
   (b) the operator supplies their own. **Operator answer (2026-09-07):**
   sequence "judge, docs pr, outsider" given without a sentence → (a)
   accepted by default. Replacing it later is a material amendment that
   re-runs the judge (round 2 of this file).
2. **Q-2 Who writes the record.** (a) the wrapper appends after a
   conforming run — *default, as drafted*; (b) the agent promotes.
   **Answer:** (a), by the same default.
3. **Q-3 Doctrine surface.** (a) one bullet in `review-pr/doctrine.md`
   plus ramp mirror re-copy — *default*; (b) adapter README only.
   **Answer:** (a), by the same default (D-2, D-3).
4. **C-7 human review of this folded FR is the GATE** before enforcement.
   A `merge`-book verdict word on the doc PR suffices.
